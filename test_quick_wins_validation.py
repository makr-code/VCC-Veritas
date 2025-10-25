"""
Validierungs-Test für Quick Win Optimierungen
==============================================
Testet ob die Optimierungen funktionieren:
1. Fachbegriff-Erkennung für höhere Complexity
2. Pattern-Regeln für bessere Intent-Classification
"""

import requests
import json

BACKEND_URL = "http://localhost:5000"
ENDPOINT = "/v2/intelligent/query"

# Queries die in Test-Session zu niedriges Budget bekamen
PROBLEMATIC_QUERIES = [
    {
        "query": "Was bedeutet Verhältnismäßigkeitsprinzip in der Verwaltung?",
        "expected_budget_before": 627,
        "expected_budget_after": ">800 (Fachbegriff +2.0)",
        "expected_complexity_before": 5.5,
        "expected_complexity_after": ">7.0"
    },
    {
        "query": "Wie wird die Abwägung bei Bebauungsplänen durchgeführt?",
        "expected_budget_before": 820,
        "expected_budget_after": ">1000 (Fachbegriff +2.0)",
        "expected_complexity_before": 7.2,
        "expected_complexity_after": ">8.0"
    },
    {
        "query": "Erkläre die Lärmgrenzwerte für Wohngebiete und Gewerbegebiete",
        "expected_budget_before": 399,
        "expected_budget_after": ">600 (Grenzwerte +1.0)",
        "expected_complexity_before": 3.5,
        "expected_complexity_after": ">5.0"
    },
    {
        "query": "Was ist der Unterschied zwischen Ermessen und Beurteilungsspielraum?",
        "expected_budget_before": 313,
        "expected_budget_after": ">800 (Ermessen +2.0, explanation statt quick_answer)",
        "expected_complexity_before": 5.5,
        "expected_complexity_after": ">7.0"
    },
]

# Queries für Intent-Pattern-Validierung
INTENT_PATTERN_QUERIES = [
    {
        "query": "Was bedeutet Ermessen?",
        "expected_intent": "explanation",
        "expected_confidence": ">0.9 (Pattern-Regel)",
        "note": "Sollte explanation sein (Pattern: 'was bedeutet'), nicht quick_answer"
    },
    {
        "query": "Liste alle Behörden in Stuttgart auf",
        "expected_intent": "quick_answer",
        "expected_confidence": ">0.9 (Pattern-Regel)",
        "note": "Pattern 'Liste X auf' sollte quick_answer triggern"
    },
    {
        "query": "Welche Unterlagen brauche ich für einen Bauantrag?",
        "expected_intent": "explanation",
        "expected_confidence": ">0.9 (Pattern-Regel)",
        "note": "Pattern 'welche unterlagen' sollte explanation triggern"
    },
]

