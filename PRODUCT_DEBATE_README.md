# 1-Sigma Novelty Explorer

A fully functioning application that uses two autonomous AI agents in structured debate to brainstorm and converge on feasible new commercial products. The agents search the "adjacent possible" within ≈ one standard deviation of novelty to discover opportunities that are realistically buildable and sellable within 6–18 months.

## Features

- **Two Autonomous Agents**: 
  - **Agent A (Opportunity Seeker)**: Uses OpenAI GPT-4 to enumerate small deviations and articulate value
  - **Agent B (Skeptical Builder)**: Uses Anthropic Claude to attack proposals on feasibility and refine them

- **Novelty Scoring**: Measures product novelty using feature vectorization and sigma distance from known products

- **Feasibility Analysis**: Comprehensive checks for BOM costs, manufacturing, compliance, channel fit, and unit economics

- **Debate Protocol**: Structured rounds of proposal, attack, and convergence

- **Export Functionality**: Generates taxonomy, one-pager, BOM CSV, and debate log

## Setup

### Prerequisites

- Python 3.11+
- OpenAI API key
- Anthropic API key

### Installation

1. **Set environment variables**:

```bash
export OPENAI_API_KEY=your_openai_key_here
export ANTHROPIC_API_KEY=sk-ant-your_anthropic_key_here
```

2. **Install dependencies** (if not already installed):

```bash
pip install -r requirements-app.txt
```

The required packages are already in `requirements-app.txt`:
- `fastapi`
- `httpx` (for LLM clients)
- `numpy` (for scoring)
- `pydantic` (for models)

## Usage

### CLI Interface

Run a debate session from the command line:

```bash
# Basic usage
python -m app.product_debate.cli --seed 42 --temperature 0.7 --max-rounds 6

# With custom market and category
python -m app.product_debate.cli \
  --seed 42 \
  --temperature 0.7 \
  --max-rounds 6 \
  --core-market "Consumer Electronics" \
  --category "Portable Power"

# With CSV file of known products
python -m app.product_debate.cli \
  --seed 42 \
  --temperature 0.7 \
  --max-rounds 6 \
  --csv products.csv
```

**CLI Arguments**:
- `--seed`: Random seed for determinism (default: 42)
- `--temperature`: Sampling temperature (default: 0.7)
- `--max-rounds`: Maximum debate rounds (default: 6)
- `--core-market`: Core market name (optional)
- `--category`: Product category (optional)
- `--csv`: Path to CSV file with known products (optional)

### Web Interface

1. **Start the FastAPI server**:

```bash
python -m app.main
# or
uvicorn app.main:app --reload
```

2. **Access the web interface**:

Open http://localhost:8000/product-debate in your browser

3. **Run a session**:
   - Fill in the form (seed, temperature, max rounds, etc.)
   - Optionally upload a CSV file with known products
   - Click "Start Debate"
   - View results and download exports

### API Endpoints

#### Start Debate Session

```bash
POST /api/product-debate/start
Content-Type: application/json

{
  "seed": 42,
  "temperature": 0.7,
  "max_rounds": 6,
  "core_market": "Consumer Electronics",
  "category": "Portable Power"
}
```

#### Start Debate with CSV

```bash
POST /api/product-debate/start-with-csv
Content-Type: multipart/form-data

seed=42
temperature=0.7
max_rounds=6
core_market=Consumer Electronics
category=Portable Power
csv_file=<file>
```

#### List Sessions

```bash
GET /api/product-debate/sessions
```

#### Get Session

```bash
GET /api/product-debate/sessions/{session_id}
```

#### Download Export

```bash
GET /api/product-debate/sessions/{session_id}/export/{export_type}
```

Export types: `taxonomy`, `one_pager`, `bom`, `debate_log`

## CSV Format

If you want to provide your own known products via CSV, use this format:

```csv
name,functional_attributes,target_user,price_band,channel,materials,regulations,pain_points
Portable Power Station,"battery,portable,AC outlet",consumer,$200-500,Amazon,"lithium battery,plastic housing",FCC,"heavy,slow charging"
Smart Water Bottle,"hydration tracking,app connected",consumer,$40-80,Amazon,"stainless steel,electronics",FCC,"battery life,cleaning"
```

## Output

When a debate session completes successfully, the following files are generated in the `out/` directory:

