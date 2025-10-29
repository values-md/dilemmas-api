#!/bin/bash
set -e

echo "=========================================="
echo "VALUES.md Dilemmas API - Starting"
echo "=========================================="

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "ERROR: DATABASE_URL environment variable is not set"
    exit 1
fi

echo "Database URL: ${DATABASE_URL%%:*}://****" # Show only protocol for security

# Run database migrations
echo ""
echo "Running database migrations..."
uv run alembic upgrade head

if [ $? -eq 0 ]; then
    echo "✓ Migrations applied successfully"
else
    echo "✗ Migration failed!"
    exit 1
fi

# Start the FastAPI server
echo ""
echo "Starting FastAPI server on port 8080..."
echo "=========================================="

# Activate virtual environment and run uvicorn directly
source /app/.venv/bin/activate
exec uvicorn dilemmas.api.app:app --host 0.0.0.0 --port 8080
