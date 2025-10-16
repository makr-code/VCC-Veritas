#!/usr/bin/env python3
"""
PROGRESSIVE DEPLOYMENT TEST (Phase 2)
Tests VERITAS with supervisor_enabled=true (9-phase system with mock agents)

Expected Behavior:
- 9 phases execute (6 scientific + 3 supervisor)
- Confidence > 0.75 (improved with agent data)
- Execution time: 44-62s
- Mock agent selection/execution
"""
import sys
import os
import json
import time
from pathlib import Path

# Setup paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'backend'))
sys.path.insert(0, str(project_root / 'backend' / 'orchestration'))

print("=" * 80)
print("PROGRESSIVE DEPLOYMENT TEST - Phase 2")
print("=" * 80)

# Test 1: Verify Configuration
print("\n[Test 1/5] Verifying Configuration...")
config_path = project_root / "config" / "scientific_methods" / "default_method.json"
with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)

print(f"  ✅ Config Version: {config.get('version')}")
print(f"  ✅ Supervisor Enabled: {config.get('supervisor_enabled')}")
print(f"  ✅ Total Phases in Config: {len(config.get('phases', []))}")

assert config.get('version') == '2.0.0', "Config version should be 2.0.0"
assert config.get('supervisor_enabled') == True, "Supervisor should be ENABLED for progressive deployment"
print("  ✅ Configuration correct for Progressive Mode")

# Test 2: Import Orchestrator
print("\n[Test 2/5] Importing Orchestrator...")
try:
    from unified_orchestrator_v7 import UnifiedOrchestratorV7
    print("  ✅ UnifiedOrchestratorV7 imported successfully")
except ImportError as e:
    print(f"  ❌ Import failed: {e}")
    sys.exit(1)

# Test 3: Initialize Orchestrator
print("\n[Test 3/5] Initializing Orchestrator...")
try:
    orchestrator = UnifiedOrchestratorV7(
        config_dir="config",
        method_id="default_method",
        uds3_strategy=None,  # Will use mock
        ollama_client=None,  # Will use mock
        agent_orchestrator=None  # Mock agents (Phase 2)
    )
    print("  ✅ Orchestrator initialized")
    
    # Check supervisor status
    supervisor_enabled = orchestrator._is_supervisor_enabled()
    print(f"  ✅ Supervisor Enabled (Runtime): {supervisor_enabled}")
    assert supervisor_enabled == True, "Supervisor should be enabled at runtime"
    
    # Check if supervisor was initialized
    if hasattr(orchestrator, 'supervisor_agent'):
        print("  ✅ SupervisorAgent initialized")
    else:
        print("  ⚠️  SupervisorAgent not yet initialized (lazy loading)")
    
except Exception as e:
    print(f"  ❌ Initialization failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Phase Execution Flow (Dry Run)
print("\n[Test 4/5] Phase Execution Flow (Dry Run)...")
print("  Checking which phases would execute...")

phases = config.get('phases', [])
expected_phases = []
supervisor_phases = []

for phase in phases:
    phase_num = phase.get('phase_number')
    phase_id = phase.get('phase_id')
    executor = phase.get('execution', {}).get('executor', 'llm')
    
    if executor in ['supervisor', 'agent_coordinator']:
        supervisor_phases.append(phase_num)
        print(f"    ✅ Phase {phase_num} ({phase_id}): Will execute (SUPERVISOR)")
    else:
        expected_phases.append(phase_num)
        print(f"    ✅ Phase {phase_num} ({phase_id}): Will execute (LLM)")

print(f"\n  ✅ LLM Phases: {len(expected_phases)} (should be 6)")
print(f"  ✅ Supervisor Phases: {len(supervisor_phases)} (should be 3)")
print(f"  ✅ Total Phases: {len(expected_phases) + len(supervisor_phases)} (should be 9)")

assert len(expected_phases) == 6, f"Expected 6 LLM phases, got {len(expected_phases)}"
assert len(supervisor_phases) == 3, f"Expected 3 supervisor phases, got {len(supervisor_phases)}"

# Test 5: Verify Supervisor Methods
print("\n[Test 5/5] Verifying Supervisor Methods...")
method_checks = [
    '_is_supervisor_enabled',
    '_ensure_supervisor_initialized',
    '_map_inputs',
    '_infer_complexity',
    '_execute_supervisor_phase',
    '_execute_agent_coordination_phase'
]

missing_methods = []
for method_name in method_checks:
    if hasattr(orchestrator, method_name):
        print(f"    ✅ {method_name}: Available")
    else:
        print(f"    ❌ {method_name}: MISSING")
        missing_methods.append(method_name)

if missing_methods:
    print(f"  ❌ Missing methods: {missing_methods}")
    sys.exit(1)
else:
    print("  ✅ All supervisor methods available")

# Summary
print("\n" + "=" * 80)
print("PROGRESSIVE DEPLOYMENT TEST - SUMMARY")
print("=" * 80)
print("✅ [1/5] Configuration: PASSED (supervisor_enabled=true)")
print("✅ [2/5] Import: PASSED")
print("✅ [3/5] Initialization: PASSED")
print("✅ [4/5] Phase Flow: PASSED (9 phases will execute)")
print("✅ [5/5] Methods: PASSED (all 6 methods available)")
print("=" * 80)
print("✅ PROGRESSIVE DEPLOYMENT VALIDATED")
print("=" * 80)
print("\nExpected Behavior (Phase 2 - Progressive Mode):")
print("  - 9 phases execute (6 LLM + 3 Supervisor)")
print("  - Phase 1.5: Supervisor selects agents (mock)")
print("  - Phase 1.6: Agents execute in parallel (mock)")
print("  - Phase 6.5: Results synthesized")
print("  - Execution time: 44-62s (estimated)")
print("  - Confidence: >0.75 (with agent data)")
print("\nNext Steps:")
print("1. Restart backend with new config")
print("2. Test with real query (optional)")
print("3. Monitor 9-phase execution")
print("4. Prepare for Phase 3 (real agents)")
print("\nStatus: ✅ READY FOR PHASE 2 (Progressive Mode)")
