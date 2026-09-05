"""Create MotherDuck database and run dbt prod."""
import os
import subprocess
import sys
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).parent.parent   # scripts/ -> repo root
env_path = ROOT / ".env"

# Parse .env manually — handles "KEY = VALUE" with spaces around =
env_vars = {}
with open(env_path, encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        env_vars[k.strip()] = v.strip()

token = env_vars.get("MotherDuck_token", "")
if not token:
    print("ERROR: MotherDuck_token not found in .env")
    sys.exit(1)

import duckdb
print("Connecting to MotherDuck...")
con = duckdb.connect(f"md:?motherduck_token={token}")
con.execute("CREATE DATABASE IF NOT EXISTS labor_market")
dbs = con.execute("SHOW DATABASES").fetchall()
print("Databases on MotherDuck:", dbs)
con.close()
print("Database 'labor_market' ready.")
