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


if __name__ == "__main__":
    unittest.main()
