"""
Test Script für ScientificPhaseExecutor - JSON Loading & Phase Execution
"""

import sys
sys.path.insert(0, '.')

from backend.services.scientific_phase_executor import ScientificPhaseExecutor, PhaseExecutionContext
import json

print("\n" + "="*60)
print("SCIENTIFIC PHASE EXECUTOR - TEST")
print("="*60)

# Test 1: Initialize Executor
print("\n[Test 1] Initialize ScientificPhaseExecutor...")
try:
    executor = ScientificPhaseExecutor(
        config_dir="config",
        method_id="default_method"  # Dateiname ist default_method.json (nicht default_scientific_method)
    )
    print("✅ ScientificPhaseExecutor erfolgreich initialisiert")
    print(f"   📋 Method ID: {executor.method_id}")
    print(f"   📁 Phasen geladen: {len(executor.method_config['phases'])}")
    print(f"   ✨ Scientific Foundation: {bool(executor.scientific_foundation)}")
except Exception as e:
    print(f"❌ Fehler: {e}")
    sys.exit(1)

# Test 2: List all phases
print("\n[Test 2] Liste aller Phasen:")
for idx, phase in enumerate(executor.method_config['phases'], 1):
    phase_id = phase['phase_id']
    model = phase['execution']['model']
    temp = phase['execution']['temperature']
    max_tokens = phase['execution']['max_tokens']
    print(f"   {idx}. {phase_id:15s} | Model: {model:10s} | Temp: {temp:.2f} | Tokens: {max_tokens}")

# Test 3: Load phase prompt
print("\n[Test 3] Lade Phase 1 Prompt (hypothesis)...")
try:
    prompt_config = executor._load_phase_prompt("hypothesis")
    print(f"✅ Phase prompt geladen: {prompt_config['phase_id']}")
    print(f"   📝 Instructions: {len(prompt_config.get('instructions', []))} steps")
    print(f"   📖 Examples: {len(prompt_config.get('example_outputs', []))}")
    print(f"   ⚠️  Common Mistakes: {len(prompt_config.get('common_mistakes', []))}")
except Exception as e:
    print(f"❌ Fehler: {e}")

# Test 4: Construct prompt
print("\n[Test 4] Konstruiere Prompt mit Mock-Daten...")
try:
    context = PhaseExecutionContext(
        user_query="Brauche ich eine Baugenehmigung für einen Carport in Baden-Württemberg?",
        rag_results={
            "semantic": [
                {
                    "source": "LBO BW § 50",
                    "content": "Verfahrensfreie Vorhaben: Gebäude bis 30m² Grundfläche ohne Aufenthaltsräume...",
                    "confidence": 0.98
                }
            ],
            "graph": []
        }
    )
    
    prompt = executor._construct_prompt("hypothesis", context)
    print(f"✅ Prompt konstruiert: {len(prompt)} Zeichen")
    print(f"\n--- PROMPT PREVIEW (erste 500 Zeichen) ---")
    print(prompt[:500])
    print("...\n")
except Exception as e:
    print(f"❌ Fehler: {e}")

# Test 5: Validate JSON schemas
print("\n[Test 5] Validiere Output Schemas...")
from jsonschema import Draft7Validator

for phase in executor.method_config['phases']:
    phase_id = phase['phase_id']
    schema = phase['output_schema']
    
    try:
        validator = Draft7Validator(schema)
        # Check if schema is valid
        validator.check_schema(schema)
        print(f"   ✅ {phase_id:15s} - Schema valid")
    except Exception as e:
        print(f"   ❌ {phase_id:15s} - Schema error: {e}")

print("\n" + "="*60)
print("TESTS ABGESCHLOSSEN")
print("="*60 + "\n")
