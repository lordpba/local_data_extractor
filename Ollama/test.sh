#!/bin/bash

echo "=========================================="
echo "Testing Ollama Data Extractor"
echo "=========================================="
echo ""

# Check if server is running
echo "Checking if server is running on http://localhost:5000..."
if ! curl -s http://localhost:5000/health > /dev/null; then
    echo "❌ Server is not running"
    echo "Start it with: python app.py"
    exit 1
else
    echo "✅ Server is running"
fi

# Test health endpoint
echo ""
echo "Testing /health endpoint..."
HEALTH_RESPONSE=$(curl -s http://localhost:5000/health)
echo "Response: $HEALTH_RESPONSE"

if echo "$HEALTH_RESPONSE" | grep -q "ok"; then
    echo "✅ Health check passed"
else
    echo "❌ Health check failed"
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ Basic tests passed!"
echo "=========================================="
echo ""
echo "Open http://localhost:5000 in your browser to use the web interface"
echo ""
