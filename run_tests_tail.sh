#!/bin/bash
# Run tests with tail support (unbuffered output)

# Add src directory to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# Force unbuffered output
export PYTHONUNBUFFERED=1

# Run tests with unbuffered flag and pipe to tail
python -u -m unittest discover -s tests -p "test_*.py" -v 2>&1 | tail -${1:-30}
