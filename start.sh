#!/bin/bash
# QTs Support — bot startup script
# Run this on your AWS EC2 instance to start the bot

cd "$(dirname "$0")"

# Load .env if it exists
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Check TOKEN is set
if [ -z "$TOKEN" ]; then
    echo "[ERROR] TOKEN environment variable is not set. Create a .env file or export TOKEN=..."
    exit 1
fi

echo "[$(date)] Installing/updating dependencies..."
pip install -r requirements.txt -q

while true; do
    echo "[$(date)] Starting QTs Support bot..."
    python3 main.py
    EXIT_CODE=$?
    if [ $EXIT_CODE -eq 0 ]; then
        echo "[$(date)] Bot exited cleanly. Restarting in 5 seconds..."
    else
        echo "[$(date)] Bot crashed (exit code $EXIT_CODE). Restarting in 5 seconds..."
    fi
    sleep 5
done
