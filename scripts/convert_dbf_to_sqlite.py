#!/usr/bin/env python3
"""
DBF to SQLite Converter
=======================

Konvertiert DBF-Dateien (dBase) nach SQLite für Database Agent Testing

Requirements:
    pip install dbfread

Author: VERITAS System
Date: 10. Oktober 2025
"""

import sys
sys.path.insert(0, '.')

import os
import sqlite3
from pathlib import Path
from typing import Dict, List, Any, Optional

try:
    from dbfread import DBF
    DBF_AVAILABLE = True
except ImportError:
    DBF_AVAILABLE = False
    print("⚠️ dbfread nicht installiert. Installiere mit: pip install dbfread")


class DBFToSQLiteConverter:
    """Konvertiert DBF-Dateien nach SQLite"""
    
    # DBF → SQLite Type Mapping
    TYPE_MAPPING = {
        'C': 'TEXT',      # Character
        'N': 'REAL',      # Numeric
        'F': 'REAL',      # Float
        'L': 'INTEGER',   # Logical (Boolean)
        'D': 'TEXT',      # Date (stored as TEXT)
        'T': 'TEXT',      # DateTime
        'I': 'INTEGER',   # Integer
        'B': 'REAL',      # Double
        'M': 'TEXT',      # Memo
        'G': 'BLOB',      # General (OLE)
        'P': 'BLOB',      # Picture
    }
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
    
    def log(self, message: str):
        """Logging"""
        if self.verbose:
            print(message)
    
    def analyze_dbf(self, dbf_path: str) -> Dict[str, Any]:
        """
        Analysiert DBF-Datei
        
        Returns:
            Dict with metadata (fields, record_count, etc.)
        """
        if not DBF_AVAILABLE:
            raise ImportError("dbfread module not available")
        
        dbf = DBF(dbf_path, load=False, encoding='latin1')
        
        fields = []
        for field in dbf.fields:
            fields.append({
                'name': field.name,
                'type': field.type,
                'length': field.length,
                'decimal_count': field.decimal_count if hasattr(field, 'decimal_count') else 0
            })
        
        # Count records
        record_count = len(dbf)
        
        return {
            'filename': os.path.basename(dbf_path),
            'path': dbf_path,
            'encoding': 'latin1',
            'fields': fields,
            'record_count': record_count,
            'last_update': dbf.date if hasattr(dbf, 'date') else None
        }
    
    def convert_dbf_to_sqlite(
        self, 
        dbf_path: str, 
        sqlite_path: str,
        table_name: Optional[str] = None,
        overwrite: bool = False
    ) -> Dict[str, Any]:
        """
        Konvertiert DBF → SQLite
        
        Args:
            dbf_path: Path zur DBF-Datei
            sqlite_path: Path zur SQLite-Datei (output)
            table_name: Tabellenname (default: DBF filename)
            overwrite: Überschreibe existierende SQLite-Datei
            
        Returns:
            Dict with conversion stats
        """
        if not DBF_AVAILABLE:
            raise ImportError("dbfread module not available. Install: pip install dbfread")
        
        # Validate input
        if not os.path.exists(dbf_path):
            raise FileNotFoundError(f"DBF file not found: {dbf_path}")
        
        # Table name
        if table_name is None:
            table_name = Path(dbf_path).stem.lower()
        
        # Check if SQLite exists
        if os.path.exists(sqlite_path) and not overwrite:
            self.log(f"⚠️ SQLite file already exists: {sqlite_path}")
            self.log(f"   Use overwrite=True to replace")
            return {'success': False, 'error': 'File exists'}
        
        self.log(f"🔄 Converting DBF → SQLite")
        self.log(f"   Source: {dbf_path}")
        self.log(f"   Target: {sqlite_path}")
        self.log(f"   Table: {table_name}")
        
        # Read DBF
        dbf = DBF(dbf_path, encoding='latin1', lowernames=True)
        
        # Analyze structure
        fields = []
        sql_types = []
        
        for field in dbf.fields:
            field_name = field.name.lower()
            field_type = self.TYPE_MAPPING.get(field.type, 'TEXT')
            
            fields.append(field_name)
            sql_types.append(f"{field_name} {field_type}")
        
        self.log(f"   Fields: {len(fields)}")
        
        # Create SQLite database
        conn = sqlite3.connect(sqlite_path)
        cursor = conn.cursor()
        
        # Create table
        create_sql = f"CREATE TABLE {table_name} ({', '.join(sql_types)})"
        cursor.execute(create_sql)
        
        self.log(f"   ✅ Table '{table_name}' created")
        
        # Insert data
        placeholders = ', '.join(['?' for _ in fields])
        insert_sql = f"INSERT INTO {table_name} VALUES ({placeholders})"
        
        records_inserted = 0
        errors = 0
        
        for record in dbf:
            try:
                # Convert record to tuple
                values = []
                for field_name in fields:
                    value = record.get(field_name)
                    
                    # Handle special types
                    if value is None:
                        values.append(None)
                    elif isinstance(value, bool):
                        values.append(1 if value else 0)
                    elif hasattr(value, 'isoformat'):  # Date/DateTime
                        values.append(value.isoformat())
                    else:
                        values.append(value)
                
                cursor.execute(insert_sql, values)
                records_inserted += 1
                
                if records_inserted % 1000 == 0:
                    self.log(f"   ... {records_inserted} records inserted")
                
            except Exception as e:
                errors += 1
                if self.verbose and errors <= 5:
                    self.log(f"   ⚠️ Error inserting record {records_inserted + 1}: {e}")
        
        conn.commit()
        conn.close()
        
        self.log(f"   ✅ Conversion complete!")
        self.log(f"   📊 Records inserted: {records_inserted}")
        if errors > 0:
            self.log(f"   ⚠️ Errors: {errors}")
        
        return {
            'success': True,
            'dbf_path': dbf_path,
            'sqlite_path': sqlite_path,
            'table_name': table_name,
            'fields': fields,
            'records_inserted': records_inserted,
            'errors': errors
        }
    
    def get_sqlite_schema(self, sqlite_path: str, table_name: str) -> str:
        """Returns SQLite table schema"""
        conn = sqlite3.connect(sqlite_path)
        cursor = conn.cursor()
        
        cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        result = cursor.fetchone()
        
        conn.close()
        
        return result[0] if result else None