1. **taxonomy.txt**: Product taxonomy structure (also printed to stdout)
2. **concept_onepager.md**: Detailed one-pager with user story, features, financials, BOM, risks, etc.
3. **bom.csv**: Bill of Materials with component costs and MOQs
4. **debate_log.json**: Complete debate session log with all rounds, proposals, and analyses

Session data is also saved to `sessions/{session_id}/session.json`.

## How It Works

### Debate Protocol

1. **Seed Selection**: Selects a core market and category from known products
2. **Deviation Proposals (Agent A)**: Generates 5-10 "1-σ" deviations with scoring:
   - User Value (0-10)
   - Novelty σ (target 0.5-1.0)
   - Complexity (0-10, lower is better)
3. **Feasibility Attack (Agent B)**: For each proposal, flags blockers and suggests fixes
4. **Convergence**: Computes Composite Score = 0.4*UserValue + 0.3*(1-Complexity/10) + 0.3*(1-|σ-0.75|) and keeps top 3
5. **Deepen Concept**: Produces a mini one-pager with full details
6. **Stop Condition**: Stops when Composite ≥ 7.5/10 and margin ≥ 45%, or after max_rounds

### Novelty Scoring

Products are represented as feature vectors with:
- Functional attributes
- Target user
- Price band
- Channel
- Materials
- Regulations
- Pain points

Novelty is measured as the sigma distance (z-score) from the centroid of known products in the category. Target: 0.5-1.0 σ (adjacent innovation, not moonshots).

### Feasibility Checks

Agent B evaluates:
- **BOM Cost**: Unit cost at MOQ 500/1000
- **Manufacturing**: DFM notes, processes, tooling
- **Compliance**: FCC/CE/UL/EPA/USDA/etc.
- **Channel Fit**: DTC/Amazon/B2B/etc.
- **Operational Complexity**: Assembly, fulfillment, etc.

## Example Session

```bash
$ python -m app.product_debate.cli --seed 42 --temperature 0.7 --max-rounds 6

Starting debate session:
  Session ID: abc123...
  Seed: 42
  Temperature: 0.7
  Max Rounds: 6
  Core Market: Consumer Electronics
  Category: Portable Power

Using 5 known products
Running debate...

Session saved to: sessions/abc123.../

Exports:
  taxonomy: out/taxonomy.txt
  one_pager: out/concept_onepager.md
  bom: out/bom.csv
  debate_log: out/debate_log.json

=== TAXONOMY ===

Core Market
  • Consumer Electronics

Category
  • Portable Power
  • Energy Storage

Subcategory
  • Portable Chargers
  • Solar Power Stations

...

=== SUMMARY ===
Rounds completed: 4
Go threshold met: True
Final concept: Compact Solar Power Bank with Wireless Charging
Gross margin: 48.2%
```

## Testing

Run tests:

```bash
pytest tests/test_product_debate.py -v
```

## Docker (Optional)

To run with Docker:

```bash
# Build
docker build -t product-debate -f docker/Dockerfile.web .

# Run
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=your_key \
  -e ANTHROPIC_API_KEY=your_key \
  product-debate
```

Or use docker-compose:

```bash
docker-compose up --build
```

## Known Products

The system comes with a curated list of known products including:
- Portable Power Station
- Mealworm Protein Powder
- Modular Chicken Coop
- Compact Hydroponic Saffron Rack
- Smart Water Bottle
- Ergonomic Standing Desk Converter
- Portable Espresso Maker
- Indoor Air Quality Monitor

You can extend this list by providing a CSV file or modifying `app/product_debate/data.py`.

## Guardrails

- Never proposes illegal, unsafe, or deceptive products
- Respects PII and content policies
- Keeps novelty within the specified σ band
- Terminates gracefully if no feasible concepts remain

## Troubleshooting

### API Key Errors

Make sure both API keys are set:

```bash
echo $OPENAI_API_KEY
echo $ANTHROPIC_API_KEY
```

### No Proposals Generated

- Check that known products are available for the selected category
- Try a different category or provide a CSV file
- Increase temperature slightly (e.g., 0.8)

### Go Threshold Not Met

- Increase max_rounds to allow more refinement
- Try different seed values
- Adjust temperature (lower = more focused, higher = more creative)

## License

MIT License

