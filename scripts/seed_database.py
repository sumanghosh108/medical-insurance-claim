#!/usr/bin/env python3
"""Seed the database with initial data from SQL files."""

import os
import sys

import psycopg2
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    """Create a database connection using environment variables."""
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        database=os.getenv("DB_NAME", "claims_db"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "Admin"),
    )


def run_sql_file(cursor, filepath: str) -> None:
    """Execute a SQL file."""
    if not os.path.exists(filepath):
        print(f"  ⚠️  File not found: {filepath}")
        return
    with open(filepath, "r", encoding="utf-8") as f:
        sql = f.read()
    cursor.execute(sql)
    print(f"  ✅ {filepath}")


def main():
    """Seed database with sample data."""
    environment = os.getenv("ENVIRONMENT", "development")
    print(f"=== Seeding Database ({environment}) ===")

    # Safety check
    if environment == "production":
        confirm = input("WARNING: Seeding production database. Continue? [y/N]: ")
        if confirm.lower() != "y":
            print("Aborted.")
            sys.exit(0)

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Run seed files in order
        seed_files = [
            "database/seeds/hospitals.sql",
            "database/seeds/patients.sql",
            "database/seeds/sample_data.sql",
        ]

        print("[1/2] Running seed files...")
        for filepath in seed_files:
            run_sql_file(cursor, filepath)

        conn.commit()

        # Verify counts
        print("[2/2] Verifying seed data...")
        tables = ["hospitals", "patients", "claims", "documents", "fraud_scores"]
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")  # noqa: S608
                count = cursor.fetchone()[0]
                print(f"  {table}: {count} rows")
            except psycopg2.Error:
                print(f"  {table}: table not found")
                conn.rollback()

        print("=== Database Seeding Complete ===")

    except Exception as e:
        conn.rollback()
        print(f"ERROR: {e}")
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    main()
