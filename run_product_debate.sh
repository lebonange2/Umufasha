#!/bin/bash
# Quick start script for Product Debate system

# Check for API keys
if [ -z "$OPENAI_API_KEY" ]; then
    echo "ERROR: OPENAI_API_KEY environment variable is not set"
    exit 1
fi

if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "ERROR: ANTHROPIC_API_KEY environment variable is not set"
    exit 1
fi

# Run the debate CLI
python -m app.product_debate.cli "$@"

