#!/usr/bin/env python3
"""
Database Agent - DBF Test Queries
==================================

Testet Database Agent mit konvertierten DBF-Dateien:
- BImSchG.sqlite (Bundesimmissionsschutzgesetz-Anlagen)
- wka.sqlite (Windkraftanlagen)

Author: VERITAS System
Date: 10. Oktober 2025
"""

import sys
sys.path.insert(0, '.')

import asyncio
from pathlib import Path

from backend.agents.veritas_api_agent_database import (
    create_database_agent,
    DatabaseQueryRequest,
    DatabaseConfig
)


async def test_bimschg_queries():
    """Testet BImSchG-Datenbank (Bundesimmissionsschutzgesetz)"""
    
    db_path = "data/BImSchG.sqlite"
    
    if not Path(db_path).exists():
        print(f"⚠️ Database not found: {db_path}")
        return
    
    agent = create_database_agent(DatabaseConfig(log_all_queries=False))
    
    print("=" * 80)
    print("BImSchG Database Tests (Bundesimmissionsschutzgesetz-Anlagen)")
    print("=" * 80)
    
    queries = [
        {
            'name': '1. Übersicht - Alle Felder (5 Datensätze)',
            'sql': 'SELECT * FROM bimschg LIMIT 5'
        },
        {
            'name': '2. Anlagen pro Ort - TOP 10',
            'sql': """
                SELECT ort, COUNT(*) as anzahl_anlagen
                FROM bimschg
                WHERE ort IS NOT NULL AND ort != ''
                GROUP BY ort
                ORDER BY anzahl_anlagen DESC
                LIMIT 10
            """
        },
        {
            'name': '3. Anlagen nach Art (4. BImSchV)',
            'sql': """
                SELECT anlart_4bv, COUNT(*) as anzahl
                FROM bimschg
                WHERE anlart_4bv IS NOT NULL AND anlart_4bv != ''
                GROUP BY anlart_4bv
                ORDER BY anzahl DESC
                LIMIT 10
            """
        },
        {
            'name': '4. Betriebsstätten mit mehreren Anlagen',
            'sql': """
                SELECT bst_name, ort, COUNT(*) as anzahl_anlagen
                FROM bimschg
                WHERE bst_name IS NOT NULL
                GROUP BY bst_name, ort
                HAVING COUNT(*) > 3
                ORDER BY anzahl_anlagen DESC
            """
        },
        {
            'name': '5. Geografische Verteilung (Ostwert/Nordwert)',
            'sql': """
                SELECT 
                    ort,
                    COUNT(*) as anzahl,
                    AVG(ostwert) as avg_ost,
                    AVG(nordwert) as avg_nord
                FROM bimschg
                WHERE ostwert > 0 AND nordwert > 0
                GROUP BY ort
                HAVING COUNT(*) >= 5
                ORDER BY anzahl DESC
                LIMIT 10
            """
        },
        {
            'name': '6. Anlagen mit Leistungsangabe',
            'sql': """
                SELECT 
                    anl_bez,
                    ort,
                    leistung,
                    einheit
                FROM bimschg
                WHERE leistung > 0
                ORDER BY leistung DESC
                LIMIT 10
            """
        },
        {
            'name': '7. IED-Anlagen (Industrial Emissions Directive)',
            'sql': """
                SELECT 
                    anlart_ied,
                    COUNT(*) as anzahl
                FROM bimschg
                WHERE anlart_ied IS NOT NULL AND anlart_ied != ''
                GROUP BY anlart_ied
                ORDER BY anzahl DESC
            """
        }
    ]
    
    for query in queries:
        print(f"\n{query['name']}")
        print("-" * 80)
        
        request = DatabaseQueryRequest(
            query_id=f"bimschg_{queries.index(query) + 1}",
            sql_query=query['sql'],
            database_path=db_path,
            max_results=20
        )
        
        response = await agent.execute_query(request)
        
        if response.success:
            print(f"✅ {response.row_count} rows | {response.query_time_ms}ms")
            
            # Show results
            if response.results:
                print(f"\n   Columns: {', '.join(response.columns)}")
                
                # Show first 3 rows
                for i, row in enumerate(response.results[:3], 1):
                    print(f"\n   Row {i}:")
                    for col, val in row.items():
                        if val is not None:
                            print(f"      {col}: {val}")
                
                if len(response.results) > 3:
                    print(f"\n   ... and {len(response.results) - 3} more rows")
        else:
            print(f"❌ ERROR: {response.error_message}")


