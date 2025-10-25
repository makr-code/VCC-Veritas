#!/usr/bin/env python3
"""
VERITAS Unified Backend Launcher
=================================

Startet das konsolidierte VERITAS Backend v4.0.0

Features:
- UDS3 v2.0.0 Integration
- Intelligent Multi-Agent Pipeline
- Unified Response Model (IEEE Citations)
- Hybrid Search, Streaming, Agent Queries

Version: 4.0.0
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

print("=" * 80)
print("⚙️  Starte VERITAS Unified Backend v4.0.0...")
print("=" * 80)
print("📁 Project Root:", project_root)
print("🌐 API Base: http://localhost:5000/api")
print("📖 Docs: http://localhost:5000/docs")
print("📊 Health: http://localhost:5000/api/system/health")
print("=" * 80)

try:
    # Import uvicorn
    import uvicorn
    
    # Starte Konsolidiertes Backend
    uvicorn.run(
        "backend.app:app",  # ✨ Backend v4.0.0: Unified Application
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