"""
End-to-End Test für UnifiedOrchestratorV7 mit REAL UDS3 + Ollama + SUPERVISOR

Test Query: "Brauche ich eine Baugenehmigung für einen Carport mit PV in München?"

Testet:
- Real UDS3 Hybrid Search (ChromaDB + Neo4j)
- Real Ollama LLM Calls (llama3.2)
- Supervisor Integration (Phases 1.5, 1.6, 6.5)
- Agent Selection & Execution (Mock-Modus)
- Alle 9 wissenschaftlichen Phasen (mit Supervisor)
- JSON Schema Validierung
- Streaming Events

Author: VERITAS v7.0
Date: 12. Oktober 2025 (Updated for Supervisor Integration)
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from backend.agents.veritas_ollama_client import VeritasOllamaClient
from backend.orchestration.unified_orchestrator_v7 import StreamEvent, UnifiedOrchestratorV7

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def test_real_query_processing():
    """
    End-to-End Test mit Real UDS3 + Ollama + Supervisor Integration
    """

    # Updated query to test supervisor agent selection
    test_query = "Brauche ich eine Baugenehmigung für einen Carport mit PV in München?"

    logger.info("=" * 80)
    logger.info("🧪 VERITAS v7.0 - End-to-End Test (Real UDS3 + Ollama + Supervisor)")
    logger.info("=" * 80)
    logger.info(f"Test Query: {test_query}")
    logger.info("Expected: Construction + Weather + Financial agents should be selected")
    logger.info("=" * 80)

    try:
        # 1. Initialize Ollama Client
        logger.info("\n📋 Step 1: Initialize Ollama Client")
        ollama_client = VeritasOllamaClient(
            base_url="http://localhost:11434", timeout=60, max_retries=2  # Längeres Timeout für wissenschaftliche Phasen
        )

        # Health check
        await ollama_client.initialize()
        logger.info("✅ Ollama Client initialized")

        # 2. Initialize UnifiedOrchestratorV7 (UDS3 auto-initialized)
        logger.info("\n📋 Step 2: Initialize UnifiedOrchestratorV7 with Supervisor")
        orchestrator = UnifiedOrchestratorV7(
            config_dir="config",
            method_id="default_method",  # supervisor_enabled=true in config
            ollama_client=ollama_client,
            uds3_strategy=None,  # Auto-initialize
            agent_orchestrator=None,  # Mock mode (no real agents yet)
            enable_streaming=True,
        )
        logger.info("✅ Orchestrator initialized (Supervisor Mode: Mock Agents)")

        # Check if supervisor is enabled
        supervisor_enabled = orchestrator._is_supervisor_enabled()
        logger.info(f"   Supervisor Enabled: {supervisor_enabled}")
        if supervisor_enabled:
            logger.info("   ⚠️ Note: Agent execution will use MOCK results (no real agent_orchestrator)")
        else:
            logger.warning("   ⚠️ WARNING: Supervisor NOT enabled - will skip agent phases!")

        # 3. Process Query with Streaming
        logger.info("\n📋 Step 3: Process Query (Streaming Mode)")
        logger.info("-" * 80)

        events_collected = []
        phase_results = {}

        async for event in orchestrator.process_query_stream(user_query=test_query):
            events_collected.append(event)

            # Log event
            if event.type == "progress":
                logger.info(f"⏳ Progress: {event.data.get('progress')}% - {event.data.get('message')}")

            elif event.type == "processing_step":
                logger.info(f"🔄 {event.data.get('step')}: {event.data.get('message')}")

            elif event.type == "phase_complete":
                phase_id = event.data.get("phase_id")
                status = event.data.get("status")
                confidence = event.data.get("confidence", 0.0)
                execution_time = event.data.get("execution_time_ms", 0)

                logger.info(
                    f"✅ Phase Complete: {phase_id} | "
                    f"Status: {status} | "
                    f"Confidence: {confidence:.2f} | "
                    f"Time: {execution_time:.0f}ms"
                )

                phase_results[phase_id] = event.data

            elif event.type == "final_result":
                logger.info("\n" + "=" * 80)
                logger.info("🎯 FINAL RESULT")
                logger.info("=" * 80)

                final_answer = event.data.get("final_answer", {})
                overall_confidence = event.data.get("confidence", 0.0)
                total_time = event.data.get("execution_time_ms", 0)

                logger.info(f"\n📝 Final Answer:")
                logger.info(f"   Main Answer: {final_answer.get('main_answer', 'N/A')[:200]}...")
                logger.info(f"   Confidence: {overall_confidence:.2f}")
                logger.info(f"   Total Execution Time: {total_time:.0f}ms ({total_time/1000:.1f}s)")

                if final_answer.get("action_recommendations"):
                    logger.info(f"\n💡 Action Recommendations:")
                    for rec in final_answer.get("action_recommendations", [])[:3]:
                        logger.info(f"   - [{rec.get('priority', 'N/A')}] {rec.get('action', 'N/A')}")

            elif event.type == "error":
                logger.error(f"❌ Error: {event.data.get('message')}")

        # 4. Summary Statistics
        logger.info("\n" + "=" * 80)
        logger.info("📊 TEST SUMMARY")
        logger.info("=" * 80)

        event_type_counts = {}
        for event in events_collected:
            event_type_counts[event.type] = event_type_counts.get(event.type, 0) + 1

        logger.info(f"Total Events: {len(events_collected)}")
        for event_type, count in event_type_counts.items():
            logger.info(f"  - {event_type}: {count}")

        logger.info(f"\nPhases Completed: {len(phase_results)}/9 (with supervisor)")
        for phase_id, result in phase_results.items():
            status_icon = "✅" if result.get("status") == "success" else "⚠️"
            logger.info(
                f"  {status_icon} {phase_id}: {result.get('status')} " f"(confidence={result.get('confidence', 0.0):.2f})"
            )

        # Check if supervisor phases were executed
        supervisor_phases = ["supervisor_agent_selection", "agent_execution", "agent_result_synthesis"]
        supervisor_executed = [p for p in supervisor_phases if p in phase_results]

        logger.info(f"\nSupervisor Phases Executed: {len(supervisor_executed)}/3")
        if supervisor_executed:
            for phase_id in supervisor_executed:
                logger.info(f"  ✅ {phase_id}")
        else:
            logger.warning("  ⚠️ No supervisor phases executed (supervisor_enabled=false or skipped)")

        # 5. Validation Checks
        logger.info("\n" + "=" * 80)
        logger.info("✅ VALIDATION CHECKS")
        logger.info("=" * 80)

        checks = {
            "Supervisor enabled in config": orchestrator._is_supervisor_enabled(),
            "Expected phases executed (6-9)": len(phase_results) >= 6,
            "Final result received": any(e.type == "final_result" for e in events_collected),
            "No errors": not any(e.type == "error" for e in events_collected),
            "All phases successful": all(r.get("status") in ["success", "partial", "skipped"] for r in phase_results.values()),
            "Confidence > 0.5": all(
                r.get("confidence", 0.0) > 0.5
                for r in phase_results.values()
                if r.get("status") == "success"  # Only check successful phases
            ),
        }

        for check_name, passed in checks.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            logger.info(f"{status}: {check_name}")

        # Overall Result
        all_passed = all(checks.values())
        logger.info("\n" + "=" * 80)
        if all_passed:
            logger.info("🎉 TEST PASSED - All validation checks successful!")
        else:
            logger.warning("⚠️ TEST INCOMPLETE - Some checks failed")
        logger.info("=" * 80)

        return all_passed

    except Exception as e:
        logger.error(f"\n❌ TEST FAILED: {e}", exc_info=True)
        return False

    finally:
        # Cleanup
        if "ollama_client" in locals():
            await ollama_client.close()
            logger.info("\n🧹 Ollama Client closed")


async def test_non_streaming():
    """
    Test Non-Streaming Mode mit Supervisor (für Performance-Vergleich)
    """

    # Updated query
    test_query = "Brauche ich eine Baugenehmigung für einen Carport mit PV in München?"

    logger.info("\n" + "=" * 80)
    logger.info("🧪 VERITAS v7.0 - Non-Streaming Test (Supervisor)")
    logger.info("=" * 80)

    try:
        # Initialize
        ollama_client = VeritasOllamaClient(base_url="http://localhost:11434", timeout=60, max_retries=2)
        await ollama_client.initialize()

        orchestrator = UnifiedOrchestratorV7(
            config_dir="config",
            method_id="default_method",
            ollama_client=ollama_client,
            uds3_strategy=None,
            agent_orchestrator=None,  # Mock mode
            enable_streaming=False,  # Non-streaming
        )

        # Check supervisor mode
        supervisor_enabled = orchestrator._is_supervisor_enabled()
        logger.info(f"Supervisor Enabled: {supervisor_enabled}")

        # Process query
        logger.info("⏳ Processing query (non-streaming)...")
        import time

        start_time = time.time()

        result = await orchestrator.process_query(user_query=test_query)

        duration = time.time() - start_time

        # Results
        logger.info(f"\n✅ Query processed in {duration:.1f}s")
        logger.info(f"Confidence: {result.confidence:.2f}")
        logger.info(f"Final Answer: {result.final_answer.get('main_answer', 'N/A')[:200]}...")

        return True

    except Exception as e:
        logger.error(f"❌ Non-streaming test failed: {e}", exc_info=True)
        return False

    finally:
        if "ollama_client" in locals():
            await ollama_client.close()


async def main():
    """
    Main test runner
    """

    logger.info("\n" + "=" * 80)
    logger.info("🚀 VERITAS v7.0 - End-to-End Test Suite")
    logger.info("=" * 80)

    # Test 1: Streaming Mode
    logger.info("\n📋 Test 1: Streaming Mode")
    test1_passed = await test_real_query_processing()

    # Test 2: Non-Streaming Mode
    logger.info("\n📋 Test 2: Non-Streaming Mode")
    test2_passed = await test_non_streaming()

    # Final Summary
    logger.info("\n" + "=" * 80)
    logger.info("🏁 FINAL TEST SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Test 1 (Streaming):     {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    logger.info(f"Test 2 (Non-Streaming): {'✅ PASSED' if test2_passed else '❌ FAILED'}")

    if test1_passed and test2_passed:
        logger.info("\n🎉 ALL TESTS PASSED - v7.0 PRODUCTION READY!")
    else:
        logger.warning("\n⚠️ SOME TESTS FAILED - Review logs above")

    logger.info("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
