#!/bin/bash
# Quick verification script to check if setup is complete

set -e

echo "=== Verifying Setup ==="
echo ""

# Check virtual environment
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Run ./setup.sh first."
    exit 1
fi
echo "✓ Virtual environment exists"

# Activate venv
source venv/bin/activate

# Check Python packages
echo ""
echo "Checking Python packages..."
python3 -c "import numpy; print(f'✓ numpy {numpy.__version__}')" || echo "❌ numpy missing"
python3 -c "import fastapi; print(f'✓ fastapi {fastapi.__version__}')" || echo "❌ fastapi missing"
python3 -c "import httpx; print(f'✓ httpx {httpx.__version__}')" || echo "❌ httpx missing"
python3 -c "import sqlalchemy; print(f'✓ sqlalchemy {sqlalchemy.__version__}')" || echo "❌ sqlalchemy missing"
python3 -c "import anthropic; print(f'✓ anthropic {anthropic.__version__}')" || echo "⚠️  anthropic missing (optional)"

# Check Ollama
echo ""
echo "Checking Ollama..."
if command -v ollama &> /dev/null; then
    echo "✓ Ollama installed"
    if pgrep -x "ollama" > /dev/null; then
        echo "✓ Ollama server running"
    else
        echo "⚠️  Ollama server not running (start with: ollama serve)"
    fi
    if ollama list 2>/dev/null | grep -q "llama3.1"; then
        echo "✓ llama3.1 model installed"
    else
        echo "⚠️  llama3.1 model not installed (install with: ollama pull llama3.1)"
    fi
else
    echo "⚠️  Ollama not installed (optional, for local AI)"
fi

# Check .env
echo ""
echo "Checking configuration..."
if [ -f ".env" ]; then
    echo "✓ .env file exists"
    if grep -q "LLM_PROVIDER=local" .env; then
        echo "✓ Local AI configured as default"
    else
        echo "⚠️  Local AI not configured as default"
    fi
else
    echo "❌ .env file missing. Run ./setup.sh first."
fi

# Check database
if [ -f "assistant.db" ]; then
    echo "✓ Database exists"
else
    echo "⚠️  Database not found (will be created on first run)"
fi

echo ""
echo "=== Verification Complete ==="
echo ""
echo "If all checks pass, you can run: ./start.sh"

