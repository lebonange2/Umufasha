#!/bin/bash

# Start Personal Assistant on RunPod with Mock LLM
echo "🚀 Starting Personal Assistant on RunPod (with Mock LLM)..."

# Set USE_MOCK_LLM for testing/demo without real AI
export USE_MOCK_LLM=true

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run ./setup.sh first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  Environment file not found. Creating minimal .env..."
    cat > .env << EOF
# Mock LLM for testing/demo
USE_MOCK_LLM=true
LLM_PROVIDER=local
LLM_MODEL=mock
EOF
fi

# Ensure USE_MOCK_LLM is set in .env
if ! grep -q "USE_MOCK_LLM" .env; then
    echo "USE_MOCK_LLM=true" >> .env
fi

# Check if database exists
if [ ! -f "assistant.db" ]; then
    echo "🗄️ Database not found. Initializing..."
    python3 scripts/init_db.py
fi

# Check for Docker Compose (OPTIONAL on RunPod)
COMPOSE_CMD=""
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif command -v docker &> /dev/null && docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
fi

if [ -n "$COMPOSE_CMD" ]; then
    # Check if Neo4j is already running
    if $COMPOSE_CMD ps neo4j 2>/dev/null | grep -q "Up"; then
        echo "✅ Neo4j is already running"
    else
        echo "🕸️ Starting Neo4j..."
        if $COMPOSE_CMD up -d neo4j 2>/dev/null; then
            echo "⏳ Waiting for Neo4j to be ready..."
            max_attempts=10
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
            fi
        else
            echo "⚠️ Failed to start Neo4j (continuing without it)"
        fi
    fi
else
    echo "ℹ️  Docker Compose not found. Skipping Neo4j (using memory store)"
fi

# Display startup information
echo ""
echo "🌐 Starting Personal Assistant with Mock LLM (instant responses)"
echo "📊 Dashboard: http://localhost:8000"
echo "🏢 Core Devices: http://localhost:8000/core-devices"
echo "📚 API Docs: http://localhost:8000/docs"
echo "🔧 Health Check: http://localhost:8000/health"
echo ""
echo "⚡ Using Mock LLM - all AI responses are instant and deterministic"
echo "   Perfect for testing, demos, and development!"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the application
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