async def test_wka_queries():
    """Testet WKA-Datenbank (Windkraftanlagen)"""
    
    db_path = "data/wka.sqlite"
    
    if not Path(db_path).exists():
        print(f"⚠️ Database not found: {db_path}")
        return
    
    agent = create_database_agent(DatabaseConfig(log_all_queries=False))
    
    print("\n" + "=" * 80)
    print("WKA Database Tests (Windkraftanlagen)")
    print("=" * 80)
    
    queries = [
        {
            'name': '1. Übersicht - Alle Felder (5 Datensätze)',
            'sql': 'SELECT * FROM wka LIMIT 5'
        },
        {
            'name': '2. Windkraftanlagen pro Betreiber - TOP 10',
            'sql': """
                SELECT betreiber, COUNT(*) as anzahl_wka
                FROM wka
                WHERE betreiber IS NOT NULL AND betreiber != ''
                GROUP BY betreiber
                ORDER BY anzahl_wka DESC
                LIMIT 10
            """
        },
        {
            'name': '3. Windkraftanlagen pro Ort - TOP 10',
            'sql': """
                SELECT ort, COUNT(*) as anzahl_wka
                FROM wka
                WHERE ort IS NOT NULL
                GROUP BY ort
                ORDER BY anzahl_wka DESC
                LIMIT 10
            """
        },
        {
            'name': '4. Gesamtleistung pro Ort',
            'sql': """
                SELECT 
                    ort,
                    COUNT(*) as anzahl,
                    SUM(leistung) as gesamtleistung,
                    AVG(leistung) as durchschn_leistung
                FROM wka
                WHERE leistung > 0 AND ort IS NOT NULL
                GROUP BY ort
                ORDER BY gesamtleistung DESC
                LIMIT 10
            """
        },
        {
            'name': '5. Nabenhöhe und Rotordurchmesser - Statistik',
            'sql': """
                SELECT 
                    AVG(nabenhoehe) as avg_nabenhoehe,
                    MAX(nabenhoehe) as max_nabenhoehe,
                    MIN(nabenhoehe) as min_nabenhoehe,
                    AVG(rotordurch) as avg_rotordurch,
                    MAX(rotordurch) as max_rotordurch,
                    MIN(rotordurch) as min_rotordurch
                FROM wka
                WHERE nabenhoehe > 0 AND rotordurch > 0
            """
        },
        {
            'name': '6. Anlagen nach Status',
            'sql': """
                SELECT status, COUNT(*) as anzahl
                FROM wka
                WHERE status IS NOT NULL AND status != ''
                GROUP BY status
                ORDER BY anzahl DESC
            """
        },
        {
            'name': '7. Lärmbelastung (Tag/Nacht)',
            'sql': """
                SELECT 
                    ort,
                    COUNT(*) as anzahl,
                    AVG(lw_tag) as avg_laerm_tag,
                    AVG(lw_nacht) as avg_laerm_nacht
                FROM wka
                WHERE lw_tag > 0 AND lw_nacht > 0
                GROUP BY ort
                HAVING COUNT(*) >= 3
                ORDER BY avg_laerm_tag DESC
            """
        },
        {
            'name': '8. Leistungsstärkste Anlagen',
            'sql': """
                SELECT 
                    anl_bez,
                    ort,
                    betreiber,
                    leistung,
                    nabenhoehe,
                    rotordurch
                FROM wka
                WHERE leistung > 0
                ORDER BY leistung DESC
                LIMIT 10
            """
        },
        {
            'name': '9. Geografische Koordinaten - Beispiele',
            'sql': """
                SELECT 
                    anl_bez,
                    ort,
                    ostwert,
                    nordwert
                FROM wka
                WHERE ostwert > 0 AND nordwert > 0
                LIMIT 10
            """
        },
        {
            'name': '10. Inbetriebnahme-Jahr (wenn vorhanden)',
            'sql': """
                SELECT 
                    inbetriebn,
                    COUNT(*) as anzahl
                FROM wka
                WHERE inbetriebn IS NOT NULL AND inbetriebn != ''
                GROUP BY inbetriebn
                ORDER BY inbetriebn DESC
            """
        }
    ]
    
    for query in queries:
        print(f"\n{query['name']}")
        print("-" * 80)
        
        request = DatabaseQueryRequest(
            query_id=f"wka_{queries.index(query) + 1}",
            sql_query=query['sql'],
            database_path=db_path,
            max_results=20
        )
        
        response = await agent.execute_query(request)
        
        if response.success:
            print(f"✅ {response.row_count} rows | {response.query_time_ms}ms")
            
            # Show results
            if response.results:
                print(f"\n   Columns: {', '.join(response.columns)}")
                
                # Show first 3 rows
                for i, row in enumerate(response.results[:3], 1):
                    print(f"\n   Row {i}:")
                    for col, val in row.items():
                        if val is not None:
                            print(f"      {col}: {val}")
                
                if len(response.results) > 3:
                    print(f"\n   ... and {len(response.results) - 3} more rows")
        else:
            print(f"❌ ERROR: {response.error_message}")


