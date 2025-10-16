#!/usr/bin/env python3
"""
Direct PostgreSQL Connection Test
Testet direkt die PostgreSQL-Verbindung und zeigt vorhandene Tabellen/Daten
"""

import psycopg2
from psycopg2 import sql

def test_postgresql_connection():
    """Test PostgreSQL connection and show available data"""
    print("=" * 80)
    print("POSTGRESQL CONNECTION TEST (Direct)")
    print("=" * 80)
    print()
    
    # Connection parameters from config.py
    conn_params = {
        'host': '192.168.178.94',
        'port': 5432,
        'user': 'postgres',
        'password': 'postgres',
        'database': 'postgres'  # Verbinde zu default DB um alle DBs zu listen
    }
    
    try:
        print(f"🔌 Verbinde zu PostgreSQL: {conn_params['host']}:{conn_params['port']}")
        print(f"   Database: {conn_params['database']}")
        print()
        
        conn = psycopg2.connect(**conn_params)
        cur = conn.cursor()
        
        print("✅ Verbindung erfolgreich!")
        print()
        
        # 0. Liste alle Datenbanken
        print("🗄️  Verfügbare Datenbanken:")
        cur.execute("""
            SELECT datname, pg_size_pretty(pg_database_size(datname)) as size
            FROM pg_database
            WHERE datistemplate = false
            ORDER BY datname;
        """)
        databases = cur.fetchall()
        
        for db in databases:
            db_name, size = db
            print(f"   - {db_name}: {size}")
        
        print()
        print("🔍 Welche Datenbank soll durchsucht werden?")
        print("   Vorschlag: Suche in allen Datenbanken nach 'BGB' / 'Gesetz'")
        print()
        
        # 1. Liste alle Tabellen
        print("📊 Verfügbare Tabellen:")
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = cur.fetchall()
        
        if tables:
            for table in tables:
                table_name = table[0]
                # Count rows
                cur.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(
                    sql.Identifier(table_name)
                ))
                count = cur.fetchone()[0]
                print(f"   - {table_name}: {count:,} Zeilen")
        else:
            print("   ⚠️  Keine Tabellen gefunden!")
        
        print()
        
        # 2. Suche nach Dokumenten
        if any('document' in str(t[0]).lower() for t in tables):
            print("📄 Dokumente-Tabellen:")
            for table in tables:
                table_name = table[0]
                if 'document' in table_name.lower():
                    print(f"\n   Tabelle: {table_name}")
                    # Show first few rows
                    cur.execute(sql.SQL("SELECT * FROM {} LIMIT 3").format(
                        sql.Identifier(table_name)
                    ))
                    rows = cur.fetchall()
                    
                    if rows:
                        # Get column names
                        col_names = [desc[0] for desc in cur.description]
                        print(f"   Spalten: {', '.join(col_names[:5])}...")
                        for row in rows:
                            print(f"   - {row[:3]}...")
                    else:
                        print("   (leer)")
        
        # 3. Suche nach "BGB" oder "Taschengeld"
        print("\n🔍 Suche nach BGB/Taschengeld-bezogenen Daten:")
        for table in tables:
            table_name = table[0]
            try:
                # Try to search in text columns
                cur.execute(sql.SQL("SELECT column_name FROM information_schema.columns WHERE table_name = %s AND data_type IN ('text', 'character varying')"), 
                           (table_name,))
                text_columns = [c[0] for c in cur.fetchall()]
                
                if text_columns:
                    # Search for BGB or Taschengeld
                    for col in text_columns[:3]:  # Limit to first 3 text columns
                        search_query = sql.SQL(
                            "SELECT COUNT(*) FROM {} WHERE {} ILIKE %s OR {} ILIKE %s"
                        ).format(
                            sql.Identifier(table_name),
                            sql.Identifier(col),
                            sql.Identifier(col)
                        )
                        cur.execute(search_query, ('%BGB%', '%Taschengeld%'))
                        count = cur.fetchone()[0]
                        if count > 0:
                            print(f"   ✅ {table_name}.{col}: {count} Treffer")
            except Exception as search_e:
                pass  # Skip tables that can't be searched
        
        cur.close()
        conn.close()
        
        print()
        print("=" * 80)
        print("TEST ABGESCHLOSSEN")
        print("=" * 80)
        
    except psycopg2.Error as e:
        print(f"❌ PostgreSQL Fehler: {e}")
        print(f"   Error Code: {e.pgcode}")
        print(f"   Error Message: {e.pgerror}")
    except Exception as e:
        print(f"❌ FEHLER: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_postgresql_connection()
