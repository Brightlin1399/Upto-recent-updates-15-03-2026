import sqlite3
import database

# Use sync sqlite3 for this standalone script (database.get_connection is async)
conn = sqlite3.connect(database.DB_path)
conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))

# List all tables
tables = conn.execute(
    "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"
).fetchall()
print("\n=== ALL TABLES (row counts) ===\n")
for t in tables:
    name = t["name"] if isinstance(t, dict) else t[0]
    try:
        count = conn.execute(f"SELECT COUNT(*) AS n FROM [{name}]").fetchone()
        n = count["n"] if isinstance(count, dict) else count[0]
        print(f"  {name}: {n} row(s)")
    except Exception as e:
        print(f"  {name}: (error: {e})")

# For each table: show all columns for every row
print("\n" + "=" * 60 + "\n")
for t in tables:
    name = t["name"] if isinstance(t, dict) else t[0]
    try:
        rows = conn.execute(f"SELECT * FROM [{name}]").fetchall()
        print(f"=== {name} ({len(rows)} rows) - ALL COLUMNS ===\n")
        for i, row in enumerate(rows):
            print(f"  --- Row {i + 1} ---")
            if isinstance(row, dict):
                for col, val in row.items():
                    print(f"    {col}: {val}")
            else:
                print(f"    {row}")
            print()
        print()
    except Exception as e:
        print(f"=== {name} === (error: {e})\n")

conn.close()
print("Done.\n")
