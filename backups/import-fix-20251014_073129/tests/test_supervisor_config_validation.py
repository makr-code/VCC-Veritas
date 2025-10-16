"""
Quick Supervisor Config Validation Test

Testet OHNE Ollama/UDS3:
- JSON Config laden
- Supervisor enabled check
- Phase count
- Custom executors
- Input mapping

Author: VERITAS v7.0
Date: 12. Oktober 2025
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

def test_config_structure():
    """Test JSON config structure"""
    
    print("=" * 80)
    print("🧪 Supervisor Config Validation Test")
    print("=" * 80)
    
    config_path = REPO_ROOT / "config" / "scientific_methods" / "default_method.json"
    
    if not config_path.exists():
        print(f"❌ Config file not found: {config_path}")
        return False
    
    # Load config
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    print(f"\n✅ Config loaded successfully")
    
    # Check version
    version = config.get('version')
    print(f"   Version: {version}")
    
    if version != "2.0.0":
        print(f"   ❌ FAIL: Expected version 2.0.0, got {version}")
        return False
    
    # Check supervisor flag
    supervisor_enabled = config.get('supervisor_enabled')
    print(f"   Supervisor Enabled: {supervisor_enabled}")
    
    if not supervisor_enabled:
        print("   ❌ FAIL: supervisor_enabled should be true")
        return False
    
    # Check phases
    phases = config.get('phases', [])
    print(f"   Phase Count: {len(phases)}")
    
    if len(phases) != 9:
        print(f"   ❌ FAIL: Expected 9 phases, got {len(phases)}")
        return False
    
    # Check supervisor phases
    print("\n📋 Supervisor Phases Check:")
    
    supervisor_phases = [
        ("supervisor_agent_selection", 1.5, "supervisor", "select_agents"),
        ("agent_execution", 1.6, "agent_coordinator", "execute_agents"),
        ("agent_result_synthesis", 6.5, "supervisor", "synthesize_results")
    ]
    
    found_phases = {}
    for phase in phases:
        phase_id = phase.get('phase_id')
        found_phases[phase_id] = phase
    
    all_passed = True
    
    for expected_id, expected_number, expected_executor, expected_method in supervisor_phases:
        if expected_id not in found_phases:
            print(f"   ❌ Phase missing: {expected_id}")
            all_passed = False
            continue
        
        phase = found_phases[expected_id]
        phase_number = phase.get('phase_number')
        executor = phase.get('execution', {}).get('executor')
        method = phase.get('execution', {}).get('method')
        
        if phase_number != expected_number:
            print(f"   ❌ {expected_id}: Wrong phase_number (expected {expected_number}, got {phase_number})")
            all_passed = False
            continue
        
        if executor != expected_executor:
            print(f"   ❌ {expected_id}: Wrong executor (expected {expected_executor}, got {executor})")
            all_passed = False
            continue
        
        if method != expected_method:
            print(f"   ❌ {expected_id}: Wrong method (expected {expected_method}, got {method})")
            all_passed = False
            continue
        
        print(f"   ✅ {expected_id}: phase_number={phase_number}, executor={executor}, method={method}")
    
    # Check input mappings
    print("\n📋 Input Mapping Check:")
    
    phase_1_5 = found_phases.get('supervisor_agent_selection', {})
    input_mapping = phase_1_5.get('input_mapping', {})
    
    required_inputs = ['query', 'missing_information', 'rag_results']
    
    for required_input in required_inputs:
        if required_input not in input_mapping:
            print(f"   ❌ Phase 1.5 missing input: {required_input}")
            all_passed = False
        else:
            mapping_path = input_mapping[required_input]
            print(f"   ✅ {required_input}: {mapping_path}")
    
    # Check orchestration config
    print("\n📋 Orchestration Config Check:")
    
    orchestration = config.get('orchestration_config', {}).get('phase_execution', {})
    execution_mode = config.get('orchestration_config', {}).get('execution_mode')
    conditional_phases = orchestration.get('conditional_phases', [])
    
    print(f"   Execution Mode: {execution_mode}")
    
    if execution_mode != "sequential_with_supervisor":
        print(f"   ❌ FAIL: Expected 'sequential_with_supervisor', got '{execution_mode}'")
        all_passed = False
    else:
        print("   ✅ Execution mode correct")
    
    print(f"   Conditional Phases: {len(conditional_phases)}")
    
    expected_conditional = ['supervisor_agent_selection', 'agent_execution', 'agent_result_synthesis']
    
    for phase_id in expected_conditional:
        if phase_id in conditional_phases:
            print(f"   ✅ {phase_id} is conditional")
        else:
            print(f"   ❌ {phase_id} should be conditional")
            all_passed = False
    
    # Final result
    print("\n" + "=" * 80)
    if all_passed:
        print("🎉 CONFIG VALIDATION PASSED - All checks successful!")
        print("=" * 80)
        return True
    else:
        print("⚠️ CONFIG VALIDATION FAILED - Some checks failed")
        print("=" * 80)
        return False


def test_orchestrator_import():
    """Test if orchestrator can be imported with supervisor integration"""
    
    print("\n" + "=" * 80)
    print("🧪 Orchestrator Import Test")
    print("=" * 80)
    
    try:
        from backend.orchestration.unified_orchestrator_v7 import UnifiedOrchestratorV7
        print("✅ UnifiedOrchestratorV7 imported successfully")
        
        # Check if new methods exist
        methods = [
            '_is_supervisor_enabled',
            '_ensure_supervisor_initialized',
            '_map_inputs',
            '_infer_complexity',
            '_execute_supervisor_phase',
            '_execute_agent_coordination_phase'
        ]
        
        print("\n📋 Method Availability Check:")
        
        all_found = True
        for method_name in methods:
            if hasattr(UnifiedOrchestratorV7, method_name):
                print(f"   ✅ {method_name}")
            else:
                print(f"   ❌ {method_name} NOT FOUND")
                all_found = False
        
        print("\n" + "=" * 80)
        if all_found:
            print("🎉 ORCHESTRATOR IMPORT PASSED - All methods available!")
        else:
            print("⚠️ ORCHESTRATOR IMPORT FAILED - Some methods missing")
        print("=" * 80)
        
        return all_found
    
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main test runner"""
    
    print("\n" + "=" * 80)
    print("🚀 SUPERVISOR INTEGRATION - Configuration Validation")
    print("=" * 80)
    
    # Test 1: Config Structure
    test1_passed = test_config_structure()
    
    # Test 2: Orchestrator Import
    test2_passed = test_orchestrator_import()
    
    # Summary
    print("\n" + "=" * 80)
    print("🏁 VALIDATION SUMMARY")
    print("=" * 80)
    print(f"Test 1 (Config Structure): {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"Test 2 (Orchestrator Import): {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 ALL VALIDATION TESTS PASSED!")
        print("   Next step: Run E2E test with real Ollama")
    else:
        print("\n⚠️ SOME VALIDATION TESTS FAILED")
        print("   Fix configuration issues before E2E testing")
    
    print("=" * 80)
    
    return test1_passed and test2_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
