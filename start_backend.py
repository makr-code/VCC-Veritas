#!/usr/bin/env python3
"""
VERITAS Backend Launcher
Startet das VERITAS Backend-API mit korrekter Pfad-Konfiguration
"""
import sys
import os
import warnings
import logging

# Unterdrücke UDS3 Module Warnings (optional)
warnings.filterwarnings('ignore', message='.*module not available.*')
logging.getLogger().setLevel(logging.ERROR)  # Nur Errors anzeigen

# Setup Python-Pfade
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'frontend'))
sys.path.insert(0, os.path.join(project_root, 'backend'))
sys.path.insert(0, os.path.join(project_root, 'shared'))
sys.path.insert(0, os.path.join(project_root, 'database'))
sys.path.insert(0, os.path.join(project_root, 'uds3'))

print("⚙️ Starte VERITAS Backend API...")
print("📁 Project Root:", project_root)
print("🌐 API wird verfügbar unter: http://localhost:5000")

try:
    # Import uvicorn
    import uvicorn
    
    # Starte Backend mit uvicorn
    uvicorn.run(
        "backend.api.veritas_api_backend:app",
        host="0.0.0.0",
        port=5000,
        log_level="info",
        reload=False
    )
    
except Exception as e:
    print(f"❌ Fehler beim Starten des Backends: {e}")
    import traceback
    traceback.print_exc()
    
    print("\n🔧 Mögliche Lösungen:")
    print("1. Fehlende Dependencies installieren:")
    print("   pip install fastapi uvicorn requests")
    print("2. Port 5000 freigeben")
    print("3. UDS3 und Database-Module überprüfen")