#!/usr/bin/env python3
"""Initialize the database with tables."""
import asyncio
import sys
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import engine
from app.models import Base


async def init_database():
    """Initialize the database with all tables."""
    print("🗄️ Initializing database...")
    
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        print("✅ Database tables created successfully!")
        
    except Exception as e:
        print(f"❌ Failed to create database tables: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(init_database())
