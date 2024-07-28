#!/bin/bash

# Function to handle the keyboard interrupt
cleanup() {
    echo "Caught keyboard interrupt. Killing all child processes..."
    for pid in ${pids[@]}; do
        kill $pid 2>/dev/null
    done
    exit 1
}

# Trap keyboard interrupt (Ctrl+C)
trap cleanup SIGINT

# Array to store process IDs
pids=()

# Activate virtual environment and start FastAPI app
source ./trustlehub-env/bin/activate
fastapi dev src/app.py &
pids+=($!)

# Start frontend
cd ./src/frontend && npm start &
pids+=($!)

# Start Node.js backend
cd ../node_backend && node server.js &
pids+=($!)

# Wait for all processes to complete
wait
