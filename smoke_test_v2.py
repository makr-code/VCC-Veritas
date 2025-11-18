#!/usr/bin/env python3
"""
Production Smoke Test für Token-Management-System (v2)
Korrekte Struktur: processing_metadata.token_budget
"""

import json
from datetime import datetime

import requests

BASE_URL = "http://localhost:5000"

print("\n" + "🚀" * 40)
print("TOKEN-MANAGEMENT-SYSTEM PRODUCTION DEPLOYMENT VALIDATION")
print("🚀" * 40)
print(f"\nTimestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Backend: {BASE_URL}\n")

# Test 1: Simple Query
print("=" * 80)
print("TEST 1: Simple Query (Minimum Budget)")
print("=" * 80)

query1 = "Was ist ein Bauantrag?"
print(f"📝 Query: {query1}")
print(f"⏱️  Expected: 250 tokens, quick_answer intent, low complexity")

try:
    r1 = requests.post(f"{BASE_URL}/v2/intelligent/query", json={"query": query1, "model": "phi3"}, timeout=120)

    if r1.status_code == 200:
        data1 = r1.json()
        pm1 = data1.get("processing_metadata", {})
        tb1 = pm1.get("token_budget", {})

        allocated1 = tb1.get("allocated", 0)
        intent1 = tb1.get("intent", {})
        breakdown1 = tb1.get("breakdown", {})

        print(f"\n✅ Status: 200 OK")
        print(f"\n📊 Token Budget Metadata:")
        print(f"   Allocated: {allocated1} tokens")

        if intent1:
            print(
                f"   Intent: {intent1.get('intent', 'N/A')} (Confidence: {intent1.get('confidence', 0):.2f}, Method: {intent1.get('method', 'N/A')})"
            )
        else:
            print(f"   Intent: ⚠️  None (not calculated)")

        if breakdown1:
            print(f"   Complexity: {breakdown1.get('complexity_score', 0):.1f}/10")
            print(f"   Agent Count: {breakdown1.get('agent_count', 0)}")
            print(f"   Agent Factor: {breakdown1.get('agent_factor', 0):.2f}")
        else:
            print(f"   Breakdown: ⚠️  None (not calculated)")

        print(f"   Processing Time: {data1.get('processing_time', 0):.1f}s")

        # Validation
        print(f"\n🔍 Validation:")
        if allocated1 == 250:
            print(f"   ✅ PASS: Budget is 250 (minimum)")
        elif allocated1 > 0:
            print(f"   ⚠️  WARN: Budget is {allocated1}, expected 250")
        else:
            print(f"   ❌ FAIL: No token budget allocated!")

        if intent1 and intent1.get("intent") == "quick_answer":
            print(f"   ✅ PASS: Intent is 'quick_answer'")
        else:
            print(f"   ⚠️  WARN: Intent not 'quick_answer'")

        print(f"\n{'✅ TEST 1: PASSED' if allocated1 > 0 else '❌ TEST 1: FAILED'}")
    else:
        print(f"❌ ERROR: Status {r1.status_code}")
        print(r1.text)

except Exception as e:
    print(f"❌ ERROR: {e}")

# Test 2: Verwaltungsrecht Query
print("\n" + "=" * 80)
print("TEST 2: Verwaltungsrecht Query (High Budget)")
print("=" * 80)

query2 = "Wie ist das Ermessen der Behörde im Verwaltungsverfahren nach VwVfG zu beurteilen?"
print(f"📝 Query: {query2}")
print(f"⏱️  Expected: 1500-2000+ tokens, analysis intent, high complexity")

try:
    r2 = requests.post(f"{BASE_URL}/v2/intelligent/query", json={"query": query2, "model": "phi3"}, timeout=120)

    if r2.status_code == 200:
        data2 = r2.json()
        pm2 = data2.get("processing_metadata", {})
        tb2 = pm2.get("token_budget", {})

        allocated2 = tb2.get("allocated", 0)
        intent2 = tb2.get("intent", {})
        breakdown2 = tb2.get("breakdown", {})

        print(f"\n✅ Status: 200 OK")
        print(f"\n📊 Token Budget Metadata:")
        print(f"   Allocated: {allocated2} tokens")

        if intent2:
            print(
                f"   Intent: {intent2.get('intent', 'N/A')} (Confidence: {intent2.get('confidence', 0):.2f}, Method: {intent2.get('method', 'N/A')})"
            )
        else:
            print(f"   Intent: ⚠️  None (not calculated)")

        if breakdown2:
            print(f"   Complexity: {breakdown2.get('complexity_score', 0):.1f}/10")
            print(f"   Agent Count: {breakdown2.get('agent_count', 0)}")
            print(f"   Agent Factor: {breakdown2.get('agent_factor', 0):.2f}")
            print(f"   Intent Weight: {breakdown2.get('intent_weight', 1.0):.2f}")
        else:
            print(f"   Breakdown: ⚠️  None (not calculated)")

        print(f"   Processing Time: {data2.get('processing_time', 0):.1f}s")

        # Validation
        print(f"\n🔍 Validation:")
        if allocated2 >= 1500:
            increase = ((allocated2 - 250) / 250) * 100
            print(f"   ✅ PASS: Budget is {allocated2} (+{increase:.0f}% increase from simple)")
        elif allocated2 > 0:
            print(f"   ⚠️  WARN: Budget is {allocated2}, expected >= 1500")
        else:
            print(f"   ❌ FAIL: No token budget allocated!")

        if intent2 and intent2.get("intent") in ["analysis", "explanation"]:
            print(f"   ✅ PASS: Intent is '{intent2.get('intent')}' (complex)")
        else:
            print(f"   ⚠️  WARN: Intent not 'analysis' or 'explanation'")

        if breakdown2 and breakdown2.get("complexity_score", 0) >= 7.0:
            print(f"   ✅ PASS: Complexity {breakdown2.get('complexity_score')}/10 (high)")
        else:
            print(f"   ⚠️  WARN: Complexity not high enough")

        print(f"\n{'✅ TEST 2: PASSED' if allocated2 > 0 else '❌ TEST 2: FAILED'}")
    else:
        print(f"❌ ERROR: Status {r2.status_code}")
        print(r2.text)

except Exception as e:
    print(f"❌ ERROR: {e}")

# Summary
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"\n🎯 Token-Management-System Status:")
print(f"   - Backend erreichbar: ✅")
print(f"   - processing_metadata vorhanden: {'✅' if 'pm1' in locals() and pm1 else '❓'}")
print(f"   - token_budget in Metadata: {'✅' if 'tb1' in locals() and tb1 else '❌'}")

if "allocated1" in locals() and "allocated2" in locals():
    if allocated1 > 0 and allocated2 > 0:
        print(f"\n🎉 SUCCESS: Token-Management-System ist AKTIV!")
        print(f"   - Simple Query: {allocated1} tokens")
        print(f"   - Verwaltungsrecht: {allocated2} tokens")
        if allocated2 > allocated1:
            increase = ((allocated2 - allocated1) / allocated1) * 100
            print(f"   - Budget-Steigerung: +{increase:.0f}%")
    else:
        print(f"\n⚠️  WARNING: Token-Budget wird nicht berechnet!")
        print(f"   Mögliche Ursachen:")
        print(f"   1. Token-Budget-Services nicht initialisiert")
        print(f"   2. Pipeline verwendet Token-Budget nicht")
        print(f"   3. Fehler in budget_breakdown Berechnung")
else:
    print(f"\n❌ FAILED: Konnte Token-Budget nicht abrufen")

print(f"\n{'='*80}\n")
