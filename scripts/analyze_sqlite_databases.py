#!/usr/bin/env python3
"""
SQLite Database Analyzer - BImSchG & WKA
Analysiert die Struktur und Inhalte der SQLite-Datenbanken
"""

import sqlite3
from pathlib import Path
from typing import Dict, List, Any
import json

# Datenbank-Pfade
PROJECT_ROOT = Path(__file__).parent.parent
DATABASES = {
    "bimschg": PROJECT_ROOT / "data" / "bimschg" / "BImSchG.sqlite",
    "wka": PROJECT_ROOT / "data" / "wka" / "wka.sqlite"
}


def analyze_database(db_path: Path) -> Dict[str, Any]:
    """Analysiert eine SQLite-Datenbank"""
    
    if not db_path.exists():
        return {"error": f"Database not found: {db_path}"}
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    analysis = {
        "database": str(db_path),
        "size_mb": db_path.stat().st_size / (1024 * 1024),
        "tables": []
    }
    
    try:
        # Tabellen auflisten
        tables = cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
        
        for (table_name,) in tables:
            table_info = {
                "name": table_name,
                "columns": [],
                "indexes": [],
                "row_count": 0,
                "sample_data": []
            }
            
            # Spalten-Info
            columns = cursor.execute(f"PRAGMA table_info({table_name})").fetchall()
            for col in columns:
                table_info["columns"].append({
                    "id": col[0],
                    "name": col[1],
                    "type": col[2],
                    "not_null": bool(col[3]),
                    "default": col[4],
                    "primary_key": bool(col[5])
                })
            
            # Indizes
            indexes = cursor.execute(
                f"SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='{table_name}'"
            ).fetchall()
            table_info["indexes"] = [idx[0] for idx in indexes]
            
            # Zeilenanzahl
            count = cursor.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
            table_info["row_count"] = count[0] if count else 0
            
            # Beispiel-Daten (erste 3 Zeilen)
            if table_info["row_count"] > 0:
                sample = cursor.execute(f"SELECT * FROM {table_name} LIMIT 3").fetchall()
                column_names = [col["name"] for col in table_info["columns"]]
                
                for row in sample:
                    row_dict = dict(zip(column_names, row))
                    table_info["sample_data"].append(row_dict)
            
            analysis["tables"].append(table_info)
    
    finally:
        conn.close()
    
    return analysis


def print_analysis(analysis: Dict[str, Any]):
    """Gibt Analyse formatiert aus"""
    
    if "error" in analysis:
        print(f"❌ {analysis['error']}")
        return
    
    print("=" * 80)
    print(f"📊 Database: {analysis['database']}")
    print(f"💾 Size: {analysis['size_mb']:.2f} MB")
    print(f"📋 Tables: {len(analysis['tables'])}")
    print("=" * 80)
    print()
    
    for table in analysis["tables"]:
        print(f"📁 Table: {table['name']}")
        print(f"   Rows: {table['row_count']:,}")
        print(f"   Columns: {len(table['columns'])}")
        
        print(f"\n   Columns:")
        for col in table["columns"]:
            pk = " (PK)" if col["primary_key"] else ""
            nn = " NOT NULL" if col["not_null"] else ""
            print(f"      - {col['name']}: {col['type']}{pk}{nn}")
        
        if table["indexes"]:
            print(f"\n   Indexes:")
            for idx in table["indexes"]:
                print(f"      - {idx}")
        
        if table["sample_data"]:
            print(f"\n   Sample Data (first {len(table['sample_data'])} rows):")
            for i, row in enumerate(table["sample_data"], 1):
                print(f"      Row {i}:")
                for key, value in row.items():
                    # Kürze lange Werte
                    val_str = str(value)
                    if len(val_str) > 50:
                        val_str = val_str[:47] + "..."
                    print(f"         {key}: {val_str}")
        
        print()


def save_analysis_to_file(analysis: Dict[str, Any], output_file: Path):
    """Speichert Analyse als JSON"""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)
    print(f"💾 Analyse gespeichert: {output_file}")


def main():
    """Hauptfunktion"""
    print("=" * 80)
    print("  SQLite Database Analyzer - BImSchG & WKA")
    print("=" * 80)
    print()
    
    for db_name, db_path in DATABASES.items():
        print(f"\n🔍 Analysiere {db_name.upper()}...")
        print()
        
        analysis = analyze_database(db_path)
        print_analysis(analysis)
        
        # Speichere Analyse
        output_file = PROJECT_ROOT / "docs" / f"database_schema_{db_name}.json"
        save_analysis_to_file(analysis, output_file)
        print()
    
    print("=" * 80)
    print("✅ Analyse abgeschlossen!")
    print("=" * 80)
    print()
    print("📄 Nächste Schritte:")
    print("   1. Schema-Dokumentation prüfen (docs/database_schema_*.json)")
    print("   2. FastAPI-Router erstellen (backend/api/v3/database_router.py)")
    print("   3. Agent-Integration implementieren")
    print()


if __name__ == "__main__":
    main()
