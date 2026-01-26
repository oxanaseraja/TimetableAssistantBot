"""
Tests for Telegram event mapping.
Specification: TELEGRAM_ADAPTER.md §3
"""
import sys
import unittest
import hashlib
from pathlib import Path
from unittest.mock import Mock
from datetime import datetime, timezone

# Add src to path
src_dir = Path(__file__).parent.parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from adapters.telegram.event_mapping import map_telegram_update
from telegram import Update, Message, User, Chat


class TestEventMapping(unittest.TestCase):
    """Test Telegram to CoreMessageEvent mapping."""
    
    def create_mock_update(self, text: str, user_id: int = 123, chat_id: int = -1001, message_id: int = 555, is_edit: bool = False):
        """Create a mock Telegram Update."""
        user = Mock(spec=User)
        user.id = user_id
        
        chat = Mock(spec=Chat)
        chat.id = chat_id
        
        message = Mock(spec=Message)
        message.text = text
        message.from_user = user
        message.chat = chat
        message.message_id = message_id
        message.date = datetime(2026, 1, 25, 12, 0, 0, tzinfo=timezone.utc)
        
        update = Mock(spec=Update)
        if is_edit:
            update.edited_message = message
            update.message = None
        else:
            update.message = message
            update.edited_message = None
        
        return update
    
    def test_basic_message_mapping(self):
        """Test basic message mapping."""
        update = self.create_mock_update("Meeting at 10:30", user_id=123, chat_id=-1001, message_id=555)
        
        result = map_telegram_update(update)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.text, "Meeting at 10:30")
        self.assertFalse(result.is_edit)
        
        # Check internal IDs are SHA256 hashes
        expected_message_id = hashlib.sha256(f"-1001:555".encode()).hexdigest()
        expected_user_id = hashlib.sha256(f"telegram:123".encode()).hexdigest()
        expected_channel_id = hashlib.sha256(f"telegram:-1001".encode()).hexdigest()
        
        self.assertEqual(result.internal_message_id, expected_message_id)
        self.assertEqual(result.internal_user_id, expected_user_id)
        self.assertEqual(result.internal_channel_id, expected_channel_id)
    
    def test_edit_message_mapping(self):
        """Test edited message mapping."""
        update = self.create_mock_update("Meeting at 10:30", is_edit=True)
        
        result = map_telegram_update(update)
        
        self.assertIsNotNone(result)
        self.assertTrue(result.is_edit)
    
    def test_no_text_returns_none(self):
        """Test that message without text returns None."""
        update = self.create_mock_update(None)
        update.message.text = None
        
        result = map_telegram_update(update)
        
        self.assertIsNone(result)
    
    def test_no_user_returns_none(self):
        """Test that message without user returns None."""
        update = self.create_mock_update("Hello")
        update.message.from_user = None
        
        result = map_telegram_update(update)
        
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
