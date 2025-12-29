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

# Check for Docker Compose (REQUIRED)
COMPOSE_CMD=""
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif command -v docker &> /dev/null && docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
fi

if [ -z "$COMPOSE_CMD" ]; then
    echo "❌ ERROR: Docker Compose is REQUIRED but not found!"
    echo ""
    echo "Docker Compose is a mandatory dependency for this application."
    echo "Please install Docker Compose and try again:"
    echo "  Debian/Ubuntu: sudo apt-get install -y docker-compose"
    echo "  Or: sudo apt-get install -y docker-compose-plugin"
    echo "  Or: pip3 install --user docker-compose"
    echo ""
    echo "Application startup ABORTED."
    exit 1
fi

if [ -n "$COMPOSE_CMD" ]; then
    # Check if Neo4j is already running
    if $COMPOSE_CMD ps neo4j 2>/dev/null | grep -q "Up"; then
        echo "✅ Neo4j is already running"
    else
        echo "🕸️ Starting Neo4j..."
        if $COMPOSE_CMD up -d neo4j 2>/dev/null; then
            echo "⏳ Waiting for Neo4j to be ready..."
            max_attempts=15
            attempt=0
            neo4j_ready=false
            
            while [ $attempt -lt $max_attempts ]; do
                if $COMPOSE_CMD exec -T neo4j cypher-shell -u neo4j -p neo4jpassword "RETURN 1" > /dev/null 2>&1; then
                    echo "✅ Neo4j is ready!"
                    neo4j_ready=true
                    break
                fi
                attempt=$((attempt + 1))
                sleep 2
            done
            
            if [ "$neo4j_ready" = false ]; then
                echo "⚠️ Neo4j is starting but not ready yet (will continue in background)"
                echo "   The application will use memory store until Neo4j is ready"
            fi
        else
            echo "⚠️ Failed to start Neo4j with $COMPOSE_CMD"
            echo "   The application will use memory store fallback"
        fi
    fi
else
    echo "ℹ️  Docker Compose not found. Neo4j will not be started."
    echo "   The application will use memory store fallback (this is fine)"
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
