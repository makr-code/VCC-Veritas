#!/usr/bin/env python3
"""
Backend Startup Diagnose
=========================
Testet die Backend-Initialisierung Schritt für Schritt
"""
import sys
import os
import asyncio

# Setup Path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

async def test_backend_initialization():
    """Teste Backend-Initialisierung"""
    print("="*60)
    print("BACKEND STARTUP DIAGNOSE")
    print("="*60)
    
    # Test 1: Imports
    print("\n[TEST 1] Imports testen...")
    try:
        from backend.api.veritas_api_backend import (
            UDS3_AVAILABLE, INTELLIGENT_PIPELINE_AVAILABLE, STREAMING_AVAILABLE,
            initialize_streaming_system, initialize_intelligent_pipeline, 
            initialize_uds3_system
        )
        print(f"  ✅ Imports OK")
        print(f"  UDS3: {UDS3_AVAILABLE}")
        print(f"  Pipeline: {INTELLIGENT_PIPELINE_AVAILABLE}")
        print(f"  Streaming: {STREAMING_AVAILABLE}")
    except Exception as e:
        print(f"  ❌ Import fehlgeschlagen: {e}")
        return
    
    # Test 2: Streaming initialisieren
    print("\n[TEST 2] Streaming initialisieren...")
    try:
        streaming_ok = initialize_streaming_system()
        print(f"  {'✅' if streaming_ok else '⚠️'} Streaming: {streaming_ok}")
    except Exception as e:
        print(f"  ❌ Streaming Fehler: {e}")
        streaming_ok = False
    
    # Test 3: UDS3 initialisieren
    print("\n[TEST 3] UDS3 initialisieren...")
    try:
        uds3_ok = initialize_uds3_system()
        print(f"  {'✅' if uds3_ok else '❌'} UDS3: {uds3_ok}")
        if not uds3_ok:
            print("  ❌ KRITISCH: UDS3 muss verfügbar sein!")
            return
    except Exception as e:
        print(f"  ❌ UDS3 Fehler: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test 4: Intelligent Pipeline initialisieren
    print("\n[TEST 4] Intelligent Pipeline initialisieren...")
    try:
        pipeline_ok = await initialize_intelligent_pipeline()
        print(f"  {'✅' if pipeline_ok else '❌'} Pipeline: {pipeline_ok}")
        if not pipeline_ok:
            print("  ❌ KRITISCH: Pipeline muss verfügbar sein!")
            return
    except Exception as e:
        print(f"  ❌ Pipeline Fehler: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test 5: Ollama Client Check
    print("\n[TEST 5] Ollama Client prüfen...")
    try:
        from backend.api.veritas_api_backend import ollama_client
        if ollama_client:
            print(f"  ✅ Ollama Client: OK")
        else:
            print(f"  ❌ Ollama Client: None (KRITISCH!)")
            return
    except Exception as e:
        print(f"  ❌ Ollama Fehler: {e}")
        return
    
    print("\n" + "="*60)
    print("✅ ALLE TESTS ERFOLGREICH - Backend sollte starten!")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(test_backend_initialization())
