#!/bin/bash
# Setup and Run Coding Environment Script
# This script sets up the environment and runs only the coding environment components
# (CWS + MCP Server) independently from the main FastAPI application

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Paths
CWS_DIR="$SCRIPT_DIR/coding-workspace-service"
MCP_DIR="$(dirname "$SCRIPT_DIR")/mcp"
ASSISTANT_DIR="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$SCRIPT_DIR/venv"
PIDS_DIR="$SCRIPT_DIR/.pids"

# Default ports (can be overridden via environment variables)
MCP_PORT=${MCP_PORT:-8080}
CWS_PORT=${CWS_PORT:-9090}

# Default workspace root (can be overridden via environment variable)
WORKSPACE_ROOT=${WORKSPACE_ROOT:-"$ASSISTANT_DIR"}

# Default transport (can be overridden via environment variable)
TRANSPORT=${TRANSPORT:-websocket}

# Detect RunPod environment
# RunPod sets RUNPOD_POD_ID or has /workspace directory
if [ -n "$RUNPOD_POD_ID" ] || [ -d "/workspace" ] || [ -d "/runpod-volume" ]; then
    IS_RUNPOD=true
    # For RunPod, bind to 0.0.0.0 to allow port forwarding
    BIND_HOST="0.0.0.0"
else
    IS_RUNPOD=false
    # For local, localhost is fine
    BIND_HOST="localhost"
fi

