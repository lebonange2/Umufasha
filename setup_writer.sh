#!/bin/bash

# Lightweight Writer Frontend Setup Script
# This script only sets up and runs the writer frontend application

set -e  # Exit on any error

echo "🚀 Setting up Writer Frontend (Lightweight Mode)..."
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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

# Check if Node.js is installed
print_status "Checking Node.js installation..."
if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed."
    print_status "Installing Node.js..."
    
    # Try to detect package manager and install Node.js
    if command -v apt-get &> /dev/null; then
        print_status "Detected apt-get, installing Node.js..."
        curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
        sudo apt-get install -y nodejs
    elif command -v yum &> /dev/null; then
        print_status "Detected yum, installing Node.js..."
        curl -fsSL https://rpm.nodesource.com/setup_18.x | sudo bash -
        sudo yum install -y nodejs
    elif command -v brew &> /dev/null; then
        print_status "Detected Homebrew, installing Node.js..."
        brew install node
    else
        print_error "Could not detect package manager. Please install Node.js manually from https://nodejs.org/"
        exit 1
    fi
fi

NODE_VERSION=$(node --version)
print_success "Node.js $NODE_VERSION found"

# Check if npm is installed
print_status "Checking npm installation..."
if ! command -v npm &> /dev/null; then
    print_error "npm is not installed. Please install npm."
    exit 1
fi

NPM_VERSION=$(npm --version)
print_success "npm $NPM_VERSION found"

# Navigate to writer directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WRITER_DIR="$SCRIPT_DIR/writer"

if [ ! -d "$WRITER_DIR" ]; then
    print_error "Writer directory not found at $WRITER_DIR"
    exit 1
fi

cd "$WRITER_DIR"
print_status "Changed to writer directory: $WRITER_DIR"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    print_status "Installing dependencies (this may take a few minutes)..."
    npm install
    print_success "Dependencies installed"
else
    print_status "Dependencies already installed"
    # Check if package.json has changed
    if [ "package.json" -nt "node_modules" ]; then
        print_warning "package.json is newer than node_modules, updating dependencies..."
        npm install
        print_success "Dependencies updated"
    fi
fi

# Check for port 5173 (default Vite port)
print_status "Checking if port 5173 is available..."
if lsof -ti:5173 > /dev/null 2>&1; then
    print_warning "Port 5173 is already in use. Attempting to stop existing process..."
    lsof -ti:5173 | xargs kill -9 2>/dev/null || true
    sleep 2
    print_success "Port 5173 is now available"
else
    print_success "Port 5173 is available"
fi

# Display startup information
echo ""
echo "=================================================="
print_success "Writer Frontend Setup Complete!"
echo "=================================================="
echo ""
echo "🌐 Starting Writer Frontend on http://localhost:5173"
echo "📝 Writer page: http://localhost:5173/writer"
echo "📚 Book Writer: http://localhost:5173/writer/book-writer"
echo "📝 Exam Generator: http://localhost:5173/exam-generator"
echo ""
print_warning "Note: This is the frontend only. API calls will fail without the backend."
print_warning "For full functionality, run ./setup.sh and ./start.sh instead."
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the Vite dev server
npm run dev
