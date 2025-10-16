#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VERITAS Office Export Test Suite
Testet Word/Excel Export-Funktionalität
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

# Import Export Service
from frontend.services.office_export import OfficeExportService

# Sample Data
SAMPLE_MESSAGES = [
    {
        'role': 'user',
        'content': 'Was ist VERITAS?',
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'attachments': []
    },
    {
        'role': 'assistant',
        'content': '''# VERITAS - Dokumenten-Analyse-System

VERITAS ist ein **intelligentes RAG-System** (Retrieval-Augmented Generation) für die Analyse von Dokumenten.

## Hauptfunktionen:
- Multi-Agenten-Architektur
- Hybrid-Search (Dense + Sparse)
- Real-time Streaming
- UDS3 Integration

## Technologie-Stack:
1. **Frontend**: Tkinter
2. **Backend**: FastAPI
3. **Datenbanken**: PostgreSQL, Neo4j, ChromaDB''',
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'metadata': {
            'confidence': 92,
            'duration': 2.3,
            'sources_count': 3,
            'agents_count': 2
        },
        'sources': [
            {'title': 'VERITAS Dokumentation', 'page': 1, 'relevance': 0.95},
            {'title': 'API Reference', 'page': 5, 'relevance': 0.88},
            {'title': 'User Manual', 'page': 12, 'relevance': 0.82}
        ]
    },
    {
        'role': 'user',
        'content': 'Wie funktioniert die Multi-Agenten-Architektur?',
        'timestamp': (datetime.now() - timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S'),
    },
    {
        'role': 'assistant',
        'content': '''## Multi-Agenten-Architektur

VERITAS verwendet spezialisierte Agenten:

### Haupt-Agenten:
- **Query Analyzer**: Interpretiert User-Queries
- **Document Retriever**: Sucht relevante Dokumente
- **Answer Generator**: Generiert Antworten
- **Quality Checker**: Validiert Ergebnisse

### Workflow:
1. Query → Analyzer
2. Analyzer → Retriever
3. Retriever → Generator
4. Generator → Quality Checker
5. Quality Checker → User''',
        'timestamp': (datetime.now() - timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S'),
        'metadata': {
            'confidence': 88,
            'duration': 1.8,
            'sources_count': 2,
            'agents_count': 4
        },
        'sources': [
            {'title': 'Agent Documentation', 'page': 8, 'relevance': 0.92},
            {'title': 'Architecture Overview', 'page': 3, 'relevance': 0.85}
        ]
    },
    {
        'role': 'user',
        'content': 'Welche Dateiformate werden unterstützt?',
        'timestamp': (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d %H:%M:%S'),
    },
    {
        'role': 'assistant',
        'content': '''### Unterstützte Dateiformate

#### Dokumente (7):
- .pdf, .docx, .doc, .txt, .md, .rtf, .odt

#### Bilder (6):
- .png, .jpg, .jpeg, .gif, .bmp, .webp

#### Daten (8):
- .csv, .xlsx, .xls, .json, .xml, .yaml, .yml

#### Code (11):
- .py, .js, .ts, .java, .cpp, .c, .h, .cs, .go, .rs, .sql''',
        'timestamp': (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d %H:%M:%S'),
        'metadata': {
            'confidence': 95,
            'duration': 1.2,
            'sources_count': 1
        },
        'sources': [
            {'title': 'File Format Documentation', 'page': 2, 'relevance': 0.98}
        ]
    }
]

SAMPLE_FEEDBACK_STATS = {
    'total_feedback': 150,
    'positive_count': 120,
    'negative_count': 20,
    'neutral_count': 10,
    'positive_ratio': 80.0,
    'average_rating': 0.667
}


def test_word_export():
    """Test: Word-Export"""
    print("\n" + "="*60)
    print("🧪 TEST 1: Word-Export (.docx)")
    print("="*60)
    
    service = OfficeExportService(output_dir=Path("./test_exports"))
    
    try:
        output_path = service.export_to_word(
            chat_messages=SAMPLE_MESSAGES,
            title="VERITAS Test-Chat",
            include_metadata=True,
            include_sources=True
        )
        
        print(f"✅ Word-Dokument erstellt: {output_path}")
        print(f"   📏 Dateigröße: {output_path.stat().st_size / 1024:.1f} KB")
        print(f"   📄 Anzahl Messages: {len(SAMPLE_MESSAGES)}")
        
        return True
    
    except Exception as e:
        print(f"❌ Fehler: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_excel_export():
    """Test: Excel-Export"""
    print("\n" + "="*60)
    print("🧪 TEST 2: Excel-Export (.xlsx)")
    print("="*60)
    
    service = OfficeExportService(output_dir=Path("./test_exports"))
    
    try:
        output_path = service.export_to_excel(
            chat_messages=SAMPLE_MESSAGES,
            feedback_stats=SAMPLE_FEEDBACK_STATS
        )
        
        print(f"✅ Excel-Arbeitsmappe erstellt: {output_path}")
        print(f"   📏 Dateigröße: {output_path.stat().st_size / 1024:.1f} KB")
        print(f"   📊 Sheets: Chat Messages, Statistiken, Quellen")
        
        return True
    
    except Exception as e:
        print(f"❌ Fehler: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_date_filtering():
    """Test: Zeitraum-Filter"""
    print("\n" + "="*60)
    print("🧪 TEST 3: Zeitraum-Filter")
    print("="*60)
    
    service = OfficeExportService()
    
    # Test verschiedene Zeiträume
    for days in [1, 7, 30]:
        filtered = service.filter_messages_by_date(SAMPLE_MESSAGES, days=days)
        print(f"✅ Letzte {days} Tage: {len(filtered)} von {len(SAMPLE_MESSAGES)} Messages")
    
    return True


def test_custom_filename():
    """Test: Custom Filename"""
    print("\n" + "="*60)
    print("🧪 TEST 4: Custom Filename")
    print("="*60)
    
    service = OfficeExportService(output_dir=Path("./test_exports"))
    
    try:
        output_path = service.export_to_word(
            chat_messages=SAMPLE_MESSAGES[:2],  # Nur erste 2 Messages
            filename="custom_test_export.docx",
            title="Custom Export Test",
            include_metadata=False,
            include_sources=False
        )
        
        print(f"✅ Custom Dateiname: {output_path.name}")
        print(f"   Erwarteter Name: custom_test_export.docx")
        print(f"   ✅ Match: {output_path.name == 'custom_test_export.docx'}")
        
        return True
    
    except Exception as e:
        print(f"❌ Fehler: {e}")
        return False


def test_empty_messages():
    """Test: Leere Message-Liste"""
    print("\n" + "="*60)
    print("🧪 TEST 5: Leere Message-Liste")
    print("="*60)
    
    service = OfficeExportService(output_dir=Path("./test_exports"))
    
    try:
        output_path = service.export_to_word(
            chat_messages=[],
            title="Leerer Chat"
        )
        
        print(f"✅ Leeres Dokument erstellt: {output_path}")
        print(f"   📄 Anzahl Messages: 0")
        
        return True
    
    except Exception as e:
        print(f"❌ Fehler: {e}")
        return False


def test_supported_formats():
    """Test: Unterstützte Formate"""
    print("\n" + "="*60)
    print("🧪 TEST 6: Unterstützte Formate")
    print("="*60)
    
    service = OfficeExportService()
    
    formats = service.get_supported_formats()
    print(f"✅ Unterstützte Formate: {', '.join(formats)}")
    
    expected = ['.docx', '.xlsx']
    success = all(fmt in formats for fmt in expected)
    print(f"   Erwartet: {expected}")
    print(f"   ✅ Alle verfügbar: {success}")
    
    return success


def run_all_tests():
    """Führt alle Tests aus"""
    print("\n" + "🧪 VERITAS Office Export Test Suite ".center(60, '='))
    print(f"Datum: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    tests = [
        ("Word-Export", test_word_export),
        ("Excel-Export", test_excel_export),
        ("Zeitraum-Filter", test_date_filtering),
        ("Custom Filename", test_custom_filename),
        ("Leere Messages", test_empty_messages),
        ("Unterstützte Formate", test_supported_formats),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success, None))
        except Exception as e:
            results.append((test_name, False, str(e)))
            print(f"\n❌ {test_name}: EXCEPTION - {e}")
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, success, _ in results if success)
    failed = len(results) - passed
    
    for test_name, success, error in results:
        status = "✅ PASS" if success else f"❌ FAIL"
        if error:
            status += f": {error}"
        print(f"{test_name:.<40} {status}")
    
    print(f"\nTotal: {len(results)}, Passed: {passed}, Failed: {failed}")
    
    # Exportierte Dateien
    export_dir = Path("./test_exports")
    if export_dir.exists():
        files = list(export_dir.glob("*"))
        print(f"\n📁 Exportierte Dateien ({len(files)}):")
        for file in files:
            print(f"   📄 {file.name} ({file.stat().st_size / 1024:.1f} KB)")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
