#!/bin/bash
# Start bench-1 baseline experiment in background

echo "Starting bench-1 baseline experiment..."
echo "This will run for ~14 hours and cost ~\$62"
echo ""
echo "Monitor with:"
echo "  tail -f experiment.log"
echo ""
echo "Check progress with:"
echo "  uv run python check_progress.py"
echo ""

# Run in background with nohup and caffeinate (prevents sleep)
nohup caffeinate -i uv run python run.py > experiment.log 2>&1 &

PID=$!
echo "Started with PID: $PID"
echo "Log file: experiment.log"
echo ""
echo "caffeinate is preventing system sleep"
echo ""
echo "To stop: kill $PID"
