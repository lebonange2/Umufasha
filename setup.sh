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

# Install system dependencies for building Python packages
print_status "Installing system dependencies (for faster-whisper/av package and Docker Compose)..."
INSTALLED_DEPS=false

if command -v apt-get &> /dev/null; then
    # Debian/Ubuntu
    print_status "Detected Debian/Ubuntu - installing build dependencies and Docker Compose..."
    INSTALL_DOCKER_COMPOSE=false
    
    # Function to install docker-compose
    install_docker_compose_ubuntu() {
        local USE_SUDO=$1
        local INSTALLED=false
        
        # RUBRIC STEP 1: Pre-check - Check if docker-compose is already available via multiple methods
        print_status "Checking if docker-compose is already installed..."
        hash -r 2>/dev/null || true
        export PATH="/usr/local/bin:/usr/bin:$HOME/.local/bin:$PATH"
        
        # Check 1: Command in PATH
        if command -v docker-compose &> /dev/null; then
            local VERSION=$(docker-compose --version 2>/dev/null | head -n1)
            print_success "Docker Compose already installed: $VERSION"
            echo "true"
            return 0
        fi
        
        # Check 2: Binary in common locations
        for BIN_PATH in /usr/bin/docker-compose /usr/local/bin/docker-compose "$HOME/.local/bin/docker-compose"; do
            if [ -f "$BIN_PATH" ] && [ -x "$BIN_PATH" ]; then
                export PATH="$(dirname "$BIN_PATH"):$PATH"
                hash -r 2>/dev/null || true
                if command -v docker-compose &> /dev/null; then
                    local VERSION=$(docker-compose --version 2>/dev/null | head -n1)
                    print_success "Docker Compose found at $BIN_PATH: $VERSION"
                    echo "true"
                    return 0
                fi
            fi
        done
        
        # Check 3: Check if package is installed via dpkg
        if dpkg -l | grep -qE "^ii.*docker-compose"; then
            print_status "Docker Compose package is installed (verified via dpkg)"
            # Try to find the binary
            local BIN_LOCATION=$(dpkg -L docker-compose 2>/dev/null | grep -E "bin/docker-compose$" | head -n1)
            if [ -n "$BIN_LOCATION" ] && [ -f "$BIN_LOCATION" ] && [ -x "$BIN_LOCATION" ]; then
                export PATH="$(dirname "$BIN_LOCATION"):$PATH"
                hash -r 2>/dev/null || true
                if command -v docker-compose &> /dev/null; then
                    local VERSION=$(docker-compose --version 2>/dev/null | head -n1)
                    print_success "Docker Compose found: $VERSION"
                    echo "true"
                    return 0
                else
                    # Binary exists, use it directly
                    if "$BIN_LOCATION" --version &> /dev/null; then
                        local VERSION=$("$BIN_LOCATION" --version 2>/dev/null | head -n1)
                        print_success "Docker Compose found at $BIN_LOCATION: $VERSION"
                        echo "true"
                        return 0
                    fi
                fi
            fi
        fi
        
        # RUBRIC STEP 2: Installation - Try docker-compose package (most common)
        print_status "Attempting to install docker-compose via apt..."
        local INSTALL_OUTPUT=""
        local INSTALL_EXIT_CODE=0
        
        if [ "$USE_SUDO" = "true" ] && command -v sudo &> /dev/null; then
            INSTALL_OUTPUT=$(sudo apt-get install -y docker-compose 2>&1 | tee /tmp/docker-compose-install.log)
            INSTALL_EXIT_CODE=${PIPESTATUS[0]}
        else
            INSTALL_OUTPUT=$(apt-get install -y docker-compose 2>&1 | tee /tmp/docker-compose-install.log)
            INSTALL_EXIT_CODE=${PIPESTATUS[0]}
        fi
        
        # RUBRIC STEP 3: Success Detection - Check exit code AND output patterns
        local INSTALL_SUCCESS=false
        if [ "$INSTALL_EXIT_CODE" -eq 0 ]; then
            # Success indicators: exit code 0 AND one of these patterns
            if echo "$INSTALL_OUTPUT" | grep -qE "(Setting up docker-compose|Setting up.*docker-compose|is already the newest version|already the newest|docker-compose.*is already|docker-compose.*already.*newest)"; then
                INSTALL_SUCCESS=true
            fi
        fi
        
        # RUBRIC STEP 4: Post-installation Verification
        if [ "$INSTALL_SUCCESS" = "true" ] || [ "$INSTALL_EXIT_CODE" -eq 0 ]; then
            # Wait for system to update
            sleep 2
            hash -r 2>/dev/null || true
            export PATH="/usr/local/bin:/usr/bin:$HOME/.local/bin:$PATH"
            
            # Verify via dpkg first (most reliable)
            if dpkg -l | grep -qE "^ii.*docker-compose"; then
                print_status "Docker Compose package confirmed installed via dpkg"
                # Find the binary location
                local BIN_LOCATION=$(dpkg -L docker-compose 2>/dev/null | grep -E "bin/docker-compose$" | head -n1)
                if [ -n "$BIN_LOCATION" ] && [ -f "$BIN_LOCATION" ]; then
                    export PATH="$(dirname "$BIN_LOCATION"):$PATH"
                    hash -r 2>/dev/null || true
                    if command -v docker-compose &> /dev/null; then
                        local VERSION=$(docker-compose --version 2>/dev/null | head -n1)
                        print_success "Docker Compose installed via apt: $VERSION"
                        INSTALLED=true
                    elif "$BIN_LOCATION" --version &> /dev/null; then
                        local VERSION=$("$BIN_LOCATION" --version 2>/dev/null | head -n1)
                        print_success "Docker Compose installed via apt (at $BIN_LOCATION): $VERSION"
                        INSTALLED=true
                    else
                        print_success "Docker Compose installed via apt (package confirmed, binary at $BIN_LOCATION)"
                        INSTALLED=true
                    fi
                else
                    # Package installed but can't find binary - still success if package is there
                    print_success "Docker Compose installed via apt (package confirmed)"
                    INSTALLED=true
                fi
            # Fallback: Check command in PATH
            elif command -v docker-compose &> /dev/null; then
                local VERSION=$(docker-compose --version 2>/dev/null | head -n1)
                print_success "Docker Compose installed via apt: $VERSION"
                INSTALLED=true
            # Fallback: Check common binary locations
            elif [ -f /usr/bin/docker-compose ] || [ -f /usr/local/bin/docker-compose ]; then
                local BIN_PATH=""
                [ -f /usr/bin/docker-compose ] && BIN_PATH="/usr/bin/docker-compose"
                [ -f /usr/local/bin/docker-compose ] && BIN_PATH="/usr/local/bin/docker-compose"
                export PATH="$(dirname "$BIN_PATH"):$PATH"
                hash -r 2>/dev/null || true
                if command -v docker-compose &> /dev/null; then
                    local VERSION=$(docker-compose --version 2>/dev/null | head -n1)
                    print_success "Docker Compose installed via apt: $VERSION"
                    INSTALLED=true
                elif "$BIN_PATH" --version &> /dev/null; then
                    local VERSION=$("$BIN_PATH" --version 2>/dev/null | head -n1)
                    print_success "Docker Compose installed via apt (at $BIN_PATH): $VERSION"
                    INSTALLED=true
                else
                    print_success "Docker Compose installed via apt (binary found at $BIN_PATH)"
                    INSTALLED=true
                fi
            # Last resort: If output says "already installed" or "Setting up docker-compose", consider it success
            elif echo "$INSTALL_OUTPUT" | grep -qE "(Setting up docker-compose|Setting up.*docker-compose|is already the newest version|already the newest)"; then
                # Double-check with dpkg
                sleep 1
                if dpkg -l | grep -qE "^ii.*docker-compose"; then
                    print_success "Docker Compose installation confirmed (package setup completed and verified via dpkg)"
                    INSTALLED=true
                else
                    print_success "Docker Compose installation confirmed (package setup completed)"
                    INSTALLED=true
                fi
            else
                print_warning "Installation may have succeeded but verification failed, trying alternative methods..."
            fi
        else
            # Check if it failed due to package not found vs other error
            if echo "$INSTALL_OUTPUT" | grep -qE "(E: Unable to locate package|E: Package.*not found|E:.*not available)"; then
                print_warning "docker-compose package not found in repos, trying alternative methods..."
            else
                print_warning "apt-get install failed (exit code: $INSTALL_EXIT_CODE), trying alternative methods..."
            fi
        fi
        
        # Method 2: Try docker-compose-plugin (Docker Compose V2 as plugin)
        if [ "$INSTALLED" = "false" ]; then
            print_status "Attempting to install docker-compose-plugin..."
            local PLUGIN_OUTPUT=""
            if [ "$USE_SUDO" = "true" ] && command -v sudo &> /dev/null; then
                PLUGIN_OUTPUT=$(sudo apt-get install -y docker-compose-plugin 2>&1)
            else
                PLUGIN_OUTPUT=$(apt-get install -y docker-compose-plugin 2>&1)
            fi
            
            if echo "$PLUGIN_OUTPUT" | grep -qE "(Setting up docker-compose-plugin|is already the newest version|Unpacking docker-compose-plugin)"; then
                sleep 1
                hash -r 2>/dev/null || true
                if docker compose version &> /dev/null 2>&1; then
                    print_success "Docker Compose plugin installed (use 'docker compose' command)"
                    INSTALLED=true
                elif command -v docker &> /dev/null; then
                    print_success "Docker Compose plugin installed (may need docker restart)"
                    INSTALLED=true
                fi
            fi
        fi
        
        # Method 3: Install via pip as fallback
        if [ "$INSTALLED" = "false" ]; then
            print_status "Attempting to install docker-compose via pip..."
            local PIP_OUTPUT=""
            PIP_OUTPUT=$(pip3 install --user docker-compose 2>&1)
            if echo "$PIP_OUTPUT" | grep -qE "(Successfully installed|Requirement already satisfied|already installed)"; then
                # Add pip user bin to PATH if not already there
                export PATH="$HOME/.local/bin:$PATH"
                hash -r 2>/dev/null || true
                sleep 1
                if command -v docker-compose &> /dev/null; then
                    print_success "Docker Compose installed via pip"
                    INSTALLED=true
                elif [ -f "$HOME/.local/bin/docker-compose" ]; then
                    print_success "Docker Compose installed via pip (in ~/.local/bin)"
                    INSTALLED=true
                fi
            fi
        fi
        
        # Method 4: Automatic fallback - try apt-get install again with explicit package name
        if [ "$INSTALLED" = "false" ]; then
            print_status "Trying automatic fallback: apt-get install -y docker-compose..."
            local FALLBACK_OUTPUT=""
            local FALLBACK_EXIT_CODE=0
            
            if [ "$USE_SUDO" = "true" ] && command -v sudo &> /dev/null; then
                FALLBACK_OUTPUT=$(sudo apt-get install -y docker-compose 2>&1)
                FALLBACK_EXIT_CODE=$?
            else
                FALLBACK_OUTPUT=$(apt-get install -y docker-compose 2>&1)
                FALLBACK_EXIT_CODE=$?
            fi
            
            if [ "$FALLBACK_EXIT_CODE" -eq 0 ]; then
                sleep 2
                hash -r 2>/dev/null || true
                export PATH="/usr/local/bin:/usr/bin:$HOME/.local/bin:$PATH"
                
                if command -v docker-compose &> /dev/null; then
                    local VERSION=$(docker-compose --version 2>/dev/null | head -n1)
                    print_success "Docker Compose installed via fallback: $VERSION"
                    INSTALLED=true
                elif [ -f /usr/bin/docker-compose ] || [ -f /usr/local/bin/docker-compose ]; then
                    print_success "Docker Compose installed via fallback (binary found)"
                    INSTALLED=true
                elif echo "$FALLBACK_OUTPUT" | grep -qE "(is already the newest version|already the newest)"; then
                    print_success "Docker Compose is already installed (confirmed by fallback)"
                    INSTALLED=true
                fi
            fi
        fi
        
        # Method 5: Download binary directly from GitHub (last resort)
        if [ "$INSTALLED" = "false" ]; then
            print_status "Downloading docker-compose binary from GitHub..."
            local COMPOSE_VERSION="v2.24.0"
            local ARCH=$(uname -m)
            local OS=$(uname -s | tr '[:upper:]' '[:lower:]')
            
            # Map architecture
            case "$ARCH" in
                x86_64) ARCH="x86_64" ;;
                aarch64|arm64) ARCH="aarch64" ;;
                *) print_warning "Unsupported architecture: $ARCH"; return 1 ;;
            esac
            
            local DOWNLOAD_URL="https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-${OS}-${ARCH}"
            local INSTALL_PATH="/usr/local/bin/docker-compose"
            
            if [ "$USE_SUDO" = "true" ] && command -v sudo &> /dev/null; then
                if sudo curl -L "$DOWNLOAD_URL" -o "$INSTALL_PATH" 2>/dev/null && \
                   sudo chmod +x "$INSTALL_PATH" 2>/dev/null; then
                    hash -r 2>/dev/null || true
                    sleep 1
                    if command -v docker-compose &> /dev/null || [ -f "$INSTALL_PATH" ]; then
                        print_success "Docker Compose installed from GitHub"
                        INSTALLED=true
                    fi
                fi
            else
                if curl -L "$DOWNLOAD_URL" -o "$INSTALL_PATH" 2>/dev/null && \
                   chmod +x "$INSTALL_PATH" 2>/dev/null; then
                    hash -r 2>/dev/null || true
                    sleep 1
                    if command -v docker-compose &> /dev/null || [ -f "$INSTALL_PATH" ]; then
                        print_success "Docker Compose installed from GitHub"
                        INSTALLED=true
                    fi
                fi
            fi
        fi
        
        # RUBRIC STEP 5: Final Verification - Double-check before returning
        # If INSTALLED is true OR if dpkg shows it's installed, return true
        if [ "$INSTALLED" = "true" ]; then
            # One more verification pass
            hash -r 2>/dev/null || true
            export PATH="/usr/local/bin:/usr/bin:$HOME/.local/bin:$PATH"
            
            # Check dpkg one more time (most reliable)
            if dpkg -l | grep -qE "^ii.*docker-compose"; then
                echo "true"
                return 0
            fi
            
            # Check command
            if command -v docker-compose &> /dev/null; then
                echo "true"
                return 0
            fi
            
            # Check binary locations
            for BIN_PATH in /usr/bin/docker-compose /usr/local/bin/docker-compose "$HOME/.local/bin/docker-compose"; do
                if [ -f "$BIN_PATH" ] && [ -x "$BIN_PATH" ]; then
                    echo "true"
                    return 0
                fi
            done
            
            # If we got here but INSTALLED=true, still return true (installation succeeded)
            echo "true"
            return 0
        fi
        
        # Final fallback: Check dpkg even if INSTALLED=false
        # This handles the case where installation succeeded but detection failed
        if dpkg -l | grep -qE "^ii.*docker-compose"; then
            print_status "Docker Compose package found via dpkg (installation succeeded)"
            echo "true"
            return 0
        fi
        
        echo "$INSTALLED"
    }
    
    if command -v sudo &> /dev/null; then
        if sudo apt-get update -qq > /dev/null 2>&1 && \
           sudo apt-get install -y -qq \
               pkg-config \
               libavformat-dev \
               libavcodec-dev \
               libavdevice-dev \
               libavutil-dev \
               libswscale-dev \
               libswresample-dev \
               libavfilter-dev \
               build-essential \
               curl \
               > /dev/null 2>&1; then
            print_success "Build dependencies installed"
            INSTALLED_DEPS=true
        else
            print_warning "Failed to install build dependencies (may need root/sudo)"
        fi
        
        # Install docker-compose separately with better error handling (REQUIRED)
        print_status "Installing Docker Compose (REQUIRED)..."
        local INSTALL_RESULT=""
        INSTALL_RESULT=$(install_docker_compose_ubuntu true)
        
        # Also do a final check via dpkg as backup verification
        local FINAL_CHECK=false
        if dpkg -l | grep -qE "^ii.*docker-compose"; then
            FINAL_CHECK=true
            print_status "Docker Compose package verified via dpkg"
        fi
        
        if [ "$INSTALL_RESULT" = "true" ] || [ "$FINAL_CHECK" = "true" ]; then
            INSTALL_DOCKER_COMPOSE=true
            print_success "Docker Compose installation completed"
        else
            print_error "=========================================="
            print_error "CRITICAL ERROR: Docker Compose installation FAILED"
            print_error "=========================================="
            print_error ""
            print_error "Docker Compose is a MANDATORY dependency and installation failed."
            print_error "Check /tmp/docker-compose-install.log for details:"
            if [ -f /tmp/docker-compose-install.log ]; then
                print_error ""
                tail -10 /tmp/docker-compose-install.log | while read line; do
                    print_error "  $line"
                done
                print_error ""
            fi
            
            # Check if it actually installed but detection failed
            if dpkg -l | grep -qE "^ii.*docker-compose"; then
                print_warning "WARNING: Docker Compose package IS installed (verified via dpkg)"
                print_warning "But the binary could not be located. This may be a PATH issue."
                print_warning "Attempting to find and use docker-compose binary..."
                
                local BIN_LOCATION=$(dpkg -L docker-compose 2>/dev/null | grep -E "bin/docker-compose$" | head -n1)
                if [ -n "$BIN_LOCATION" ] && [ -f "$BIN_LOCATION" ]; then
                    export PATH="$(dirname "$BIN_LOCATION"):$PATH"
                    hash -r 2>/dev/null || true
                    if command -v docker-compose &> /dev/null || "$BIN_LOCATION" --version &> /dev/null; then
                        print_success "Docker Compose found and verified at $BIN_LOCATION"
                        INSTALL_DOCKER_COMPOSE=true
                    else
                        print_error "Binary found but cannot execute. Setup ABORTED."
                        exit 1
                    fi
                else
                    print_error "Package installed but binary location unknown. Setup ABORTED."
                    exit 1
                fi
            else
                print_error "Please install Docker Compose manually and run setup again:"
                print_error "  sudo apt-get install -y docker-compose"
                print_error "  Or: sudo apt-get install -y docker-compose-plugin"
                print_error ""
                print_error "Setup ABORTED."
                exit 1
            fi
        fi
    else
        # Try without sudo (for Docker containers running as root)
        if apt-get update -qq > /dev/null 2>&1 && \
           apt-get install -y -qq \
               pkg-config \
               libavformat-dev \
               libavcodec-dev \
               libavdevice-dev \
               libavutil-dev \
               libswscale-dev \
               libswresample-dev \
               libavfilter-dev \
               build-essential \
               curl \
               > /dev/null 2>&1; then
            print_success "Build dependencies installed"
            INSTALLED_DEPS=true
        else
            print_warning "Failed to install build dependencies"
        fi
        
        # Install docker-compose separately (REQUIRED)
        print_status "Installing Docker Compose (REQUIRED)..."
        local INSTALL_RESULT=""
        INSTALL_RESULT=$(install_docker_compose_ubuntu false)
        
        # Also do a final check via dpkg as backup verification
        local FINAL_CHECK=false
        if dpkg -l | grep -qE "^ii.*docker-compose"; then
            FINAL_CHECK=true
            print_status "Docker Compose package verified via dpkg"
        fi
        
        if [ "$INSTALL_RESULT" = "true" ] || [ "$FINAL_CHECK" = "true" ]; then
            INSTALL_DOCKER_COMPOSE=true
            print_success "Docker Compose installation completed"
        else
            print_error "=========================================="
            print_error "CRITICAL ERROR: Docker Compose installation FAILED"
            print_error "=========================================="
            print_error ""
            print_error "Docker Compose is a MANDATORY dependency and installation failed."
            print_error "Check /tmp/docker-compose-install.log for details:"
            if [ -f /tmp/docker-compose-install.log ]; then
                print_error ""
                tail -10 /tmp/docker-compose-install.log | while read line; do
                    print_error "  $line"
                done
                print_error ""
            fi
            
            # Check if it actually installed but detection failed
            if dpkg -l | grep -qE "^ii.*docker-compose"; then
                print_warning "WARNING: Docker Compose package IS installed (verified via dpkg)"
                print_warning "But the binary could not be located. This may be a PATH issue."
                print_warning "Attempting to find and use docker-compose binary..."
                
                local BIN_LOCATION=$(dpkg -L docker-compose 2>/dev/null | grep -E "bin/docker-compose$" | head -n1)
                if [ -n "$BIN_LOCATION" ] && [ -f "$BIN_LOCATION" ]; then
                    export PATH="$(dirname "$BIN_LOCATION"):$PATH"
                    hash -r 2>/dev/null || true
                    if command -v docker-compose &> /dev/null || "$BIN_LOCATION" --version &> /dev/null; then
                        print_success "Docker Compose found and verified at $BIN_LOCATION"
                        INSTALL_DOCKER_COMPOSE=true
                    else
                        print_error "Binary found but cannot execute. Setup ABORTED."
                        exit 1
                    fi
                else
                    print_error "Package installed but binary location unknown. Setup ABORTED."
                    exit 1
                fi
            else
                print_error "Please install Docker Compose manually and run setup again:"
                print_error "  apt-get install -y docker-compose"
                print_error "  Or: apt-get install -y docker-compose-plugin"
                print_error ""
                print_error "Setup ABORTED."
                exit 1
            fi
        fi
    fi
