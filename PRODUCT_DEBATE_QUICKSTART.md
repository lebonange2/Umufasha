# Product Debate System - Quick Start

## One-Command Setup

```bash
# Set API keys
export OPENAI_API_KEY=your_key_here
export ANTHROPIC_API_KEY=sk-ant-your_key_here

# Install dependencies (if needed)
pip install -r requirements-app.txt
```

## One-Command Run

### CLI

```bash
# Basic run
python -m app.product_debate.cli --seed 42 --temperature 0.7 --max-rounds 6

# Or use the helper script
./run_product_debate.sh --seed 42 --temperature 0.7 --max-rounds 6
```

### Web UI

```bash
# Start server
python -m app.main
# or
uvicorn app.main:app --reload

# Open browser
open http://localhost:8000/product-debate
```

### Docker (if configured)

```bash
docker-compose up --build
```

## Example with CSV

```bash
python -m app.product_debate.cli \
  --seed 42 \
  --temperature 0.7 \
  --max-rounds 6 \
  --csv examples/product_debate_example.csv
```

## Output

After running, check:
- `out/taxonomy.txt` - Product taxonomy
- `out/concept_onepager.md` - Full concept details
- `out/bom.csv` - Bill of materials
- `out/debate_log.json` - Complete session log
- `sessions/{session_id}/session.json` - Session data

Taxonomy is also printed to stdout.

## See Also

- **[Full Documentation](PRODUCT_DEBATE_README.md)** - Complete guide with all features
- **[Examples](examples/)** - Example CSV files and scripts

