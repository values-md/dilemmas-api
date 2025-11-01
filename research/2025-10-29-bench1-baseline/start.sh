#!/bin/bash
# Start bench-1 baseline experiment in background

echo "Starting bench-1 baseline experiment..."
echo "This will run for ~14 hours and cost ~\$62"
echo ""
echo "Monitor with:"
echo "  tail -f experiment.log"
echo "  tail -f logs/experiment_debug.log"
echo ""
echo "Check progress with:"
echo "  uv run python check_progress.py"
echo ""

# Load .env file from project root (2 levels up)
PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
if [ -f "$PROJECT_ROOT/.env" ]; then
    echo "Loading environment from $PROJECT_ROOT/.env"
    set -a
    source "$PROJECT_ROOT/.env"
    set +a
else
    echo "Warning: .env file not found at $PROJECT_ROOT/.env"
fi

# Run in background with nohup and caffeinate (prevents sleep)
nohup caffeinate -i uv run python run.py > experiment.log 2>&1 &

PID=$!
echo "Started with PID: $PID"
echo "Log file: experiment.log"
echo ""
echo "caffeinate is preventing system sleep"
echo ""
echo "To stop: kill $PID"
