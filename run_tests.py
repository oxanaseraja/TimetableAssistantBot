#!/usr/bin/env python3
"""
Run tests and optionally show last N lines.
Usage: python run_tests.py [--last N]
"""
import sys
import subprocess
import os
from pathlib import Path

# Add src to path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

# Set unbuffered output
os.environ['PYTHONUNBUFFERED'] = '1'

# Parse arguments
show_last = None
if len(sys.argv) > 1 and sys.argv[1] == '--last':
    show_last = int(sys.argv[2]) if len(sys.argv) > 2 else 10

# Run tests
cmd = [
    sys.executable, '-u', '-m', 'unittest', 
    'discover', '-s', 'tests', '-p', 'test_*.py', '-v'
]

process = subprocess.Popen(
    cmd,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=0  # Unbuffered
)

# Collect output
output_lines = []
for line in process.stdout:
    print(line, end='', flush=True)
    output_lines.append(line)

process.wait()

# Show last N lines if requested
if show_last and output_lines:
    print("\n" + "="*50)
    print(f"Last {show_last} lines:")
    print("="*50)
    for line in output_lines[-show_last:]:
        print(line, end='')

sys.exit(process.returncode)
