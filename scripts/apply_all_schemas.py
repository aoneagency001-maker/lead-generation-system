#!/usr/bin/env python3
"""
Apply All Database Schemas to Supabase
Applies the combined schema from ALL_SCHEMAS_TO_APPLY.sql
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load .env
load_dotenv()


def get_connection_string():
    """Build PostgreSQL connection string from Supabase URL"""
    supabase_url = os.getenv("SUPABASE_URL")
    db_password = os.getenv("DATABASE_PASSWORD") or os.getenv("SUPABASE_DB_PASSWORD")

    if not supabase_url:
        print("SUPABASE_URL not found in .env")
        return None

    if not db_password:
        print("DATABASE_PASSWORD not found in .env")
        print()
        print("To set the database password, add to your .env file:")
        print("DATABASE_PASSWORD=your_database_password")
        print()
        print("You can find your database password in:")
        print("Supabase Dashboard -> Settings -> Database -> Connection string")
        print()
        return None

    # Extract project ID from URL
    # https://upgowxrbwjgyoqbjcegc.supabase.co -> upgowxrbwjgyoqbjcegc
    project_id = supabase_url.replace("https://", "").replace(".supabase.co", "")

    # Supabase PostgreSQL connection string (IPv4 pooler for better compatibility)
    conn_string = f"postgresql://postgres.{project_id}:{db_password}@aws-0-eu-central-1.pooler.supabase.com:6543/postgres"

    return conn_string


def apply_schema(conn_string: str, schema_path: Path) -> bool:
    """Apply SQL schema using psycopg2"""
    try:
        import psycopg2
    except ImportError:
        print("psycopg2 not installed. Install with: pip install psycopg2-binary")
        return False

    if not schema_path.exists():
        print(f"Schema file not found: {schema_path}")
        return False

    print(f"Reading schema from {schema_path.name}...")
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema_sql = f.read()

    print(f"Connecting to PostgreSQL...")
    try:
        conn = psycopg2.connect(conn_string)
        conn.autocommit = True  # Important for CREATE statements
        cursor = conn.cursor()

        print(f"Connected successfully!")
        print(f"Applying schema...")

        # Execute SQL
        cursor.execute(schema_sql)

        print(f"Schema applied successfully!")

        # Verify tables created
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)

        tables = cursor.fetchall()
        print(f"\nCreated/existing tables in public schema:")
        for table in tables:
            print(f"   - {table[0]}")

        cursor.close()
        conn.close()

        return True

    except psycopg2.OperationalError as e:
        print(f"Connection error: {e}")
        print()
        print("Make sure your DATABASE_PASSWORD is correct.")
        print("You can find it in Supabase Dashboard -> Settings -> Database -> Connection string")
        return False
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False


def print_manual_instructions(schema_path: Path):
    """Print instructions for manual schema application"""
    print("=" * 70)
    print("MANUAL APPLICATION INSTRUCTIONS")
    print("=" * 70)
    print()
    print("1. Open https://supabase.com/dashboard")
    print("2. Select your project")
    print("3. Go to SQL Editor (left menu)")
    print("4. Click 'New query'")
    print("5. Copy contents from:")
    print(f"   {schema_path}")
    print("6. Paste into SQL Editor and click 'Run' (or Ctrl+Enter)")
    print()
    print("Quick copy command (macOS):")
    print(f"   cat {schema_path} | pbcopy")
    print()
    print("=" * 70)


def main():
    print("=" * 70)
    print("Apply Database Schemas - Lead Generation System")
    print("=" * 70)
    print()

    # Schema file path
    schema_path = Path(__file__).parent / "ALL_SCHEMAS_TO_APPLY.sql"

    if not schema_path.exists():
        print(f"Schema file not found: {schema_path}")
        return 1

    print(f"Schema file: {schema_path.name}")
    print()

    # Try to get connection string
    conn_string = get_connection_string()

    if conn_string:
        print("Attempting automatic schema application...")
        print()
        success = apply_schema(conn_string, schema_path)

        if success:
            print()
            print("=" * 70)
            print("DATABASE SETUP COMPLETE!")
            print("=" * 70)
            print()
            print("Tables created:")
            print("  L1: raw_events - Raw data from all sources")
            print("  L2: normalized_events - Unified format")
            print("  L3: feature_store - Computed features")
            print("  + visitors, tilda_webhooks, user_feature_aggregates, data_intake_log")
            print()
            return 0
        else:
            print()
            print("Automatic application failed.")
            print_manual_instructions(schema_path)
            return 1
    else:
        print_manual_instructions(schema_path)
        return 1


if __name__ == "__main__":
    sys.exit(main())
