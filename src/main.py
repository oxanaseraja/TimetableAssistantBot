"""
Main entry point for TimetableAssistantBot.
"""
import asyncio
import sys
from pathlib import Path

# Load .env file if it exists (before any other imports)
try:
    from dotenv import load_dotenv
    # Try to load .env from project root (parent of src/)
    project_root = Path(__file__).parent.parent
    env_path = project_root / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    # Also try .env in src/ directory
    src_env_path = Path(__file__).parent / ".env"
    if src_env_path.exists():
        load_dotenv(src_env_path)
except ImportError:
    # python-dotenv not installed, skip .env loading
    pass

# Add src directory to Python path for imports
src_dir = Path(__file__).parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from adapters.telegram.adapter import main as adapter_main


if __name__ == "__main__":
    # Determine config path
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    else:
        # Default: configuration.yaml in src/ directory
        script_dir = Path(__file__).parent
        config_path = script_dir / "configuration.yaml"
    
    # Run adapter
    asyncio.run(adapter_main(str(config_path)))
