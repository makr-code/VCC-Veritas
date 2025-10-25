import sqlite3

db_path = "data/test_databases/immissionsschutz_test.sqlite"

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Teste ob die Tabellen existieren
tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
print("📊 Verfügbare Tabellen:")
for table_name, in tables:
    count = cursor.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    print(f"   {table_name}: {count} Datensätze")

print("\n🔍 Teste Dokumente-Query:")
cursor.execute("SELECT * FROM dokumente WHERE status = 'aktiv' ORDER BY erstellt_datum DESC LIMIT 3")
rows = cursor.fetchall()
columns = [desc[0] for desc in cursor.description]
print(f"Columns: {columns}")
print(f"Rows: {len(rows)}")

if rows:
    for row in rows:
        dok = dict(zip(columns, row))
        print(f"   - {dok['dokument_id']}: {dok['dokumenttyp']} - {dok['titel']}")

conn.close()
