#!/bin/bash

# Stop Personal Assistant
echo "🛑 Stopping Personal Assistant..."

# Kill any running uvicorn processes
pkill -f uvicorn

echo "✅ Personal Assistant stopped"
