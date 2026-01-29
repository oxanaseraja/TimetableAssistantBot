#!/bin/bash
# Run tests and show last N lines (works reliably on macOS)

# Add src directory to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# Force unbuffered output
export PYTHONUNBUFFERED=1

# Number of lines to show (default 10)
LINES=${1:-10}

# Run tests and show last N lines using Python (works better than tail on macOS)
python -u -m unittest discover -s tests -p "test_*.py" -v 2>&1 | python3 -c "import sys; lines = sys.stdin.readlines(); print(''.join(lines[-${LINES}:]), end='')"
