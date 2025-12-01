#!/bin/bash

# Start Unified Assistant
echo "🚀 Starting Unified Assistant..."

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

# Start the unified application
echo "🌐 Starting Unified Assistant on http://localhost:8000"
echo "📊 Dashboard: http://localhost:8000"
echo "🧠 Brainstorming: http://localhost:8000/brainstorm"
echo "📅 Personal Assistant: http://localhost:8000/personal"
echo "⚙️ Admin Panel: http://localhost:8000/admin"
echo "📚 API Docs: http://localhost:8000/docs"
echo "🔧 Health Check: http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python3 unified_app.py --host 0.0.0.0 --port 8000 --reload
