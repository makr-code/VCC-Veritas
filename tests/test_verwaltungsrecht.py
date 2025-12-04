"""Quick test for Verwaltungsrecht query with max token budget"""
import json

import requests

query = "Wie ist das Ermessen der Behörde im Verwaltungsverfahren nach VwVfG zu beurteilen? Analysiere die Rechtsprechung und erläutere die Ermessensfehler."

print("Sending complex Verwaltungsrecht query...")
print(f"Query: {query[:80]}...")
print()

r = requests.post("http://localhost:5000/v2/intelligent/query", json={"query": query, "model": "llama3.1:8b"}, timeout=120)

print(f"Status: {r.status_code}")
print()

if r.status_code == 200:
    data = r.json()

    print("=" * 80)
    print("TOKEN BUDGET ANALYSIS")
    print("=" * 80)

    tb = data.get("processing_metadata", {}).get("token_budget", {})

    print(f"\n✅ Allocated Budget: {tb.get('allocated')} tokens")

    intent_data = tb.get("intent", {})
    print(f"\n🎯 Intent Classification:")
    print(f"   Intent:     {intent_data.get('intent')}")
    print(f"   Confidence: {intent_data.get('confidence'):.2%}")
    print(f"   Method:     {intent_data.get('method')}")

    bd = tb.get("breakdown", {})
    print(f"\n📊 Budget Breakdown:")
    print(f"   Base Tokens:         {bd.get('base_tokens')}")
    print(f"   Complexity Score:    {bd.get('complexity_score')}/10")
    print(f"   Complexity Factor:   {bd.get('complexity_factor'):.2f}x")
    print(f"   Chunk Count:         {bd.get('chunk_count')}")
    print(f"   Source Diversity:    {bd.get('source_diversity'):.2f}x")
    print(f"   Agent Count:         {bd.get('agent_count')}")
    print(f"   Agent Factor:        {bd.get('agent_factor'):.2f}x")
    print(f"   Intent Weight:       {bd.get('intent_weight'):.2f}x")
    print(f"   Final Budget:        {bd.get('final_budget')}")

    print(f"\n⏱️  Processing Time: {data.get('processing_time'):.2f}s")
    print(f"🤖 Agents Used: {data.get('agents_used')}")

    print(f"\n💬 Answer Preview:")
    answer = data.get("answer", "")
    print(f"   {answer[:300]}...")

else:
    print(f"❌ Error: {r.text}")
