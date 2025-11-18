#!/usr/bin/env python3
"""
VERITAS Frontend Migration - Manuelle Anpassung
Da API_BASE_URL jetzt /api/v3 enthält, müssen wir die Endpoint-Aufrufe im Frontend prüfen.

Strategie:
1. Config.py: API_BASE_URL = "http://127.0.0.1:5000/api/v3" ✅ Bereits erledigt
2. Frontend API-Calls müssen relative Pfade für v3 verwenden

   ALT: f"{API_BASE_URL}/v2/query"
   →  http://127.0.0.1:5000/v2/query

   NEU: f"{API_BASE_URL}/query/execute"
   →  http://127.0.0.1:5000/api/v3/query/execute

3. Root-Endpoints (health) brauchen absolute URLs
"""

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
VERITAS_APP = PROJECT_ROOT / "frontend" / "veritas_app.py"

# Mapping der Endpoint-Aufrufe
ENDPOINT_REPLACEMENTS = {
    # Query-Endpoints
    r'f"{API_BASE_URL}/v2/query"': 'f"{API_BASE_URL}/query/execute"',
    r'f"{API_BASE_URL}/ask"': 'f"{API_BASE_URL}/query"',
    r'f"{API_BASE_URL}/v2/intelligent/query"': 'f"{API_BASE_URL}/query/execute"',
    # System-Endpoints
    r'f"{API_BASE_URL}/capabilities"': 'f"{API_BASE_URL}/system/capabilities"',
    r'f"{API_BASE_URL}/get_models"': 'f"{API_BASE_URL}/system/models"',
    r'f"{API_BASE_URL}/modes"': 'f"{API_BASE_URL}/system/modes"',
    # Health braucht ROOT (ohne /api/v3)
    r'f"{API_BASE_URL}/health"': 'f"http://127.0.0.1:5000/health"',
    # UDS3-Endpoints
    r'f"{API_BASE_URL}/uds3/query"': 'f"{API_BASE_URL}/uds3/query"',  # Bleibt gleich
    r'f"{API_BASE_URL}/uds3/status"': 'f"{API_BASE_URL}/uds3/stats"',
    # Conversations
    r'f"{API_BASE_URL}/recent_conversations"': 'f"{API_BASE_URL}/system/conversations/recent"',
}


def migrate_veritas_app():
    """Migriert veritas_app.py zu API v3"""
    print("=" * 80)
    print("  VERITAS App - API v3 Migration")
    print("=" * 80)
    print()

    if not VERITAS_APP.exists():
        print(f"❌ Datei nicht gefunden: {VERITAS_APP}")
        return

    # Lese Datei
    with open(VERITAS_APP, "r", encoding="utf-8") as f:
        content = f.read()

    original_content = content
    changes = 0

    # Ersetze Endpoints
    for old, new in ENDPOINT_REPLACEMENTS.items():
        # Entferne r'' Prefix für Matching
        old_pattern = old.replace('r"', '"').replace("r'", "'")
        if old_pattern in content:
            content = content.replace(old_pattern, new.replace('"', ""))
            changes += 1
            print(f"✅ {old_pattern}")
            print(f"   → {new}")
            print()

    if changes > 0:
        # Backup erstellen
        backup_path = VERITAS_APP.with_suffix(".py.backup_pre_v3")
        with open(backup_path, "w", encoding="utf-8") as f:
            f.write(original_content)
        print(f"📦 Backup erstellt: {backup_path}")

        # Speichere geänderte Datei
        with open(VERITAS_APP, "w", encoding="utf-8") as f:
            f.write(content)

        print()
        print(f"✅ Migration abgeschlossen: {changes} Änderungen")
    else:
        print("ℹ️  Keine Änderungen nötig")


if __name__ == "__main__":
    migrate_veritas_app()
