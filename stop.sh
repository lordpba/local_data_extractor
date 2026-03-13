#!/bin/bash

echo "=========================================="
echo "Stopping Local Data Extractor"
echo "=========================================="
echo ""

# Find and kill the Flask app process
echo "Looking for running instances..."
PIDS=$(pgrep -f "python.*src/app.py" || true)

if [ -z "$PIDS" ]; then
    echo "No running instances found."
else
    echo "Found instances with PID(s): $PIDS"
    echo "Killing processes..."
    pkill -f "python.*src/app.py"
    
    # Wait a moment and check if they are actually dead
    sleep 1
    if pgrep -f "python.*src/app.py" > /dev/null; then
        echo "⚠️  Some processes did not stop gracefully. Forcing kill..."
        pkill -9 -f "python.*src/app.py"
        echo "✅ Processes forcefully stopped."
    else
        echo "✅ Server stopped successfully."
    fi
fi
echo ""
