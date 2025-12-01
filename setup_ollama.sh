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
else
    echo "Installing Ollama..."
    
    # Install Ollama
    curl -fsSL https://ollama.com/install.sh | sh
    
    echo "✓ Ollama installed successfully"
fi

echo ""
echo "Starting Ollama service..."

# Start Ollama in the background if not already running
if ! pgrep -x "ollama" > /dev/null; then
    # Start Ollama server
    ollama serve &
    OLLAMA_PID=$!
    echo "Ollama server started (PID: $OLLAMA_PID)"
    
    # Wait a moment for server to start
    sleep 3
else
    echo "✓ Ollama server is already running"
fi

echo ""
echo "Pulling llama3.1 model (this may take a while)..."
echo "This will download the model - it's large (~4-8GB depending on variant)"
echo ""

# Pull the llama3.1 model
ollama pull llama3.1

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Ollama is now running with llama3.1 model"
echo ""
echo "Test it with:"
echo "  ollama run llama3.1 'Hello, how are you?'"
echo ""
echo "Or test the API:"
echo "  curl http://localhost:11434/api/generate -d '{\"model\": \"llama3.1\", \"prompt\": \"Hello\"}'"
echo ""
echo "Your FastAPI app should now use the local model by default!"
echo ""

