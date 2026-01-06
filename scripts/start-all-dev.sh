#!/bin/bash

# Kill any process running on port 8000 (Backend) to prevent "Address already in use"
if lsof -i :8000 -t >/dev/null; then
    echo "Port 8000 is in use. Killing existing process..."
    lsof -i :8000 -t | xargs kill -9
fi

# Function to kill background processes on exit
cleanup() {
    echo "Stopping all services..."
    # Kill the entire process group
    kill 0 2>/dev/null
    exit
}

# Trap SIGINT (Ctrl+C) and call cleanup
trap cleanup SIGINT SIGTERM EXIT

# Start Backend
echo "Starting Backend..."
(
    source .venv/bin/activate
    # exec ensuring this process is replaced, so sending signal to group works better
    exec sh scripts/start-dev.sh
) &

# Start Frontend
echo "Starting Frontend..."
(
    cd frontend
    exec npm run dev
) &

# Wait for all background processes
wait
