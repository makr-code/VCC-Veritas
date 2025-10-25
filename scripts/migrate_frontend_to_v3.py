#!/usr/bin/env python3
"""
VERITAS Frontend Migration Script - API v2 → v3
Automatisches Migrieren aller Frontend API-Calls auf API v3
"""

import os
import re
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple

# =============================================================================
# KONFIGURATION
# =============================================================================

PROJECT_ROOT = Path(__file__).parent.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"
BACKUP_DIR = PROJECT_ROOT / "backup_frontend_pre_v3_migration"

# Endpoint-Mapping: Old → New
# HINWEIS: Die meisten Endpoints müssen NICHT geändert werden, 
# da API_BASE_URL jetzt bereits "/api/v3" enthält!
# Wir ändern nur die Legacy-Endpoints die noch absolut sind.
ENDPOINT_MIGRATIONS = {
    # Legacy absolute Endpoints → Relative Endpoints
    # Diese werden automatisch mit API_BASE_URL kombiniert
    
    # Beispiel: "/ask" → "/query" (wird zu /api/v3/query mit neuer BASE_URL)
    # ABER: veritas_app.py nutzt f"{API_BASE_URL}/ask" - bleibt so!
    
    # Nur spezielle Fälle:
    r'"/health"': '"/health"',  # Root-Endpoint (außerhalb /api/v3)
    r"'/health'": "'/health'",
}

# Response-Field-Mapping
RESPONSE_FIELD_MIGRATIONS = {
    # Legacy Fields → API v3 Fields
    r'\.get\("response"\)': '.get("content")',
    r'\["response"\]': '["content"]',
    r'response_data\["response"\]': 'response_data["content"]',
    r'data\["response"\]': 'data["content"]',
    
    r'\.get\("status"\)': '.get("status")',  # Bleibt gleich
    r'\.get\("sources"\)': '.get("sources")',  # Bleibt gleich
    r'\.get\("confidence"\)': '.get("confidence")',  # Bleibt gleich
}

# Dateien die ignoriert werden sollen
IGNORE_PATTERNS = [
    "__pycache__",
    "*.pyc",
    ".git",
    ".vscode",
    "node_modules",
    "venv",
    ".pytest_cache"
]

# =============================================================================
# HILFSFUNKTIONEN
# =============================================================================

def should_ignore(path: Path) -> bool:
    """Prüft ob Datei/Verzeichnis ignoriert werden soll"""
    path_str = str(path)
    for pattern in IGNORE_PATTERNS:
        if pattern.replace("*", "") in path_str:
            return True
    return False


def find_python_files(directory: Path) -> List[Path]:
    """Findet alle Python-Dateien rekursiv"""
    python_files = []
    for root, dirs, files in os.walk(directory):
        # Ignoriere bestimmte Verzeichnisse
        dirs[:] = [d for d in dirs if not should_ignore(Path(root) / d)]
        
        for file in files:
            if file.endswith('.py'):
                file_path = Path(root) / file
                if not should_ignore(file_path):
                    python_files.append(file_path)
    
    return python_files


def analyze_file(file_path: Path) -> Dict[str, List[Tuple[int, str, str]]]:
    """Analysiert Datei auf zu migrierende API-Calls"""
    results = {
        "endpoints": [],
        "response_fields": []
    }
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for line_num, line in enumerate(lines, 1):
            # Prüfe Endpoint-Patterns
            for old_pattern, new_endpoint in ENDPOINT_MIGRATIONS.items():
                if re.search(old_pattern, line):
                    old_endpoint = old_pattern.strip('r"\'')
                    results["endpoints"].append((line_num, old_endpoint, new_endpoint.strip('"')))
            
            # Prüfe Response-Field-Patterns
            for old_pattern, new_field in RESPONSE_FIELD_MIGRATIONS.items():
                if re.search(old_pattern, line):
                    results["response_fields"].append((line_num, old_pattern, new_field))
    
    except Exception as e:
        print(f"❌ Fehler beim Analysieren von {file_path}: {e}")
    
    return results


