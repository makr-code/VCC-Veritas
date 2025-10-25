#!/usr/bin/env python3
"""
Test Worker Registry Pipeline Integration
==========================================
Tests die Integration der Worker Registry in die Intelligent Pipeline.
"""

import sys
import os
import asyncio
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.agents.veritas_intelligent_pipeline import IntelligentMultiAgentPipeline, IntelligentPipelineRequest

async def test_pipeline_worker_registry_integration():
    """Test Pipeline mit Worker Registry Integration"""
    print("\n" + "="*80)
    print("TEST: Pipeline Worker Registry Integration")
    print("="*80)
    
    # Pipeline initialisieren
    print("\nSchritt 1: Pipeline initialisieren...")
    pipeline = IntelligentMultiAgentPipeline(max_workers=3)
    
    init_success = await pipeline.initialize()
    
    if not init_success:
        print("FEHLER: Pipeline-Initialisierung fehlgeschlagen")
        return False
    
    print("  Pipeline initialisiert")
    print(f"  Ollama Client: {'OK' if pipeline.ollama_client else 'FEHLT'}")
    print(f"  RAG Service: {'OK' if pipeline.rag_service else 'FEHLT'}")
    print(f"  Worker Registry: {'OK' if pipeline.worker_registry else 'FEHLT'}")
    
    if not pipeline.worker_registry:
        print("\nWARNING: Worker Registry nicht verfuegbar - Test uebersprungen")
        return False
    
    # Workers anzeigen
    print("\nSchritt 2: Verfuegbare Workers...")
    available_workers = pipeline.worker_registry.list_available_workers()
    print(f"  Verfuegbare Workers: {len(available_workers)}")
    for worker_id, info in available_workers.items():
        print(f"    - {worker_id} ({info['domain']})")
    
    # Test-Queries
    test_queries = [
        {
            "query": "Wie ist die Luftqualitaet in Muenchen?",
            "expected_workers": ["EnvironmentalAgent", "AtmosphericFlowAgent"],
            "description": "Umwelt-Query sollte Environmental + Atmospheric Workers matchen"
        },
        {
            "query": "Welche chemischen Stoffe sind gefaehrlich?",
            "expected_workers": ["ChemicalDataAgent"],
            "description": "Chemie-Query sollte Chemical Worker matchen"
        },
        {
            "query": "Was sind die DIN-Normen fuer Bauvorhaben?",
            "expected_workers": ["TechnicalStandardsAgent"],
            "description": "Standards-Query sollte Technical Worker matchen"
        },
        {
            "query": "Was ist die Hauptstadt von Deutschland?",
            "expected_workers": ["WikipediaAgent"],
            "description": "Allgemeinwissen-Query sollte Wikipedia Worker matchen"
        }
    ]
    
    print("\nSchritt 3: Test-Queries durchfuehren...")
    print("-" * 80)
    
    test_results = []
    
    for i, test in enumerate(test_queries, 1):
        print(f"\nTest Query {i}/{len(test_queries)}")
        print(f"Query: {test['query']}")
        print(f"Expected: {', '.join(test['expected_workers'])}")
        
        # Pipeline Request erstellen
        request = IntelligentPipelineRequest(
            query_text=test['query'],
            user_context={},
            enable_supervisor=False,  # Worker Registry nutzen
            streaming=False
        )
        
        try:
            # Nur Agent Selection testen (nicht full pipeline)
            # Direkt _step_agent_selection aufrufen
            analysis_context = {
                "analysis": {
                    "complexity": "standard",
                    "domain": "general"
                },
                "rag": {
                    "documents": []
                }
            }
            
            selection_result = await pipeline._step_agent_selection(request, analysis_context)
            
            selected_agents = selection_result.get("selected_agents", [])
            priority_map = selection_result.get("priority_map", {})
            insights = selection_result.get("insights", [])
            registry_context = selection_result.get("worker_registry_context")
            
            print(f"  Selected: {', '.join(selected_agents)}")
            print(f"  Method: {registry_context.get('mode', 'unknown') if registry_context else 'standard'}")
            
            if insights:
                print(f"  Insights: {insights[0]}")
            
            # Checke ob erwartete Workers dabei sind
            matches = [w for w in test['expected_workers'] if w in selected_agents]
            match_rate = len(matches) / len(test['expected_workers']) if test['expected_workers'] else 0
            
            result = {
                "query": test['query'],
                "expected": test['expected_workers'],
                "selected": selected_agents,
                "matches": matches,
                "match_rate": match_rate,
                "passed": match_rate >= 0.5  # Mindestens 50% Match
            }
            
            test_results.append(result)
            
            status = "PASS" if result['passed'] else "FAIL"
            print(f"  Status: [{status}] {len(matches)}/{len(test['expected_workers'])} matches ({match_rate*100:.0f}%)")
            
        except Exception as e:
            print(f"  ERROR: {e}")
            test_results.append({
                "query": test['query'],
                "passed": False,
                "error": str(e)
            })
    
    # Test-Zusammenfassung
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed_count = sum(1 for r in test_results if r.get('passed', False))
    total_count = len(test_results)
    
    for i, result in enumerate(test_results, 1):
        status = "PASS" if result.get('passed', False) else "FAIL"
        query_short = result['query'][:50] + "..." if len(result['query']) > 50 else result['query']
        print(f"  [{status}] Test {i}: {query_short}")
        
        if 'matches' in result:
            print(f"        Matched: {', '.join(result['matches'])}")
    
    print(f"\nTotal: {passed_count}/{total_count} tests passed")
    print(f"Success rate: {passed_count/total_count*100:.1f}%")
    
    # Statistiken
    print("\n" + "="*80)
    print("PIPELINE STATISTICS")
    print("="*80)
    print(f"Worker Registry Usage: {pipeline.stats.get('worker_registry_usage', 0)}")
    print(f"Supervisor Usage: {pipeline.stats.get('supervisor_usage', 0)}")
    print(f"Orchestrator Usage: {pipeline.stats.get('orchestrator_usage', 0)}")
    
    print("\n" + "="*80)
    if passed_count == total_count:
        print("ALL TESTS PASSED!")
    else:
        print(f"SOME TESTS FAILED ({total_count - passed_count} failures)")
    print("="*80)
    
    return passed_count == total_count