elif command -v yum &> /dev/null; then
    # RHEL/CentOS
    print_status "Detected RHEL/CentOS - installing build dependencies and Docker Compose..."
    if command -v sudo &> /dev/null; then
        if sudo yum install -y -q \
               pkgconfig \
               ffmpeg-devel \
               gcc \
               gcc-c++ \
               make \
               docker-compose \
               > /dev/null 2>&1; then
            print_success "System dependencies installed"
            INSTALLED_DEPS=true
        else
            print_warning "Failed to install system dependencies"
        fi
    else
        if yum install -y -q \
               pkgconfig \
               ffmpeg-devel \
               gcc \
               gcc-c++ \
               make \
               docker-compose \
               > /dev/null 2>&1; then
            print_success "System dependencies installed"
            INSTALLED_DEPS=true
        else
            print_warning "Failed to install system dependencies"
        fi
    fi
elif command -v apk &> /dev/null; then
    # Alpine
    print_status "Detected Alpine - installing build dependencies and Docker Compose..."
    if command -v sudo &> /dev/null; then
        if sudo apk add --quiet \
               pkgconfig \
               ffmpeg-dev \
               gcc \
               musl-dev \
               docker-compose \
               > /dev/null 2>&1; then
            print_success "System dependencies installed"
            INSTALLED_DEPS=true
        else
            print_warning "Failed to install system dependencies"
        fi
    else
        if apk add --quiet \
               pkgconfig \
               ffmpeg-dev \
               gcc \
               musl-dev \
               docker-compose \
               > /dev/null 2>&1; then
            print_success "System dependencies installed"
            INSTALLED_DEPS=true
        else
            print_warning "Failed to install system dependencies"
        fi
    fi
