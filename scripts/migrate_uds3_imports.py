#!/usr/bin/env python3
"""
VERITAS UDS3 Import Migration Script
=====================================

Aktualisiert alle UDS3-Imports in VERITAS fuer die neue Package-Struktur:
- UDS3 liegt jetzt bei: C:/VCC/uds3 (ausserhalb von VERITAS)
- PYTHONPATH: C:/VCC (dauerhaft gesetzt)
- Import-Pattern: 'from uds3_X' -> 'from uds3.uds3_X'

Betroffene Dateien (9):
1. backend/agents/veritas_intelligent_pipeline.py       ✅ Bereits korrekt
2. backend/agents/veritas_api_agent_orchestrator.py     ✅ Bereits korrekt  
3. backend/agents/veritas_api_agent_core_components.py  ❌ Zu ändern
4. backend/agents/veritas_api_agent_registry.py         ❌ Zu ändern
5. backend/agents/veritas_api_agent_environmental.py    ❌ Zu ändern
6. backend/agents/veritas_agent_template.py             ❌ Zu ändern
7. backend/api/veritas_api_backend.py                   ❌ Zu ändern
8. backend/api/veritas_api_manager_enhanced.py          ❌ Zu ändern
9. shared/core/veritas_core.py                          ❌ Zu ändern
10. setup_veritas.py                                    ❌ Zu ändern
11. test_frontend_backend_uds3.py                       ❌ Zu ändern
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple, Dict

# ANSI Color Codes
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
CYAN = '\033[96m'
RESET = '\033[0m'

# Betroffene Dateien (relativ zu VERITAS root)
FILES_TO_UPDATE = [
    "backend/agents/veritas_api_agent_core_components.py",
    "backend/agents/veritas_api_agent_registry.py",
    "backend/agents/veritas_api_agent_environmental.py",
    "backend/agents/veritas_agent_template.py",
    "backend/api/veritas_api_backend.py",
    "backend/api/veritas_api_manager_enhanced.py",
    "shared/core/veritas_core.py",
    "setup_veritas.py",
    "test_frontend_backend_uds3.py",
]

# Import-Replacement Patterns
# Format: (pattern, replacement, description)
IMPORT_PATTERNS: List[Tuple[str, str, str]] = [
    # Pattern 1: from uds3_X import Y
    (
        r'^(\s*)from uds3_(\w+) import (.+)$',
        r'\1from uds3.uds3_\2 import \3',
        "from uds3_X import Y → from uds3.uds3_X import Y"
    ),
    # Pattern 2: import uds3_X
    (
        r'^(\s*)import uds3_(\w+)(.*)$',
        r'\1import uds3.uds3_\2\3',
        "import uds3_X → import uds3.uds3_X"
    ),
    # Pattern 3: from uds3_X.Y import Z (nested modules)
    (
        r'^(\s*)from uds3_(\w+)\.(\w+) import (.+)$',
        r'\1from uds3.uds3_\2.\3 import \4',
        "from uds3_X.Y import Z → from uds3.uds3_X.Y import Z"
    ),
]


def analyze_file(file_path: Path) -> Dict[str, any]:
    """
    Analysiere eine Datei und finde alle zu ändernden Imports.
    
    Returns:
        Dict mit 'changes': List[(line_num, old_line, new_line)]
    """
    if not file_path.exists():
        return {'error': 'Datei nicht gefunden', 'changes': []}
    
    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception as e:
        return {'error': f'Fehler beim Lesen: {e}', 'changes': []}
    
    lines = content.split('\n')
    changes = []
    
    for line_num, line in enumerate(lines, 1):
        for pattern, replacement, description in IMPORT_PATTERNS:
            match = re.match(pattern, line)
            if match:
                new_line = re.sub(pattern, replacement, line)
                if new_line != line:
                    changes.append({
                        'line_num': line_num,
                        'old_line': line,
                        'new_line': new_line,
                        'pattern_desc': description
                    })
                break  # Only apply first matching pattern
    
    return {
        'changes': changes,
        'total_lines': len(lines)
    }


def apply_changes(file_path: Path, dry_run: bool = False) -> bool:
    """
    Wende Import-Änderungen auf eine Datei an.
    
    Args:
        file_path: Pfad zur Datei
        dry_run: Wenn True, nur Analyse ohne Änderungen
    
    Returns:
        True wenn Änderungen vorgenommen wurden
    """
    if not file_path.exists():
        print(f"{RED}❌ Datei nicht gefunden: {file_path}{RESET}")
        return False
    
    try:
        content = file_path.read_text(encoding='utf-8')
        original_content = content
        
        # Wende alle Patterns an
        for pattern, replacement, _ in IMPORT_PATTERNS:
            content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
        
        if content == original_content:
            return False  # Keine Änderungen
        
        if not dry_run:
            # Backup erstellen
            backup_path = file_path.with_suffix('.py.bak')
            file_path.rename(backup_path)
            
            # Neue Datei schreiben
            file_path.write_text(content, encoding='utf-8')
            print(f"{GREEN}✅ {file_path.relative_to(Path.cwd())}: Aktualisiert{RESET}")
            print(f"   Backup: {backup_path.name}")
        else:
            print(f"{YELLOW}📝 {file_path.relative_to(Path.cwd())}: Würde aktualisiert{RESET}")
        
        return True
        
    except Exception as e:
        print(f"{RED}❌ Fehler bei {file_path}: {e}{RESET}")
        return False


def main():
    """Haupt-Migrations-Funktion"""
    print(f"{CYAN}{'=' * 80}{RESET}")
    print(f"{CYAN}VERITAS UDS3 IMPORT MIGRATION{RESET}")
    print(f"{CYAN}{'=' * 80}{RESET}\n")
    
    # Prüfe ob wir im VERITAS-Verzeichnis sind
    project_root = Path.cwd()
    if not (project_root / 'backend' / 'agents').exists():
        print(f"{RED}❌ Fehler: Nicht im VERITAS-Root-Verzeichnis!{RESET}")
        print(f"   Aktuelles Verzeichnis: {project_root}")
        print(f"   Bitte zu C:\\VCC\\veritas wechseln!")
        sys.exit(1)
    
    print(f"📁 VERITAS Root: {project_root}\n")
    
    # Dry-Run Parameter
    dry_run = '--dry-run' in sys.argv or '-n' in sys.argv
    if dry_run:
        print(f"{YELLOW}🔍 DRY-RUN MODE (keine Änderungen){RESET}\n")
    
    # Analysiere alle Dateien
    print(f"{CYAN}📊 Analysiere Dateien...{RESET}\n")
    
    results = []
    for file_rel in FILES_TO_UPDATE:
        file_path = project_root / file_rel
        print(f"\n📄 {file_rel}")
        print(f"   {'─' * 60}")
        
        analysis = analyze_file(file_path)
        
        if 'error' in analysis:
            print(f"   {RED}❌ {analysis['error']}{RESET}")
            continue
        
        changes = analysis['changes']
        if not changes:
            print(f"   {GREEN}✅ Keine Änderungen nötig (bereits korrekt){RESET}")
            results.append({'file': file_rel, 'status': 'ok', 'changes': 0})
            continue
        
        # Zeige Änderungen
        print(f"   {YELLOW}📝 {len(changes)} Import(s) zu ändern:{RESET}")
        for change in changes:
            print(f"   Line {change['line_num']}:")
            print(f"      {RED}- {change['old_line']}{RESET}")
            print(f"      {GREEN}+ {change['new_line']}{RESET}")
        
        # Wende Änderungen an
        if apply_changes(file_path, dry_run=dry_run):
            results.append({'file': file_rel, 'status': 'updated', 'changes': len(changes)})
        else:
            results.append({'file': file_rel, 'status': 'error', 'changes': 0})
    
    # Zusammenfassung
    print(f"\n{CYAN}{'=' * 80}{RESET}")
    print(f"{CYAN}ZUSAMMENFASSUNG{RESET}")
    print(f"{CYAN}{'=' * 80}{RESET}\n")
    
    total_files = len(results)
    updated_files = sum(1 for r in results if r['status'] == 'updated')
    ok_files = sum(1 for r in results if r['status'] == 'ok')
    error_files = sum(1 for r in results if r['status'] == 'error')
    total_changes = sum(r['changes'] for r in results)
    
    print(f"📊 Dateien gesamt:    {total_files}")
    print(f"{GREEN}✅ Bereits korrekt:   {ok_files}{RESET}")
    print(f"{YELLOW}📝 Aktualisiert:      {updated_files}{RESET}")
    print(f"{RED}❌ Fehler:            {error_files}{RESET}")
    print(f"🔄 Änderungen gesamt: {total_changes}")
    
    if dry_run:
        print(f"\n{YELLOW}💡 Führe ohne --dry-run aus um Änderungen anzuwenden{RESET}")
    else:
        if updated_files > 0:
            print(f"\n{GREEN}✅ Migration abgeschlossen!{RESET}")
            print(f"\n📝 Nächste Schritte:")
            print(f"   1. Prüfe Änderungen: git diff")
            print(f"   2. Teste Pipeline: python backend/evaluation/run_baseline_evaluation.py")
            print(f"   3. Commit Änderungen: git commit -am 'Migrate UDS3 imports to C:\\VCC\\uds3'")
    
    print(f"\n{CYAN}{'=' * 80}{RESET}\n")


if __name__ == "__main__":
    main()
