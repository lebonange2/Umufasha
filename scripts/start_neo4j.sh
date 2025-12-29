#!/bin/bash
# Script to start Neo4j using docker-compose

set -e

echo "Starting Neo4j..."
cd "$(dirname "$0")/.."

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null && ! command -v docker &> /dev/null; then
    echo "⚠️  Error: docker-compose or docker is not installed"
    echo ""
    echo "If you're running inside a Docker container, you need to run this from the host machine:"
    echo "  docker-compose up -d neo4j"
    echo ""
    echo "Or if you're on the host machine, install Docker:"
    echo "  https://docs.docker.com/get-docker/"
    echo ""
    echo "Note: The application will work without Neo4j using the memory store fallback."
    exit 1
fi

# Use docker-compose if available, otherwise use docker compose
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
else
    COMPOSE_CMD="docker compose"
fi

# Start Neo4j
echo "Starting Neo4j container..."
$COMPOSE_CMD up -d neo4j

# Wait for Neo4j to be ready
echo "Waiting for Neo4j to be ready..."
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if $COMPOSE_CMD exec -T neo4j cypher-shell -u neo4j -p neo4jpassword "RETURN 1" > /dev/null 2>&1; then
        echo "✅ Neo4j is ready!"
        echo ""
        echo "Neo4j is available at:"
        echo "  - HTTP: http://localhost:7474"
        echo "  - Bolt: bolt://localhost:7687"
        echo "  - Username: neo4j"
        echo "  - Password: neo4jpassword"
        exit 0
    fi
    
    attempt=$((attempt + 1))
    echo "Waiting for Neo4j... ($attempt/$max_attempts)"
    sleep 2
done

echo "⚠️  Neo4j did not become ready within expected time"
echo "Check logs with: $COMPOSE_CMD logs neo4j"
exit 1