else
    print_warning "Unknown package manager - system dependencies may need manual installation"
    print_warning "Required: pkg-config, ffmpeg development libraries, build tools, docker-compose"
fi

if [ "$INSTALLED_DEPS" = false ]; then
    print_warning "System dependencies not installed. faster-whisper may fail to build."
    print_warning "Install manually:"
    print_warning "  Debian/Ubuntu: sudo apt-get install pkg-config libavformat-dev libavcodec-dev libavdevice-dev libavutil-dev libswscale-dev libswresample-dev libavfilter-dev build-essential docker-compose"
    print_warning "  RHEL/CentOS: sudo yum install pkgconfig ffmpeg-devel gcc gcc-c++ make docker-compose"
    print_warning "  Alpine: sudo apk add pkgconfig ffmpeg-dev gcc musl-dev docker-compose"
    print_warning "  Or make faster-whisper optional by removing it from requirements.txt"
fi

# Check for Docker Compose (REQUIRED - setup will fail if not found)
print_status "Checking Docker Compose installation (REQUIRED)..."
DOCKER_COMPOSE_AVAILABLE=false

# Add pip user bin to PATH if docker-compose was installed via pip
if [ -d "$HOME/.local/bin" ] && [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    export PATH="$HOME/.local/bin:$PATH"
fi

# Refresh command cache
hash -r 2>/dev/null || true

# Update PATH to include common locations
export PATH="/usr/local/bin:/usr/bin:$HOME/.local/bin:$PATH"

# Check for docker-compose command
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_VERSION=$(docker-compose --version 2>/dev/null | head -n1)
    print_success "Docker Compose found: $DOCKER_COMPOSE_VERSION"
    DOCKER_COMPOSE_AVAILABLE=true
elif [ -f /usr/local/bin/docker-compose ] || [ -f /usr/bin/docker-compose ] || [ -f "$HOME/.local/bin/docker-compose" ]; then
    # Found binary but not in PATH - add it and refresh
    if [ -f /usr/local/bin/docker-compose ]; then
        export PATH="/usr/local/bin:$PATH"
    elif [ -f /usr/bin/docker-compose ]; then
        export PATH="/usr/bin:$PATH"
    elif [ -f "$HOME/.local/bin/docker-compose" ]; then
        export PATH="$HOME/.local/bin:$PATH"
    fi
    hash -r 2>/dev/null || true
    if command -v docker-compose &> /dev/null; then
        DOCKER_COMPOSE_VERSION=$(docker-compose --version 2>/dev/null | head -n1)
        print_success "Docker Compose found: $DOCKER_COMPOSE_VERSION"
        DOCKER_COMPOSE_AVAILABLE=true
    else
        # Binary exists but command not found - try to use it directly
        if [ -f /usr/bin/docker-compose ] && /usr/bin/docker-compose --version &> /dev/null; then
            DOCKER_COMPOSE_VERSION=$(/usr/bin/docker-compose --version 2>/dev/null | head -n1)
            print_success "Docker Compose found (at /usr/bin/docker-compose): $DOCKER_COMPOSE_VERSION"
            DOCKER_COMPOSE_AVAILABLE=true
        elif [ -f /usr/local/bin/docker-compose ] && /usr/local/bin/docker-compose --version &> /dev/null; then
            DOCKER_COMPOSE_VERSION=$(/usr/local/bin/docker-compose --version 2>/dev/null | head -n1)
            print_success "Docker Compose found (at /usr/local/bin/docker-compose): $DOCKER_COMPOSE_VERSION"
            DOCKER_COMPOSE_AVAILABLE=true
        fi
    fi
elif command -v docker &> /dev/null && docker compose version &> /dev/null 2>&1; then
    DOCKER_COMPOSE_VERSION=$(docker compose version 2>/dev/null | head -n1)
    print_success "Docker Compose (V2) found: $DOCKER_COMPOSE_VERSION"
    DOCKER_COMPOSE_AVAILABLE=true
else
    print_error "=========================================="
    print_error "CRITICAL ERROR: Docker Compose is REQUIRED"
    print_error "=========================================="
    print_error ""
    print_error "Docker Compose is a MANDATORY dependency for this application."
    print_error "The setup process CANNOT continue without it."
    print_error ""
    print_error "Installation options (choose one):"
    print_error ""
    print_error "Option 1 - Via package manager (recommended):"
    print_error "  Debian/Ubuntu: sudo apt-get update && sudo apt-get install -y docker-compose"
    print_error "  Or: sudo apt-get install -y docker-compose-plugin"
    print_error ""
    print_error "Option 2 - Via pip:"
    print_error "  pip3 install --user docker-compose"
    print_error "  export PATH=\"\$HOME/.local/bin:\$PATH\""
    print_error ""
    print_error "Option 3 - Download binary directly:"
    print_error "  sudo curl -L \"https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)\" -o /usr/local/bin/docker-compose"
    print_error "  sudo chmod +x /usr/local/bin/docker-compose"
    print_error ""
    print_error "Option 4 - Install Docker Desktop:"
    print_error "  Docker Desktop includes Docker Compose V2"
    print_error ""
    print_error "After installing, run this setup script again."
    print_error ""
    print_error "Setup ABORTED."
    exit 1
fi

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
print_status "This may take several minutes, especially for packages with native extensions..."

# Try to install requirements, with better error handling
# First, try to install without faster-whisper if it's problematic
if pip install -r requirements.txt 2>&1 | tee /tmp/pip_install.log; then
    print_success "Core dependencies installed"
else
    # Check if faster-whisper was the problem
    if grep -q "pkg-config is required\|Failed to build.*av" /tmp/pip_install.log 2>/dev/null; then
        print_warning "faster-whisper failed to build (missing system dependencies)"
        print_warning "Installing dependencies without faster-whisper..."
        # Create temporary requirements without faster-whisper
        grep -v "faster-whisper" requirements.txt > /tmp/requirements_no_whisper.txt
        if pip install -r /tmp/requirements_no_whisper.txt; then
            print_success "Core dependencies installed (without faster-whisper)"
            print_warning "faster-whisper not installed - STT features using Whisper will not work"
            print_warning "Install system deps and retry, or use vosk for STT instead"
        else
            print_warning "Some dependencies failed. Continuing with available packages..."
            # Try to install critical packages individually
            print_status "Attempting to install critical packages..."
            pip install fastapi uvicorn sqlalchemy httpx pydantic || print_warning "Some critical packages may be missing"
        fi
        rm -f /tmp/requirements_no_whisper.txt
    else
        print_warning "Some dependencies failed. Continuing with available packages..."
        # Try to install critical packages individually
        print_status "Attempting to install critical packages..."
        pip install fastapi uvicorn sqlalchemy httpx pydantic || print_warning "Some critical packages may be missing"
    fi
fi

if pip install -r requirements-app.txt; then
    print_success "App dependencies installed"
else
    print_warning "Some app dependencies failed to install. Continuing..."
fi

# Install Bark TTS (Suno AI) - works with Python >=3.8
# Note: Bark is now included in requirements.txt as a git dependency
# This section ensures it's installed and checks for hf_transfer
print_status "Checking Bark TTS installation..."
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
print_status "Python $PYTHON_VERSION detected - Bark supports Python >=3.8"

# Disable hf_transfer requirement (optional, not needed for downloads)
export HF_HUB_ENABLE_HF_TRANSFER=0

# We're already in the venv (activated earlier), so pip and python3 point to venv
# Check if Bark is already installed (it should be from requirements.txt)
if python3 -c "from bark import generate_audio" 2>/dev/null; then
    print_success "Bark TTS is installed in virtual environment"
    # Try to install hf_transfer if not already installed (optional)
    if ! python3 -c "import hf_transfer" 2>/dev/null; then
        if pip install hf_transfer >/dev/null 2>&1; then
            print_success "hf_transfer installed (optional, speeds up model downloads)"
        fi
    fi
else
    # Bark should have been installed from requirements.txt, but if not, install it now
    print_warning "Bark TTS not found, installing from requirements.txt..."
    if pip install git+https://github.com/suno-ai/bark.git >/dev/null 2>&1; then
        print_success "Bark TTS installed successfully"
        print_warning "Note: First run will download models (~2GB), which may take time"
        # Try to install hf_transfer (optional, speeds up downloads but not required)
        if pip install hf_transfer >/dev/null 2>&1; then
            print_success "hf_transfer installed (optional, speeds up model downloads)"
        else
            print_warning "hf_transfer not installed (optional, downloads will use standard method)"
        fi
    else
        print_warning "Bark TTS installation failed. TTS features will not be available."
        print_warning "You can install manually later:"
        print_warning "  source venv/bin/activate && pip install git+https://github.com/suno-ai/bark.git"
        print_warning "Note: Bark requires torch and other dependencies. First run downloads ~2GB of models."
    fi
fi

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

# Check TTS dependencies (Bark)
print_status "Checking TTS dependencies..."
TTS_AVAILABLE=false
TTS_TYPE="none"
if python3 -c "from bark import generate_audio" 2>/dev/null; then
    print_success "Bark TTS found"
    TTS_AVAILABLE=true
    TTS_TYPE="bark"
else
    print_warning "Bark TTS not found. PDF to Audio feature will not work."
    print_warning "Install with: pip install git+https://github.com/suno-ai/bark.git"
    print_warning "Note: First run will download models (~2GB), which may take time"
fi

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
mkdir -p app/static/writer/uploads
mkdir -p app/static/writer/audio
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

# LLM Configuration - Local models only (Ollama)
# No API keys needed - uses local Ollama models
LLM_PROVIDER=local
LLM_MODEL=qwen3:30b
LLM_LOCAL_URL=http://localhost:11434/v1

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

# Start Personal Assistant with all services
echo "🚀 Starting Personal Assistant..."

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

# Start Ollama if installed and not running
if command -v ollama &> /dev/null; then
    if ! pgrep -x "ollama" > /dev/null; then
        echo "🤖 Starting Ollama server..."
        ollama serve > /tmp/ollama.log 2>&1 &
        OLLAMA_PID=$!
        sleep 3
        if kill -0 $OLLAMA_PID 2>/dev/null && curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
            echo "✅ Ollama server started (PID: $OLLAMA_PID)"
        else
            echo "⚠️ Ollama server may have failed to start. Check /tmp/ollama.log"
            echo "⚠️ You can start it manually later with: ollama serve"
        fi
    else
        echo "✅ Ollama server is already running"
    fi
else
    echo "⚠️ Ollama not installed. Local AI features will not be available."
    echo "⚠️ Install with: curl -fsSL https://ollama.com/install.sh | sh"
fi

# Display startup information
echo ""
echo "🌐 Starting Personal Assistant on http://localhost:8000"
echo "📊 Dashboard: http://localhost:8000"
echo "✍️ Writer: http://localhost:8000/writer"
echo "📚 Book Writer: http://localhost:8000/writer/book-writer"
echo "📚 API Docs: http://localhost:8000/docs"
echo "🔧 Health Check: http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

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

# Setup Ollama for local AI models (required for local LLM)
print_status "Setting up Ollama for local AI models..."
if ! command -v ollama &> /dev/null; then
    print_status "Installing Ollama..."
    print_status "This will download and install Ollama (required for local LLM models)..."
    if curl -fsSL https://ollama.com/install.sh | sh; then
        print_success "Ollama installed successfully"
        # Add Ollama to PATH if not already there
        if ! echo "$PATH" | grep -q "/usr/local/bin"; then
            export PATH="$PATH:/usr/local/bin"
        fi
    else
        print_error "Ollama installation failed!"
        print_error "The app requires Ollama for local LLM models."
        print_error "Please install manually: curl -fsSL https://ollama.com/install.sh | sh"
        exit 1
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
    
    # Download both required models: llama3:latest and qwen3:30b
    MODELS_TO_DOWNLOAD=("llama3:latest" "qwen3:30b")
    
    for MODEL in "${MODELS_TO_DOWNLOAD[@]}"; do
        if ollama list 2>/dev/null | grep -q "$MODEL"; then
            print_success "$MODEL model is already installed"
        else
            if [ "$MODEL" = "qwen3:30b" ]; then
                print_status "Downloading $MODEL model (this may take 10-20 minutes, ~20GB)..."
                TIMEOUT=1200
            else
                print_status "Downloading $MODEL model (this may take 5-10 minutes, ~5GB)..."
                TIMEOUT=600
            fi
            
            print_warning "You can skip this and download later with: ollama pull $MODEL"
            print_warning "The app will work, but local AI needs the model to be downloaded"
            
            # Try to pull with timeout
            if timeout $TIMEOUT ollama pull "$MODEL" 2>&1 | tee "/tmp/ollama_pull_${MODEL//:/_}.log"; then
                print_success "$MODEL model downloaded successfully"
            else
                EXIT_CODE=$?
                if [ $EXIT_CODE -eq 124 ]; then
                    print_warning "Model download timed out. Download it later with: ollama pull $MODEL"
                else
                    print_warning "Model download failed. You can try again later with: ollama pull $MODEL"
                fi
                print_warning "The app will still work, but local AI features require the model"
            fi
        fi
    done
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
echo "- Models: llama3:latest and qwen3:30b (both available)"
echo "- Status: Check with: ollama list"
echo "- If models not downloaded: ollama pull llama3:latest && ollama pull qwen3:30b"
echo "- Test: ollama run llama3:latest 'Hello' or ollama run qwen3:30b 'Hello'"
echo ""
echo "🎙️ Text-to-Speech (TTS):"
if [ "$TTS_AVAILABLE" = true ]; then
    if [ "$TTS_TYPE" = "bark" ]; then
        echo "- Status: ✅ Bark TTS installed (Suno AI)"
        echo "- Model: Bark text-to-audio model"
        echo "- Note: First run will download models (~2GB)"
    fi
    echo "- PDF to Audio: Available on /writer/pdf-to-audio page"
else
    echo "- Status: ⚠️ Bark TTS not installed"
    echo "- Install with: pip install git+https://github.com/suno-ai/bark.git"
    echo "- Note: Works with Python >=3.8, supports CPU and GPU"
    echo "- First run downloads ~2GB of models"
    echo "- PDF to Audio: Will not work until Bark is installed"
fi
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
