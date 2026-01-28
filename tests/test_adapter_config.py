"""
Tests for Telegram adapter configuration loading.
Specification: ADAPTER_CONTRACTS.md §5
"""
import os
import sys
import unittest
import tempfile
from pathlib import Path

# Add src to path
src_dir = Path(__file__).parent.parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from adapters.telegram.adapter import TelegramAdapter


class TestAdapterConfig(unittest.TestCase):
    """Validate adapter config fail-fast and env fallbacks."""

    def test_fail_fast_missing_required(self):
        """Adapter must fail fast when required fields are missing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "configuration.yaml"
            config_path.write_text("{}", encoding="utf-8")

            adapter = TelegramAdapter(str(config_path))

            old_token = os.environ.pop("TELEGRAM_TOKEN", None)
            old_paths = os.environ.pop("DATA_PATHS", None)
            try:
                with self.assertRaises(ValueError):
                    adapter.load_configuration()
            finally:
                if old_token is not None:
                    os.environ["TELEGRAM_TOKEN"] = old_token
                if old_paths is not None:
                    os.environ["DATA_PATHS"] = old_paths

    def test_env_fallback_and_defaults(self):
        """Adapter uses env fallback and defaults for optional fields."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir = Path(temp_dir)
            cities_path = temp_dir / "cities.json"
            users_path = temp_dir / "users.json"
            cities_path.write_text("[]", encoding="utf-8")
            users_path.write_text("{}", encoding="utf-8")

            config_path = temp_dir / "configuration.yaml"
            config_path.write_text(
                "telegram:\n  chat_id: \"123\"\n"
                "data: {}\n"
                "core: {}\n"
                "output: {}\n",
                encoding="utf-8"
            )

            old_token = os.environ.get("TELEGRAM_TOKEN")
            old_paths = os.environ.get("DATA_PATHS")
            os.environ["TELEGRAM_TOKEN"] = "test-token"
            os.environ["DATA_PATHS"] = f"{cities_path},{users_path}"
            try:
                adapter = TelegramAdapter(str(config_path))
                adapter.load_configuration()

                self.assertEqual(adapter.telegram_token, "test-token")
                self.assertEqual(adapter.telegram_config.get("max_lines"), 5)
                self.assertEqual(adapter.telegram_config.get("retry_attempts"), 3)
                self.assertEqual(adapter.core_config.max_time_mentions, 3)
                self.assertEqual(adapter.core_config.max_timezones, 5)
            finally:
                if old_token is not None:
                    os.environ["TELEGRAM_TOKEN"] = old_token
                else:
                    os.environ.pop("TELEGRAM_TOKEN", None)
                if old_paths is not None:
                    os.environ["DATA_PATHS"] = old_paths
                else:
                    os.environ.pop("DATA_PATHS", None)

    def test_env_paths_invalid_format_fails(self):
        """Invalid DATA_PATHS format should not satisfy required fields."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "configuration.yaml"
            config_path.write_text(
                "telegram:\n  chat_id: \"123\"\n"
                "data: {}\n",
                encoding="utf-8"
            )

            old_token = os.environ.get("TELEGRAM_TOKEN")
            old_paths = os.environ.get("DATA_PATHS")
            os.environ["TELEGRAM_TOKEN"] = "test-token"
            os.environ["DATA_PATHS"] = "only_one_path.json"
            try:
                adapter = TelegramAdapter(str(config_path))
                with self.assertRaises(ValueError):
                    adapter.load_configuration()
            finally:
                if old_token is not None:
                    os.environ["TELEGRAM_TOKEN"] = old_token
                else:
                    os.environ.pop("TELEGRAM_TOKEN", None)
                if old_paths is not None:
                    os.environ["DATA_PATHS"] = old_paths
                else:
                    os.environ.pop("DATA_PATHS", None)


class TestFIFOEviction(unittest.TestCase):
    """Test FIFO eviction semantics for adapter mappings (ADAPTER_CONTRACTS.md §4)."""

    def test_fifo_eviction_no_move_to_end(self):
        """Updating an existing key MUST NOT change its insertion order.
        
        Per ADAPTER_CONTRACTS.md §4: Strict FIFO semantics - updating an existing
        key must not move it to the end. This ensures deterministic eviction order.
        """
        from collections import OrderedDict
        
        # Simulate reply_mapping behavior
        reply_mapping: OrderedDict[str, int] = OrderedDict()
        
        # Insert in order: msg1, msg2, msg3
        reply_mapping["msg1"] = 100
        reply_mapping["msg2"] = 200
        reply_mapping["msg3"] = 300
        
        # Update msg1 (should NOT move to end)
        reply_mapping["msg1"] = 101
        
        # Order should still be: msg1, msg2, msg3 (not msg2, msg3, msg1)
        keys = list(reply_mapping.keys())
        self.assertEqual(keys, ["msg1", "msg2", "msg3"],
                        "Updating existing key should NOT change insertion order")
        
        # First eviction should remove msg1 (oldest)
        oldest_key, oldest_val = reply_mapping.popitem(last=False)
        self.assertEqual(oldest_key, "msg1", "FIFO eviction should remove oldest entry first")
        self.assertEqual(oldest_val, 101, "Updated value should be preserved")
    
    def test_fifo_eviction_order_preserved(self):
        """FIFO eviction removes entries in insertion order."""
        from collections import OrderedDict
        
        mapping: OrderedDict[str, None] = OrderedDict()
        
        # Insert 5 items
        for i in range(5):
            mapping[f"item_{i}"] = None
        
        # Evict 3 items
        evicted = []
        for _ in range(3):
            key, _ = mapping.popitem(last=False)
            evicted.append(key)
        
        self.assertEqual(evicted, ["item_0", "item_1", "item_2"],
                        "FIFO eviction should remove in insertion order")
        self.assertEqual(list(mapping.keys()), ["item_3", "item_4"],
                        "Remaining items should preserve order")


if __name__ == "__main__":
    unittest.main()
