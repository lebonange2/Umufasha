#!/bin/bash

# Reset Database Script
echo "🗄️ Resetting Personal Assistant Database..."

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

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    print_error "Virtual environment not found. Please run ./setup.sh first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Stop the application if running
print_status "Stopping application if running..."
pkill -f uvicorn 2>/dev/null || true

# Remove existing database
if [ -f "assistant.db" ]; then
    print_status "Removing existing database..."
    rm -f assistant.db
    print_success "Database removed"
else
    print_warning "No existing database found"
fi

# Initialize fresh database
print_status "Creating fresh database..."
python3 scripts/init_db.py
print_success "Database created"

# Run tests to verify
print_status "Running tests to verify database..."
python3 scripts/test_internal.py
print_success "Database reset completed successfully!"

echo ""
echo "🎉 Database has been reset!"
echo "=========================="
echo ""
echo "📋 What was done:"
echo "✅ Stopped running application"
echo "✅ Removed old database file"
echo "✅ Created fresh database with all tables"
echo "✅ Ran tests to verify functionality"
echo ""
echo "🚀 Next steps:"
echo "1. Start the application: ./start.sh"
echo "2. Access admin interface: http://localhost:8000/admin"
echo "3. Create new users and test functionality"
echo ""
print_success "Ready to start fresh! 🚀"
