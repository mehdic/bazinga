#!/bin/bash
#
# BAZINGA Dashboard Test Script
#
# Tests the dashboard by creating sample coordination data
# and verifying the server can start.

set -e

echo "🧪 Testing BAZINGA Dashboard..."
echo ""

# Check if coordination folder exists
if [ ! -d "../bazinga" ]; then
    echo "⚠️  Coordination folder not found. Running init-orchestration.sh..."
    cd ..
    ./scripts/init-orchestration.sh
    cd dashboard
fi

# Check Python dependencies
echo "📦 Checking Python dependencies..."
if ! python3 -c "import flask, flask_sock, watchdog" 2>/dev/null; then
    echo "⚠️  Dependencies not installed. Installing..."
    pip3 install -q -r requirements.txt
    echo "✅ Dependencies installed"
else
    echo "✅ Dependencies already installed"
fi

# Test if port 53124 is available
echo ""
echo "🔍 Checking if port 53124 is available..."
if lsof -Pi :53124 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Port 53124 is already in use"
    echo "   Skipping server start test"
    echo "   You can manually test by stopping the running server and executing:"
    echo "   python3 server.py"
else
    echo "✅ Port 53124 is available"

    # Start server in background
    echo ""
    echo "🚀 Starting dashboard server..."
    python3 server.py > /tmp/bazinga-dashboard-test.log 2>&1 &
    SERVER_PID=$!

    # Wait for server to start
    sleep 3

    # Check if server is running
    if kill -0 $SERVER_PID 2>/dev/null; then
        echo "✅ Dashboard server started successfully (PID: $SERVER_PID)"
        echo ""
        echo "🌐 Dashboard URL: http://localhost:53124"
        echo "📋 Server logs: tail -f /tmp/bazinga-dashboard-test.log"
        echo ""
        echo "🧪 Test Steps:"
        echo "   1. Open http://localhost:53124 in your browser"
        echo "   2. Verify the dashboard loads"
        echo "   3. Check WebSocket connection status (top right)"
        echo "   4. Try refreshing the page"
        echo ""
        echo "Press Ctrl+C to stop the test server..."
        echo ""

        # Keep server running and tail logs
        trap "echo ''; echo '🛑 Stopping test server...'; kill $SERVER_PID 2>/dev/null; echo '✅ Test server stopped'; exit 0" INT TERM

        # Tail logs
        tail -f /tmp/bazinga-dashboard-test.log
    else
        echo "❌ Failed to start dashboard server"
        echo ""
        echo "📋 Check logs:"
        cat /tmp/bazinga-dashboard-test.log
        exit 1
    fi
fi

echo ""
echo "✅ Dashboard test complete!"
