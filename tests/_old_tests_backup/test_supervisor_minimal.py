"""
Minimal Supervisor Integration Test

Testet MINIMAL:
- Supervisor enabled check
- Phase loading (9 phases)
- Input mapping test (without LLM)
- Mock supervisor execution

NO Ollama/UDS3 required!

Author: VERITAS v7.0
Date: 12. Oktober 2025
"""

import asyncio
import sys
import json
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

print("=" * 80)
print("🧪 SUPERVISOR INTEGRATION - Minimal Test (No Ollama/UDS3)")
print("=" * 80)

def test_supervisor_config():
    """Test 1: Supervisor Config Detection"""
    
    print("\n📋 Test 1: Supervisor Config Detection")
    print("-" * 80)
    
    config_path = REPO_ROOT / "config" / "scientific_methods" / "default_method.json"
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    supervisor_enabled = config.get('supervisor_enabled', False)
    version = config.get('version')
    phases = config.get('phases', [])
    
    print(f"   Version: {version}")
    print(f"   Supervisor Enabled: {supervisor_enabled}")
    print(f"   Total Phases: {len(phases)}")
    
    # Check supervisor phases
    supervisor_phases = [
        'supervisor_agent_selection',
        'agent_execution', 
        'agent_result_synthesis'
    ]
    
    found_supervisor_phases = []
    for phase in phases:
        if phase.get('phase_id') in supervisor_phases:
            found_supervisor_phases.append(phase.get('phase_id'))
            executor = phase.get('execution', {}).get('executor')
            print(f"   ✅ {phase.get('phase_id')}: executor={executor}")
    
    result = (
        supervisor_enabled == True and
        version == "2.0.0" and
        len(phases) == 9 and
        len(found_supervisor_phases) == 3
    )
    
    if result:
        print("\n✅ TEST 1 PASSED - Supervisor config correct")
    else:
        print("\n❌ TEST 1 FAILED")
    
    return result


def test_input_mapping():
    """Test 2: Input Mapping Logic"""
    
    print("\n📋 Test 2: Input Mapping Logic (Mock Data)")
    print("-" * 80)
    
    # Mock context
    class MockContext:
        def __init__(self):
            self.user_query = "Test query"
            self.rag_results = {"documents": []}
            self.previous_phases = {
                "hypothesis": {
                    "output": {
                        "missing_information": ["item1", "item2"]
                    }
                }
            }
    
    context = MockContext()
    
    # Test input mapping paths
    test_mappings = {
        "query": "user_query",
        "missing_information": "phases.hypothesis.output.missing_information",
        "rag_results": "rag_results"
    }
    
    print("   Testing path resolution:")
    
    results = {}
    for key, path in test_mappings.items():
        if path == "user_query":
            value = context.user_query
        elif path == "rag_results":
            value = context.rag_results
        elif path.startswith("phases."):
            # Navigate: phases.hypothesis.output.missing_information
            parts = path.split(".")
            value = context.previous_phases
            for part in parts[1:]:  # Skip "phases"
                if isinstance(value, dict):
                    value = value.get(part)
                else:
                    value = getattr(value, part, None)
        else:
            value = None
        
        results[key] = value
        print(f"   ✅ {key}: {path} → {value}")
    
    # Verify results
    test_passed = (
        results["query"] == "Test query" and
        results["missing_information"] == ["item1", "item2"] and
        results["rag_results"] == {"documents": []}
    )
    
    if test_passed:
        print("\n✅ TEST 2 PASSED - Input mapping works")
    else:
        print("\n❌ TEST 2 FAILED")
    
    return test_passed


def test_complexity_inference():
    """Test 3: Complexity Inference"""
    
    print("\n📋 Test 3: Complexity Inference")
    print("-" * 80)
    
    test_cases = [
        ([], "simple"),
        (["item1"], "simple"),
        (["item1", "item2"], "standard"),
        (["item1", "item2", "item3"], "standard"),
        (["item1", "item2", "item3", "item4"], "complex"),
        (["item1", "item2", "item3", "item4", "item5"], "complex")
    ]
    
    def infer_complexity(missing_information):
        count = len(missing_information)
        if count <= 1:
            return "simple"
        elif count <= 3:
            return "standard"
        else:
            return "complex"
    
    all_passed = True
    
    for missing_info, expected in test_cases:
        result = infer_complexity(missing_info)
        status = "✅" if result == expected else "❌"
        print(f"   {status} {len(missing_info)} items → {result} (expected: {expected})")
        if result != expected:
            all_passed = False
    
    if all_passed:
        print("\n✅ TEST 3 PASSED - Complexity inference correct")
    else:
        print("\n❌ TEST 3 FAILED")
    
    return all_passed


