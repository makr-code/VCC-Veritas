"""
Live-Test des Token-Budget-Systems mit echtem Backend

Sendet Queries an das laufende Backend und zeigt
Token-Budget-Progression und Metadaten.
"""

import requests
import json
import time
from typing import Dict, Any


def test_query(query: str, model: str = "phi3", agent_mode: str = "intelligent") -> Dict[str, Any]:
    """
    Sendet Query an Backend und gibt Response zurück
    
    Args:
        query: Die Testfrage
        model: Ollama-Modell
        agent_mode: Agent-Modus (intelligent, simple, etc.)
        
    Returns:
        Response-Dict
    """
    url = "http://localhost:5000/v2/intelligent/query"
    
    payload = {
        "query": query,
        "model": model,
        "agent_mode": agent_mode
    }
    
    print(f"\n{'='*80}")
    print(f"TEST: {query[:70]}...")
    print(f"Model: {model} | Agent Mode: {agent_mode}")
    print(f"{'='*80}\n")
    
    try:
        start_time = time.time()
        response = requests.post(url, json=payload, timeout=120)
        elapsed_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            
            # Token-Budget-Metadaten extrahieren
            metadata = data.get("metadata", {})
            processing_metadata = data.get("processing_metadata", {})
            
            print("✅ RESPONSE ERFOLGREICH")
            print(f"   Response Time: {elapsed_time:.2f}s")
            print()
            
            # Token-Budget-Informationen
            if "token_budget" in processing_metadata:
                token_budget = processing_metadata["token_budget"]
                print("📊 TOKEN BUDGET PROGRESSION:")
                print(f"   Initial Budget:      {token_budget.get('initial', 'N/A')} tokens")
                print(f"   After RAG:           {token_budget.get('after_rag', 'N/A')} tokens")
                print(f"   Final (After Agents): {token_budget.get('final', 'N/A')} tokens")
                
                if "breakdown" in token_budget:
                    breakdown = token_budget["breakdown"]
                    print()
                    print("📈 BUDGET BREAKDOWN:")
                    print(f"   Complexity Score:    {breakdown.get('complexity_score', 'N/A')}")
                    print(f"   Chunk Count:         {breakdown.get('chunk_count', 'N/A')}")
                    print(f"   Source Diversity:    {breakdown.get('source_diversity', 'N/A')}")
                    print(f"   Agent Count:         {breakdown.get('agent_count', 'N/A')}")
                    print(f"   Intent Weight:       {breakdown.get('intent_weight', 'N/A')}")
                print()
            
            # Intent-Classification
            if "intent" in processing_metadata:
                intent_data = processing_metadata["intent"]
                print("🎯 INTENT CLASSIFICATION:")
                print(f"   Intent:     {intent_data.get('intent', 'N/A')}")
                print(f"   Confidence: {intent_data.get('confidence', 'N/A')}")
                print(f"   Method:     {intent_data.get('method', 'N/A')}")
                print()
            
            # Agent-Informationen
            if "agents_used" in metadata:
                agents = metadata["agents_used"]
                print(f"🤖 AGENTS: {len(agents)} verwendet")
                for agent in agents:
                    print(f"   - {agent}")
                print()
            
            # Antwort (gekürzt)
            answer = data.get("answer", "")
            print("💬 ANTWORT (gekürzt):")
            print(f"   {answer[:200]}...")
            print()
            
            return data
            
        else:
            print(f"❌ ERROR: {response.status_code}")
            print(f"   {response.text}")
            return {}
            
    except requests.exceptions.ConnectionError:
        print("❌ CONNECTION ERROR: Backend nicht erreichbar")
        print("   Starte Backend mit: python start_backend.py")
        return {}
    except requests.exceptions.Timeout:
        print("❌ TIMEOUT: Query dauerte zu lange (>120s)")
        return {}
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return {}


def main():
    """Führt Live-Tests aus"""
    print("\n" + "="*80)
    print("VERITAS TOKEN-BUDGET LIVE-TEST")
    print("="*80)
    print()
    print("Testet das Token-Budget-System mit echtem Backend")
    print("Backend muss auf http://localhost:5000 laufen")
    print()
    
    # Test-Szenarien
    tests = [
        {
            "name": "Simple Question",
            "query": "Was ist ein Bauantrag?",
            "model": "phi3",
            "expected_budget": "250-500 tokens"
        },
        {
            "name": "Verwaltungsrecht Query",
            "query": "Wie ist das Ermessen der Behörde im Verwaltungsverfahren nach VwVfG zu beurteilen?",
            "model": "llama3.1:8b",
            "expected_budget": "2000-4000 tokens"
        },
        {
            "name": "Complex Analysis",
            "query": "Analysiere die rechtlichen und finanziellen Auswirkungen der neuen Bauverordnung.",
            "model": "llama3.1:8b",
            "expected_budget": "1500-3000 tokens"
        }
    ]
    
    results = []
    
    for i, test in enumerate(tests, 1):
        print(f"\n{'#'*80}")
        print(f"# TEST {i}/{len(tests)}: {test['name']}")
        print(f"# Expected Budget: {test['expected_budget']}")
        print(f"{'#'*80}")
        
        result = test_query(
            query=test["query"],
            model=test["model"]
        )
        
        results.append({
            "test": test["name"],
            "result": result,
            "expected": test["expected_budget"]
        })
        
        # Warte zwischen Tests
        if i < len(tests):
            print("\n⏳ Warte 3 Sekunden...")
            time.sleep(3)
    
    # Zusammenfassung
    print("\n" + "="*80)
    print("ZUSAMMENFASSUNG")
    print("="*80)
    
    successful = sum(1 for r in results if r["result"])
    total = len(results)
    
    print(f"\n✅ Erfolgreiche Tests: {successful}/{total}")
    
    for r in results:
        status = "✅" if r["result"] else "❌"
        final_budget = "N/A"
        if r["result"] and "processing_metadata" in r["result"]:
            token_budget = r["result"]["processing_metadata"].get("token_budget", {})
            final_budget = token_budget.get("final", "N/A")
        
        print(f"{status} {r['test']}: Final Budget = {final_budget} (Expected: {r['expected']})")


if __name__ == "__main__":
    main()