async def test_advanced_queries():
    """Testet erweiterte SQL-Features mit DBF-Daten"""
    
    db_path = "data/wka.sqlite"
    
    if not Path(db_path).exists():
        return
    
    agent = create_database_agent(DatabaseConfig(log_all_queries=False))
    
    print("\n" + "=" * 80)
    print("Advanced SQL Features - WKA Database")
    print("=" * 80)
    
    queries = [
        {
            'name': 'Window Function - Leistungsranking pro Ort',
            'sql': """
                SELECT 
                    ort,
                    anl_bez,
                    leistung,
                    ROW_NUMBER() OVER (PARTITION BY ort ORDER BY leistung DESC) as rang_im_ort
                FROM wka
                WHERE leistung > 0 AND ort IS NOT NULL
                LIMIT 20
            """
        },
        {
            'name': 'CTE - Top-Betreiber mit Anlagendetails',
            'sql': """
                WITH top_betreiber AS (
                    SELECT betreiber, COUNT(*) as anzahl
                    FROM wka
                    WHERE betreiber IS NOT NULL
                    GROUP BY betreiber
                    HAVING COUNT(*) >= 10
                )
                SELECT 
                    w.betreiber,
                    COUNT(*) as anzahl_anlagen,
                    SUM(w.leistung) as gesamtleistung,
                    AVG(w.nabenhoehe) as avg_nabenhoehe
                FROM wka w
                INNER JOIN top_betreiber tb ON w.betreiber = tb.betreiber
                GROUP BY w.betreiber
                ORDER BY gesamtleistung DESC
            """
        },
        {
            'name': 'CASE - Leistungsklassifizierung',
            'sql': """
                SELECT 
                    CASE 
                        WHEN leistung >= 3.0 THEN 'Hochleistung (>= 3 MW)'
                        WHEN leistung >= 2.0 THEN 'Mittelleistung (2-3 MW)'
                        WHEN leistung >= 1.0 THEN 'Standardleistung (1-2 MW)'
                        ELSE 'Niedrigleistung (< 1 MW)'
                    END as leistungsklasse,
                    COUNT(*) as anzahl,
                    AVG(leistung) as avg_leistung
                FROM wka
                WHERE leistung > 0
                GROUP BY leistungsklasse
                ORDER BY avg_leistung DESC
            """
        }
    ]
    
    for query in queries:
        print(f"\n{query['name']}")
        print("-" * 80)
        
        request = DatabaseQueryRequest(
            query_id=f"advanced_{queries.index(query) + 1}",
            sql_query=query['sql'],
            database_path=db_path,
            max_results=20
        )
        
        response = await agent.execute_query(request)
        
        if response.success:
            print(f"✅ {response.row_count} rows | {response.query_time_ms}ms")
            
            if response.results:
                print(f"\n   Columns: {', '.join(response.columns)}")
                
                for i, row in enumerate(response.results[:5], 1):
                    print(f"\n   Row {i}:")
                    for col, val in row.items():
                        if val is not None:
                            print(f"      {col}: {val}")
                
                if len(response.results) > 5:
                    print(f"\n   ... and {len(response.results) - 5} more rows")
        else:
            print(f"❌ ERROR: {response.error_message}")


async def main():
    """Führt alle Tests aus"""
    
    print("🗄️  Database Agent - DBF Test Suite")
    print("=" * 80)
    print()
    
    await test_bimschg_queries()
    await test_wka_queries()
    await test_advanced_queries()
    
    print("\n" + "=" * 80)
    print("✅ All DBF database tests completed!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
