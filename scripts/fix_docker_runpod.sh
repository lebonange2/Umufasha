#!/bin/bash

# Quick fix for Docker issues in RunPod/container environments
# Attempts to start Docker or provides alternative solutions

set -e

echo "🔧 Docker Quick Fix for RunPod"
echo "==============================="
echo ""

# Check if Docker daemon is running
if docker info &> /dev/null 2>&1; then
    echo "✓ Docker is already running!"
    echo ""
    echo "You can now use docker-compose:"
    echo "  docker-compose up -d neo4j"
    exit 0
fi

echo "Docker daemon is not running. Attempting fixes..."
echo ""

# Try to start Docker service
echo "Attempt 1: Starting Docker service..."
if service docker start 2>/dev/null; then
    sleep 3
    if docker info &> /dev/null 2>&1; then
        echo "✓ Docker started successfully!"
        echo ""
        echo "You can now use docker-compose:"
        echo "  docker-compose up -d neo4j"
        exit 0
    fi
fi

echo "✗ Could not start Docker service"
echo ""

# Try systemctl
echo "Attempt 2: Starting Docker via systemctl..."
if command -v systemctl &> /dev/null; then
    if systemctl start docker 2>/dev/null; then
        sleep 3
        if docker info &> /dev/null 2>&1; then
            echo "✓ Docker started successfully!"
            echo ""
            echo "You can now use docker-compose:"
            echo "  docker-compose up -d neo4j"
            exit 0
        fi
    fi
    echo "✗ Could not start Docker via systemctl"
else
    echo "✗ systemctl not available"
fi
echo ""

# Check if dockerd exists and try to start it directly
echo "Attempt 3: Starting Docker daemon directly..."
if command -v dockerd &> /dev/null; then
    echo "Starting dockerd in background..."
    nohup dockerd > /tmp/dockerd.log 2>&1 &
    DOCKERD_PID=$!
    
    # Wait for Docker to start
    for i in {1..10}; do
        sleep 1
        if docker info &> /dev/null 2>&1; then
            echo "✓ Docker daemon started successfully (PID: $DOCKERD_PID)!"
            echo ""
            echo "You can now use docker-compose:"
            echo "  docker-compose up -d neo4j"
            exit 0
        fi
    done
    
    echo "✗ Docker daemon failed to start"
    echo "Check logs: tail /tmp/dockerd.log"
else
    echo "✗ dockerd command not found"
fi
echo ""

# All attempts failed
echo "======================================"
echo "Could not start Docker automatically"
echo "======================================"
echo ""
echo "This usually means:"
echo "  1. You're in a container without Docker-in-Docker support"
echo "  2. The container wasn't started with --privileged flag"
echo "  3. Docker socket isn't mounted"
echo ""
echo "Alternative Solutions:"
echo ""
echo "Option A: Install services directly (RECOMMENDED for RunPod)"
echo "  chmod +x scripts/setup_runpod_services.sh"
echo "  ./scripts/setup_runpod_services.sh"
echo ""
echo "Option B: Use cloud services"
echo "  - Neo4j Aura (free tier): https://neo4j.com/cloud/aura/"
echo "  - Redis Cloud (free tier): https://redis.com/try-free/"
echo "  - Update .env with cloud credentials"
echo ""
echo "Option C: Restart container with Docker support"
echo "  Exit this container and start with:"
echo "  docker run --privileged -v /var/run/docker.sock:/var/run/docker.sock ..."
echo ""
echo "For now, run this to install Neo4j directly:"
echo "  chmod +x scripts/setup_runpod_services.sh"
echo "  ./scripts/setup_runpod_services.sh"
echo ""
