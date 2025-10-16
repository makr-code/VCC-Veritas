#!/usr/bin/env python3
"""
VERITAS Backend Launcher - DEBUG MODE
Startet das VERITAS Backend-API mit maximalen Debug-Logs
"""
import sys
import os
import warnings
import logging

# Setup DETAILED Logging BEFORE any imports
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s [%(name)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/backend_debug.log', mode='w')
    ]
)

# Setup Python-Pfade
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'frontend'))
sys.path.insert(0, os.path.join(project_root, 'backend'))
sys.path.insert(0, os.path.join(project_root, 'shared'))
sys.path.insert(0, os.path.join(project_root, 'database'))
sys.path.insert(0, os.path.join(project_root, 'uds3'))

logger = logging.getLogger(__name__)

print("=" * 80)
print("VERITAS Backend API - DEBUG MODE")
print("=" * 80)
print(f"Project Root: {project_root}")
print(f"API: http://localhost:5000")
print(f"Debug Log: data/backend_debug.log")
print(f"Reload: DISABLED (for code stability)")
print("=" * 80)

try:
    # Import uvicorn
    import uvicorn
    
    # Starte Backend mit uvicorn - OHNE reload
    logger.info("Starting uvicorn Server...")
    uvicorn.run(
        "backend.api.veritas_api_backend:app",
        host="0.0.0.0",
        port=5000,
        log_level="debug",
        reload=False,  # DISABLED - vermeidet Reload-Probleme
        access_log=True
    )
    
except KeyboardInterrupt:
    logger.info("Server stopped by user")
    
except Exception as e:
    logger.error(f"Error starting backend: {e}")
    import traceback
    traceback.print_exc()
    
    print("\n🔧 Mögliche Lösungen:")
    print("1. Fehlende Dependencies installieren:")
    print("   pip install fastapi uvicorn requests")
    print("2. Port 5000 freigeben")
    print("3. UDS3 und Database-Module überprüfen")
