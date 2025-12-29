#!/bin/bash

# Docker Status Check Script
# Diagnoses Docker and Docker Compose issues

echo "🔍 Docker Environment Diagnostic"
echo "================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check Docker binary
echo "1. Checking Docker binary..."
if command -v docker &> /dev/null; then
    echo -e "   ${GREEN}✓${NC} Docker command found: $(which docker)"
    docker --version
else
    echo -e "   ${RED}✗${NC} Docker command not found"
fi
echo ""

# Check Docker daemon
echo "2. Checking Docker daemon..."
if docker info &> /dev/null; then
    echo -e "   ${GREEN}✓${NC} Docker daemon is running"
    docker info 2>&1 | grep "Server Version" || true
else
    echo -e "   ${RED}✗${NC} Docker daemon is NOT running"
    echo ""
    echo "   Error details:"
    docker info 2>&1 | head -5
    echo ""
    echo "   Possible fixes:"
    echo "   - Start Docker: service docker start"
    echo "   - Check if you're in a container without Docker-in-Docker support"
    echo "   - Ensure container is running in privileged mode"
fi
echo ""

# Check docker-compose
echo "3. Checking docker-compose..."
if command -v docker-compose &> /dev/null; then
    echo -e "   ${GREEN}✓${NC} docker-compose command found: $(which docker-compose)"
    docker-compose --version
else
    echo -e "   ${RED}✗${NC} docker-compose command not found"
fi
echo ""

# Check if running in container
echo "4. Checking if running in container..."
if [ -f /.dockerenv ]; then
    echo -e "   ${YELLOW}!${NC} Running inside a Docker container"
    echo "   Docker-in-Docker requires:"
    echo "   - Privileged mode: docker run --privileged"
    echo "   - Or mount Docker socket: -v /var/run/docker.sock:/var/run/docker.sock"
else
    echo -e "   ${GREEN}✓${NC} Not running in a container (or can't detect)"
fi
echo ""

# Check Docker socket
echo "5. Checking Docker socket..."
if [ -S /var/run/docker.sock ]; then
    echo -e "   ${GREEN}✓${NC} Docker socket exists: /var/run/docker.sock"
    ls -la /var/run/docker.sock
else
    echo -e "   ${RED}✗${NC} Docker socket not found: /var/run/docker.sock"
fi
echo ""

# Summary and recommendations
echo "================================="
echo "Summary & Recommendations"
echo "================================="
echo ""

# Determine environment
DOCKER_WORKS=false
if docker info &> /dev/null 2>&1; then
    DOCKER_WORKS=true
fi

if [ "$DOCKER_WORKS" = true ]; then
    echo -e "${GREEN}✓ Docker is working!${NC}"
    echo ""
    echo "You can use docker-compose:"
    echo "  docker-compose up -d neo4j"
    echo "  docker-compose up -d redis"
    echo "  docker-compose up -d"
else
    echo -e "${RED}✗ Docker is NOT working${NC}"
    echo ""
    echo "Recommended actions:"
    echo ""
    echo "Option 1: Start Docker daemon (if available)"
    echo "  service docker start"
    echo "  # Or: systemctl start docker"
    echo ""
    echo "Option 2: Use direct installation (no Docker)"
    echo "  ./scripts/setup_runpod_services.sh"
    echo "  # This will install Neo4j directly"
    echo ""
    echo "Option 3: Use cloud services"
    echo "  - Neo4j Aura: https://neo4j.com/cloud/aura/"
    echo "  - Redis Cloud: https://redis.com/try-free/"
    echo ""
fi

# Check if in RunPod
if [ -d "/workspace" ] || [ -d "/runpod-volume" ]; then
    echo ""
    echo -e "${YELLOW}Note: Detected RunPod environment${NC}"
    echo "For RunPod, we recommend:"
    echo "  1. Use ./scripts/setup_runpod_services.sh for direct installation"
    echo "  2. Or use cloud-hosted databases (Neo4j Aura, Redis Cloud)"
fi
