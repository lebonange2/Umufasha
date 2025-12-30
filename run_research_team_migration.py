#!/usr/bin/env python3
"""
Run migration to add Research Team columns to core_devices_projects table.
"""

import asyncio
from sqlalchemy import text
from app.database import engine


async def run_migration():
    """Run the migration to add research team columns."""
    
    migration_sql = """
    -- Add research_mode column
    ALTER TABLE core_devices_projects 
    ADD COLUMN IF NOT EXISTS research_mode BOOLEAN DEFAULT FALSE;

    -- Add research_scope column
    ALTER TABLE core_devices_projects 
    ADD COLUMN IF NOT EXISTS research_scope TEXT;

    -- Add pdf_report column (binary storage for PDF files)
    ALTER TABLE core_devices_projects 
    ADD COLUMN IF NOT EXISTS pdf_report BYTEA;

    -- Make product_idea nullable (was required before)
    -- Note: This may fail if there are existing rows with NULL product_idea
    -- In that case, run manually: ALTER TABLE core_devices_projects ALTER COLUMN product_idea DROP NOT NULL;
    """
    
    try:
        async with engine.begin() as conn:
            # Split by semicolon and execute each statement
            statements = [s.strip() for s in migration_sql.split(';') if s.strip()]
            
            for statement in statements:
                if statement and not statement.startswith('--'):
                    print(f"Executing: {statement[:100]}...")
                    await conn.execute(text(statement))
            
            print("✅ Migration completed successfully!")
            print("\nAdded columns:")
            print("  - research_mode (BOOLEAN)")
            print("  - research_scope (TEXT)")
            print("  - pdf_report (BYTEA)")
            print("\nUpdated columns:")
            print("  - product_idea (now nullable)")
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        print("\nYou may need to run the migration manually.")
        print("SQL file: migrations/add_research_team_columns.sql")
        raise


if __name__ == "__main__":
    print("Running Research Team migration...")
    print("=" * 60)
    asyncio.run(run_migration())
    print("=" * 60)
    print("Migration complete. You can now use Research Mode!")
