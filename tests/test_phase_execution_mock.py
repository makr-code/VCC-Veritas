"""
Test: Single Phase Execution (Mock Mode - ohne Ollama)
"""

import sys
sys.path.insert(0, '.')

import asyncio
import json
from backend.services.scientific_phase_executor import ScientificPhaseExecutor, PhaseExecutionContext

async def test_phase_execution():
    print("\n" + "="*60)
    print("SINGLE PHASE EXECUTION TEST (Mock Mode)")
    print("="*60)
    
    # Initialize executor (Mock mode - ohne Ollama)
    print("\n[1] Initialize ScientificPhaseExecutor...")
    executor = ScientificPhaseExecutor(
        config_dir="config",
        method_id="default_method",
        ollama_client=None  # Mock mode
    )
    print("✅ Executor initialized (Mock mode)")
    
    # Create execution context
    print("\n[2] Create PhaseExecutionContext...")
    context = PhaseExecutionContext(
        user_query="Brauche ich eine Baugenehmigung für einen Carport in Baden-Württemberg?",
        rag_results={
            "semantic": [
                {
                    "source": "LBO BW § 50 Abs. 1",
                    "source_type": "gesetz",
                    "content": "Verfahrensfreie Vorhaben: Gebäude ohne Aufenthaltsräume, Toiletten oder Feuerstätten mit bis zu 30 m² Grundfläche...",
                    "confidence": 0.98,
                    "relevance": 0.95
                },
                {
                    "source": "VGH Baden-Württemberg, Urteil vom 15.03.2023",
                    "source_type": "rechtsprechung",
                    "content": "Carports unter 30 m² sind grundsätzlich verfahrensfrei, sofern keine Abstandsflächenverletzung vorliegt.",
                    "confidence": 0.90,
                    "relevance": 0.88
                },
                {
                    "source": "Merkblatt Bauaufsicht BW (Stand 2024)",
                    "source_type": "merkblatt",
                    "content": "Checkliste Carport: Fläche < 30 m², Abstand Grundstücksgrenze ≥ 2,5m, nicht in Denkmalschutzgebiet...",
                    "confidence": 0.72,
                    "relevance": 0.85
                }
            ],
            "graph": []
        }
    )
    print("✅ Context created")
    print(f"   User Query: {context.user_query}")
    print(f"   RAG Results: {len(context.rag_results['semantic'])} semantic sources")
    
    # Execute Phase 1: Hypothesis
    print("\n[3] Execute Phase 1 (Hypothesis)...")
    result = await executor.execute_phase("hypothesis", context)
    
    print(f"\n{'='*60}")
    print("PHASE 1 RESULT")
    print(f"{'='*60}")
    print(f"Status:           {result.status}")
    print(f"Confidence:       {result.confidence:.2f}")
    print(f"Execution Time:   {result.execution_time_ms:.0f} ms")
    print(f"Retry Count:      {result.retry_count}")
    print(f"Validation Errors: {len(result.validation_errors)}")
    
    if result.validation_errors:
        print("\nValidation Errors:")
        for err in result.validation_errors:
            print(f"  ❌ {err}")
    
    print(f"\n{'='*60}")
    print("OUTPUT (JSON)")
    print(f"{'='*60}")
    print(json.dumps(result.output, indent=2, ensure_ascii=False))
    
    print(f"\n{'='*60}")
    print("RAW LLM OUTPUT")
    print(f"{'='*60}")
    print(result.raw_llm_output)
    
    print("\n✅ TEST ABGESCHLOSSEN\n")
    return result

if __name__ == "__main__":
    asyncio.run(test_phase_execution())
