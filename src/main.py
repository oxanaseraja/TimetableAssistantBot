"""
Main entry point for TimetableAssistantBot.
"""
import asyncio
import sys
from pathlib import Path

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
