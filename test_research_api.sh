#!/bin/bash

echo "================================"
echo "Research Phase API Test"
echo "================================"
echo ""

# Set to use mock LLM
export USE_MOCK_LLM=true

# Base URL
BASE_URL="http://localhost:8000"

# Step 1: Create a new project in research mode
echo "Step 1: Creating project in research mode..."
PROJECT_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/core-devices/projects" \
  -H "Content-Type: application/json" \
  -d '{
    "product_idea": "",
    "primary_need": "",
    "research_mode": true,
    "research_scope": "Explore opportunities in consumer electronics for everyday needs",
    "model": "mock"
  }')

echo "$PROJECT_RESPONSE" | jq '.'

PROJECT_ID=$(echo "$PROJECT_RESPONSE" | jq -r '.id')

if [ "$PROJECT_ID" = "null" ] || [ -z "$PROJECT_ID" ]; then
  echo "❌ Failed to create project"
  exit 1
fi

echo "✅ Project created: $PROJECT_ID"
echo ""

# Step 2: Execute research phase
echo "Step 2: Executing research phase..."
EXECUTE_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/core-devices/projects/${PROJECT_ID}/execute-research" \
  -H "Content-Type: application/json")

echo "$EXECUTE_RESPONSE" | jq '.'
echo ""

# Step 3: Poll for completion (check every 2 seconds, max 30 seconds)
echo "Step 3: Waiting for research to complete..."
MAX_ATTEMPTS=15
ATTEMPT=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
  ATTEMPT=$((ATTEMPT + 1))
  echo "  Checking status (attempt $ATTEMPT/$MAX_ATTEMPTS)..."
  
  STATUS_RESPONSE=$(curl -s "${BASE_URL}/api/core-devices/projects/${PROJECT_ID}/phase-status")
  STATUS=$(echo "$STATUS_RESPONSE" | jq -r '.status')
  
  echo "    Status: $STATUS"
  
  if [ "$STATUS" = "completed" ]; then
    echo "✅ Research phase completed!"
    echo ""
    echo "Full status response:"
    echo "$STATUS_RESPONSE" | jq '.'
    break
  elif [ "$STATUS" = "failed" ]; then
    echo "❌ Research phase failed!"
    echo "$STATUS_RESPONSE" | jq '.'
    exit 1
  fi
  
  sleep 2
done

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
  echo "❌ Timeout waiting for research completion"
  exit 1
fi

# Step 4: Get final project state
echo ""
echo "Step 4: Getting final project state..."
FINAL_RESPONSE=$(curl -s "${BASE_URL}/api/core-devices/projects/${PROJECT_ID}")
echo "$FINAL_RESPONSE" | jq '.artifacts.research_discovery | keys'

echo ""
echo "================================"
echo "✅ ALL TESTS PASSED!"
echo "================================"