def migrate_file(file_path: Path, dry_run: bool = False) -> Tuple[int, int]:
    """Migriert eine Datei zu API v3"""
    endpoint_count = 0
    field_count = 0
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Migriere Endpoints
        for old_pattern, new_endpoint in ENDPOINT_MIGRATIONS.items():
            if re.search(old_pattern, content):
                content = re.sub(old_pattern, new_endpoint, content)
                endpoint_count += 1
        
        # Migriere Response-Fields
        for old_pattern, new_field in RESPONSE_FIELD_MIGRATIONS.items():
            if re.search(old_pattern, content):
                content = re.sub(old_pattern, new_field, content)
                field_count += 1
        
        # Schreibe nur wenn geändert und nicht Dry-Run
        if content != original_content and not dry_run:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
    
    except Exception as e:
        print(f"❌ Fehler beim Migrieren von {file_path}: {e}")
    
    return endpoint_count, field_count


def create_backup():
    """Erstellt Backup des Frontend-Verzeichnisses"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / timestamp
    
    print(f"📦 Erstelle Backup: {backup_path}")
    
    try:
        shutil.copytree(FRONTEND_DIR, backup_path, 
                       ignore=shutil.ignore_patterns(*IGNORE_PATTERNS))
        print(f"✅ Backup erstellt: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"❌ Backup fehlgeschlagen: {e}")
        return None


def create_report(analysis_results: Dict[Path, Dict], 
                 migration_results: Dict[Path, Tuple[int, int]],
                 output_path: Path):
    """Erstellt Migrations-Report"""
    
    report_lines = [
        "# VERITAS Frontend Migration Report - API v3",
        "",
        f"**Datum**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "---",
        "",
        "## 📊 Zusammenfassung",
        ""
    ]
    
    # Statistiken
    total_files = len(analysis_results)
    migrated_files = len([f for f, (e, r) in migration_results.items() if e > 0 or r > 0])
    total_endpoints = sum(e for e, r in migration_results.values())
    total_fields = sum(r for e, r in migration_results.values())
    
    report_lines.extend([
        f"- **Analysierte Dateien**: {total_files}",
        f"- **Migrierte Dateien**: {migrated_files}",
        f"- **Migrierte Endpoints**: {total_endpoints}",
        f"- **Migrierte Response-Fields**: {total_fields}",
        "",
        "---",
        "",
        "## 📁 Migrierte Dateien",
        ""
    ])
    
    # Datei-Details
    for file_path, (endpoint_count, field_count) in migration_results.items():
        if endpoint_count > 0 or field_count > 0:
            rel_path = file_path.relative_to(PROJECT_ROOT)
            report_lines.append(f"### `{rel_path}`")
            report_lines.append("")
            report_lines.append(f"- **Endpoints**: {endpoint_count}")
            report_lines.append(f"- **Response-Fields**: {field_count}")
            
            # Details aus Analyse
            if file_path in analysis_results:
                analysis = analysis_results[file_path]
                
                if analysis["endpoints"]:
                    report_lines.append("")
                    report_lines.append("**Endpoint-Änderungen:**")
                    for line_num, old, new in analysis["endpoints"]:
                        report_lines.append(f"- Line {line_num}: `{old}` → `{new}`")
                
                if analysis["response_fields"]:
                    report_lines.append("")
                    report_lines.append("**Response-Field-Änderungen:**")
                    for line_num, old, new in analysis["response_fields"]:
                        report_lines.append(f"- Line {line_num}: `{old}` → `{new}`")
            
            report_lines.append("")
    
    # Endpoint-Mapping
    report_lines.extend([
        "---",
        "",
        "## 🔄 Endpoint-Mapping",
        "",
        "| Legacy Endpoint | API v3 Endpoint |",
        "|-----------------|-----------------|"
    ])
    
    unique_mappings = {}
    for old, new in ENDPOINT_MIGRATIONS.items():
        old_clean = old.strip('r"\'')
        new_clean = new.strip('"\'')
        unique_mappings[old_clean] = new_clean
    
    for old, new in sorted(unique_mappings.items()):
        report_lines.append(f"| `{old}` | `{new}` |")
    
    # Response-Field-Mapping
    report_lines.extend([
        "",
        "---",
        "",
        "## 🔄 Response-Field-Mapping",
        "",
        "| Legacy Field | API v3 Field |",
        "|--------------|--------------|"
    ])
    
    unique_field_mappings = {}
    for old, new in RESPONSE_FIELD_MIGRATIONS.items():
        unique_field_mappings[old] = new
    
    for old, new in sorted(unique_field_mappings.items()):
        report_lines.append(f"| `{old}` | `{new}` |")
    
    # Schreibe Report
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))
        print(f"✅ Report erstellt: {output_path}")
    except Exception as e:
        print(f"❌ Report-Erstellung fehlgeschlagen: {e}")


# =============================================================================
# HAUPTFUNKTIONEN
# =============================================================================

def analyze_frontend():
    """Analysiert Frontend-Dateien"""
    print("=" * 80)
    print("  VERITAS Frontend Migration - Analyse")
    print("=" * 80)
    print()
    
    python_files = find_python_files(FRONTEND_DIR)
    print(f"📁 Gefundene Python-Dateien: {len(python_files)}")
    print()
    
    analysis_results = {}
    files_to_migrate = []
    
    for file_path in python_files:
        results = analyze_file(file_path)
        if results["endpoints"] or results["response_fields"]:
            analysis_results[file_path] = results
            files_to_migrate.append(file_path)
            
            rel_path = file_path.relative_to(PROJECT_ROOT)
            print(f"📄 {rel_path}")
            print(f"   Endpoints: {len(results['endpoints'])}")
            print(f"   Response-Fields: {len(results['response_fields'])}")
    
    print()
    print(f"📊 Zu migrierende Dateien: {len(files_to_migrate)}")
    print()
    
    return analysis_results


def migrate_frontend(dry_run: bool = False):
    """Migriert Frontend zu API v3"""
    print("=" * 80)
    print(f"  VERITAS Frontend Migration - {'DRY RUN' if dry_run else 'LIVE'}")
    print("=" * 80)
    print()
    
    # Backup erstellen (nur bei Live-Run)
    if not dry_run:
        backup_path = create_backup()
        if not backup_path:
            print("❌ Backup fehlgeschlagen - Migration abgebrochen!")
            return
        print()
    
    # Analysiere zuerst
    analysis_results = {}
    python_files = find_python_files(FRONTEND_DIR)
    
    for file_path in python_files:
        results = analyze_file(file_path)
        if results["endpoints"] or results["response_fields"]:
            analysis_results[file_path] = results
    
    print(f"📁 Zu migrierende Dateien: {len(analysis_results)}")
    print()
    
    # Migriere Dateien
    migration_results = {}
    total_endpoints = 0
    total_fields = 0
    
    for file_path in analysis_results.keys():
        endpoint_count, field_count = migrate_file(file_path, dry_run=dry_run)
        migration_results[file_path] = (endpoint_count, field_count)
        total_endpoints += endpoint_count
        total_fields += field_count
        
        rel_path = file_path.relative_to(PROJECT_ROOT)
        if endpoint_count > 0 or field_count > 0:
            status = "✅" if not dry_run else "🔍"
            print(f"{status} {rel_path}")
            print(f"   Endpoints: {endpoint_count}, Fields: {field_count}")
    
    print()
    print("=" * 80)
    print("  Zusammenfassung")
    print("=" * 80)
    print(f"Migrierte Dateien: {len([f for f, (e, r) in migration_results.items() if e > 0 or r > 0])}")
    print(f"Migrierte Endpoints: {total_endpoints}")
    print(f"Migrierte Response-Fields: {total_fields}")
    print()
    
    # Erstelle Report (nur bei Live-Run)
    if not dry_run:
        report_path = PROJECT_ROOT / "docs" / "FRONTEND_MIGRATION_V3_REPORT.md"
        create_report(analysis_results, migration_results, report_path)
        print()
    
    return analysis_results, migration_results


def main():
    """Hauptfunktion"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="VERITAS Frontend Migration - API v2 → v3"
    )
    parser.add_argument(
        "--analyze",
        action="store_true",
        help="Nur analysieren, keine Änderungen"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry-Run: Zeige was geändert würde"
    )
    parser.add_argument(
        "--migrate",
        action="store_true",
        help="Live-Migration durchführen"
    )
    
    args = parser.parse_args()
    
    if args.analyze:
        analyze_frontend()
    elif args.dry_run:
        migrate_frontend(dry_run=True)
    elif args.migrate:
        print("⚠️  WARNUNG: Live-Migration startet in 3 Sekunden...")
        print("⚠️  Drücke Ctrl+C zum Abbrechen")
        import time
        time.sleep(3)
        migrate_frontend(dry_run=False)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