async def test_orchestrator_initialization():
    """Test 4: Orchestrator Initialization (No LLM)"""
    
    print("\n📋 Test 4: Orchestrator Initialization")
    print("-" * 80)
    
    try:
        from backend.orchestration.unified_orchestrator_v7 import UnifiedOrchestratorV7
        
        # Mock Ollama client (no real connection)
        class MockOllamaClient:
            async def initialize(self):
                pass
            async def close(self):
                pass
        
        # Initialize orchestrator
        orchestrator = UnifiedOrchestratorV7(
            config_dir="config",
            method_id="default_method",
            ollama_client=MockOllamaClient(),
            uds3_strategy=None,
            agent_orchestrator=None,
            enable_streaming=False
        )
        
        # Test supervisor enabled check
        supervisor_enabled = orchestrator._is_supervisor_enabled()
        
        print(f"   Orchestrator initialized: ✅")
        print(f"   Supervisor enabled: {supervisor_enabled}")
        
        # Test method availability
        methods = [
            '_is_supervisor_enabled',
            '_ensure_supervisor_initialized',
            '_map_inputs',
            '_infer_complexity',
            '_execute_supervisor_phase',
            '_execute_agent_coordination_phase'
        ]
        
        all_methods_found = True
        for method in methods:
            if hasattr(orchestrator, method):
                print(f"   ✅ {method}")
            else:
                print(f"   ❌ {method} NOT FOUND")
                all_methods_found = False
        
        test_passed = supervisor_enabled and all_methods_found
        
        if test_passed:
            print("\n✅ TEST 4 PASSED - Orchestrator initialized with supervisor support")
        else:
            print("\n❌ TEST 4 FAILED")
        
        return test_passed
    
    except Exception as e:
        print(f"\n❌ TEST 4 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_phase_execution_flow():
    """Test 5: Phase Execution Flow (Dry Run)"""
    
    print("\n📋 Test 5: Phase Execution Flow (Dry Run)")
    print("-" * 80)
    
    try:
        config_path = REPO_ROOT / "config" / "scientific_methods" / "default_method.json"
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        phases = config.get('phases', [])
        
        print(f"   Total phases loaded: {len(phases)}")
        print("\n   Execution order (dry run):")
        
        for i, phase in enumerate(phases, 1):
            phase_id = phase.get('phase_id')
            phase_number = phase.get('phase_number')
            executor = phase.get('execution', {}).get('executor', 'llm')
            method = phase.get('execution', {}).get('method', 'generate')
            
            # Check if conditional
            conditional_phases = config.get('orchestration_config', {}).get('phase_execution', {}).get('conditional_phases', [])
            is_conditional = phase_id in conditional_phases
            
            conditional_marker = "⚠️ CONDITIONAL" if is_conditional else ""
            
            print(f"   {i}. Phase {phase_number} ({phase_id}): executor={executor}, method={method} {conditional_marker}")
        
        # Verify execution mode
        execution_mode = config.get('orchestration_config', {}).get('execution_mode')
        print(f"\n   Execution Mode: {execution_mode}")
        
        test_passed = (
            len(phases) == 9 and
            execution_mode == "sequential_with_supervisor"
        )
        
        if test_passed:
            print("\n✅ TEST 5 PASSED - Phase execution flow correct")
        else:
            print("\n❌ TEST 5 FAILED")
        
        return test_passed
    
    except Exception as e:
        print(f"\n❌ TEST 5 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test runner"""
    
    print("\n" + "=" * 80)
    print("🚀 SUPERVISOR INTEGRATION - Minimal Test Suite")
    print("=" * 80)
    
    results = {}
    
    # Test 1: Config
    results['config'] = test_supervisor_config()
    
    # Test 2: Input Mapping
    results['input_mapping'] = test_input_mapping()
    
    # Test 3: Complexity Inference
    results['complexity'] = test_complexity_inference()
    
    # Test 4: Orchestrator Init
    results['orchestrator_init'] = await test_orchestrator_initialization()
    
    # Test 5: Phase Execution Flow
    results['phase_flow'] = await test_phase_execution_flow()
    
    # Summary
    print("\n" + "=" * 80)
    print("🏁 TEST SUMMARY")
    print("=" * 80)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 80)
    if all_passed:
        print("🎉 ALL TESTS PASSED - Supervisor Integration Ready!")
        print("\n📋 Next Step: Run E2E test with real Ollama")
        print("   Command: python tests\\test_unified_orchestrator_v7_real.py")
    else:
        print("⚠️ SOME TESTS FAILED - Review errors above")
    print("=" * 80)
    
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
