#!/usr/bin/env python3
"""Initialize Neo4j schema."""
import sys
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.graph.schema import create_constraints_and_indexes

if __name__ == "__main__":
    print("Initializing Neo4j schema...")
    create_constraints_and_indexes()
    print("✅ Schema initialization complete!")

