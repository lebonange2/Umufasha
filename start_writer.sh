#!/bin/bash

# Start Writer Assistant
echo "🚀 Starting Writer Assistant..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run ./setup.sh first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if .env exists (optional for writer)
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found. Create one with OPENAI_API_KEY if needed."
fi

# Kill any existing processes on port 8000
echo "🔄 Checking for existing processes on port 8000..."
if lsof -ti:8000 > /dev/null 2>&1; then
    echo "🛑 Found existing processes on port 8000. Stopping them..."
    lsof -ti:8000 | xargs kill -9 2>/dev/null
    sleep 2
    echo "✅ Existing processes stopped"
else
    echo "✅ Port 8000 is available"
fi

# Check if database exists (optional for writer)
if [ ! -f "assistant.db" ]; then
    echo "🗄️ Database not found. Initializing..."
    python3 scripts/init_db.py 2>/dev/null || echo "⚠️  Database init skipped (optional for writer)"
fi

# Start the application
echo "🌐 Starting Writer Assistant on http://localhost:8000"
echo "✍️  Writer page: http://localhost:8000/writer"
echo "📚 API docs: http://localhost:8000/docs"
echo "🔧 Health check: http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

