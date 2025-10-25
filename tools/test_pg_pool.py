"""
Smoke test for PostgreSQL connection pool: runs SELECT 1.
"""
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Ensure secure secrets are enabled for the test run
os.environ.setdefault("ENABLE_SECURE_SECRETS", "true")

from backend.database.connection_pool import get_cursor

print("Running SELECT 1 via pooled connection...")
try:
    with get_cursor() as cur:
        cur.execute("SELECT 1")
        row = cur.fetchone()
        print("Result:", row)
    print("OK: Pool operational.")
except Exception as e:
    print("Pool test failed:", e)
    sys.exit(1)