def main():
    """Convert DBF files in data folder"""
    
    if not DBF_AVAILABLE:
        print("❌ dbfread module not installed!")
        print("   Install with: pip install dbfread")
        return
    
    print("=" * 80)
    print("DBF to SQLite Converter")
    print("=" * 80)
    
    # Find DBF files in data folder
    data_dir = Path("data")
    dbf_files = list(data_dir.glob("**/*.dbf"))
    
    if not dbf_files:
        print("⚠️ No DBF files found in data folder")
        return
    
    print(f"\n📂 Found {len(dbf_files)} DBF file(s):")
    for dbf_file in dbf_files:
        print(f"   - {dbf_file}")
    
    converter = DBFToSQLiteConverter(verbose=True)
    
    results = []
    
    for dbf_file in dbf_files:
        print(f"\n" + "=" * 80)
        
        # Analyze first
        try:
            metadata = converter.analyze_dbf(str(dbf_file))
            
            print(f"📋 Analyzing: {metadata['filename']}")
            print(f"   Records: {metadata['record_count']}")
            print(f"   Fields: {len(metadata['fields'])}")
            print(f"   Fields: {', '.join([f['name'] for f in metadata['fields'][:10]])}")
            if len(metadata['fields']) > 10:
                print(f"           ... and {len(metadata['fields']) - 10} more")
        
        except Exception as e:
            print(f"❌ Error analyzing {dbf_file}: {e}")
            continue
        
        # Convert
        try:
            # Output SQLite path
            sqlite_path = dbf_file.with_suffix('.sqlite')
            table_name = dbf_file.stem.lower()
            
            result = converter.convert_dbf_to_sqlite(
                dbf_path=str(dbf_file),
                sqlite_path=str(sqlite_path),
                table_name=table_name,
                overwrite=True
            )
            
            results.append(result)
            
            # Show schema
            schema = converter.get_sqlite_schema(str(sqlite_path), table_name)
            print(f"\n   📐 SQLite Schema:")
            print(f"   {schema}")
        
        except Exception as e:
            print(f"❌ Conversion failed: {e}")
            import traceback
            traceback.print_exc()
    
    # Summary
    print("\n" + "=" * 80)
    print("Conversion Summary")
    print("=" * 80)
    
    for result in results:
        if result['success']:
            print(f"✅ {result['dbf_path']}")
            print(f"   → {result['sqlite_path']}")
            print(f"   Table: {result['table_name']}")
            print(f"   Records: {result['records_inserted']}")
            if result['errors'] > 0:
                print(f"   ⚠️ Errors: {result['errors']}")
    
    print("\n✅ Conversion complete!")
    print(f"\n💡 Test with Database Agent:")
    for result in results:
        if result['success']:
            print(f"\n   python -c \"import asyncio; from backend.agents.veritas_api_agent_database import *; ")
            print(f"   agent = create_database_agent(); ")
            print(f"   req = DatabaseQueryRequest(query_id='test', sql_query='SELECT * FROM {result['table_name']} LIMIT 5', database_path='{result['sqlite_path']}'); ")
            print(f"   print(asyncio.run(agent.execute_query(req)))\"")


if __name__ == "__main__":
    main()
