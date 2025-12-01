#!/bin/bash

# Start Personal Assistant
echo "🚀 Starting Personal Assistant..."

# Activate virtual environment
source venv/bin/activate

# Start the application
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
