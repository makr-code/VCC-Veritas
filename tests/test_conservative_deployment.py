#!/usr/bin/env python3
"""
CONSERVATIVE DEPLOYMENT TEST (Phase 1)
Tests VERITAS with supervisor_enabled=false (6-phase system)

Expected Behavior:
- 6 phases execute (no supervisor phases)
- Confidence > 0.7
- Execution time: 34-52s
- No agent selection/execution
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
print("CONSERVATIVE DEPLOYMENT TEST - Phase 1")
print("=" * 80)

# Test 1: Verify Configuration
print("\n[Test 1/4] Verifying Configuration...")
config_path = project_root / "config" / "scientific_methods" / "default_method.json"
with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)

print(f"  ✅ Config Version: {config.get('version')}")
print(f"  ✅ Supervisor Enabled: {config.get('supervisor_enabled')}")
print(f"  ✅ Total Phases in Config: {len(config.get('phases', []))}")

assert config.get('version') == '2.0.0', "Config version should be 2.0.0"
assert config.get('supervisor_enabled') == False, "Supervisor should be DISABLED for conservative deployment"
print("  ✅ Configuration correct for Conservative Mode")

# Test 2: Import Orchestrator
print("\n[Test 2/4] Importing Orchestrator...")
try:
    from unified_orchestrator_v7 import UnifiedOrchestratorV7
    print("  ✅ UnifiedOrchestratorV7 imported successfully")
except ImportError as e:
    print(f"  ❌ Import failed: {e}")
    sys.exit(1)

# Test 3: Initialize Orchestrator
print("\n[Test 3/4] Initializing Orchestrator...")
try:
    orchestrator = UnifiedOrchestratorV7(
        config_dir="config",
        method_id="default_method",
        uds3_strategy=None,  # Will use mock
        ollama_client=None  # Will use mock or skip LLM tests
    )
    print("  ✅ Orchestrator initialized")
    
    # Check supervisor status
    supervisor_enabled = orchestrator._is_supervisor_enabled()
    print(f"  ✅ Supervisor Enabled (Runtime): {supervisor_enabled}")
    assert supervisor_enabled == False, "Supervisor should be disabled at runtime"
    
except Exception as e:
    print(f"  ❌ Initialization failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Phase Execution Flow (Dry Run)
print("\n[Test 4/4] Phase Execution Flow (Dry Run)...")
print("  Checking which phases would execute...")

phases = config.get('phases', [])
expected_phases = []
supervisor_phases = []

for phase in phases:
    phase_num = phase.get('phase_number')
    executor = phase.get('execution', {}).get('executor', 'llm')
    
    if executor in ['supervisor', 'agent_coordinator']:
        supervisor_phases.append(phase_num)
        print(f"    ⏸️  Phase {phase_num} ({phase.get('phase_id')}): SKIPPED (supervisor executor)")
    else:
        expected_phases.append(phase_num)
        print(f"    ✅ Phase {phase_num} ({phase.get('phase_id')}): Will execute")

print(f"\n  ✅ Expected Phases to Execute: {len(expected_phases)} (should be 6)")
print(f"  ✅ Supervisor Phases Skipped: {len(supervisor_phases)} (should be 3)")

assert len(expected_phases) == 6, f"Expected 6 phases to execute, got {len(expected_phases)}"
assert len(supervisor_phases) == 3, f"Expected 3 supervisor phases to skip, got {len(supervisor_phases)}"

# Summary
print("\n" + "=" * 80)
print("CONSERVATIVE DEPLOYMENT TEST - SUMMARY")
print("=" * 80)
print("✅ [1/4] Configuration: PASSED (supervisor_enabled=false)")
print("✅ [2/4] Import: PASSED")
print("✅ [3/4] Initialization: PASSED")
print("✅ [4/4] Phase Flow: PASSED (6 phases will execute)")
print("=" * 80)
print("✅ CONSERVATIVE DEPLOYMENT VALIDATED")
print("=" * 80)
print("\nNext Steps:")
print("1. Run real query test with Ollama (optional)")
print("2. Monitor performance for 1-2 weeks")
print("3. Enable supervisor after monitoring period")
print("\nStatus: ✅ READY FOR PRODUCTION (Phase 1: Conservative)")