# Allow override via environment variable
BIND_HOST=${BIND_HOST_OVERRIDE:-$BIND_HOST}

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Coding Environment Setup & Run${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

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

# Check Python version
print_status "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.10 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]); then
    print_error "Python 3.10 or higher is required. Found: Python $PYTHON_VERSION"
    exit 1
fi

print_success "Python $PYTHON_VERSION found"

# Check if required directories exist
print_status "Checking required directories..."
if [ ! -d "$CWS_DIR" ]; then
    print_error "CWS directory not found: $CWS_DIR"
    exit 1
fi

if [ ! -d "$MCP_DIR" ]; then
    print_error "MCP directory not found: $MCP_DIR"
    exit 1
fi

print_success "Required directories found"

# Check if virtual environment exists
print_status "Checking virtual environment..."
if [ ! -d "$VENV_DIR" ]; then
    print_warning "Virtual environment not found. Creating..."
    python3 -m venv "$VENV_DIR"
    print_success "Virtual environment created"
    VENV_CREATED=true
else
    print_success "Virtual environment already exists - skipping creation"
    VENV_CREATED=false
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Only upgrade pip and install dependencies if venv was just created
# or if user wants to update dependencies
if [ "$VENV_CREATED" = true ]; then
    # Upgrade pip
    print_status "Upgrading pip..."
    pip install --upgrade pip --quiet
    
    # Install CWS dependencies
    print_status "Installing CWS dependencies..."
    if [ -f "$CWS_DIR/requirements.txt" ]; then
        pip install -r "$CWS_DIR/requirements.txt" --quiet
        print_success "CWS dependencies installed"
    else
        print_error "CWS requirements.txt not found at $CWS_DIR/requirements.txt"
        exit 1
    fi
    
    # Install MCP server dependencies
    print_status "Installing MCP server dependencies..."
    if [ -f "$MCP_DIR/pyproject.toml" ]; then
        # Install MCP server in editable mode with app-management extras
        cd "$MCP_DIR"
        pip install -e ".[app-management]" --quiet
        cd "$SCRIPT_DIR"
        print_success "MCP server dependencies installed"
    else
        print_error "MCP pyproject.toml not found at $MCP_DIR/pyproject.toml"
        exit 1
    fi
    
    # Install CWS package in editable mode if pyproject.toml exists
    if [ -f "$CWS_DIR/pyproject.toml" ]; then
        print_status "Installing CWS package..."
        cd "$CWS_DIR"
        pip install -e . --quiet 2>/dev/null || pip install -r requirements.txt --quiet
        cd "$SCRIPT_DIR"
    fi
else
    print_status "Virtual environment already set up - skipping dependency installation"
    print_status "To update dependencies, run: pip install -r $CWS_DIR/requirements.txt --upgrade"
fi

# Create PIDs directory
print_status "Creating PIDs directory..."
mkdir -p "$PIDS_DIR"
print_success "PIDs directory ready"

# Check if ports are available
print_status "Checking if ports are available..."
if lsof -Pi :$MCP_PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    print_warning "Port $MCP_PORT is already in use. MCP Server may not start correctly."
fi

if lsof -Pi :$CWS_PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    print_warning "Port $CWS_PORT is already in use. CWS may not start correctly."
fi

# Display configuration
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Configuration${NC}"
echo -e "${BLUE}========================================${NC}"
echo "Workspace Root: $WORKSPACE_ROOT"
echo "Transport: $TRANSPORT"
echo "Bind Host: $BIND_HOST"
if [ "$IS_RUNPOD" = true ]; then
    echo -e "${GREEN}RunPod Environment: Detected${NC}"
    echo "  Services will bind to 0.0.0.0 for port forwarding"
fi
echo "MCP Server Port: $MCP_PORT"
echo "CWS Port: $CWS_PORT"
echo ""
echo "To customize, set environment variables:"
echo "  export WORKSPACE_ROOT=/path/to/workspace"
echo "  export MCP_PORT=8080"
echo "  export CWS_PORT=9090"
echo "  export TRANSPORT=websocket  # or 'stdio'"
echo "  export BIND_HOST_OVERRIDE=0.0.0.0  # for RunPod or external access"
echo ""

# Ask if user wants to start the services
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Ready to Start${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "The coding environment services will start on:"
echo "  - MCP Server: http://localhost:$MCP_PORT"
echo "  - CWS: http://localhost:$CWS_PORT"
echo ""
read -p "Start the services now? (Y/n): " start_services

if [[ "$start_services" =~ ^[Nn]$ ]]; then
    echo ""
    print_status "Setup complete! Start the services later with:"
    echo "  cd $SCRIPT_DIR"
    echo "  source venv/bin/activate"
    echo "  ./setup_and_run.sh"
    echo ""
    exit 0
fi

echo ""
print_status "Starting services..."
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    print_status "Stopping services..."
    
    # Stop MCP Server
    if [ -f "$PIDS_DIR/mcp.pid" ]; then
        MCP_PID=$(cat "$PIDS_DIR/mcp.pid")
        if kill -0 "$MCP_PID" 2>/dev/null; then
            kill "$MCP_PID" 2>/dev/null || true
            print_status "MCP Server stopped (PID: $MCP_PID)"
        fi
        rm -f "$PIDS_DIR/mcp.pid"
    fi
    
    # Stop CWS
    if [ -f "$PIDS_DIR/cws.pid" ]; then
        CWS_PID=$(cat "$PIDS_DIR/cws.pid")
        if kill -0 "$CWS_PID" 2>/dev/null; then
            kill "$CWS_PID" 2>/dev/null || true
            print_status "CWS stopped (PID: $CWS_PID)"
        fi
        rm -f "$PIDS_DIR/cws.pid"
    fi
    
    print_success "All services stopped"
    exit 0
}

# Set up trap for cleanup
trap cleanup INT TERM

# Start MCP Server
print_status "Starting MCP Server..."
cd "$ASSISTANT_DIR"
if [ "$TRANSPORT" = "stdio" ]; then
    print_status "  Transport: stdio"
    python3 -m mcp.server --transport stdio > "$PIDS_DIR/mcp.log" 2>&1 &
    MCP_PID=$!
else
    print_status "  Transport: websocket on $BIND_HOST:$MCP_PORT"
    python3 -m mcp.server --transport websocket --host "$BIND_HOST" --port $MCP_PORT > "$PIDS_DIR/mcp.log" 2>&1 &
    MCP_PID=$!
fi
echo $MCP_PID > "$PIDS_DIR/mcp.pid"
print_success "MCP Server started (PID: $MCP_PID)"
print_status "  Log: $PIDS_DIR/mcp.log"

# Wait a moment for MCP to start
sleep 2

# Start CWS
print_status "Starting CWS..."
cd "$CWS_DIR"
if [ "$TRANSPORT" = "stdio" ]; then
    print_status "  Transport: stdio"
    python3 -m cws.main --transport stdio --workspace-root "$WORKSPACE_ROOT" > "$PIDS_DIR/cws.log" 2>&1 &
    CWS_PID=$!
else
    print_status "  Transport: websocket on $BIND_HOST:$CWS_PORT"
    python3 -m cws.main --transport websocket --host "$BIND_HOST" --port $CWS_PORT --workspace-root "$WORKSPACE_ROOT" > "$PIDS_DIR/cws.log" 2>&1 &
    CWS_PID=$!
fi
echo $CWS_PID > "$PIDS_DIR/cws.pid"
print_success "CWS started (PID: $CWS_PID)"
print_status "  Log: $PIDS_DIR/cws.log"

# Wait a moment for CWS to start
sleep 2

# Display status
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Services Running${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "MCP Server:"
if [ "$TRANSPORT" = "websocket" ]; then
    if [ "$BIND_HOST" = "0.0.0.0" ]; then
        echo "  - URL: http://localhost:$MCP_PORT (or use RunPod port forwarding)"
        if [ "$IS_RUNPOD" = true ]; then
            echo "  - RunPod: Configure port $MCP_PORT in RunPod UI for external access"
        fi
    else
        echo "  - URL: http://localhost:$MCP_PORT"
    fi
else
    echo "  - Transport: stdio"
fi
echo "  - PID: $MCP_PID"
echo "  - Log: $PIDS_DIR/mcp.log"
echo ""
echo "CWS:"
if [ "$TRANSPORT" = "websocket" ]; then
    if [ "$BIND_HOST" = "0.0.0.0" ]; then
        echo "  - URL: http://localhost:$CWS_PORT (or use RunPod port forwarding)"
        if [ "$IS_RUNPOD" = true ]; then
            echo "  - RunPod: Configure port $CWS_PORT in RunPod UI for external access"
        fi
    else
        echo "  - URL: http://localhost:$CWS_PORT"
    fi
else
    echo "  - Transport: stdio"
fi
echo "  - PID: $CWS_PID"
echo "  - Log: $PIDS_DIR/cws.log"
echo "  - Workspace: $WORKSPACE_ROOT"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
echo ""

# Wait for services (or user interrupt)
wait