def test_query(query_data, test_type="budget"):
    """Testet eine Query und zeigt Ergebnisse"""
    query = query_data["query"]
    
    print(f"\n{'='*80}")
    print(f"Query: \"{query}\"")
    print(f"{'='*80}")
    
    try:
        response = requests.post(f"{BACKEND_URL}{ENDPOINT}", json={"query": query}, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            pm = data.get("processing_metadata", {})
            tb = pm.get("token_budget", {})
            
            if tb:
                allocated = tb.get("allocated", 0)
                intent = tb.get("intent", {}).get("intent", "unknown")
                confidence = tb.get("intent", {}).get("confidence", 0.0)
                method = tb.get("intent", {}).get("method", "unknown")
                complexity = tb.get("breakdown", {}).get("complexity_score", 0)
                
                if test_type == "budget":
                    print(f"\n📊 BUDGET COMPARISON:")
                    print(f"   Before: {query_data['expected_budget_before']} tokens")
                    print(f"   After:  {allocated} tokens")
                    print(f"   Expected: {query_data['expected_budget_after']}")
                    
                    diff = allocated - query_data['expected_budget_before']
                    diff_pct = (diff / query_data['expected_budget_before']) * 100
                    
                    if diff > 0:
                        print(f"   ✅ IMPROVEMENT: +{diff} tokens (+{diff_pct:.1f}%)")
                    else:
                        print(f"   ⚠️  NO IMPROVEMENT: {diff} tokens ({diff_pct:.1f}%)")
                    
                    print(f"\n🔢 COMPLEXITY COMPARISON:")
                    print(f"   Before: {query_data['expected_complexity_before']}/10")
                    print(f"   After:  {complexity:.1f}/10")
                    print(f"   Expected: {query_data['expected_complexity_after']}")
                    
                    comp_diff = complexity - query_data['expected_complexity_before']
                    if comp_diff > 0:
                        print(f"   ✅ IMPROVEMENT: +{comp_diff:.1f} complexity points")
                    else:
                        print(f"   ⚠️  NO IMPROVEMENT: {comp_diff:.1f}")
                
                elif test_type == "intent":
                    print(f"\n🎯 INTENT CLASSIFICATION:")
                    print(f"   Intent: {intent}")
                    print(f"   Expected: {query_data['expected_intent']}")
                    print(f"   Confidence: {confidence:.2f}")
                    print(f"   Expected: {query_data['expected_confidence']}")
                    print(f"   Method: {method}")
                    print(f"   Note: {query_data['note']}")
                    
                    if intent == query_data['expected_intent']:
                        print(f"   ✅ INTENT CORRECT")
                    else:
                        print(f"   ❌ INTENT MISMATCH")
                    
                    if confidence > 0.8:
                        print(f"   ✅ CONFIDENCE HIGH")
                    else:
                        print(f"   ⚠️  CONFIDENCE LOW")
                
                print(f"\n📋 FULL DETAILS:")
                print(f"   Budget: {allocated} tokens")
                print(f"   Intent: {intent} (conf: {confidence:.2f}, method: {method})")
                print(f"   Complexity: {complexity:.1f}/10")
                print(f"   Agents: {tb.get('breakdown', {}).get('agent_count', 0)}")
                
            else:
                print(f"❌ ERROR: Token budget nicht in Response gefunden")
        else:
            print(f"❌ ERROR: HTTP {response.status_code}")
    
    except Exception as e:
        print(f"❌ EXCEPTION: {str(e)}")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("🧪 QUICK WIN OPTIMIERUNGEN - VALIDIERUNGS-TEST")
    print("="*80)
    print("\nOptimierungen:")
    print("  1. ✅ Fachbegriff-Complexity: Verhältnismäßigkeit, Abwägung, Ermessen → +2.0")
    print("  2. ✅ Fachbegriff-Complexity: Grenzwerte, Verordnung → +1.0")
    print("  3. ✅ Intent-Pattern: 'Was bedeutet X?' → explanation (nicht quick_answer)")
    print("  4. ✅ Intent-Pattern: 'Unterschied zwischen X und Y' → explanation")
    print("  5. ✅ Intent-Pattern: 'Liste X auf' → quick_answer")
    print("  6. ✅ Intent-Pattern: 'Welche Unterlagen' → explanation")
    
    print("\n\n" + "="*80)
    print("TEIL 1: BUDGET & COMPLEXITY TESTS (Fachbegriff-Erkennung)")
    print("="*80)
    
    for query_data in PROBLEMATIC_QUERIES:
        test_query(query_data, test_type="budget")
        input("\nWeiter mit Enter...")
    
    print("\n\n" + "="*80)
    print("TEIL 2: INTENT PATTERN TESTS (Pattern-Regeln)")
    print("="*80)
    
    for query_data in INTENT_PATTERN_QUERIES:
        test_query(query_data, test_type="intent")
        input("\nWeiter mit Enter...")
    
    print("\n\n" + "="*80)
    print("✅ VALIDIERUNGS-TEST ABGESCHLOSSEN")
    print("="*80)
    print("\nErgebnis: Prüfe ob Improvements sichtbar sind")
    print("  - Budget sollte höher sein für Fachbegriffe")
    print("  - Complexity sollte höher sein")
    print("  - Intent-Classification sollte akkurater sein")
    print("\nWenn erfolgreich: Quick Wins implementiert! ✅")
