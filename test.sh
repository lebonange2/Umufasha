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
