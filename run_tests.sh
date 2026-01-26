#!/bin/bash
# Run all tests

# Add src directory to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# Force unbuffered output (prevents hanging with tail/pipe)
export PYTHONUNBUFFERED=1

# Run tests with unbuffered flag
# Note: Always use -u flag for unbuffered output when piping to tail/head
python -u -m unittest discover -s tests -p "test_*.py" -v

# Alternative: using pytest
# python -u -m pytest tests/ -v

# To see last N lines, use:
# python -u -m unittest discover -s tests -p "test_*.py" -v 2>&1 | python3 -c "import sys; lines = sys.stdin.readlines(); print(''.join(lines[-10:]))"
