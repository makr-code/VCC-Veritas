#!/usr/bin/env python3
"""
Test Agent Registry - Standalone Agent Selection
===================================================
Testet die Agent Registry Selection-Logik direkt ohne Pipeline-Dependencies.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.agents.agent_registry import (
    AgentRegistry,
    AgentDomain,
    get_agent_registry,
    reset_agent_registry
)

def test_capability_based_selection():
    """Test Capability-based Worker Selection"""
    print("\n" + "="*80)
    print("TEST 1: Capability-Based Selection")
    print("="*80)
    
    registry = get_agent_registry()
    
    test_cases = [
        {
            "query": "Wie ist die Luftqualitaet in Muenchen?",
            "keywords": ["luft", "umwelt", "air"],
            "expected_agents": ["EnvironmentalAgent", "AtmosphericFlowAgent"],
            "description": "Umwelt-Query"
        },
        {
            "query": "Welche chemischen Stoffe sind gefaehrlich?",
            "keywords": ["chemical", "gefahrstoff", "toxicity"],
            "expected_agents": ["ChemicalDataAgent"],
            "description": "Chemie-Query"
        },
        {
            "query": "Was sind DIN-Normen fuer Bauprojekte?",
            "keywords": ["din", "normen", "standards"],
            "expected_agents": ["TechnicalStandardsAgent"],
            "description": "Standards-Query"
        },
        {
            "query": "Was ist die Hauptstadt von Deutschland?",
            "keywords": ["wikipedia", "wissen", "knowledge"],
            "expected_agents": ["WikipediaAgent"],
            "description": "Allgemeinwissen-Query"
        },
        {
            "query": "Wie verbreiten sich Schadstoffe in der Atmosphaere?",
            "keywords": ["atmospheric", "dispersion", "flow"],
            "expected_agents": ["AtmosphericFlowAgent"],
            "description": "Atmosphaeren-Query"
        }
    ]
    
    results = []
    
    for i, test in enumerate(test_cases, 1):
        print(f"\nTest Case {i}: {test['description']}")
        print(f"Query: {test['query']}")
        print(f"Expected: {', '.join(test['expected_agents'])}")
        
        # Methode 1: Text Search
        text_search_results = registry.search_agents(test['query'])
        
        # Methode 2: Capability Search
        capability_results = set()
        for keyword in test['keywords']:
            capability_results.update(registry.get_agents_by_capability(keyword))
        
        # Combined Results
        all_matches = set(text_search_results) | capability_results
        
        print(f"  Text Search: {text_search_results}")
        print(f"  Capability Search: {list(capability_results)}")
        print(f"  Combined: {list(all_matches)}")
        
        # Check matches
        expected_set = set(test['expected_agents'])
        matches = expected_set & all_matches
        match_rate = len(matches) / len(expected_set) if expected_set else 0
        
        passed = match_rate >= 0.5  # Mindestens 50% Match
        
        results.append({
            "test": test['description'],
            "expected": test['expected_agents'],
            "found": list(all_matches),
            "matches": list(matches),
            "match_rate": match_rate,
            "passed": passed
        })
        
        status = "PASS" if passed else "FAIL"
        print(f"  Status: [{status}] {len(matches)}/{len(expected_set)} matches ({match_rate*100:.0f}%)")
    
    # Summary
    print("\n" + "-"*80)
    print("SUMMARY")
    print("-"*80)
    
    passed_count = sum(1 for r in results if r['passed'])
    total_count = len(results)
    
    for r in results:
        status = "PASS" if r['passed'] else "FAIL"
        print(f"  [{status}] {r['test']}: {len(r['matches'])}/{len(r['expected'])} matches")
    
    print(f"\nTotal: {passed_count}/{total_count} tests passed ({passed_count/total_count*100:.0f}%)")
    print(f"RESULT: {'PASS' if passed_count == total_count else 'PARTIAL'}")
    
    return passed_count == total_count

def test_domain_based_selection():
    """Test Domain-based Worker Selection"""
    print("\n" + "="*80)
    print("TEST 2: Domain-Based Selection")
    print("="*80)
    
    registry = get_agent_registry()
    
    test_cases = [
        {
            "domain": AgentDomain.ENVIRONMENTAL,
            "expected_count": 2,  # EnvironmentalAgent, ChemicalDataAgent
            "expected_agents": ["EnvironmentalAgent", "ChemicalDataAgent"]
        },
        {
            "domain": AgentDomain.TECHNICAL,
            "expected_count": 1,  # TechnicalStandardsAgent
            "expected_agents": ["TechnicalStandardsAgent"]
        },
        {
            "domain": AgentDomain.KNOWLEDGE,
            "expected_count": 1,  # WikipediaAgent
            "expected_agents": ["WikipediaAgent"]
        },
        {
            "domain": AgentDomain.ATMOSPHERIC,
            "expected_count": 1,  # AtmosphericFlowAgent
            "expected_agents": ["AtmosphericFlowAgent"]
        },
        {
            "domain": AgentDomain.DATABASE,
            "expected_count": 1,  # DatabaseAgent
            "expected_agents": ["DatabaseAgent"]
        }
    ]
    
    results = []
    
    for test in test_cases:
        domain = test['domain']
        agents = registry.get_agents_by_domain(domain)
        
        print(f"\nDomain: {domain.value}")
        print(f"  Expected count: {test['expected_count']}")
        print(f"  Found count: {len(agents)}")
        print(f"  Agents: {agents}")
        
        count_match = len(agents) == test['expected_count']
        agent_match = set(agents) == set(test['expected_agents'])
        
        passed = count_match and agent_match
        
        results.append({
            "domain": domain.value,
            "passed": passed,
            "expected": test['expected_agents'],
            "found": agents
        })
        
        status = "PASS" if passed else "FAIL"
        print(f"  Status: [{status}]")
    
    # Summary
    print("\n" + "-"*80)
    print("SUMMARY")
    print("-"*80)
    
    passed_count = sum(1 for r in results if r['passed'])
    total_count = len(results)
    
    for r in results:
        status = "PASS" if r['passed'] else "FAIL"
        print(f"  [{status}] {r['domain']}: {len(r['found'])} agents")
    
    print(f"\nTotal: {passed_count}/{total_count} domains tested ({passed_count/total_count*100:.0f}%)")
    print(f"RESULT: {'PASS' if passed_count == total_count else 'FAIL'}")
    
    return passed_count == total_count

def test_priority_scoring():
    """Test Priority Scoring Simulation"""
    print("\n" + "="*80)
    print("TEST 3: Priority Scoring Simulation")
    print("="*80)
    
    registry = get_agent_registry()
    
    # Simuliere Pipeline Agent Selection Logik
    test_query = "Wie ist die Luftqualitaet in Muenchen und welche Schadstoffe sind gefaehrlich?"
    
    print(f"\nQuery: {test_query}")
    print("\nPriority Scoring:")
    
    priority_map = {}
    selection_reasoning = []
    
    # Phase 1: Text Search
    text_agents = registry.search_agents(test_query)
    print(f"\n  Phase 1 - Text Search: {text_agents}")
    for agent_id in text_agents:
        priority_map[worker_id] = priority_map.get(agent_id, 0.0) + 0.8
        selection_reasoning.append((agent_id, 0.8, "Text match"))
    
    # Phase 2: Capability Matching
    keywords = ["luft", "luftqualitaet", "schadstoffe", "chemical", "umwelt"]
    print(f"\n  Phase 2 - Capability Matching: {keywords}")
    for keyword in keywords:
        capability_matches = registry.get_agents_by_capability(keyword)
        for agent_id in capability_matches:
            boost = 0.6
            priority_map[agent_id] = min(priority_map.get(agent_id, 0.0) + boost, 1.0)
            selection_reasoning.append((agent_id, boost, f"Capability '{keyword}'"))
            print(f"    {keyword} -> {agent_id} (+{boost})")
    
    # Phase 3: Domain Boost
    env_agents = registry.get_agents_by_domain(AgentDomain.ENVIRONMENTAL)
    print(f"\n  Phase 3 - Domain Boost (ENVIRONMENTAL): {env_agents}")
    for agent_id in env_agents:
        boost = 0.2
        priority_map[agent_id] = min(priority_map.get(agent_id, 0.0) + boost, 1.0)
        selection_reasoning.append((agent_id, boost, "Domain boost"))
    
    # Ergebnis
    sorted_agents = sorted(
        priority_map.items(),
        key=lambda x: x[1],
        reverse=True
    )
    
    print(f"\n  Final Priority Map:")
    for agent_id, score in sorted_agents:
        print(f"    {agent_id}: {score:.2f}")
    
    # Execution Plan
    parallel_agents = [w for w, _ in sorted_agents[:3]]
    sequential_agents = [w for w, _ in sorted_agents[3:]]
    
    print(f"\n  Execution Plan:")
    print(f"    Parallel (Top 3): {parallel_agents}")
    print(f"    Sequential: {sequential_agents}")
    
    # Validation
    expected_top = ["EnvironmentalAgent", "ChemicalDataAgent"]
    top_2 = parallel_agents[:2]
    
    matches = sum(1 for w in expected_top if w in top_2)
    passed = matches >= 1  # Mindestens 1 von 2 erwartet
    
    print(f"\n  Validation:")
    print(f"    Expected Top 2: {expected_top}")
    print(f"    Actual Top 2: {top_2}")
    print(f"    Matches: {matches}/2")
    
    status = "PASS" if passed else "FAIL"
    print(f"\nRESULT: [{status}]")
    
    return passed

def run_all_tests():
    """Alle Tests ausfuehren"""
    print("\n" + "="*80)
    print("WORKER REGISTRY - AGENT SELECTION TESTS")
    print("="*80)
    
    # Registry initialisieren
    reset_agent_registry()
    registry = get_agent_registry()
    
    print(f"\nAgent Registry Status:")
    print(f"  Total agents: {len(registry.list_available_agents())}")
    
    tests = [
        ("Capability-Based Selection", test_capability_based_selection),
        ("Domain-Based Selection", test_domain_based_selection),
        ("Priority Scoring Simulation", test_priority_scoring)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"\nERROR in {test_name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Final Summary
    print("\n\n" + "="*80)
    print("FINAL TEST SUMMARY")
    print("="*80)
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    for test_name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {test_name}")
    
    print(f"\nTotal: {passed_count}/{total_count} test suites passed")
    print(f"Success rate: {passed_count/total_count*100:.1f}%")
    
    print("\n" + "="*80)
    if passed_count == total_count:
        print("ALL TEST SUITES PASSED!")
    else:
        print(f"SOME TEST SUITES FAILED ({total_count - passed_count} failures)")
    print("="*80)
    
    return passed_count == total_count

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
