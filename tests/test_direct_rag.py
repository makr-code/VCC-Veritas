#!/usr/bin/env python3
"""
DIRECT RAG TEST - Bypass Pipeline
==================================
Testet RAG direkt ohne Intelligent Pipeline

Ziel: Prüfen ob Problem am Prompt oder an der Pipeline liegt
"""

import json

import requests

BACKEND_URL = "http://localhost:5000"

# Einfache Frage
question = "Was regelt § 58 LBO BW?"

print("=" * 80)
print("🧪 DIRECT RAG TEST (Ohne Pipeline)")
print("=" * 80)
print(f"\nFrage: {question}")
print(f"Endpoint: {BACKEND_URL}/ask")
print(f"Mode: intelligent")

# Sende Request
payload = {"question": question, "mode": "intelligent", "model": "codellama:latest", "temperature": 0.7, "max_tokens": 800}

print("\n📤 Sende Request...")
response = requests.post(f"{BACKEND_URL}/ask", json=payload, timeout=60)

if response.status_code == 200:
    data = response.json()

    print("\n✅ Response erhalten:")
    print(f"\n📝 Antwort ({len(data.get('answer', ''))} Zeichen):")
    print("-" * 80)
    print(data.get("answer", "Keine Antwort"))
    print("-" * 80)

    print(f"\n📚 Quellen: {len(data.get('sources', []))}")
    for i, source in enumerate(data.get("sources", [])[:3], 1):
        print(f"  [{i}] {source.get('title', 'Unknown')}")

    print(f"\n🔧 Metadata:")
    metadata = data.get("metadata", {})
    print(f"  Mode: {metadata.get('mode')}")
    print(f"  Model: {metadata.get('model')}")
    print(f"  Agent Count: {metadata.get('agent_count', 'N/A')}")
    print(f"  Pipeline Mode: {metadata.get('pipeline_mode', 'N/A')}")

    # Prüfe Zitationen
    answer = data.get("answer", "")
    import re

    citations = re.findall(r"\[(\d+)\]", answer)

    print(f"\n📊 ZITAT-ANALYSE:")
    print(f"  Gefundene [N] Zitationen: {len(set(citations))}")
    if citations:
        print(f"  Zitate: {sorted(set(citations))}")
    else:
        print(f"  ❌ KEINE [1],[2],[3] Zitationen gefunden!")

    # Prüfe Follow-ups
    if "💡" in answer or "Vorschläge" in answer:
        print(f"  ✅ Follow-up Vorschläge vorhanden")
    else:
        print(f"  ❌ Keine Follow-up Vorschläge")

else:
    print(f"\n❌ Error: HTTP {response.status_code}")
    print(response.text)

print("\n" + "=" * 80)
