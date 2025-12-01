"""CLI interface for product debate system."""
import asyncio
import argparse
import sys
from pathlib import Path
from app.product_debate.debate import DebateOrchestrator
from app.product_debate.storage import SessionStorage
from app.product_debate.exporter import SessionExporter
from app.product_debate.data import KNOWN_PRODUCTS, get_products_by_category, load_products_from_csv
from app.core.config import settings


async def run_debate(
    seed: int = 42,
    temperature: float = 0.7,
    max_rounds: int = 6,
    core_market: str = None,
    category: str = None,
    csv_file: str = None
):
    """Run a debate session from CLI.
    
    Args:
        seed: Random seed
        temperature: Sampling temperature
        max_rounds: Maximum debate rounds
        core_market: Core market name
        category: Product category
        csv_file: Path to CSV file with known products
    """
    import uuid
    
    # Validate API keys
    if not settings.OPENAI_API_KEY:
        print("ERROR: OPENAI_API_KEY environment variable is not set", file=sys.stderr)
        sys.exit(1)
    if not settings.ANTHROPIC_API_KEY:
        print("ERROR: ANTHROPIC_API_KEY environment variable is not set", file=sys.stderr)
        sys.exit(1)
    
    # Generate session ID
    session_id = str(uuid.uuid4())
    
    # Load known products
    if csv_file:
        known_products = load_products_from_csv(csv_file)
        if not known_products:
            print(f"ERROR: No products loaded from CSV file: {csv_file}", file=sys.stderr)
            sys.exit(1)
        print(f"Loaded {len(known_products)} products from CSV")
    else:
        if category:
            known_products = get_products_by_category(category)
        else:
            known_products = KNOWN_PRODUCTS[:5]
        print(f"Using {len(known_products)} known products")
    
    # Determine core market and category
    core_market = core_market or "Consumer Electronics"
    category = category or "Portable Power"
    
    print(f"\nStarting debate session:")
    print(f"  Session ID: {session_id}")
    print(f"  Seed: {seed}")
    print(f"  Temperature: {temperature}")
    print(f"  Max Rounds: {max_rounds}")
    print(f"  Core Market: {core_market}")
    print(f"  Category: {category}")
    print()
    
    # Create orchestrator
    orchestrator = DebateOrchestrator(
        session_id=session_id,
        seed=seed,
        temperature=temperature,
        max_rounds=max_rounds,
        core_market=core_market,
        category=category,
        known_products=known_products
    )
    
    # Run debate
    try:
        print("Running debate...")
        session = await orchestrator.run_debate()
        
        # Save session
        storage = SessionStorage()
        storage.save_session(session)
        print(f"\nSession saved to: sessions/{session_id}/")
        
        # Export results
        exporter = SessionExporter()
        session_path = storage.get_session_path(session_id)
        exports = exporter.export_session(session, session_path)
        
        print("\nExports:")
        for export_type, path in exports.items():
            print(f"  {export_type}: {path}")
        
        # Print taxonomy to stdout (exact format as required)
        if session.taxonomy:
            print("\n=== TAXONOMY ===\n")
            for level, items in session.taxonomy.items():
                if items:
                    print(f"• {level}")
                    for item in items:
                        print(f"  • {item}")
        else:
            print("\nNo taxonomy generated (concept did not meet Go Threshold)")
        
        # Print summary
        print(f"\n=== SUMMARY ===")
        print(f"Rounds completed: {len(session.rounds)}")
        print(f"Go threshold met: {session.go_threshold_met}")
        if session.final_concept:
            print(f"Final concept: {session.final_concept.name}")
            print(f"Gross margin: {session.final_concept.gross_margin:.1f}%")
        
        return 0
    except Exception as e:
        print(f"\nERROR: Debate failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="1-Sigma Novelty Explorer: AI agents debate to find feasible products"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for determinism (default: 42)"
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.7,
        help="Sampling temperature (default: 0.7)"
    )
    parser.add_argument(
        "--max-rounds",
        type=int,
        default=6,
        help="Maximum debate rounds (default: 6)"
    )
    parser.add_argument(
        "--core-market",
        type=str,
        help="Core market name (default: Consumer Electronics)"
    )
    parser.add_argument(
        "--category",
        type=str,
        help="Product category (default: Portable Power)"
    )
    parser.add_argument(
        "--csv",
        type=str,
        help="Path to CSV file with known products"
    )
    
    args = parser.parse_args()
    
    exit_code = asyncio.run(run_debate(
        seed=args.seed,
        temperature=args.temperature,
        max_rounds=args.max_rounds,
        core_market=args.core_market,
        category=args.category,
        csv_file=args.csv
    ))
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

