#!/bin/bash
set -e

echo "Building Docker image..."
docker build -t dilemmas-test .

echo ""
echo "Testing Docker image locally..."
echo "Starting container with SQLite (no DATABASE_URL required for test)"
echo ""

# Run with a dummy DATABASE_URL for testing
docker run --rm -p 8080:8080 \
  -e DATABASE_URL="sqlite:///./test.db" \
  -e OPENROUTER_API_KEY="test-key" \
  dilemmas-test

echo ""
echo "Container stopped."
