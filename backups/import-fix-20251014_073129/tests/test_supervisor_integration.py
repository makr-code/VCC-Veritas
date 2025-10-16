"""#!/usr/bin/env python3

Test Supervisor Integration in UnifiedOrchestratorV7"""

Test: Supervisor-Integration in IntelligentMultiAgentPipeline

Tests:==============================================================

1. Supervisor mode detection

2. Phase execution with supervisor phasesTestet die neue enable_supervisor-Funktion mit einem Vergleich:

3. Input mapping from previous phases- Standard-Modus (enable_supervisor=False)

4. Agent selection phase execution- Supervisor-Modus (enable_supervisor=True)

5. Final answer extraction from agent synthesis"""



Author: VERITAS v7.0 Developmentimport asyncio

Date: 12. Oktober 2025import json

"""import sys

import os

import asynciofrom pathlib import Path

import json

import logging# Python-Pfad sicherstellen

from pathlib import PathREPO_ROOT = Path(__file__).parent.parent.absolute()

if str(REPO_ROOT) not in sys.path:

# Setup logging    sys.path.insert(0, str(REPO_ROOT))

logging.basicConfig(

    level=logging.INFO,# Set PYTHONPATH

    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'os.environ['PYTHONPATH'] = str(REPO_ROOT.parent)

)

logger = logging.getLogger(__name__)from backend.agents.veritas_intelligent_pipeline import (

    get_intelligent_pipeline,

    IntelligentPipelineRequest

async def test_supervisor_mode_detection():)

    """Test 1: Verify supervisor mode is enabled in config"""

    print("\n" + "="*60)async def test_supervisor_integration():

    print("TEST 1: Supervisor Mode Detection")    """Test der Supervisor-Integration"""

    print("="*60)    

        print("=" * 80)

    from backend.orchestration.unified_orchestrator_v7 import UnifiedOrchestratorV7    print("SUPERVISOR-INTEGRATION TEST")

        print("=" * 80)

    orchestrator = UnifiedOrchestratorV7(    

        config_dir="config",    # Pipeline initialisieren

        method_id="default_method",    print("\n🚀 Initialisiere Pipeline...")

        ollama_client=None,    pipeline = await get_intelligent_pipeline()

        uds3_strategy=None,    

        agent_orchestrator=None,    # Test-Query

        enable_streaming=False    test_query = "Wie ist die Luftqualität in München und welche Behörden sind für Umweltschutz zuständig?"

    )    

        print(f"\n📝 Test-Query: {test_query}")

    # Check if supervisor is enabled    print()

    is_enabled = orchestrator._is_supervisor_enabled()    

        # ========================================================================

    print(f"\n✅ Supervisor enabled: {is_enabled}")    # TEST 1: STANDARD-MODUS (Baseline)

    print(f"✅ Supervisor initialization pending: {orchestrator._supervisor_initialization_pending}")    # ========================================================================

        

    # Load and verify config    print("=" * 80)

    method_config_path = Path("config/scientific_methods/default_method.json")    print("TEST 1: STANDARD-MODUS (enable_supervisor=False)")

    with open(method_config_path, 'r', encoding='utf-8') as f:    print("=" * 80)

        method_config = json.load(f)    

        request_standard = IntelligentPipelineRequest(

    print(f"✅ Method version: {method_config.get('version', 'unknown')}")        query_id="test_standard_001",

    print(f"✅ Supervisor enabled in config: {method_config.get('supervisor_enabled', False)}")        query_text=test_query,

    print(f"✅ Total phases: {len(method_config.get('phases', []))}")        user_context={"location": "München", "user_type": "citizen"},

            enable_supervisor=False,  # ⚠️ STANDARD-MODUS

    # List all phases        enable_llm_commentary=False  # Schneller für Test

    print("\n📋 Phases in config:")    )

    for phase in method_config.get('phases', []):    

        phase_id = phase.get('phase_id')    print("\n⏱️ Starte Standard-Pipeline...")

        phase_num = phase.get('phase_number')    response_standard = await pipeline.process_intelligent_query(request_standard)

        executor = phase.get('execution', {}).get('executor', 'llm')    

        print(f"   {phase_num:>4} | {phase_id:30} | executor={executor}")    print(f"\n✅ Standard-Pipeline abgeschlossen")

        print(f"   - Confidence: {response_standard.confidence_score:.2f}")

    assert is_enabled, "Supervisor should be enabled"    print(f"   - Processing Time: {response_standard.total_processing_time:.2f}s")

    assert method_config.get('supervisor_enabled'), "supervisor_enabled flag should be True"    print(f"   - Agents Used: {len(response_standard.agent_results)}")

        print(f"   - Response Preview: {response_standard.response_text[:200]}...")

    print("\n✅ TEST 1 PASSED: Supervisor mode is enabled")    

    # ========================================================================

    # TEST 2: SUPERVISOR-MODUS

