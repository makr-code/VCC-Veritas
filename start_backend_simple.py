#!/usr/bin/env python3
"""
Einfacher Backend-Start mit Status-Output
"""
import os
import sys

print("=" * 80)
print("🚀 VERITAS Backend wird gestartet...")
print("=" * 80)

# Python-Pfad prüfen
print(f"Python: {sys.version}")
print(f"CWD: {os.getcwd()}")

try:
    print("\n📦 Importiere Module...")

    # Backend importieren
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

    from backend.api import veritas_api_backend

    print("✅ Backend-Modul geladen")
    print("\n🌐 Starte FastAPI Server auf http://localhost:5000...")
    print("=" * 80)
    print("\nDrücke Ctrl+C zum Beenden\n")

    # Server starten
    import uvicorn

    uvicorn.run(veritas_api_backend.app, host="0.0.0.0", port=5000, log_level="info")

except ImportError as e:
    print(f"\n❌ Import-Fehler: {e}")
    print("\nFehlende Module installieren:")
    print("  pip install fastapi uvicorn aiohttp")
    sys.exit(1)
except Exception as e:
    print(f"\n❌ Fehler beim Start: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)
