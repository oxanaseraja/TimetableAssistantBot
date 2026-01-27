"""
Telegram event to CoreMessageEvent mapping.
Specification: TELEGRAM_ADAPTER.md §3, ADAPTER_CONTRACTS.md §2.3
"""
import hashlib
import logging
from datetime import datetime, timezone
from typing import Optional
from telegram import Update
from core.contracts import CoreMessageEvent

logger = logging.getLogger(__name__)


def map_telegram_update(update: Update) -> Optional[CoreMessageEvent]:
    """
    Convert Telegram Update to CoreMessageEvent.
    
    Args:
        update: Telegram Update object
    
    Returns:
        CoreMessageEvent or None if message is not valid
    """
    # Handle message or edited message
    message = update.message or update.edited_message
    if not message or not message.text:
        return None
    
    # Get platform IDs
    telegram_chat_id = str(message.chat.id)
    telegram_user_id = str(message.from_user.id) if message.from_user else None
    telegram_message_id = str(message.message_id)
    
    if not telegram_user_id:
        return None
    
    # Compute internal IDs using SHA256
    internal_message_id = hashlib.sha256(
        f"{telegram_chat_id}:{telegram_message_id}".encode()
    ).hexdigest()
    
    internal_user_id = hashlib.sha256(
        f"telegram:{telegram_user_id}".encode()
    ).hexdigest()
    
    internal_channel_id = hashlib.sha256(
        f"telegram:{telegram_chat_id}".encode()
    ).hexdigest()
    
    # Determine if this is an edit
    is_edit = update.edited_message is not None
    
    # Get timestamp (make it timezone-aware UTC)
    # message.date should always be present per Telegram API, but handle gracefully
    # Specification: ADAPTER_CONTRACTS.md §2.3 - Message Timestamp Requirement
    if not message.date:
        # If date is missing, reject message (violates determinism if we use datetime.now())
        logger.debug(f"Message {telegram_message_id} discarded: missing timestamp (per ADAPTER_CONTRACTS.md §2.3)")
        return None
    
    # Use astimezone() instead of replace() to properly convert timezone
    # message.date from Telegram is already timezone-aware, replace() could create incorrect time
    timestamp_utc = message.date.astimezone(timezone.utc)
    
    return CoreMessageEvent(
        internal_message_id=internal_message_id,
        internal_user_id=internal_user_id,
        internal_channel_id=internal_channel_id,
        text=message.text,
        is_edit=is_edit,
        timestamp_utc=timestamp_utc
    )
