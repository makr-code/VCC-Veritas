#!/usr/bin/env python3
"""
VERITAS Frontend Launcher
Startet die VERITAS Frontend-Anwendung mit korrekter Pfad-Konfiguration
"""
import os
import sys

# Setup Python-Pfade
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "frontend"))
sys.path.insert(0, os.path.join(project_root, "backend"))
sys.path.insert(0, os.path.join(project_root, "shared"))
sys.path.insert(0, os.path.join(project_root, "database"))
sys.path.insert(0, os.path.join(project_root, "uds3"))

print("🚀 Starte VERITAS Frontend...")
print("📁 Project Root:", project_root)

try:
    # Importiere und starte das Frontend
    os.chdir(os.path.join(project_root, "frontend"))

    # Führe veritas_app.py aus
    with open("veritas_app.py", "r", encoding="utf-8") as f:
        exec(f.read())

except Exception as e:
    print(f"❌ Fehler beim Starten des Frontends: {e}")
    import traceback

    traceback.print_exc()

    print("\n🔧 Mögliche Lösungen:")
    print("1. Fehlende Dependencies installieren:")
    print("   pip install tkinter requests sseclient-py")
    print("2. UDS3 und Database-Module überprüfen")
    print("3. Missing 'universal_json_payload' Module")
