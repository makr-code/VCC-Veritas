"""
Connectivity test against pgBouncer on localhost:6432.
"""
import psycopg2
import os

host = os.getenv("POSTGRES_HOST", "localhost")
port = int(os.getenv("POSTGRES_PORT", "6432"))
db = os.getenv("POSTGRES_DATABASE", os.getenv("POSTGRES_DB", "veritas"))
user = os.getenv("POSTGRES_USER", "postgres")
password = os.getenv("POSTGRES_PASSWORD", "postgres")

print(f"Connecting to {host}:{port}/{db} via pgBouncer ...")
try:
    conn = psycopg2.connect(host=host, port=port, dbname=db, user=user, password=password)
    cur = conn.cursor()
    cur.execute("SELECT version()")
    print("PostgreSQL:", cur.fetchone()[0])
    cur.close()
    conn.close()
    print("OK: Connectivity via pgBouncer works.")
except Exception as e:
    print("Failed:", e)
    raise SystemExit(1)
