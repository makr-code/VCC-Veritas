"""
Test: UnifiedOrchestratorV7 - Streaming Query Processing
"""

import sys
sys.path.insert(0, '.')

import asyncio
from backend.orchestration.unified_orchestrator_v7 import UnifiedOrchestratorV7

async def test_streaming():
    print("\n" + "="*80)
    print("UNIFIED ORCHESTRATOR V7.0 - STREAMING TEST")
    print("="*80)
    
    # Initialize orchestrator (Mock mode)
    print("\n[1] Initialize UnifiedOrchestratorV7...")
    orchestrator = UnifiedOrchestratorV7(
        config_dir="config",
        method_id="default_method",
        ollama_client=None,  # Mock mode
        rag_service=None,  # Mock RAG
        enable_streaming=True
    )
    print("✅ Orchestrator initialized (Mock mode)")
    print(f"   Method: {orchestrator.method_id}")
    print(f"   Streaming: {orchestrator.enable_streaming}")
    
    # Test Query
    query = "Brauche ich eine Baugenehmigung für einen Carport in Baden-Württemberg?"
    print(f"\n[2] Processing Query (Streaming)...")
    print(f"   Query: {query}")
    print("\n" + "-"*80)
    
    # Collect events
    events = []
    async for event in orchestrator.process_query_stream(query):
        events.append(event)
        
        # Pretty print event
        event_type = event.type
        timestamp = event.timestamp
        
        if event_type == 'progress':
            progress = event.data.get('progress', 0.0)
            stage = event.data.get('stage', 'unknown')
            message = event.data.get('message', '')
            print(f"📊 PROGRESS  [{progress:4.0%}] {stage:20s} {message}")
        
        elif event_type == 'processing_step':
            step_id = event.data.get('step_id', 'unknown')
            status = event.data.get('status', 'unknown')
            results_count = event.data.get('results_count', '')
            emoji = "▶️" if status == 'started' else "✅"
            print(f"{emoji} STEP      [{status:10s}] {step_id:30s} {results_count}")
        
        elif event_type == 'phase_complete':
            phase_id = event.data.get('phase_id', 'unknown')
            phase_status = event.data.get('status', 'unknown')
            confidence = event.data.get('confidence', 0.0)
            exec_time = event.data.get('execution_time_ms', 0.0)
            print(f"✨ PHASE     [Phase {phase_id:15s}] status={phase_status}, confidence={confidence:.2f}, time={exec_time:.0f}ms")
        
        elif event_type == 'final_result':
            print(f"\n🎯 FINAL RESULT:")
            final_answer = event.data.get('final_answer', '')
            confidence = event.data.get('confidence', 0.0)
            exec_time_total = event.data.get('execution_time_ms', 0.0)
            print(f"   Answer: {final_answer}")
            print(f"   Confidence: {confidence:.2f}")
            print(f"   Total Time: {exec_time_total:.0f}ms")
        
        elif event_type == 'error':
            error_msg = event.data.get('error', 'Unknown error')
            stage = event.data.get('stage', 'unknown')
            print(f"❌ ERROR     [{stage}] {error_msg}")
    
    print("-"*80)
    print(f"\n[3] Streaming Complete")
    print(f"   Total Events: {len(events)}")
    print(f"   Event Types: {set(e.type for e in events)}")
    
    # Event breakdown
    print(f"\n[4] Event Breakdown:")
    for event_type in ['progress', 'processing_step', 'phase_complete', 'final_result', 'error']:
        count = len([e for e in events if e.type == event_type])
        print(f"   {event_type:20s}: {count:2d}")
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80 + "\n")

if __name__ == "__main__":
    asyncio.run(test_streaming())
