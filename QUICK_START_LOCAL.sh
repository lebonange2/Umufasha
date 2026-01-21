#!/bin/bash
# Quick Start Script for Local Development
# Minimal setup - assumes you've run setup_and_run_local.sh at least once

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Quick Start - Local Application${NC}"
echo ""

# Check virtual environment
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment not found.${NC}"
    echo "Run ./setup_and_run_local.sh first for full setup."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check OpenAI API key
if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${YELLOW}OPENAI_API_KEY not set.${NC}"
    echo "Set it with: export OPENAI_API_KEY=sk-your-key-here"
    echo ""
    read -p "Enter OpenAI API key now (or press Enter to use local provider): " api_key
    if [ -n "$api_key" ]; then
        export OPENAI_API_KEY="$api_key"
        export LLM_PROVIDER=openai
        export OPENAI_MODEL=gpt-4o
    else
        export LLM_PROVIDER=local
    fi
else
    export LLM_PROVIDER=${LLM_PROVIDER:-openai}
    export OPENAI_MODEL=${OPENAI_MODEL:-gpt-4o}
fi

# Initialize database if needed
if [ ! -f "assistant.db" ]; then
    echo "Initializing database..."
    python3 scripts/init_db.py 2>/dev/null || echo "Database will be created on first run"
fi

# Export PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:${SCRIPT_DIR}"

echo ""
echo -e "${GREEN}Starting server on http://localhost:8000${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
echo ""

# Start server
exec python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