async def test_input_mapping():    # ========================================================================

    """Test 2: Test _map_inputs functionality"""    

    print("\n" + "="*60)    print("\n" + "=" * 80)

    print("TEST 2: Input Mapping from Previous Phases")    print("TEST 2: SUPERVISOR-MODUS (enable_supervisor=True)")

    print("="*60)    print("=" * 80)

        

    from backend.orchestration.unified_orchestrator_v7 import UnifiedOrchestratorV7    request_supervisor = IntelligentPipelineRequest(

    from backend.services.scientific_phase_executor import PhaseExecutionContext, PhaseResult        query_id="test_supervisor_001",

            query_text=test_query,

    orchestrator = UnifiedOrchestratorV7(        user_context={"location": "München", "user_type": "citizen"},

        config_dir="config",        enable_supervisor=True,  # 🆕 SUPERVISOR-MODUS

        method_id="default_method",        enable_llm_commentary=False  # Schneller für Test

        ollama_client=None,    )

        uds3_strategy=None    

    )    print("\n⏱️ Starte Supervisor-Pipeline...")

        response_supervisor = await pipeline.process_intelligent_query(request_supervisor)

    # Mock context with previous phases    

    context = PhaseExecutionContext(    print(f"\n✅ Supervisor-Pipeline abgeschlossen")

        user_query="Brauche ich Baugenehmigung für Carport?",    print(f"   - Confidence: {response_supervisor.confidence_score:.2f}")

        rag_results={"semantic": [], "graph": []},    print(f"   - Processing Time: {response_supervisor.total_processing_time:.2f}s")

        previous_phases={    print(f"   - Agents Used: {len(response_supervisor.agent_results)}")

            "hypothesis": {    print(f"   - Response Preview: {response_supervisor.response_text[:200]}...")

                "hypothesis": "Carport bis 30m² ist verfahrensfrei",    

                "missing_information": ["solar radiation data", "cost estimate", "local building regulations"],    # ========================================================================

                "confidence": 0.7    # VERGLEICH

            }    # ========================================================================

        },    

        metadata={"user_context": {"location": "München"}}    print("\n" + "=" * 80)

    )    print("VERGLEICH: STANDARD vs. SUPERVISOR")

        print("=" * 80)

    # Test input mapping    

    input_mapping = {    print(f"\n📊 METRIKEN:")

        "query": "user_query",    print(f"   Confidence Score:")

        "missing_information": "phases.hypothesis.missing_information",    print(f"      Standard:   {response_standard.confidence_score:.2f}")

        "hypothesis": "phases.hypothesis.hypothesis",    print(f"      Supervisor: {response_supervisor.confidence_score:.2f}")

        "rag_results": "rag_results",    print(f"      Δ: {response_supervisor.confidence_score - response_standard.confidence_score:+.2f}")

        "user_context": "metadata.user_context"    

    }    print(f"\n   Processing Time:")

        print(f"      Standard:   {response_standard.total_processing_time:.2f}s")

    mapped = orchestrator._map_inputs(input_mapping, context)    print(f"      Supervisor: {response_supervisor.total_processing_time:.2f}s")

        print(f"      Δ: {response_supervisor.total_processing_time - response_standard.total_processing_time:+.2f}s")

    print("\n📊 Mapped Inputs:")    

    for key, value in mapped.items():    print(f"\n   Agents Used:")

        print(f"   {key:25} = {value}")    print(f"      Standard:   {len(response_standard.agent_results)}")

        print(f"      Supervisor: {len(response_supervisor.agent_results)}")

    # Verify mappings    

    assert mapped["query"] == "Brauche ich Baugenehmigung für Carport?", "Query should be mapped"    print(f"\n   Response Length:")

    assert len(mapped["missing_information"]) == 3, "Should have 3 missing_information items"    print(f"      Standard:   {len(response_standard.response_text)} chars")

    assert "solar radiation data" in mapped["missing_information"], "Should contain 'solar radiation data'"    print(f"      Supervisor: {len(response_supervisor.response_text)} chars")

    assert mapped["hypothesis"] == "Carport bis 30m² ist verfahrensfrei", "Hypothesis should be mapped"    

    assert mapped["user_context"]["location"] == "München", "User context should be mapped"    # ========================================================================

        # DETAILLIERTE ANTWORTEN

    print("\n✅ TEST 2 PASSED: Input mapping works correctly")    # ========================================================================

    

    print("\n" + "=" * 80)

