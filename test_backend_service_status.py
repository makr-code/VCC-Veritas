#!/usr/bin/env python3
"""
Backend Service Status Test
Prüft Verfügbarkeit von Services für Hypothesis-Integration
"""
import requests
import json

BASE_URL = "http://localhost:5000"

print("=" * 60)
print("BACKEND SERVICE STATUS")
print("=" * 60)

# Test 1: Health Check
print("\n1️⃣  Health Check...")
try:
    response = requests.get(f"{BASE_URL}/health")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Backend Health: {data['status']}")
        print(f"   • Streaming: {data.get('streaming_available', '?')}")
        print(f"   • Intelligent Pipeline: {data.get('intelligent_pipeline_available', '?')}")
        print(f"   • UDS3: {data.get('uds3_available', '?')}")
        print(f"   • Ollama: {data.get('ollama_available', '?')}")
    else:
        print(f"   ❌ Health Check fehlgeschlagen: {response.status_code}")
except Exception as e:
    print(f"   ❌ Fehler: {e}")

# Test 2: Capabilities (Registry)
print("\n2️⃣  Capabilities Check...")
try:
    response = requests.get(f"{BASE_URL}/capabilities")
    if response.status_code == 200:
        data = response.json()
        agents = data.get('agents', [])
        print(f"   ✅ {len(agents)} Agents registriert")
    else:
        print(f"   ❌ Capabilities fehlgeschlagen: {response.status_code}")
except Exception as e:
    print(f"   ❌ Fehler: {e}")

# Test 3: Pipeline Stats
print("\n3️⃣  Pipeline Stats...")
try:
    response = requests.get(f"{BASE_URL}/stats")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Pipeline Status: {data['status']}")
        ollama_stats = data.get('ollama_stats', {})
        if ollama_stats:
            print(f"   • Ollama Client Stats: {ollama_stats.get('total_requests', 0)} requests")
            print(f"   • Ollama Base URL: {ollama_stats.get('base_url', 'N/A')}")
        else:
            print(f"   ⚠️  Keine Ollama Stats (ollama_client = None?)")
    else:
        print(f"   ⚠️  Stats nicht verfügbar: {response.status_code}")
except Exception as e:
    print(f"   ❌ Fehler: {e}")

print("\n" + "=" * 60)
print("ZUSAMMENFASSUNG")
print("=" * 60)
print("""
ERWARTUNG für Hypothesis-Integration:
- ✅ streaming_available = True
- ✅ intelligent_pipeline_available = True
- ✅ ollama_available = True
- ✅ ollama_client != None (in Pipeline-Code)

Falls ollama_client = None:
→ Hypothesis-Stage wird übersprungen!
→ Prüfe: get_ollama_client() in veritas_api_backend.py
""")
