#!/bin/bash

# RunPod Services Setup Script
# This script sets up Neo4j and other services for RunPod environments
# where Docker-in-Docker may not be available

set -e

echo "🚀 Setting up services for RunPod environment..."
echo "================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is available
print_status "Checking Docker availability..."
if command -v docker &> /dev/null && docker ps &> /dev/null; then
    print_success "Docker is available and running"
    DOCKER_AVAILABLE=true
else
    print_warning "Docker is not available or not running"
    DOCKER_AVAILABLE=false
fi

# Check if docker-compose is available
if [ "$DOCKER_AVAILABLE" = true ] && command -v docker-compose &> /dev/null; then
    print_success "Docker Compose is available"
    DOCKER_COMPOSE_AVAILABLE=true
else
    print_warning "Docker Compose is not available"
    DOCKER_COMPOSE_AVAILABLE=false
fi

if [ "$DOCKER_AVAILABLE" = false ]; then
    print_warning "========================================================"
    print_warning "Docker is not available in this environment"
    print_warning "========================================================"
    echo ""
    echo "For RunPod environments, you have several options:"
    echo ""
    echo "Option 1: Start Docker daemon (if container has privileged access)"
    echo "  service docker start"
    echo "  # Then run this script again"
    echo ""
    echo "Option 2: Install Neo4j directly (without Docker)"
    echo "  We'll do this for you automatically..."
    echo ""
    echo "Option 3: Use cloud Neo4j (Aura)"
    echo "  - Visit: https://neo4j.com/cloud/aura/"
    echo "  - Create a free instance"
    echo "  - Update .env with NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD"
    echo ""
    
    read -p "Do you want to install Neo4j directly (without Docker)? [Y/n] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
        print_status "Installing Neo4j directly..."
        
        # Install Java (required for Neo4j)
        print_status "Installing Java..."
        if command -v apt-get &> /dev/null; then
            apt-get update -qq
            apt-get install -y openjdk-17-jdk wget gnupg
            print_success "Java installed"
        else
            print_error "apt-get not available. Please install Java manually."
            exit 1
        fi
        
        # Install Neo4j
        print_status "Installing Neo4j Community Edition..."
        wget -O - https://debian.neo4j.com/neotechnology.gpg.key | apt-key add -
        echo 'deb https://debian.neo4j.com stable latest' > /etc/apt/sources.list.d/neo4j.list
        apt-get update -qq
        apt-get install -y neo4j
        
        # Configure Neo4j
        print_status "Configuring Neo4j..."
        
        # Set initial password
        NEO4J_PASSWORD="neo4jpassword"
        neo4j-admin set-initial-password "$NEO4J_PASSWORD"
        
        # Enable remote connections
        sed -i 's/#dbms.default_listen_address=0.0.0.0/dbms.default_listen_address=0.0.0.0/' /etc/neo4j/neo4j.conf
        
        # Start Neo4j
        print_status "Starting Neo4j..."
        neo4j start
        
        # Wait for Neo4j to be ready
        print_status "Waiting for Neo4j to be ready..."
        for i in {1..30}; do
            if curl -s http://localhost:7474 > /dev/null; then
                print_success "Neo4j is ready!"
                break
            fi
            echo -n "."
            sleep 2
        done
        echo ""
        
        print_success "=========================================="
        print_success "Neo4j installed and running!"
        print_success "=========================================="
        echo ""
        echo "Connection details:"
        echo "  URI: bolt://localhost:7687"
        echo "  Browser: http://localhost:7474"
        echo "  Username: neo4j"
        echo "  Password: $NEO4J_PASSWORD"
        echo ""
        echo "Add to your .env file:"
        echo "  NEO4J_URI=bolt://localhost:7687"
        echo "  NEO4J_USER=neo4j"
        echo "  NEO4J_PASSWORD=$NEO4J_PASSWORD"
        
        # Update .env if it exists
        if [ -f ".env" ]; then
            print_status "Updating .env file..."
            
            # Remove existing Neo4j settings
            sed -i '/NEO4J_URI/d' .env
            sed -i '/NEO4J_USER/d' .env
            sed -i '/NEO4J_PASSWORD/d' .env
            
            # Add new settings
            cat >> .env << EOF

# Neo4j Database (installed directly)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=$NEO4J_PASSWORD
EOF
            print_success ".env file updated"
        fi
        
    else
        print_warning "Skipping Neo4j installation"
        print_warning "You'll need to set up Neo4j manually or use cloud instance"
    fi
    
    exit 0
fi

# Docker is available - use docker-compose
print_status "Docker is available - checking docker-compose setup..."

if [ "$DOCKER_COMPOSE_AVAILABLE" = false ]; then
    print_error "Docker Compose is not installed"
    print_error "Please run ./setup.sh first to install Docker Compose"
    exit 1
fi

# Check if docker-compose.yml exists
if [ ! -f "docker-compose.yml" ]; then
    print_error "docker-compose.yml not found"
    exit 1
fi

# Start services with docker-compose
print_status "Starting services with Docker Compose..."

# Set default environment variables
export OPENAI_API_KEY=${OPENAI_API_KEY:-""}
export NGROK_AUTHTOKEN=${NGROK_AUTHTOKEN:-""}

# Start Neo4j only
print_status "Starting Neo4j..."
docker-compose up -d neo4j

# Wait for Neo4j to be healthy
print_status "Waiting for Neo4j to be healthy..."
for i in {1..30}; do
    if docker-compose ps neo4j | grep -q "healthy"; then
        print_success "Neo4j is healthy!"
        break
    fi
    echo -n "."
    sleep 2
done
echo ""

# Show service status
print_status "Service status:"
docker-compose ps neo4j

print_success "=========================================="
print_success "Services started successfully!"
print_success "=========================================="
echo ""
echo "Neo4j is now running:"
echo "  Browser: http://localhost:7474"
echo "  Bolt: bolt://localhost:7687"
echo "  Username: neo4j"
echo "  Password: neo4jpassword"
echo ""
echo "To start other services:"
echo "  docker-compose up -d redis    # Start Redis"
echo "  docker-compose up -d db       # Start PostgreSQL"
echo "  docker-compose up -d          # Start all services"
echo ""
echo "To stop services:"
echo "  docker-compose down"
