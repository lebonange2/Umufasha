#!/bin/bash

# Start Personal Assistant
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

# Also kill any uvicorn processes
echo "🔄 Checking for existing uvicorn processes..."
if pgrep -f uvicorn > /dev/null; then
    echo "🛑 Found existing uvicorn processes. Stopping them..."
    pkill -f uvicorn
    sleep 2
    echo "✅ Uvicorn processes stopped"
fi

# Check if database exists
if [ ! -f "assistant.db" ]; then
    echo "🗄️ Database not found. Initializing..."
    python3 scripts/init_db.py
fi

# Start the application
echo "🌐 Starting Personal Assistant on http://localhost:8000"
echo "📊 Admin interface: http://localhost:8000/admin"
echo "📚 API docs: http://localhost:8000/docs"
echo "🔧 Health check: http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
