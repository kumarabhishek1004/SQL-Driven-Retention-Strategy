"""
02_db_setup.py
==============
Phase 2: Database Setup & Query Execution

Creates a SQLite database (customer_intel.db) from customer_features.csv
and executes all segmentation queries from 02_segmentation.sql.

Business Goal:
    Build a structured query layer to answer the brand's core business
    questions about customer value, loyalty, promo dependency, and geography.

Note: Uses SQLite for zero-dependency portability. All queries are standard
SQL and work on MySQL/PostgreSQL with no modification.
"""

import sqlite3
import csv
import os
import re

DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DB_DIR, "customer_intel.db")
CSV_PATH = os.path.join(DB_DIR, "customer_features.csv")
SQL_PATH = os.path.join(DB_DIR, "02_segmentation.sql")


def create_database():
    """Create SQLite database and import customer_features.csv."""
    # Remove existing DB
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Read CSV header and create table dynamically
    with open(CSV_PATH, "r", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        headers = next(reader)

    # Clean headers for SQL (replace spaces with underscores, lowercase)
    sql_columns = []
    for h in headers:
        col = h.strip().replace(" ", "_").replace("(", "").replace(")", "").replace("?", "").replace("%", "pct").replace("/", "_").lower()
        sql_columns.append(col)

    # Create table
    col_defs = ", ".join([f'"{c}" TEXT' for c in sql_columns])
    cur.execute(f"CREATE TABLE IF NOT EXISTS customers ({col_defs})")
    conn.commit()

    # Import data
    with open(CSV_PATH, "r", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        next(reader)  # skip header
        rows = list(reader)

    placeholders = ", ".join(["?"] * len(sql_columns))
    cur.executemany(f"INSERT INTO customers VALUES ({placeholders})", rows)
    conn.commit()

    # Create indexes for performance
    for idx_col in ["location", "category", "value_tier", "loyalty_score_c", "customer_id"]:
        try:
            cur.execute(f'CREATE INDEX idx_{idx_col} ON customers("{idx_col}")')
        except sqlite3.OperationalError:
            pass  # Index already exists
    conn.commit()

    row_count = cur.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
    col_count = len(sql_columns)
    print(f"[DB] Created database: {DB_PATH}")
    print(f"[DB] Table 'customers': {row_count} rows × {col_count} columns")
    print(f"[DB] Column names: {sql_columns}")

    return conn, sql_columns


def execute_sql_file(conn, sql_path):
    """Read and execute all queries from the SQL file."""
    with open(sql_path, "r") as f:
        sql_content = f.read()

    # Split by query markers (comments starting with -- QUERY)
    queries = re.split(r'-- QUERY:', sql_content)

    cur = conn.cursor()

    for i, query_block in enumerate(queries):
        if not query_block.strip():
            continue

        # Extract query name from first comment line
        lines = query_block.strip().split("\n")
        query_name = lines[0].strip() if lines else f"Query {i}"

        # Get the actual SQL (skip comment lines)
        sql_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("--") and not stripped.startswith("-- QUERY"):
                continue  # skip other comments
            if stripped.startswith("/*") or stripped.startswith("*/"):
                continue
            if stripped.upper().startswith("SELECT") or stripped.upper().startswith("WITH") or stripped.upper().startswith("CREATE"):
                sql_lines.append(line)
            elif sql_lines:  # continuation of query
                sql_lines.append(line)

        sql = "\n".join(sql_lines).strip()
        if not sql or not sql.upper().startswith(("SELECT", "WITH", "CREATE")):
            continue

        # For CREATE VIEW queries, just execute
        if sql.upper().startswith("CREATE"):
            try:
                cur.execute(sql)
                conn.commit()
                print(f"\n[VIEW] {query_name} — created successfully")
            except Exception as e:
                print(f"\n[VIEW] {query_name} — error: {e}")
            continue

        # For SELECT queries, execute and print results
        try:
            print(f"\n{'='*70}")
            print(f"QUERY: {query_name}")
            print(f"{'='*70}")
            cur.execute(sql)
            columns = [desc[0] for desc in cur.description]
            rows = cur.fetchall()

            # Print header
            header = " | ".join([f"{c:>20}" for c in columns])
            print(header)
            print("-" * len(header))

            # Print rows (limit to 25 for readability)
            for j, row in enumerate(rows[:25]):
                row_str = " | ".join([f"{str(v):>20}" for v in row])
                print(row_str)

            if len(rows) > 25:
                print(f"  ... ({len(rows) - 25} more rows)")

            print(f"({len(rows)} total rows)")

        except Exception as e:
            print(f"\n[ERROR] {query_name}: {e}")

    return cur


def main():
    print("=" * 70)
    print("PHASE 2: Database Setup & Segmentation Queries")
    print("=" * 70)

    # Step 1: Create database
    print("\n--- Step 1: Creating database and importing data ---")
    conn, columns = create_database()

    # Step 2: Execute segmentation queries
    print("\n--- Step 2: Executing segmentation queries ---")
    execute_sql_file(conn, SQL_PATH)

    conn.close()
    print(f"\n{'='*70}")
    print(f"Database saved to: {DB_PATH}")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
