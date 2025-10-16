#!/usr/bin/env python3
"""
Check SQLite databases for available data
"""

import sqlite3
from pathlib import Path

def check_database(db_path: Path):
    """Check SQLite database content"""
    print(f"\n{'='*80}")
    print(f"DATABASE: {db_path.name}")
    print(f"Pfad: {db_path}")
    print(f"Größe: {db_path.stat().st_size / 1024:.2f} KB")
    print('='*80)
    
    try:
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()
        
        # Liste Tabellen
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cur.fetchall()
        
        if not tables:
            print("⚠️  Keine Tabellen gefunden")
            return
        
        print(f"\n📊 Tabellen ({len(tables)}):")
        for (table_name,) in tables:
            # Count rows
            cur.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cur.fetchone()[0]
            print(f"   - {table_name}: {count:,} Zeilen")
            
            # Show sample if has data
            if count > 0:
                cur.execute(f"PRAGMA table_info({table_name})")
                columns = [col[1] for col in cur.fetchall()]
                print(f"     Spalten: {', '.join(columns[:5])}{'...' if len(columns) > 5 else ''}")
                
                # Show first row
                cur.execute(f"SELECT * FROM {table_name} LIMIT 1")
                row = cur.fetchone()
                if row:
                    # Try to find text content
                    for i, val in enumerate(row[:5]):
                        if isinstance(val, str) and len(val) > 20:
                            preview = val[:100] + "..." if len(val) > 100 else val
                            print(f"     Sample {columns[i]}: {preview}")
                
                # Search for BGB/Gesetz keywords
                text_search_done = False
                for col in columns:
                    if not text_search_done:
                        try:
                            cur.execute(f"SELECT COUNT(*) FROM {table_name} WHERE {col} LIKE ? OR {col} LIKE ? OR {col} LIKE ?", 
                                      ('%BGB%', '%Gesetz%', '%Paragraph%'))
                            keyword_count = cur.fetchone()[0]
                            if keyword_count > 0:
                                print(f"     🔍 {keyword_count} Treffer für BGB/Gesetz in '{col}'")
                                text_search_done = True
                        except:
                            pass
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Fehler: {e}")

def main():
    """Main function"""
    print("\n" + "="*80)
    print("SQLITE DATABASE CONTENT CHECKER")
    print("="*80)
    
    # Check UDS3 databases
    uds3_data = Path("uds3/data")
    if uds3_data.exists():
        for db_file in sorted(uds3_data.glob("*.db")):
            check_database(db_file)
    
    # Check other locations
    other_dbs = [
        Path("data/veritas_backend.sqlite"),
        Path("backend/api/data/covina_documents.db"),
        Path("frontend/data/covina_documents.db"),
    ]
    
    for db_path in other_dbs:
        if db_path.exists():
            check_database(db_path)
    
    print("\n" + "="*80)
    print("ANALYSE ABGESCHLOSSEN")
    print("="*80)

if __name__ == "__main__":
    main()