async def test_complexity_inference():    print("STANDARD-MODUS ANTWORT:")

    """Test 3: Test complexity inference from missing_information"""    print("=" * 80)

    print("\n" + "="*60)    print(response_standard.response_text)

    print("TEST 3: Complexity Inference")    

    print("="*60)    print("\n" + "=" * 80)

        print("SUPERVISOR-MODUS ANTWORT:")

    from backend.orchestration.unified_orchestrator_v7 import UnifiedOrchestratorV7    print("=" * 80)

        print(response_supervisor.response_text)

    orchestrator = UnifiedOrchestratorV7(    

        config_dir="config",    # ========================================================================

        method_id="default_method"    # PIPELINE-STATISTIKEN

    )    # ========================================================================

        

    # Test cases    print("\n" + "=" * 80)

    test_cases = [    print("PIPELINE-STATISTIKEN:")

        ([], "simple"),    print("=" * 80)

        (["one item"], "simple"),    

        (["item1", "item2"], "standard"),    stats = pipeline.stats

        (["item1", "item2", "item3"], "standard"),    print(f"\n   Total Pipelines: {stats['pipelines_processed']}")

        (["item1", "item2", "item3", "item4"], "complex"),    print(f"   Successful: {stats['successful_pipelines']}")

        (["item1", "item2", "item3", "item4", "item5"], "complex"),    print(f"   Failed: {stats['failed_pipelines']}")

    ]    print(f"   Supervisor Usage: {stats.get('supervisor_usage', 0)}")

        print(f"   Orchestrator Usage: {stats.get('orchestrator_usage', 0)}")

    print("\n📊 Complexity Inference Test:")    

    for missing_info, expected in test_cases:    print("\n✅ TEST ABGESCHLOSSEN!")

        result = orchestrator._infer_complexity(missing_info)    print("=" * 80)

        status = "✅" if result == expected else "❌"

        print(f"   {status} {len(missing_info)} items → {result:10} (expected: {expected})")if __name__ == "__main__":

        assert result == expected, f"Expected {expected}, got {result}"    asyncio.run(test_supervisor_integration())

    
    print("\n✅ TEST 3 PASSED: Complexity inference works correctly")


async def test_phase_execution_flow():
    """Test 4: Test phase execution with supervisor phases (mock mode)"""
    print("\n" + "="*60)
    print("TEST 4: Phase Execution Flow (Mock Mode)")
    print("="*60)
    
    from backend.orchestration.unified_orchestrator_v7 import UnifiedOrchestratorV7
    
    # Note: This test runs in mock mode (no real Ollama/UDS3)
    orchestrator = UnifiedOrchestratorV7(
        config_dir="config",
        method_id="default_method",
        ollama_client=None,  # Mock mode
        uds3_strategy=None,  # Mock mode
        agent_orchestrator=None,  # Mock mode
        enable_streaming=False
    )
    
    print("\n🔧 Orchestrator initialized (mock mode)")
    print(f"   Supervisor enabled: {orchestrator._is_supervisor_enabled()}")
    print(f"   Method ID: {orchestrator.method_id}")
    
    # Load method config
    method_config_path = Path("config/scientific_methods/default_method.json")
    with open(method_config_path, 'r', encoding='utf-8') as f:
        method_config = json.load(f)
    
    phases = method_config.get("phases", [])
    supervisor_enabled = method_config.get("supervisor_enabled", False)
    
    print(f"\n📋 Phase Execution Plan:")
    print(f"   Total phases in config: {len(phases)}")
    print(f"   Supervisor enabled: {supervisor_enabled}")
    
    # Count phases by executor type
    executor_counts = {}
    for phase in phases:
        executor = phase.get("execution", {}).get("executor", "llm")
        executor_counts[executor] = executor_counts.get(executor, 0) + 1
    
    print(f"\n📊 Phase Distribution:")
    for executor, count in executor_counts.items():
        print(f"   {executor:20} = {count} phases")
    
    expected_executors = ["llm", "supervisor", "agent_coordinator"]
    for executor in expected_executors:
        assert executor in executor_counts, f"Expected executor '{executor}' not found"
    
    print("\n✅ TEST 4 PASSED: Phase execution flow is configured correctly")


