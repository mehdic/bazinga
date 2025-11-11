#!/bin/bash
#
# BAZINGA Dashboard Management Script
#
# Usage:
#   ./dashboard.sh start    - Start the dashboard server
#   ./dashboard.sh stop     - Stop the dashboard server
#   ./dashboard.sh restart  - Restart the dashboard server
#   ./dashboard.sh status   - Check if dashboard is running
#   ./dashboard.sh logs     - Tail the dashboard logs

set -e

DASHBOARD_PORT="${DASHBOARD_PORT:-53124}"
DASHBOARD_PID_FILE="/tmp/bazinga-dashboard.pid"
DASHBOARD_LOG_FILE="/tmp/bazinga-dashboard.log"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Check if dashboard is running
is_running() {
    if [ -f "$DASHBOARD_PID_FILE" ]; then
        PID=$(cat "$DASHBOARD_PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            return 0
        fi
    fi
    return 1
}

# Start dashboard
start_dashboard() {
    print_info "Starting BAZINGA Dashboard..."

    # Check if already running
    if is_running; then
        PID=$(cat "$DASHBOARD_PID_FILE")
        print_warning "Dashboard is already running (PID: $PID)"
        print_info "URL: http://localhost:$DASHBOARD_PORT"
        return 0
    fi

    # Check if port is in use
    if lsof -Pi :$DASHBOARD_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_error "Port $DASHBOARD_PORT is already in use by another process"
        print_info "Change port: export DASHBOARD_PORT=<new-port>"
        return 1
    fi

    # Check dependencies
    print_info "Checking Python dependencies..."
    if ! python3 -c "import flask, flask_sock, watchdog, anthropic" 2>/dev/null; then
        print_warning "Dependencies not installed. Installing..."
        pip3 install -q -r "$SCRIPT_DIR/requirements.txt"
        print_success "Dependencies installed"
    fi

    # Start server in background
    cd "$SCRIPT_DIR"
    python3 server.py > "$DASHBOARD_LOG_FILE" 2>&1 &
    DASHBOARD_PID=$!
    echo $DASHBOARD_PID > "$DASHBOARD_PID_FILE"

    # Wait for server to start
    sleep 2

    # Verify it started
    if is_running; then
        print_success "Dashboard started (PID: $DASHBOARD_PID)"
        echo ""
        print_info "🌐 Dashboard URL: http://localhost:$DASHBOARD_PORT"
        print_info "📋 View logs: tail -f $DASHBOARD_LOG_FILE"
        echo ""
        return 0
    else
        print_error "Failed to start dashboard"
        print_info "Check logs: cat $DASHBOARD_LOG_FILE"
        rm -f "$DASHBOARD_PID_FILE"
        return 1
    fi
}

# Stop dashboard
stop_dashboard() {
    print_info "Stopping BAZINGA Dashboard..."

    if ! is_running; then
        print_warning "Dashboard is not running"
        return 0
    fi

    PID=$(cat "$DASHBOARD_PID_FILE")

    # Try graceful shutdown first
    kill "$PID" 2>/dev/null || true

    # Wait up to 5 seconds for graceful shutdown
    for i in {1..5}; do
        if ! kill -0 "$PID" 2>/dev/null; then
            break
        fi
        sleep 1
    done

    # Force kill if still running
    if kill -0 "$PID" 2>/dev/null; then
        print_warning "Graceful shutdown failed, forcing..."
        kill -9 "$PID" 2>/dev/null || true
    fi

    rm -f "$DASHBOARD_PID_FILE"
    print_success "Dashboard stopped"
}

# Restart dashboard
restart_dashboard() {
    stop_dashboard
    sleep 1
    start_dashboard
}

# Show status
show_status() {
    if is_running; then
        PID=$(cat "$DASHBOARD_PID_FILE")
        print_success "Dashboard is running (PID: $PID)"
        echo ""
        print_info "🌐 URL: http://localhost:$DASHBOARD_PORT"
        print_info "📁 PID file: $DASHBOARD_PID_FILE"
        print_info "📋 Log file: $DASHBOARD_LOG_FILE"
        echo ""

        # Show process details
        print_info "Process details:"
        ps -p "$PID" -o pid,ppid,%cpu,%mem,etime,cmd 2>/dev/null || print_warning "Could not get process details"

        return 0
    else
        print_warning "Dashboard is not running"
        if [ -f "$DASHBOARD_PID_FILE" ]; then
            print_info "Cleaning up stale PID file..."
            rm -f "$DASHBOARD_PID_FILE"
        fi
        return 1
    fi
}

# Show logs
show_logs() {
    if [ ! -f "$DASHBOARD_LOG_FILE" ]; then
        print_warning "Log file not found: $DASHBOARD_LOG_FILE"
        return 1
    fi

    print_info "Tailing dashboard logs (Ctrl+C to stop)..."
    echo ""
    tail -f "$DASHBOARD_LOG_FILE"
}

# Main command handler
case "${1:-}" in
    start)
        start_dashboard
        ;;
    stop)
        stop_dashboard
        ;;
    restart)
        restart_dashboard
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    *)
        echo "BAZINGA Dashboard Management"
        echo ""
        echo "Usage: $0 {start|stop|restart|status|logs}"
        echo ""
        echo "Commands:"
        echo "  start    - Start the dashboard server"
        echo "  stop     - Stop the dashboard server"
        echo "  restart  - Restart the dashboard server"
        echo "  status   - Check if dashboard is running"
        echo "  logs     - Tail the dashboard logs"
        echo ""
        echo "Environment Variables:"
        echo "  DASHBOARD_PORT - Port to run on (default: 53124)"
        echo ""
        echo "Examples:"
        echo "  $0 start"
        echo "  $0 status"
        echo "  DASHBOARD_PORT=8080 $0 start"
        exit 1
        ;;
esac
