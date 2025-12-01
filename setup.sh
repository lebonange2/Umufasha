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

# Verify critical packages
print_status "Verifying critical packages..."
MISSING_PACKAGES=()

python3 -c "import numpy; print(f'✓ numpy {numpy.__version__}')" 2>/dev/null || {
    print_warning "numpy not found, reinstalling..."
    pip install numpy==1.26.3
    MISSING_PACKAGES+=("numpy")
}

python3 -c "import fastapi; print(f'✓ fastapi {fastapi.__version__}')" 2>/dev/null || {
    print_error "fastapi installation failed"
    exit 1
}

python3 -c "import httpx; print(f'✓ httpx {httpx.__version__}')" 2>/dev/null || {
    print_warning "httpx not found, installing..."
    pip install httpx==0.25.2
    MISSING_PACKAGES+=("httpx")
}

python3 -c "import sqlalchemy; print(f'✓ sqlalchemy {sqlalchemy.__version__}')" 2>/dev/null || {
    print_warning "sqlalchemy not found, installing..."
    pip install "sqlalchemy[asyncio]==2.0.23"
    MISSING_PACKAGES+=("sqlalchemy")
}

if [ ${#MISSING_PACKAGES[@]} -gt 0 ]; then
    print_warning "Some packages were missing and have been reinstalled: ${MISSING_PACKAGES[*]}"
else
    print_success "All critical packages verified"
fi

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

# LLM Configuration - Default to local model (Ollama)
LLM_PROVIDER=local
LLM_MODEL=llama3.1
LLM_LOCAL_URL=http://localhost:11434/v1

# Optional: Cloud providers (uncomment if needed)
# OPENAI_API_KEY=your_openai_api_key_here
# ANTHROPIC_API_KEY=your_anthropic_api_key_here
# LLM_BASE_URL=

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

# Setup Ollama for local AI models (optional but recommended)
print_status "Setting up Ollama for local AI models..."
if ! command -v ollama &> /dev/null; then
    print_status "Installing Ollama..."
    if curl -fsSL https://ollama.com/install.sh | sh; then
        print_success "Ollama installed"
    else
        print_warning "Ollama installation failed. You can install it later with: curl -fsSL https://ollama.com/install.sh | sh"
        print_warning "The app will work without Ollama, but local AI features won't be available"
    fi
else
    print_success "Ollama is already installed"
fi

# Start Ollama in background if not running (only if installed)
if command -v ollama &> /dev/null; then
    if ! pgrep -x "ollama" > /dev/null; then
        print_status "Starting Ollama server..."
        ollama serve > /tmp/ollama.log 2>&1 &
        OLLAMA_PID=$!
        sleep 3
        if kill -0 $OLLAMA_PID 2>/dev/null && curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
            print_success "Ollama server started (PID: $OLLAMA_PID)"
        else
            print_warning "Ollama server may have failed to start. Check /tmp/ollama.log"
            print_warning "You can start it manually later with: ollama serve"
        fi
    else
        print_success "Ollama server is already running"
    fi
    
    # Check if llama3.1 model is already installed
    if ollama list 2>/dev/null | grep -q "llama3.1"; then
        print_success "llama3.1 model is already installed"
    else
        print_status "Downloading llama3.1 model (this may take 5-10 minutes, ~5GB)..."
        print_warning "You can skip this and download later with: ollama pull llama3.1"
        print_warning "The app will work, but local AI needs the model to be downloaded"
        
        # Try to pull with timeout (10 minutes)
        if timeout 600 ollama pull llama3.1 2>&1 | tee /tmp/ollama_pull.log; then
            print_success "llama3.1 model downloaded successfully"
        else
            EXIT_CODE=$?
            if [ $EXIT_CODE -eq 124 ]; then
                print_warning "Model download timed out (10 minutes). Download it later with: ollama pull llama3.1"
            else
                print_warning "Model download failed. You can try again later with: ollama pull llama3.1"
            fi
            print_warning "The app will still work, but local AI features require the model"
        fi
    fi
else
    print_warning "Ollama not installed. Local AI features will not be available."
    print_warning "Install with: curl -fsSL https://ollama.com/install.sh | sh"
fi

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
echo "1. Start application: ./start.sh"
echo "2. Open dashboard: http://localhost:8000"
echo "3. Mindmapper: http://localhost:8000/brainstorm/mindmapper"
echo "4. Login with: admin / admin123"
echo "5. Run tests: ./test.sh"
echo "6. Stop application: ./stop.sh"
echo ""
echo "🤖 Local AI (Ollama):"
echo "- Model: llama3.1 (default)"
echo "- Status: Check with: ollama list"
echo "- If model not downloaded: ollama pull llama3.1"
echo "- Test: ollama run llama3.1 'Hello'"
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
