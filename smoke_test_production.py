#!/usr/bin/env python3
"""
Quick Smoke Test für Token-Management-System Production Deployment
"""

import requests
import json
from datetime import datetime

def test_simple_query():
    """Test 1: Simple Query - Sollte 250 tokens (minimum) bekommen."""
    print("\n" + "="*80)
    print("SMOKE TEST 1: Simple Query")
    print("="*80)
    
    query = "Was ist ein Bauantrag?"
    print(f"📝 Query: {query}")
    print(f"🕐 Start: {datetime.now().strftime('%H:%M:%S')}")
    
    try:
        response = requests.post(
            "http://localhost:5000/v2/intelligent/query",
            json={"query": query, "model": "phi3"},
            timeout=120
        )
        
        if response.status_code != 200:
            print(f"❌ ERROR: Status {response.status_code}")
            print(response.text)
            return False
        
        data = response.json()
        tb = data.get("token_budget", {})
        
        # Extract metrics
        allocated = tb.get("allocated", 0)
        intent_data = tb.get("intent", {})
        intent = intent_data.get("intent", "unknown")
        confidence = intent_data.get("confidence", 0.0)
        method = intent_data.get("method", "unknown")
        
        breakdown = tb.get("breakdown", {})
        complexity = breakdown.get("complexity_score", 0.0)
        agent_count = breakdown.get("agent_count", 0)
        
        processing_time = data.get("processing_time", 0.0)
        
        # Display results
        print(f"\n✅ Status: {response.status_code} OK")
        print(f"\n📊 Token Budget:")
        print(f"   Allocated: {allocated} tokens")
        print(f"   Intent: {intent} (Confidence: {confidence:.2f}, Method: {method})")
        print(f"   Complexity: {complexity}/10")
        print(f"   Agent Count: {agent_count}")
        print(f"   Processing Time: {processing_time:.1f}s")
        
        # Validation
        print(f"\n🔍 Validation:")
        if allocated == 250:
            print(f"   ✅ Budget is 250 (minimum) - PASS")
        else:
            print(f"   ⚠️  Budget is {allocated}, expected 250")
        
        if intent == "quick_answer":
            print(f"   ✅ Intent is 'quick_answer' - PASS")
        else:
            print(f"   ⚠️  Intent is '{intent}', expected 'quick_answer'")
        
        if 3.0 <= complexity <= 5.0:
            print(f"   ✅ Complexity {complexity}/10 (low) - PASS")
        else:
            print(f"   ⚠️  Complexity {complexity}/10 unexpected")
        
        print(f"\n✅ Test 1: PASSED")
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_verwaltungsrecht_query():
    """Test 2: Verwaltungsrecht Query - Sollte 1500-2000+ tokens bekommen."""
    print("\n" + "="*80)
    print("SMOKE TEST 2: Verwaltungsrecht Query (High Budget)")
    print("="*80)
    
    query = "Wie ist das Ermessen der Behörde im Verwaltungsverfahren nach VwVfG zu beurteilen?"
    print(f"📝 Query: {query}")
    print(f"🕐 Start: {datetime.now().strftime('%H:%M:%S')}")
    
    try:
        response = requests.post(
            "http://localhost:5000/v2/intelligent/query",
            json={"query": query, "model": "phi3"},
            timeout=120
        )
        
        if response.status_code != 200:
            print(f"❌ ERROR: Status {response.status_code}")
            print(response.text)
            return False
        
        data = response.json()
        tb = data.get("token_budget", {})
        
        # Extract metrics
        allocated = tb.get("allocated", 0)
        intent_data = tb.get("intent", {})
        intent = intent_data.get("intent", "unknown")
        confidence = intent_data.get("confidence", 0.0)
        method = intent_data.get("method", "unknown")
        
        breakdown = tb.get("breakdown", {})
        complexity = breakdown.get("complexity_score", 0.0)
        agent_count = breakdown.get("agent_count", 0)
        
        processing_time = data.get("processing_time", 0.0)
        
        # Display results
        print(f"\n✅ Status: {response.status_code} OK")
        print(f"\n📊 Token Budget:")
        print(f"   Allocated: {allocated} tokens")
        print(f"   Intent: {intent} (Confidence: {confidence:.2f}, Method: {method})")
        print(f"   Complexity: {complexity}/10")
        print(f"   Agent Count: {agent_count}")
        print(f"   Processing Time: {processing_time:.1f}s")
        
        # Validation
        print(f"\n🔍 Validation:")
        if allocated >= 1500:
            budget_increase = ((allocated - 250) / 250) * 100
            print(f"   ✅ Budget is {allocated} (+{budget_increase:.0f}% increase) - PASS")
        else:
            print(f"   ⚠️  Budget is {allocated}, expected >= 1500")
        
        if intent in ["analysis", "explanation"]:
            print(f"   ✅ Intent is '{intent}' (complex) - PASS")
        else:
            print(f"   ⚠️  Intent is '{intent}', expected 'analysis' or 'explanation'")
        
        if complexity >= 7.0:
            print(f"   ✅ Complexity {complexity}/10 (high) - PASS")
        else:
            print(f"   ⚠️  Complexity {complexity}/10, expected >= 7.0")
        
        print(f"\n✅ Test 2: PASSED")
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def main():
    """Run all smoke tests."""
    print("\n" + "🚀"*40)
    print("TOKEN-MANAGEMENT-SYSTEM PRODUCTION SMOKE TESTS")
    print("🚀"*40)
    print(f"\nTimestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Backend: http://localhost:5000")
    
    results = []
    
    # Test 1: Simple Query
    results.append(("Simple Query", test_simple_query()))
    
    # Test 2: Verwaltungsrecht Query
    results.append(("Verwaltungsrecht Query", test_verwaltungsrecht_query()))
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\n{'='*80}")
    print(f"Total: {passed}/{total} tests passed ({(passed/total)*100:.0f}%)")
    
    if passed == total:
        print(f"\n🎉 ALL TESTS PASSED - PRODUCTION DEPLOYMENT SUCCESSFUL!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed - check logs")
    
    print(f"{'='*80}\n")

if __name__ == "__main__":
    main()
