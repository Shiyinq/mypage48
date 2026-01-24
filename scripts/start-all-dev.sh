#!/bin/bash

# Parse command line arguments
if [ -d ".venv" ]; then
    echo "Activating .venv..."
    source .venv/bin/activate
fi

OPEN_BROWSER=false
for arg in "$@"; do
    case $arg in
        --open)
            OPEN_BROWSER=true
            shift
            ;;
    esac
done

# Kill any process running on port 8000 (Backend) to prevent "Address already in use"
if lsof -i :8000 -t >/dev/null; then
    echo "Port 8000 is in use. Killing existing process..."
    lsof -i :8000 -t | xargs kill -9
fi

# Flag to prevent cleanup from running multiple times
CLEANUP_DONE=false

# Function to kill background processes on exit
cleanup() {
    if [ "$CLEANUP_DONE" = true ]; then
        return
    fi
    CLEANUP_DONE=true
    echo ""
    echo "Stopping all services..."
    # Kill all child processes
    pkill -P $$ 2>/dev/null
    wait 2>/dev/null
    echo "All services stopped."
    exit 0
}

# Trap SIGINT (Ctrl+C) and call cleanup
trap cleanup SIGINT SIGTERM

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

# Open browser if --open flag is provided
if [ "$OPEN_BROWSER" = true ]; then
    echo "Opening browser in 3 seconds..."
    (
        sleep 3
        open "http://localhost:5173"
    ) &
fi

# Wait for all background processes
wait
