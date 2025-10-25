#!/usr/bin/env python3
"""
Test Agent Registry Integration
==================================
Tests the Agent Registry with all 6 production-ready agents.
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

def test_agent_registry_initialization():
    """Test registry initialization"""
    print("\n" + "="*80)
    print("TEST 1: Agent Registry Initialization")
    print("="*80)
    
    reset_agent_registry()
    registry = AgentRegistry()
    
    agents = registry.list_available_agents()
    print(f"Workers registered: {len(agents)}")
    
    for worker_id, info in agents.items():
        status = "INITIALIZED" if info['initialized'] else "REGISTERED"
        print(f"  [{status}] {worker_id}")
        print(f"    Domain: {info['domain']}")
        print(f"    Capabilities: {len(info['capabilities'])} items")
    
    assert len(agents) == 6, f"Expected 6 agents, found {len(agents)}"
    print("\nRESULT: PASS")
    return True

def test_get_worker():
    """Test getting individual agents"""
    print("\n" + "="*80)
    print("TEST 2: Get Individual Workers")
    print("="*80)
    
    registry = get_agent_registry()
    
    # Test each worker
    agents_to_test = [
        "EnvironmentalAgent",
        "ChemicalDataAgent",
        "TechnicalStandardsAgent",
        "WikipediaAgent",
        "AtmosphericFlowAgent",
        "DatabaseAgent"
    ]
    
    success_count = 0
    for worker_id in agents_to_test:
        print(f"\nGetting worker: {worker_id}")
        worker = registry.get_agent(worker_id)
        
        if worker is not None:
            print(f"  SUCCESS: {type(worker).__name__} instantiated")
            success_count += 1
        else:
            print(f"  FAILED: Could not instantiate {worker_id}")
    
    print(f"\nWorkers instantiated: {success_count}/{len(agents_to_test)}")
    print(f"RESULT: {'PASS' if success_count == len(agents_to_test) else 'PARTIAL'}")
    return success_count == len(agents_to_test)

def test_search_by_capability():
    """Test capability-based search"""
    print("\n" + "="*80)
    print("TEST 3: Search by Capability")
    print("="*80)
    
    registry = get_agent_registry()
    
    test_capabilities = [
        ("luftqualitaet", ["EnvironmentalAgent"]),
        ("chemical", ["ChemicalDataAgent"]),
        ("din", ["TechnicalStandardsAgent"]),
        ("wikipedia", ["WikipediaAgent"]),
        ("atmospheric", ["AtmosphericFlowAgent"]),
        ("database", ["DatabaseAgent"])
    ]
    
    all_passed = True
    for capability, expected_agents in test_capabilities:
        results = registry.get_agents_by_capability(capability)
        print(f"\nCapability: '{capability}'")
        print(f"  Expected: {expected_agents}")
        print(f"  Found: {results}")
        
        if set(results) == set(expected_agents):
            print("  STATUS: PASS")
        else:
            print("  STATUS: FAIL")
            all_passed = False
    
    print(f"\nRESULT: {'PASS' if all_passed else 'FAIL'}")
    return all_passed

def test_search_by_domain():
    """Test domain-based search"""
    print("\n" + "="*80)
    print("TEST 4: Search by Domain")
    print("="*80)
    
    registry = get_agent_registry()
    
    # Environmental domain should have 2 agents
    env_agents = registry.get_agents_by_domain(AgentDomain.ENVIRONMENTAL)
    print(f"\nEnvironmental domain agents: {env_agents}")
    print(f"  Count: {len(env_agents)} (expected: 2)")
    
    # Technical domain should have 1 worker
    tech_agents = registry.get_agents_by_domain(AgentDomain.TECHNICAL)
    print(f"\nTechnical domain agents: {tech_agents}")
    print(f"  Count: {len(tech_agents)} (expected: 1)")
    
    # Knowledge domain should have 1 worker
    know_agents = registry.get_agents_by_domain(AgentDomain.KNOWLEDGE)
    print(f"\nKnowledge domain agents: {know_agents}")
    print(f"  Count: {len(know_agents)} (expected: 1)")
    
    passed = (
        len(env_agents) == 2 and
        len(tech_agents) == 1 and
        len(know_agents) == 1
    )
    
    print(f"\nRESULT: {'PASS' if passed else 'FAIL'}")
    return passed

def test_search_agents():
    """Test text search functionality"""
    print("\n" + "="*80)
    print("TEST 5: Text Search")
    print("="*80)
    
    registry = get_agent_registry()
    
    test_searches = [
        ("luft", 2),  # EnvironmentalAgent, AtmosphericFlowAgent
        ("umwelt", 1),  # EnvironmentalAgent
        ("standards", 1),  # TechnicalStandardsAgent
        ("wissen", 1),  # WikipediaAgent
    ]
    
    all_passed = True
    for query, expected_count in test_searches:
        results = registry.search_agents(query)
        print(f"\nSearch: '{query}'")
        print(f"  Expected count: {expected_count}")
        print(f"  Found: {len(results)} agents - {results}")
        
        if len(results) >= expected_count:
            print("  STATUS: PASS")
        else:
            print("  STATUS: FAIL")
            all_passed = False
    
    print(f"\nRESULT: {'PASS' if all_passed else 'FAIL'}")
    return all_passed

def test_worker_info():
    """Test getting detailed worker information"""
    print("\n" + "="*80)
    print("TEST 6: Get Worker Info")
    print("="*80)
    
    registry = get_agent_registry()
    
    worker_id = "EnvironmentalAgent"
    info = registry.get_agent_info(worker_id)
    
    print(f"\nWorker: {worker_id}")
    if info:
        print(f"  Domain: {info['domain']}")
        print(f"  Description: {info['description']}")
        print(f"  Capabilities: {len(info['capabilities'])} items")
        print(f"  Requires DB: {info['requires_db']}")
        print(f"  Requires API: {info['requires_api']}")
        print("\nRESULT: PASS")
        return True
    else:
        print("  ERROR: Worker not found")
        print("\nRESULT: FAIL")
        return False

def test_singleton_pattern():
    """Test singleton pattern"""
    print("\n" + "="*80)
    print("TEST 7: Singleton Pattern")
    print("="*80)
    
    registry1 = get_agent_registry()
    registry2 = get_agent_registry()
    
    print(f"\nRegistry 1 ID: {id(registry1)}")
    print(f"Registry 2 ID: {id(registry2)}")
    
    if registry1 is registry2:
        print("STATUS: Same instance (singleton working)")
        print("\nRESULT: PASS")
        return True
    else:
        print("STATUS: Different instances (singleton NOT working)")
        print("\nRESULT: FAIL")
        return False

def run_all_tests():
    """Run all tests"""
    print("\n" + "="*80)
    print("VERITAS WORKER REGISTRY - INTEGRATION TESTS")
    print("="*80)
    
    tests = [
        ("Initialization", test_agent_registry_initialization),
        ("Get Workers", test_get_worker),
        ("Search by Capability", test_search_by_capability),
        ("Search by Domain", test_search_by_domain),
        ("Text Search", test_search_agents),
        ("Worker Info", test_worker_info),
        ("Singleton Pattern", test_singleton_pattern)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"\nERROR in {test_name}: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    for test_name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {test_name}")
    
    print(f"\nTotal: {passed_count}/{total_count} tests passed")
    print(f"Success rate: {passed_count/total_count*100:.1f}%")
    
    print("\n" + "="*80)
    if passed_count == total_count:
        print("ALL TESTS PASSED!")
    else:
        print(f"SOME TESTS FAILED ({total_count - passed_count} failures)")
    print("="*80)
    
    return passed_count == total_count

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
