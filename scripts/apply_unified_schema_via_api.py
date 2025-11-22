#!/usr/bin/env python3
"""
Apply unified_analytics_schema.sql via Supabase REST API
Uses SUPABASE_SERVICE_KEY (already in .env)
"""

import os
import sys
from pathlib import Path

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(override=True)

from supabase import create_client

def main():
    print("=" * 60)
    print("Applying Unified Analytics Schema via Supabase API")
    print("=" * 60)

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")

    if not url or not key:
        print("ERROR: SUPABASE_URL or SUPABASE_KEY not found in .env")
        return 1

    print(f"Supabase URL: {url}")
    print(f"Using service key: {'yes' if os.getenv('SUPABASE_SERVICE_KEY') else 'no (anon key)'}")

    # Read schema
    schema_path = Path(__file__).parent / "unified_analytics_schema.sql"
    if not schema_path.exists():
        print(f"ERROR: Schema file not found: {schema_path}")
        return 1

    print(f"\nReading schema from {schema_path.name}...")

    # Create client
    client = create_client(url, key)

    # Test connection by checking existing tables
    print("\nChecking existing tables...")
    try:
        # Try to query unified_metrics to see if it exists
        result = client.table("unified_metrics").select("id").limit(1).execute()
        print("  unified_metrics: EXISTS")
    except Exception as e:
        if "Could not find" in str(e) or "PGRST205" in str(e):
            print("  unified_metrics: NOT FOUND (needs creation)")
        else:
            print(f"  unified_metrics: ERROR - {e}")

    try:
        result = client.table("analytics_insights").select("id").limit(1).execute()
        print("  analytics_insights: EXISTS")
    except Exception as e:
        if "Could not find" in str(e) or "PGRST205" in str(e):
            print("  analytics_insights: NOT FOUND (needs creation)")
        else:
            print(f"  analytics_insights: ERROR - {e}")

    try:
        result = client.table("llm_processing_queue").select("id").limit(1).execute()
        print("  llm_processing_queue: EXISTS")
    except Exception as e:
        if "Could not find" in str(e) or "PGRST205" in str(e):
            print("  llm_processing_queue: NOT FOUND (needs creation)")
        else:
            print(f"  llm_processing_queue: ERROR - {e}")

    print("\n" + "=" * 60)
    print("NOTE: Supabase REST API cannot execute raw SQL.")
    print("To create tables, you need to:")
    print("1. Go to https://supabase.com/dashboard")
    print("2. Select your project -> SQL Editor")
    print("3. Paste contents of unified_analytics_schema.sql")
    print("4. Click Run")
    print("=" * 60)

    # Copy to clipboard for convenience
    print("\nCopying SQL to clipboard...")
    try:
        import subprocess
        with open(schema_path, 'r') as f:
            sql = f.read()
        subprocess.run(['pbcopy'], input=sql.encode(), check=True)
        print("SQL copied to clipboard! Paste in Supabase SQL Editor.")
    except Exception as e:
        print(f"Could not copy to clipboard: {e}")
        print(f"Please manually copy from: {schema_path}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
