"""
Telegram adapter - main adapter implementation.
Specification: TELEGRAM_ADAPTER.md
"""
import asyncio
import logging
import json
import os
from collections import OrderedDict
from pathlib import Path
from typing import Dict, Set, Optional
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from telegram.error import TelegramError

from core.processor import process
from core.contracts import CoreConfig, CoreMessageEvent
from .config_loader import load_config, build_core_config, validate_telegram_config
from .event_mapping import map_telegram_update
from .formatter import format_display_block_with_cities, load_cities_index, load_cities_data
from .user_loader import load_users, get_user_profile, get_channel_context


# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class TelegramAdapter:
    """Telegram adapter for TimetableAssistantBot."""
    
    def __init__(self, config_path: str):
        """
        Initialize adapter.
        
        Args:
            config_path: Path to configuration.yaml
        """
        self.config_path = config_path
        self.config_dict = {}
        self.core_config: Optional[CoreConfig] = None
        self.telegram_config = {}
        self.data_config = {}
        self.users_data: Dict[str, dict] = {}
        self.cities_data = []
        self.city_index: Dict[str, str] = {}
        # Use OrderedDict for FIFO eviction guarantee (ADAPTER_CONTRACTS.md §4)
        self.processed_message_ids: OrderedDict[str, None] = OrderedDict()
        self.reply_mapping: OrderedDict[str, int] = OrderedDict()  # internal_message_id -> telegram_reply_id
        self.id_mapping: Dict[str, str] = {}  # platform_id -> internal_id (optional persistence)
        self.persistence_path: Optional[str] = None
        self.application: Optional[Application] = None
    
    def load_configuration(self):
        """Load and validate configuration."""
        self.config_dict = load_config(self.config_path)
        
        # Extract sections
        self.telegram_config = self.config_dict.get("telegram", {})
        self.data_config = self.config_dict.get("data", {})
        
        # Validate required fields
        token = self.telegram_config.get("token", "")
        if token.startswith("${") and token.endswith("}"):
            # Environment variable
            env_var = token[2:-1]
            token = os.environ.get(env_var, "")
        
        if not token:
            raise ValueError("telegram.token is required (set via config or environment variable)")
        
        chat_id = self.telegram_config.get("chat_id")
        if not chat_id:
            raise ValueError("telegram.chat_id is required")
        
        cities_path = self.data_config.get("cities_path")
        if not cities_path:
            raise ValueError("data.cities_path is required")
        
        users_path = self.data_config.get("users_path")
        if not users_path:
            raise ValueError("data.users_path is required")
        
        # Build core config
        self.core_config = build_core_config(self.config_dict)
        
        # Validate telegram config (max_lines, retry_attempts)
        validated_telegram = validate_telegram_config(self.config_dict)
        # Merge validated values into telegram_config
        self.telegram_config.update(validated_telegram)
        
        # Load data files
        self.load_data_files(cities_path, users_path)
        
        # Store token for application
        self.telegram_token = token
        self.telegram_chat_id = chat_id
        
        # Load persistence if configured (ADAPTER_CONTRACTS.md §4)
        self.persistence_path = self.telegram_config.get("persistence_path")
        if self.persistence_path:
            self.load_id_mapping()
    
    def load_data_files(self, cities_path: str, users_path: str):
        """Load cities.json and users.json."""
        # Check if cities file exists (empty list [] is valid state)
        path = Path(cities_path)
        if not path.exists():
            raise FileNotFoundError(f"Cities file not found: {cities_path}")
        
        # Load cities data (empty list [] is valid - system works with IANA IDs and offsets only)
        self.cities_data = load_cities_data(cities_path)
        
        # Build city index
        self.city_index = load_cities_index(cities_path)
        
        # Log if cities.json is empty (valid state per ADAPTER_CONTRACTS.md §5)
        if not self.city_index:
            logger.info("Loaded empty cities.json, city extraction disabled (system relies on IANA IDs and offsets only)")
        
        # Load users
        self.users_data = load_users(users_path)
    
    async def on_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle incoming message or edit.
        
        Specification: ADAPTER_CONTRACTS.md §4
        """
        # Map Telegram update to CoreMessageEvent
        event = map_telegram_update(update)
        if not event:
            return
        
        # Check for duplicates (unless it's an edit)
        if not event.is_edit:
            if event.internal_message_id in self.processed_message_ids:
                return  # Already processed
        
        # Handle edit: delete old reply
        if event.is_edit and event.internal_message_id in self.reply_mapping:
            old_reply_id = self.reply_mapping[event.internal_message_id]
            try:
                await context.bot.delete_message(
                    chat_id=update.effective_chat.id,
                    message_id=old_reply_id
                )
            except Exception as e:
                logger.warning(f"Failed to delete old reply: {e}")
        
        # Get user profile and channel context
        message = update.message or update.edited_message
        if not message or not message.from_user:
            return
        
        platform_user_id = f"telegram:{message.from_user.id}"
        platform_chat_id = str(message.chat.id)
        
        user_profile = get_user_profile(platform_user_id, self.users_data)
        channel_context = get_channel_context(platform_chat_id, self.users_data)
        
        # Call core processor
        try:
            display_block = process(
                event,
                user_profile,
                channel_context,
                self.city_index,
                self.core_config
            )
        except Exception as exc:
            # Invariant #12: Adapter suppresses all core errors
            logger.error(f"Core error: {exc}", exc_info=True)
            display_block = None
        
        # Send reply if display_block is not None
        if display_block is None:
            # Remove from reply mapping if it was there
            self.reply_mapping.pop(event.internal_message_id, None)
            return
        
        # Format and send reply
        try:
            formatted_text = format_display_block_with_cities(display_block, self.cities_data)
            
            # Cap to max_lines (default 5)
            # This is intentional UX design: limit applies after formatting to restrict actual response size
            # Telegram API limits visual lines, not internal entries
            max_lines = self.telegram_config.get("max_lines", 5)
            lines = formatted_text.split("\n")
            if len(lines) > max_lines:
                lines = lines[:max_lines]
                formatted_text = "\n".join(lines)
            
            # Send reply with retry logic (ADAPTER_CONTRACTS.md §2)
            retry_attempts = self.telegram_config.get("retry_attempts", 3)
            reply_message = None
            
            for attempt in range(retry_attempts):
                try:
                    reply_message = await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=formatted_text,
                        reply_to_message_id=message.message_id
                    )
                    break  # Success
                except Exception as e:
                    error_code = getattr(e, 'error_code', None)
                    # Check if it's a 4xx error (invalid token, forbidden) - don't retry
                    if error_code and 400 <= error_code < 500:
                        logger.error(f"Telegram API 4xx error (disabling adapter): {e}")
                        # Disable adapter per ADAPTER_CONTRACTS.md §2
                        await self.stop()
                        raise  # Re-raise to stop processing
                    
                    # Network/5xx error - retry with fixed backoff 500ms (ADAPTER_CONTRACTS.md §2)
                    if attempt < retry_attempts - 1:
                        await asyncio.sleep(0.5)  # Fixed backoff 500ms
                        logger.warning(f"Telegram API error (attempt {attempt + 1}/{retry_attempts}): {e}")
                    else:
                        # Last attempt failed
                        logger.error(f"Telegram API error after {retry_attempts} attempts: {e}")
                        raise
            
            if reply_message is None:
                return  # Failed to send
            
            # Update mappings
            self.reply_mapping[event.internal_message_id] = reply_message.message_id
            
            # Limit size of reply_mapping (max 10,000, drop oldest FIFO) (ADAPTER_CONTRACTS.md §4)
            if len(self.reply_mapping) > 10000:
                # Remove oldest entry (FIFO) - OrderedDict.popitem(last=False) removes first (oldest) item
                self.reply_mapping.popitem(last=False)
            
            if not event.is_edit:
                # Add to processed_message_ids (OrderedDict preserves insertion order)
                self.processed_message_ids[event.internal_message_id] = None
                
                # Limit size of processed_message_ids (max 10,000, drop oldest FIFO)
                # OrderedDict.popitem(last=False) removes oldest (first) item
                if len(self.processed_message_ids) > 10000:
                    self.processed_message_ids.popitem(last=False)
        
        except Exception as e:
            logger.error(f"Failed to send reply: {e}", exc_info=True)
    
    def setup_application(self):
        """Setup Telegram application with handlers."""
        # Create application
        self.application = Application.builder().token(self.telegram_token).build()
        
        # Create chat filter for configured chat_id
        chat_filter = filters.Chat(chat_id=int(self.telegram_chat_id))
        
        # Add message handler (handles both new messages and edits)
        # Filter: text messages (not commands) in the configured chat
        self.application.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND & chat_filter,
                self.on_message
            )
        )
    
    async def start(self):
        """Start the adapter."""
        logger.info("Starting Telegram adapter...")
        self.load_configuration()
        self.setup_application()
        
        # Start polling
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        
        logger.info("Adapter started and polling for updates")
    
    def load_id_mapping(self):
        """
        Load id_mapping from persistence file if exists.
        
        Specification: ADAPTER_CONTRACTS.md §4
        - Load on startup if file exists
        - Failure to load → ignored
        """
        if not self.persistence_path:
            return
        
        try:
            path = Path(self.persistence_path)
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Restore id_mapping if present
                    # Format: {"platform_id": "internal_id", ...}
                    if isinstance(data, dict):
                        self.id_mapping = data
                        logger.info(f"Loaded {len(self.id_mapping)} entries from persistence file")
        except Exception as e:
            # Failure to load → ignored per spec
            logger.warning(f"Failed to load persistence file {self.persistence_path}: {e}")
            self.id_mapping = {}
    
    def save_id_mapping(self):
        """
        Save id_mapping to persistence file.
        
        Specification: ADAPTER_CONTRACTS.md §4
        - Save on graceful shutdown
        - Failure to save → ignored
        """
        if not self.persistence_path:
            return
        
        try:
            path = Path(self.persistence_path)
            # Create parent directory if needed
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self.id_mapping, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {len(self.id_mapping)} entries to persistence file")
        except Exception as e:
            # Failure to save → ignored per spec
            logger.warning(f"Failed to save persistence file {self.persistence_path}: {e}")
    
    async def stop(self):
        """Stop the adapter gracefully."""
        # Save persistence before shutdown (ADAPTER_CONTRACTS.md §4)
        if self.persistence_path:
            self.save_id_mapping()
        
        if self.application:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
        logger.info("Adapter stopped")


async def main(config_path: str):
    """Main entry point for adapter."""
    adapter = TelegramAdapter(config_path)
    try:
        await adapter.start()
        # Keep running
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    finally:
        await adapter.stop()


if __name__ == "__main__":
    import sys
    import os
    
    # Default config path
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    else:
        # Assume config is in src/ directory
        script_dir = Path(__file__).parent.parent.parent
        config_path = script_dir / "configuration.yaml"
    
    asyncio.run(main(str(config_path)))
