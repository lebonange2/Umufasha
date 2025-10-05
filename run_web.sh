#!/bin/bash
# Run script for web interface

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🌐 Brainstorming Assistant - Web Interface${NC}"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment not found. Creating...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Activate virtual environment
source venv/bin/activate

# Check if Flask is installed
if ! python -c "import flask" &> /dev/null; then
    echo -e "${YELLOW}Installing web dependencies...${NC}"
    pip install flask flask-socketio python-socketio
    echo -e "${GREEN}✓ Dependencies installed${NC}"
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Warning: .env file not found${NC}"
    echo -e "Creating from .env.example..."
    cp .env.example .env
    echo -e "${GREEN}✓ Created .env file${NC}"
    echo -e "${YELLOW}Please edit .env with your API keys${NC}"
fi

# Run the web application
echo ""
echo -e "${GREEN}Starting web server...${NC}"
echo -e "${BLUE}Open your browser to: http://127.0.0.1:5000${NC}"
echo -e "${YELLOW}Note: Use 127.0.0.1 (not localhost) for microphone access${NC}"
echo ""

python3 web/app.py
