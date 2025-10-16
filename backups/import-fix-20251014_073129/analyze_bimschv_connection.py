"""
Analyse der Verbindung zwischen 4. BImSchV und BST/Anlagennummer
Zeigt die Beziehung zwischen Verordnungsnummern und Betriebsstätten/Anlagen
"""

import sqlite3
from pathlib import Path

db_path = Path("data/BImSchG.sqlite")

def print_section(title):
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")

def execute_query(conn, query, description):
    print(f"📊 {description}")
    print(f"   SQL: {query[:100]}...")
    cursor = conn.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    
    if results:
        # Header
        col_names = [desc[0] for desc in cursor.description]
        header = " | ".join(f"{name:20}" for name in col_names)
        print(f"\n   {header}")
        print(f"   {'-' * len(header)}")
        
        # Data rows
        for row in results[:30]:  # Limit to 30 rows
            print("   " + " | ".join(f"{str(val)[:20]:20}" for val in row))
        
        if len(results) > 30:
            print(f"\n   ... und {len(results) - 30} weitere Zeilen")
        else:
            print(f"\n   ✅ Gesamt: {len(results)} Zeilen")
    else:
        print("   ⚠️ Keine Ergebnisse")
    print()

with sqlite3.connect(db_path) as conn:
    
    # 1. Übersicht: Wie viele Einträge haben 4. BImSchV-Nummern?
    print_section("1. Übersicht: 4. BImSchV Abdeckung")
    
    execute_query(conn, """
        SELECT 
            COUNT(*) as gesamt_anlagen,
            COUNT(DISTINCT nr_4bv) as anzahl_4bv_nummern,
            COUNT(CASE WHEN nr_4bv IS NOT NULL AND nr_4bv != '' THEN 1 END) as mit_4bv,
            COUNT(CASE WHEN nr_4bv IS NULL OR nr_4bv = '' THEN 1 END) as ohne_4bv
        FROM BImSchG
    """, "Statistik zu 4. BImSchV-Nummern")
    
    # 2. Top 20 häufigste 4. BImSchV-Nummern
    print_section("2. Häufigste 4. BImSchV-Nummern (TOP 20)")
    
    execute_query(conn, """
        SELECT 
            nr_4bv,
            anlart_4bv,
            COUNT(*) as anzahl_anlagen,
            COUNT(DISTINCT bst_nr) as anzahl_betriebsstaetten
        FROM BImSchG
        WHERE nr_4bv IS NOT NULL AND nr_4bv != ''
        GROUP BY nr_4bv, anlart_4bv
        ORDER BY anzahl_anlagen DESC
        LIMIT 20
    """, "TOP 20 4. BImSchV-Nummern nach Anlagenanzahl")
    
    # 3. Verbindung BST/Anlagennummer zu 4. BImSchV
    print_section("3. Verbindung: Betriebsstätte/Anlage ↔ 4. BImSchV")
    
    execute_query(conn, """
        SELECT 
            bst_nr,
            bst_name,
            anl_nr,
            anl_bez,
            nr_4bv,
            anlart_4bv,
            ort
        FROM BImSchG
        WHERE nr_4bv IS NOT NULL AND nr_4bv != ''
        ORDER BY bst_nr, anl_nr
        LIMIT 30
    """, "Beispiele: BST-Nr → Anlagen-Nr → 4. BImSchV")
    
    # 4. Betriebsstätten mit mehreren 4. BImSchV-Nummern
    print_section("4. Betriebsstätten mit mehreren verschiedenen 4. BImSchV-Anlagen")
    
    execute_query(conn, """
        SELECT 
            bst_nr,
            bst_name,
            ort,
            COUNT(DISTINCT nr_4bv) as anzahl_4bv_typen,
            COUNT(*) as gesamt_anlagen
        FROM BImSchG
        WHERE nr_4bv IS NOT NULL AND nr_4bv != ''
        GROUP BY bst_nr, bst_name, ort
        HAVING COUNT(DISTINCT nr_4bv) > 1
        ORDER BY anzahl_4bv_typen DESC, gesamt_anlagen DESC
        LIMIT 20
    """, "Betriebsstätten mit diversen 4. BImSchV-Anlagentypen")
    
    # 5. Detailansicht einer Beispiel-Betriebsstätte
    print_section("5. Detailansicht: PCK Raffinerie GmbH (Beispiel)")
    
    execute_query(conn, """
        SELECT 
            anl_nr,
            anl_bez,
            nr_4bv,
            anlart_4bv,
            anlgr_4bv,
            leistung,
            einheit
        FROM BImSchG
        WHERE bst_name = 'PCK Raffinerie GmbH'
        AND nr_4bv IS NOT NULL AND nr_4bv != ''
        ORDER BY nr_4bv, anl_nr
    """, "Alle Anlagen der PCK Raffinerie mit 4. BImSchV-Zuordnung")
    
    # 6. Anlagennummern-Struktur
    print_section("6. Struktur der Anlagennummern")
    
    execute_query(conn, """
        SELECT 
            bst_nr,
            anl_nr,
            COUNT(*) as anzahl
        FROM BImSchG
        WHERE anl_nr IS NOT NULL AND anl_nr != ''
        GROUP BY bst_nr, anl_nr
        HAVING COUNT(*) > 1
        ORDER BY anzahl DESC
        LIMIT 20
    """, "Mehrfach vergebene BST/Anlagennummern-Kombinationen")
    
    # 7. Cross-Tabelle: BST vs 4. BImSchV
    print_section("7. Beispiel-Mapping: BST-Nr → Multiple Anlagen → 4. BImSchV")
    
    execute_query(conn, """
        WITH bst_sample AS (
            SELECT DISTINCT bst_nr 
            FROM BImSchG 
            WHERE nr_4bv IS NOT NULL AND nr_4bv != ''
            LIMIT 5
        )
        SELECT 
            b.bst_nr,
            b.bst_name,
            b.anl_nr,
            b.anl_bez,
            b.nr_4bv,
            b.anlart_4bv
        FROM BImSchG b
        INNER JOIN bst_sample s ON b.bst_nr = s.bst_nr
        WHERE b.nr_4bv IS NOT NULL AND b.nr_4bv != ''
        ORDER BY b.bst_nr, b.anl_nr
    """, "5 Beispiel-Betriebsstätten mit allen Anlagen")
    
    # 8. Eindeutigkeits-Analyse
    print_section("8. Eindeutigkeits-Analyse der Identifikatoren")
    
    execute_query(conn, """
        SELECT 
            'BST_NR' as identifikator,
            COUNT(*) as gesamt,
            COUNT(DISTINCT bst_nr) as eindeutig
        FROM BImSchG
        WHERE bst_nr IS NOT NULL
        
        UNION ALL
        
        SELECT 
            'ANL_NR' as identifikator,
            COUNT(*) as gesamt,
            COUNT(DISTINCT anl_nr) as eindeutig
        FROM BImSchG
        WHERE anl_nr IS NOT NULL
        
        UNION ALL
        
        SELECT 
            'BST_NR + ANL_NR' as identifikator,
            COUNT(*) as gesamt,
            COUNT(DISTINCT bst_nr || '_' || anl_nr) as eindeutig
        FROM BImSchG
        WHERE bst_nr IS NOT NULL AND anl_nr IS NOT NULL
        
        UNION ALL
        
        SELECT 
            'BIMSCHG_ID' as identifikator,
            COUNT(*) as gesamt,
            COUNT(DISTINCT bimschg_id) as eindeutig
        FROM BImSchG
        WHERE bimschg_id IS NOT NULL
    """, "Eindeutigkeit verschiedener Identifikatoren")

print("\n✅ Analyse abgeschlossen!")
print(f"\n💾 Datenbank: {db_path}")
print(f"📊 Alle Abfragen erfolgreich ausgeführt\n")
