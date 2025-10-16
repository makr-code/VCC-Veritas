#!/usr/bin/env python3
"""
VERITAS Setup Script
Konfiguriert Python-Pfade und Umgebung für das reorganisierte Projekt
"""
import sys
import os

# Bestimme das Projekt-Root-Verzeichnis
project_root = os.path.dirname(os.path.abspath(__file__))

# Füge alle notwendigen Pfade zum Python-Pfad hinzu
paths_to_add = [
    project_root,                           # Root für direkte Imports
    os.path.join(project_root, 'frontend'), # Frontend-Pakete
    os.path.join(project_root, 'backend'),  # Backend-Pakete  
    os.path.join(project_root, 'shared'),   # Shared-Pakete
    os.path.join(project_root, 'database'), # Database-Module
    os.path.join(project_root, 'uds3'),     # UDS3-Module
    os.path.join(project_root, 'config'),   # Config-Module
]

# Pfade hinzufügen (nur wenn noch nicht vorhanden)
for path in paths_to_add:
    if path not in sys.path:
        sys.path.insert(0, path)

print("✅ VERITAS Python-Pfade konfiguriert:")
for i, path in enumerate(sys.path[:len(paths_to_add) + 3]):
    print(f"   {i+1}. {path}")

# Teste kritische Imports
print("\n🧪 Teste kritische Imports...")

try:
    from uds3.uds3_core import OptimizedUnifiedDatabaseStrategy
    print("✅ UDS3 Core verfügbar")
except ImportError as e:
    print(f"❌ UDS3 Core fehlt: {e}")

try:
    from database_api import MultiDatabaseAPI  
    print("✅ Database API verfügbar")
except ImportError as e:
    print(f"❌ Database API fehlt: {e}")

try:
    from shared.core.veritas_core import VeritasCore
    print("✅ VERITAS Core verfügbar")
except ImportError as e:
    print(f"❌ VERITAS Core fehlt: {e}")

try:
    from frontend.ui.veritas_ui_components import Tooltip
    print("✅ UI Components verfügbar")
except ImportError as e:
    print(f"❌ UI Components fehlen: {e}")

print("\n🎯 Setup abgeschlossen. Ready für VERITAS!")