#!/bin/bash
# Example script to run a product debate session

# Set API keys (or export them in your environment)
export OPENAI_API_KEY=${OPENAI_API_KEY:-"your_key_here"}
export ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-"your_key_here"}

# Run debate with default settings
python -m app.product_debate.cli \
  --seed 42 \
  --temperature 0.7 \
  --max-rounds 6 \
  --core-market "Consumer Electronics" \
  --category "Portable Power"

# Or with CSV file
# python -m app.product_debate.cli \
#   --seed 42 \
#   --temperature 0.7 \
#   --max-rounds 6 \
#   --csv examples/product_debate_example.csv

