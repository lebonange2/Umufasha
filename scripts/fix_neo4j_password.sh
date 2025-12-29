#!/bin/bash

# Fix Neo4j Password Script
# Resets Neo4j password to match .env configuration

set -e

echo "🔧 Fixing Neo4j Password..."
echo "============================"

# Colors
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

# Check if Neo4j is installed
if ! command -v neo4j &> /dev/null; then
    print_error "Neo4j command not found"
    print_error "Neo4j may not be installed, or you're using Docker"
    echo ""
    echo "If using Docker, run:"
    echo "  docker-compose down neo4j"
    echo "  docker-compose up -d neo4j"
    exit 1
fi

# Stop Neo4j if running
print_status "Stopping Neo4j..."
neo4j stop 2>/dev/null || true
sleep 2

# Reset password
NEO4J_PASSWORD="neo4jpassword"

print_status "Resetting Neo4j password..."

# Try new command format (Neo4j 5+)
if neo4j-admin dbms set-initial-password "$NEO4J_PASSWORD" --force 2>/dev/null; then
    print_success "Password reset using Neo4j 5+ command"
elif neo4j-admin dbms set-initial-password "$NEO4J_PASSWORD" 2>/dev/null; then
    print_success "Password reset using Neo4j 5+ command"
# Try old command format (Neo4j 4)
elif neo4j-admin set-initial-password "$NEO4J_PASSWORD" 2>/dev/null; then
    print_success "Password reset using Neo4j 4 command"
else
    print_warning "Could not reset password with standard commands"
    print_warning "Trying alternative method..."
    
    # Alternative: Delete auth file and restart
    if [ -f /var/lib/neo4j/data/dbms/auth ]; then
        print_status "Removing auth file..."
        rm -f /var/lib/neo4j/data/dbms/auth
        print_success "Auth file removed"
    elif [ -f ~/neo4j/data/dbms/auth ]; then
        print_status "Removing auth file..."
        rm -f ~/neo4j/data/dbms/auth
        print_success "Auth file removed"
    fi
fi

# Start Neo4j
print_status "Starting Neo4j..."
if neo4j start; then
    print_success "Neo4j started"
    
    # Wait for Neo4j to be ready
    print_status "Waiting for Neo4j to be ready..."
    sleep 5
    
    # If auth file was deleted, set password now
    if [ ! -f /var/lib/neo4j/data/dbms/auth ] && [ ! -f ~/neo4j/data/dbms/auth ]; then
        print_status "Setting initial password..."
        if neo4j-admin dbms set-initial-password "$NEO4J_PASSWORD" 2>/dev/null; then
            print_success "Initial password set"
        elif neo4j-admin set-initial-password "$NEO4J_PASSWORD" 2>/dev/null; then
            print_success "Initial password set"
        fi
        
        # Restart to apply
        print_status "Restarting Neo4j..."
        neo4j restart
        sleep 5
    fi
    
    # Test connection
    print_status "Testing connection..."
    if curl -s -u neo4j:$NEO4J_PASSWORD http://localhost:7474 > /dev/null; then
        print_success "=========================================="
        print_success "Neo4j password fixed successfully!"
        print_success "=========================================="
        echo ""
        echo "Connection details:"
        echo "  URI: bolt://localhost:7687"
        echo "  Browser: http://localhost:7474"
        echo "  Username: neo4j"
        echo "  Password: $NEO4J_PASSWORD"
        echo ""
        echo "You can now restart your application:"
        echo "  ./stop.sh"
        echo "  ./start.sh"
    else
        print_warning "Could not verify connection"
        print_warning "Try accessing Neo4j browser at http://localhost:7474"
        print_warning "Username: neo4j"
        print_warning "Password: $NEO4J_PASSWORD"
    fi
else
    print_error "Failed to start Neo4j"
    print_error "Check logs with: journalctl -u neo4j"
    exit 1
fi
