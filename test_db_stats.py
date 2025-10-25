import sqlite3

conn = sqlite3.connect('data/test_databases/immissionsschutz_test.sqlite')
cursor = conn.cursor()

print("\n📊 Datenbank-Statistiken:\n")
print("="*60)

tables = cursor.execute('SELECT name FROM sqlite_master WHERE type="table" ORDER BY name').fetchall()

for table_name, in tables:
    count = cursor.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    print(f"   {table_name:.<40} {count:>6,} Datensätze")

print("="*60)

# Beispiel-Abfragen
print("\n📋 Beispiel-Daten:\n")

print("🔍 Top 3 Anlagen mit meisten Messungen:")
result = cursor.execute("""
    SELECT bst_nr, anl_nr, COUNT(*) as anzahl
    FROM messungen
    GROUP BY bst_nr, anl_nr
    ORDER BY anzahl DESC
    LIMIT 3
""").fetchall()
for bst, anl, anzahl in result:
    print(f"   {bst}/{anl}: {anzahl} Messungen")

print("\n📈 Messreihen-Übersicht:")
result = cursor.execute("""
    SELECT bewertung, COUNT(*) as anzahl
    FROM messreihen
    GROUP BY bewertung
""").fetchall()
for bewertung, anzahl in result:
    print(f"   {bewertung}: {anzahl}")

print("\n⚠️  Mängel nach Schweregrad:")
result = cursor.execute("""
    SELECT schweregrad, COUNT(*) as anzahl
    FROM maengel
    WHERE status = 'offen'
    GROUP BY schweregrad
    ORDER BY CASE schweregrad 
        WHEN 'kritisch' THEN 1
        WHEN 'schwer' THEN 2
        WHEN 'mittel' THEN 3
        WHEN 'gering' THEN 4
    END
""").fetchall()
for schweregrad, anzahl in result:
    print(f"   {schweregrad}: {anzahl}")

print("\n🔧 Wartungen:")
result = cursor.execute("""
    SELECT status, COUNT(*) as anzahl
    FROM wartung
    GROUP BY status
""").fetchall()
for status, anzahl in result:
    print(f"   {status}: {anzahl}")

print("\n📋 Compliance-Bewertungen:")
result = cursor.execute("""
    SELECT ergebnis, COUNT(*) as anzahl
    FROM compliance_historie
    GROUP BY ergebnis
""").fetchall()
for ergebnis, anzahl in result:
    print(f"   {ergebnis}: {anzahl}")

conn.close()
