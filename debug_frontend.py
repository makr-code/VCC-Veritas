"""
Debug-Skript um Frontend-Fehler zu finden
"""
import sys
import traceback

print("=" * 60)
print("DEBUG: Starting Veritas Frontend")
print("=" * 60)

try:
    print("DEBUG: Importing veritas_app...")
    sys.path.insert(0, 'frontend')
    
    # Importiere nur die main Funktion
    from veritas_app import main
    
    print("DEBUG: Import successful, calling main()...")
    main()
    
except ImportError as e:
    print(f"❌ IMPORT ERROR: {e}")
    traceback.print_exc()
    sys.exit(1)
    
except Exception as e:
    print(f"❌ RUNTIME ERROR: {e}")
    traceback.print_exc()
    sys.exit(1)

print("DEBUG: Frontend exited normally")
