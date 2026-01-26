#!/bin/bash
# Stop Coding Environment Services
# This script stops the MCP Server and CWS services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PIDS_DIR="$SCRIPT_DIR/.pids"

# Function to print status messages
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Stopping Coding Environment Services${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if PIDs directory exists
if [ ! -d "$PIDS_DIR" ]; then
    print_warning "PIDs directory not found. Services may not be running."
    exit 0
fi

# Stop MCP Server
if [ -f "$PIDS_DIR/mcp.pid" ]; then
    MCP_PID=$(cat "$PIDS_DIR/mcp.pid")
    if kill -0 "$MCP_PID" 2>/dev/null; then
        print_status "Stopping MCP Server (PID: $MCP_PID)..."
        kill "$MCP_PID" 2>/dev/null || true
        sleep 1
        # Force kill if still running
        if kill -0 "$MCP_PID" 2>/dev/null; then
            print_warning "MCP Server did not stop gracefully, forcing termination..."
            kill -9 "$MCP_PID" 2>/dev/null || true
        fi
        print_success "MCP Server stopped"
    else
        print_warning "MCP Server process (PID: $MCP_PID) is not running"
    fi
    rm -f "$PIDS_DIR/mcp.pid"
else
    print_warning "MCP Server PID file not found"
fi

# Stop CWS
if [ -f "$PIDS_DIR/cws.pid" ]; then
    CWS_PID=$(cat "$PIDS_DIR/cws.pid")
    if kill -0 "$CWS_PID" 2>/dev/null; then
        print_status "Stopping CWS (PID: $CWS_PID)..."
        kill "$CWS_PID" 2>/dev/null || true
        sleep 1
        # Force kill if still running
        if kill -0 "$CWS_PID" 2>/dev/null; then
            print_warning "CWS did not stop gracefully, forcing termination..."
            kill -9 "$CWS_PID" 2>/dev/null || true
        fi
        print_success "CWS stopped"
    else
        print_warning "CWS process (PID: $CWS_PID) is not running"
    fi
    rm -f "$PIDS_DIR/cws.pid"
else
    print_warning "CWS PID file not found"
fi

# Clean up PIDs directory if empty
if [ -d "$PIDS_DIR" ] && [ -z "$(ls -A "$PIDS_DIR")" ]; then
    rmdir "$PIDS_DIR" 2>/dev/null || true
fi

echo ""
print_success "All services stopped"
echo ""
