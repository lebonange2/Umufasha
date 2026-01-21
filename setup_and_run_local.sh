#!/bin/bash
# Setup and Run Local Application Script
# This script sets up the environment and runs the application locally with OpenAI API

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

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Local Application Setup & Run${NC}"
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
    print_error "Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
    print_error "Python 3.8 or higher is required. Found: Python $PYTHON_VERSION"
    exit 1
fi

print_success "Python $PYTHON_VERSION found"

# Check if virtual environment exists
print_status "Checking virtual environment..."
if [ ! -d "venv" ]; then
    print_warning "Virtual environment not found. Creating..."
    python3 -m venv venv
    print_success "Virtual environment created"
else
    print_success "Virtual environment exists"
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip --quiet

# Install dependencies
print_status "Installing dependencies (this may take a few minutes)..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt --quiet
    print_success "Dependencies installed"
else
    print_error "requirements.txt not found!"
    exit 1
fi

# Check for OpenAI API key
print_status "Checking for OpenAI API key..."
if [ -z "$OPENAI_API_KEY" ]; then
    print_warning "OPENAI_API_KEY environment variable is not set"
    echo ""
    read -p "Enter your OpenAI API key (or press Enter to skip): " api_key
    if [ -n "$api_key" ]; then
        export OPENAI_API_KEY="$api_key"
        print_success "OpenAI API key set for this session"
        echo ""
        echo -e "${YELLOW}Note: To make this persistent, add to ~/.bashrc or ~/.zshrc:${NC}"
        echo -e "${YELLOW}  export OPENAI_API_KEY=$api_key${NC}"
        echo ""
    else
        print_warning "No API key provided. You can set it later with:"
        echo "  export OPENAI_API_KEY=sk-your-key-here"
        echo ""
    fi
else
    print_success "OpenAI API key found in environment"
fi

# Set default provider if not set
if [ -z "$LLM_PROVIDER" ]; then
    if [ -n "$OPENAI_API_KEY" ]; then
        export LLM_PROVIDER=openai
        export OPENAI_MODEL=gpt-4o
        print_status "Using OpenAI provider (LLM_PROVIDER=openai)"
    else
        export LLM_PROVIDER=local
        print_status "Using local provider (LLM_PROVIDER=local)"
        print_warning "Note: Local provider requires Ollama. For OpenAI, set OPENAI_API_KEY"
    fi
else
    print_status "Using provider: $LLM_PROVIDER"
fi

# Initialize database if needed
print_status "Checking database..."
if [ ! -f "assistant.db" ]; then
    print_warning "Database not found. Initializing..."
    if [ -f "scripts/init_db.py" ]; then
        python3 scripts/init_db.py
        print_success "Database initialized"
    else
        print_warning "init_db.py not found. Database will be created on first run."
    fi
else
    print_success "Database exists"
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_warning ".env file not found. Creating basic .env file..."
    cat > .env << EOF
# LLM Configuration
LLM_PROVIDER=${LLM_PROVIDER:-local}
LLM_MODEL=${LLM_MODEL:-gemma2:2b}
LLM_LOCAL_URL=http://localhost:11434/v1
OPENAI_MODEL=${OPENAI_MODEL:-gpt-4o}

# Database
DATABASE_URL=sqlite:///./assistant.db

# Other settings
LOG_LEVEL=INFO
EOF
    print_success ".env file created"
else
    print_success ".env file exists"
fi

# Display configuration
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Configuration${NC}"
echo -e "${BLUE}========================================${NC}"
echo "Provider: ${LLM_PROVIDER:-local}"
if [ "${LLM_PROVIDER:-local}" = "openai" ]; then
    if [ -n "$OPENAI_API_KEY" ]; then
        echo "OpenAI API Key: ${OPENAI_API_KEY:0:10}... (set)"
    else
        echo "OpenAI API Key: NOT SET"
    fi
    echo "OpenAI Model: ${OPENAI_MODEL:-gpt-4o}"
else
    echo "Local Model: ${LLM_MODEL:-gemma2:2b}"
fi
echo ""

# Ask if user wants to start the server
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Ready to Start${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "The application will start on:"
echo "  - Main: http://localhost:8000"
echo "  - Exam Generator: http://localhost:8000/writer/exam-generator"
echo "  - Writer: http://localhost:8000/writer"
echo "  - API Docs: http://localhost:8000/docs"
echo "  - Admin Panel: http://localhost:8000/admin (admin/admin123)"
echo ""
read -p "Start the server now? (Y/n): " start_server

if [[ "$start_server" =~ ^[Nn]$ ]]; then
    echo ""
    print_status "Setup complete! Start the server later with:"
    echo "  source venv/bin/activate"
    echo "  ./start_server.sh"
    echo ""
    echo "Or run this script again to start immediately."
    exit 0
fi

echo ""
print_status "Starting server..."
echo ""
echo -e "${GREEN}Server is starting...${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
echo ""

# Export PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:${SCRIPT_DIR}"

# Start the server
exec python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
