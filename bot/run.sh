#!/bin/bash

# TimetableAssistantBot - Telegram Adapter Entrypoint
# Usage: ./run.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Load environment variables if .env exists
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Check required environment variables
if [ -z "$TELEGRAM_TOKEN" ]; then
    echo "ERROR: TELEGRAM_TOKEN environment variable is not set"
    echo "Create a .env file with: TELEGRAM_TOKEN=your_token_here"
    exit 1
fi

# Run the bot
echo "Starting TimetableAssistantBot..."
python -m adapters.telegram.adapter
