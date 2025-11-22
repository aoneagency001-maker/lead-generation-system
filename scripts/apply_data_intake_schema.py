#!/usr/bin/env python3
"""
Apply Data Intake Schema to Supabase

Creates the three-layer data architecture tables:
- L1: raw_events
- L2: normalized_events
- L3: feature_store

Usage:
    python scripts/apply_data_intake_schema.py
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

load_dotenv()


def apply_schema():
    """Apply the data intake schema to Supabase."""
    from supabase import create_client

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")

    if not url or not key:
        print("Error: SUPABASE_URL and SUPABASE_KEY must be set")
        sys.exit(1)

    # Read schema file
    schema_path = project_root / "data_intake" / "database" / "schema.sql"
    if not schema_path.exists():
        print(f"Error: Schema file not found: {schema_path}")
        sys.exit(1)

    schema_sql = schema_path.read_text()

    print(f"Connecting to Supabase: {url[:50]}...")

    client = create_client(url, key)

    # Execute schema
    # Note: Supabase REST API doesn't support raw SQL execution directly
    # You need to run this via SQL Editor in Supabase Dashboard
    # or use pg connection directly

    print("\n" + "=" * 60)
    print("SCHEMA SQL TO EXECUTE")
    print("=" * 60)
    print("\nCopy the SQL below and run it in Supabase SQL Editor:")
    print("https://app.supabase.com/project/YOUR_PROJECT/sql/new")
    print("\n" + "-" * 60 + "\n")
    print(schema_sql)
    print("\n" + "-" * 60)
    print("\nAlternatively, use psql to connect directly:")
    print("psql $DATABASE_URL < data_intake/database/schema.sql")
    print("=" * 60)


if __name__ == "__main__":
    apply_schema()
