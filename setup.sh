#!/bin/bash

# Personal Assistant Setup Script
# This script sets up the LLM-Powered Personal Assistant for internal testing

set -e  # Exit on any error

echo "🚀 Setting up LLM-Powered Personal Assistant..."
echo "=============================================="

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

# Check if Python 3 is installed
print_status "Checking Python 3 installation..."
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
print_success "Python $PYTHON_VERSION found"

# Check if pip is installed
print_status "Checking pip installation..."
if ! command -v pip3 &> /dev/null; then
    print_error "pip3 is not installed. Please install pip3."
    exit 1
fi
print_success "pip3 found"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    print_status "Creating virtual environment..."
    python3 -m venv venv
    print_success "Virtual environment created"
else
    print_status "Virtual environment already exists"
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate
print_success "Virtual environment activated"

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip

# Install requirements
print_status "Installing Python dependencies..."
pip install -r requirements-app.txt
print_success "Dependencies installed"

# Install additional SQLite driver
print_status "Installing SQLite driver..."
pip install aiosqlite
print_success "SQLite driver installed"

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p app/static
mkdir -p logs
print_success "Directories created"

# Generate secure keys
print_status "Generating secure encryption keys..."
OAUTH_ENC_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    print_status "Creating environment configuration..."
    cat > .env << EOF
# Personal Assistant Environment Configuration
# Generated on $(date)

# Database - Using SQLite for local testing
DATABASE_URL=sqlite+aiosqlite:///./assistant.db
REDIS_URL=redis://localhost:6379/0

# Mock Mode - Set to true to use mock clients (no external APIs needed)
MOCK_MODE=true
MOCK_TWILIO=true
MOCK_SENDGRID=true

# LLM Configuration (optional for testing)
OPENAI_API_KEY=your_openai_api_key_here
LLM_BASE_URL=
LLM_MODEL=gpt-4o

# Twilio Configuration (not used in mock mode)
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_CALLER_ID=+1234567890

# Email Configuration (not used in mock mode)
SENDGRID_API_KEY=your_sendgrid_api_key

# Google Calendar OAuth (optional for testing)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# Security (auto-generated)
OAUTH_ENC_KEY=$OAUTH_ENC_KEY
SECRET_KEY=$SECRET_KEY

# Scheduler
SCHEDULER=apscheduler

# Base URL for webhooks
BASE_URL=http://localhost:8000

# Admin credentials
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123

# Logging
LOG_LEVEL=INFO
EOF
    print_success "Environment configuration created"
else
    print_warning ".env file already exists, skipping creation"
fi

# Initialize database
print_status "Initializing database..."
python3 scripts/init_db.py
print_success "Database initialized"

# Clear any existing test data
print_status "Clearing existing test data..."
rm -f assistant.db
python3 scripts/init_db.py
print_success "Database cleared and reinitialized"

# Run internal tests
print_status "Running internal tests..."
python3 scripts/test_internal.py
print_success "Internal tests passed"

# Create start script
print_status "Creating start script..."
cat > start.sh << 'EOF'
#!/bin/bash

# Start Personal Assistant
echo "🚀 Starting Personal Assistant..."

# Activate virtual environment
source venv/bin/activate

# Start the application
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
EOF

chmod +x start.sh
print_success "Start script created"

# Create unified start script
print_status "Creating unified start script..."
cat > start_unified.sh << 'EOF'
#!/bin/bash

# Start Unified Assistant
echo "🚀 Starting Unified Assistant..."

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

# Start the unified application
echo "🌐 Starting Unified Assistant on http://localhost:8000"
echo "📊 Dashboard: http://localhost:8000"
echo "🧠 Brainstorming: http://localhost:8000/brainstorm"
echo "📅 Personal Assistant: http://localhost:8000/personal"
echo "⚙️ Admin Panel: http://localhost:8000/admin"
echo "📚 API Docs: http://localhost:8000/docs"
echo "🔧 Health Check: http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python3 unified_app.py --host 0.0.0.0 --port 8000 --reload
EOF

chmod +x start_unified.sh
print_success "Unified start script created"

# Create stop script
print_status "Creating stop script..."
cat > stop.sh << 'EOF'
#!/bin/bash

# Stop Personal Assistant
echo "🛑 Stopping Personal Assistant..."

# Kill any running uvicorn processes
pkill -f uvicorn

echo "✅ Personal Assistant stopped"
EOF

chmod +x stop.sh
print_success "Stop script created"

# Create test script
print_status "Creating test script..."
cat > test.sh << 'EOF'
#!/bin/bash

# Test Personal Assistant
echo "🧪 Testing Personal Assistant..."

# Activate virtual environment
source venv/bin/activate

# Run internal tests
python3 scripts/test_internal.py

# Test API endpoints
echo "Testing API endpoints..."
curl -s http://localhost:8000/health | python3 -m json.tool || echo "❌ Health check failed"

echo "✅ Testing completed"
EOF

chmod +x test.sh
print_success "Test script created"

echo ""
echo "🎉 Setup completed successfully!"
echo "================================"
echo ""
echo "📋 Next steps:"
echo "1. Start unified application: ./start_unified.sh"
echo "2. Open dashboard: http://localhost:8000"
echo "3. Or start personal assistant only: ./start.sh"
echo "4. Login with: admin / admin123"
echo "5. Run tests: ./test.sh"
echo "6. Stop application: ./stop.sh"
echo ""
echo "📚 Documentation:"
echo "- Quick Start Guide: QUICKSTART.md"
echo "- Testing Guide: TESTING_GUIDE.md"
echo "- API Documentation: http://localhost:8000/docs"
echo ""
echo "🔧 Configuration:"
echo "- Environment file: .env"
echo "- Database: assistant.db (SQLite)"
echo "- Mock mode: Enabled (no external APIs needed)"
echo ""
print_success "Ready to start your Personal Assistant! 🚀"