async def test_worker_registry_statistics():
    """Test Worker Registry Statistiken"""
    print("\n" + "="*80)
    print("TEST: Worker Registry Statistics")
    print("="*80)
    
    pipeline = IntelligentMultiAgentPipeline(max_workers=2)
    await pipeline.initialize()
    
    if not pipeline.worker_registry:
        print("Worker Registry nicht verfuegbar")
        return False
    
    # Mehrere Queries durchfuehren
    queries = [
        "Luftqualitaet",
        "Chemische Stoffe",
        "DIN Normen",
        "Wikipedia Suche",
        "Atmosphaere"
    ]
    
    print(f"\nFuehre {len(queries)} Queries durch...")
    
    for query in queries:
        request = IntelligentPipelineRequest(
            query_text=query,
            user_context={},
            enable_supervisor=False,
            streaming=False
        )
        
        context = {
            "analysis": {"complexity": "standard", "domain": "general"},
            "rag": {"documents": []}
        }
        
        await pipeline._step_agent_selection(request, context)
    
    # Statistiken pruefen
    registry_usage = pipeline.stats.get('worker_registry_usage', 0)
    
    print(f"\nStatistiken:")
    print(f"  Worker Registry Usage: {registry_usage}")
    print(f"  Expected: {len(queries)}")
    
    passed = registry_usage == len(queries)
    
    print(f"\nRESULT: {'PASS' if passed else 'FAIL'}")
    
    return passed

async def run_all_tests():
    """Alle Tests ausfuehren"""
    print("\n" + "="*80)
    print("WORKER REGISTRY PIPELINE INTEGRATION - TESTS")
    print("="*80)
    
    tests = [
        ("Pipeline Integration", test_pipeline_worker_registry_integration),
        ("Statistics", test_worker_registry_statistics)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            print(f"\n\nRunning: {test_name}")
            print("="*80)
            passed = await test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"\nERROR in {test_name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Zusammenfassung
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
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