async def test_json_config_validity():
    """Test 5: Validate JSON config structure"""
    print("\n" + "="*60)
    print("TEST 5: JSON Config Validity")
    print("="*60)
    
    method_config_path = Path("config/scientific_methods/default_method.json")
    
    with open(method_config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    print("\n📋 Config Validation:")
    
    # Check version
    assert config.get("version") == "2.0.0", "Version should be 2.0.0"
    print(f"   ✅ Version: {config.get('version')}")
    
    # Check supervisor_enabled
    assert config.get("supervisor_enabled") == True, "supervisor_enabled should be True"
    print(f"   ✅ Supervisor enabled: {config.get('supervisor_enabled')}")
    
    # Check phases
    phases = config.get("phases", [])
    assert len(phases) >= 8, "Should have at least 8 phases (6 original + 3 supervisor)"
    print(f"   ✅ Total phases: {len(phases)}")
    
    # Check supervisor phases
    phase_ids = [p.get("phase_id") for p in phases]
    supervisor_phases = ["supervisor_agent_selection", "agent_execution", "agent_result_synthesis"]
    
    for supervisor_phase in supervisor_phases:
        assert supervisor_phase in phase_ids, f"Missing supervisor phase: {supervisor_phase}"
        print(f"   ✅ Supervisor phase present: {supervisor_phase}")
    
    # Check orchestration_config
    orch_config = config.get("orchestration_config", {})
    assert orch_config.get("execution_mode") == "sequential_with_supervisor", "Wrong execution mode"
    print(f"   ✅ Execution mode: {orch_config.get('execution_mode')}")
    
    # Check conditional_phases
    conditional = orch_config.get("phase_execution", {}).get("conditional_phases", [])
    for supervisor_phase in supervisor_phases:
        assert supervisor_phase in conditional, f"Supervisor phase {supervisor_phase} should be conditional"
    print(f"   ✅ Conditional phases: {len(conditional)} phases")
    
    # Check version history
    version_history = config.get("version_history", [])
    assert len(version_history) >= 2, "Should have at least 2 version history entries"
    print(f"   ✅ Version history entries: {len(version_history)}")
    
    latest_version = version_history[0]
    assert latest_version.get("version") == "2.0.0", "Latest version should be 2.0.0"
    assert "Supervisor Integration" in latest_version.get("changes", ""), "Changes should mention Supervisor"
    print(f"   ✅ Latest version: {latest_version.get('version')}")
    
    print("\n✅ TEST 5 PASSED: JSON config is valid")


async def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("SUPERVISOR INTEGRATION TEST SUITE")
    print("="*80)
    print("\nTesting Supervisor Integration in UnifiedOrchestratorV7")
    print("Author: VERITAS v7.0 Development")
    print("Date: 12. Oktober 2025, 04:00 Uhr")
    
    try:
        # Run tests
        await test_supervisor_mode_detection()
        await test_input_mapping()
        await test_complexity_inference()
        await test_phase_execution_flow()
        await test_json_config_validity()
        
        print("\n" + "="*80)
        print("✅ ALL TESTS PASSED (5/5)")
        print("="*80)
        print("\n🎉 Supervisor Integration is working correctly!")
        print("\nNext Steps:")
        print("   1. Test with real Ollama client")
        print("   2. Test with real agent orchestrator")
        print("   3. Run E2E test with construction query")
        
    except Exception as e:
        print("\n" + "="*80)
        print(f"❌ TEST FAILED: {e}")
        print("="*80)
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    asyncio.run(main())
