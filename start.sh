#!/bin/bash

# Start Personal Assistant with all services
echo "🚀 Starting Personal Assistant..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run ./setup.sh first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ Environment file not found. Please run ./setup.sh first."
    exit 1
fi

# Check if database exists
if [ ! -f "assistant.db" ]; then
    echo "🗄️ Database not found. Initializing..."
    python3 scripts/init_db.py
fi

# Start Ollama if installed and not running
if command -v ollama &> /dev/null; then
    if ! pgrep -x "ollama" > /dev/null; then
        echo "🤖 Starting Ollama server..."
        ollama serve > /tmp/ollama.log 2>&1 &
        OLLAMA_PID=$!
        sleep 3
        if kill -0 $OLLAMA_PID 2>/dev/null && curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
            echo "✅ Ollama server started (PID: $OLLAMA_PID)"
        else
            echo "⚠️ Ollama server may have failed to start. Check /tmp/ollama.log"
            echo "⚠️ You can start it manually later with: ollama serve"
        fi
    else
        echo "✅ Ollama server is already running"
    fi
else
    echo "⚠️ Ollama not installed. Local AI features will not be available."
    echo "⚠️ Install with: curl -fsSL https://ollama.com/install.sh | sh"
fi

# Display startup information
echo ""
echo "🌐 Starting Personal Assistant on http://localhost:8000"
echo "📊 Dashboard: http://localhost:8000"
echo "✍️ Writer: http://localhost:8000/writer"
echo "📚 Book Writer: http://localhost:8000/writer/book-writer"
echo "📚 API Docs: http://localhost:8000/docs"
echo "🔧 Health Check: http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the application
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
