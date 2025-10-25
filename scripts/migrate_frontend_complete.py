#!/usr/bin/env python3
"""
VERITAS Frontend - Vollständige API v3 Migration
Migriert alle Frontend-Dateien zu API v3
"""

from pathlib import Path
import re

PROJECT_ROOT = Path(__file__).parent.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"

# Dateien und ihre spezifischen Ersetzungen
MIGRATION_TASKS = [
    {
        "file": FRONTEND_DIR / "ui" / "veritas_ui_toolbar.py",
        "replacements": [
            (
                r'f"{API_BASE_URL}/recent_conversations"',
                'f"{API_BASE_URL}/system/conversations/recent"'
            ),
            (
                r'f"{API_BASE_URL}/health"',
                'f"http://127.0.0.1:5000/health"'  # Health ist Root-Endpoint
            ),
        ]
    },
    {
        "file": FRONTEND_DIR / "ui" / "veritas_ui_map_widget.py",
        "replacements": [
            (
                'backend_url: str = "http://localhost:5000"',
                'backend_url: str = "http://localhost:5000/api/v3"'
            ),
        ]
    },
    {
        "file": FRONTEND_DIR / "ui" / "veritas_ui_source_links.py",
        "replacements": [
            # Prüfe ob hier API-Calls sind
        ]
    },
]

def migrate_files():
    """Führt Migration durch"""
    print("=" * 80)
    print("  VERITAS Frontend - Vollständige API v3 Migration")
    print("=" * 80)
    print()
    
    total_changes = 0
    total_files = 0
    
    for task in MIGRATION_TASKS:
        file_path = task["file"]
        
        if not file_path.exists():
            print(f"⚠️  Datei nicht gefunden: {file_path}")
            continue
        
        # Lese Datei
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        file_changes = 0
        
        # Führe Ersetzungen durch
        for old, new in task["replacements"]:
            if old in content:
                content = content.replace(old, new)
                file_changes += 1
                print(f"✅ {file_path.name}")
                print(f"   {old}")
                print(f"   → {new}")
                print()
        
        if file_changes > 0:
            # Backup erstellen
            backup_path = file_path.with_suffix(file_path.suffix + '.backup_pre_v3')
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(original_content)
            
            # Speichere geänderte Datei
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            total_files += 1
            total_changes += file_changes
    
    print("=" * 80)
    print(f"✅ Migration abgeschlossen")
    print(f"   Dateien: {total_files}")
    print(f"   Änderungen: {total_changes}")
    print("=" * 80)

if __name__ == "__main__":
    migrate_files()
