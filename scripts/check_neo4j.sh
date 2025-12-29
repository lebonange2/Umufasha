#!/bin/bash
# Script to check if Neo4j is running and accessible

set -e

echo "Checking Neo4j status..."
cd "$(dirname "$0")/.."

# Check if docker-compose is available
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif command -v docker &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    echo "Error: docker-compose or docker is not installed"
    exit 1
fi

# Check if Neo4j container is running
if $COMPOSE_CMD ps neo4j 2>/dev/null | grep -q "Up"; then
    echo "✅ Neo4j container is running"
    
    # Check if port is accessible
    if timeout 2 bash -c "echo > /dev/tcp/localhost/7687" 2>/dev/null; then
        echo "✅ Neo4j port 7687 is accessible"
        
        # Try to connect with cypher-shell
        if $COMPOSE_CMD exec -T neo4j cypher-shell -u neo4j -p neo4jpassword "RETURN 1" > /dev/null 2>&1; then
            echo "✅ Neo4j is ready and accepting connections"
            echo ""
            echo "Neo4j is available at:"
            echo "  - HTTP: http://localhost:7474"
            echo "  - Bolt: bolt://localhost:7687"
            exit 0
        else
            echo "⚠️  Neo4j container is running but not ready yet"
            echo "Check logs with: $COMPOSE_CMD logs neo4j"
            exit 1
        fi
    else
        echo "⚠️  Neo4j container is running but port 7687 is not accessible"
        echo "Check logs with: $COMPOSE_CMD logs neo4j"
        exit 1
    fi
else
    echo "❌ Neo4j container is not running"
    echo ""
    echo "To start Neo4j, run:"
    echo "  ./scripts/start_neo4j.sh"
    echo "  or"
    echo "  docker-compose up -d neo4j"
    exit 1
fi

