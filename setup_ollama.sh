#!/bin/bash
# Setup script for Ollama on RunPod GPU
# This installs and configures Ollama to run locally with GPU support

set -e

echo "=== Ollama Setup for RunPod GPU ==="
echo ""

# Check if Ollama is already installed
if command -v ollama &> /dev/null; then
    echo "✓ Ollama is already installed"
    ollama --version
    OLLAMA_INSTALLED=true
else
    echo "Installing Ollama..."
    
    # Install Ollama
    if curl -fsSL https://ollama.com/install.sh | sh; then
        echo "✓ Ollama installed successfully"
        
        # Add to PATH
        export PATH="$PATH:/usr/local/bin"
        hash -r 2>/dev/null || true
        
        # Verify installation
        sleep 2
        if command -v ollama &> /dev/null; then
            OLLAMA_INSTALLED=true
            ollama --version
        else
            echo "⚠️ Installation completed but ollama command not found in PATH"
            echo "Trying to locate ollama binary..."
            if [ -f /usr/local/bin/ollama ]; then
                export PATH="$PATH:/usr/local/bin"
                hash -r 2>/dev/null || true
                if command -v ollama &> /dev/null; then
                    OLLAMA_INSTALLED=true
                    echo "✓ Found ollama at /usr/local/bin/ollama"
                fi
            fi
        fi
    else
        echo "❌ Ollama installation failed!"
        exit 1
    fi
fi

if [ "$OLLAMA_INSTALLED" != true ]; then
    echo "❌ Ollama is not installed or not accessible"
    exit 1
fi

echo ""
echo "Starting Ollama service..."

# Check if Ollama is already running
OLLAMA_RUNNING=false
if pgrep -x "ollama" > /dev/null 2>&1; then
    OLLAMA_RUNNING=true
fi

# Check if API is accessible
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    OLLAMA_RUNNING=true
    echo "✓ Ollama server is already running and accessible"
fi

# Start Ollama if not running
if [ "$OLLAMA_RUNNING" = false ]; then
    echo "Starting Ollama server in background..."
    
    # Ensure PATH is set
    export PATH="$PATH:/usr/local/bin"
    hash -r 2>/dev/null || true
    
    # Start with nohup to persist
    nohup ollama serve > /tmp/ollama.log 2>&1 &
    OLLAMA_PID=$!
    
    echo "Ollama server starting (PID: $OLLAMA_PID)..."
    
    # Wait for server to be ready
    echo "Waiting for Ollama to be ready..."
    for i in {1..15}; do
        sleep 2
        if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
            echo "✓ Ollama server is ready!"
            OLLAMA_RUNNING=true
            break
        fi
        echo -n "."
    done
    echo ""
    
    if [ "$OLLAMA_RUNNING" = false ]; then
        echo "⚠️ Ollama server may not have started properly"
        echo "Check logs: tail -f /tmp/ollama.log"
        echo "Try manually: ollama serve"
    fi
fi

# Verify Ollama is accessible
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo ""
    echo "✓ Ollama API is accessible at http://localhost:11434"
    
    # List installed models
    echo ""
    echo "Installed models:"
    ollama list || echo "  (none yet)"
    
    echo ""
    echo "=== Setup Complete ==="
    echo ""
    echo "Ollama is running and ready to use!"
    echo ""
    echo "To pull models:"
    echo "  ollama pull llama3:latest"
    echo "  ollama pull qwen3:30b"
    echo ""
    echo "Test it with:"
    echo "  curl http://localhost:11434/api/tags"
    echo ""
    echo "Or run a model:"
    echo "  ollama run llama3:latest 'Hello'"
    echo ""
else
    echo "❌ Ollama API is not accessible"
    echo "Check if server is running: pgrep -x ollama"
    echo "Check logs: tail -f /tmp/ollama.log"
    exit 1
fi

