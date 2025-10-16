#!/usr/bin/env python3
"""
Test-Skript für Dual-Prompt Streaming System - Brandenburg Edition
===================================================================
Testet Stage-Reflections mit Brandenburg-spezifischer Baugenehmigungsfrage

Usage: python test_dual_prompt_brandenburg.py
"""

import requests
import json
import time
from datetime import datetime

# Konfiguration
BACKEND_URL = "http://localhost:5000"
TEST_QUERY = "Wie beantrage ich eine Baugenehmigung für ein Einfamilienhaus in Brandenburg?"

def colorize(text, color_code):
    """Fügt ANSI-Farbcodes hinzu"""
    return f"\033[{color_code}m{text}\033[0m"

def print_separator(char="─", length=80):
    """Druckt Trennlinie"""
    print(char * length)

def test_streaming_with_reflections():
    """
    Testet Streaming-Endpoint mit Stage-Reflections für Brandenburg
    """
    print(colorize("\n🧪 DUAL-PROMPT STREAMING SYSTEM TEST - BRANDENBURG EDITION", "1;36"))
    print_separator("=")
    print(f"📝 Test-Query: {colorize(TEST_QUERY, '1;33')}")
    print(f"🌐 Backend: {BACKEND_URL}")
    print(f"⏰ Start: {datetime.now().strftime('%H:%M:%S')}\n")
    
    # 1. Initiate Streaming Query
    print(colorize("🚀 1. Initiiere Streaming-Query...", "1;32"))
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/v2/query/stream",
            json={
                "query": TEST_QUERY,
                "enable_llm_thinking": True,         # Aktiviert Stage-Reflections!
                "enable_intermediate_results": True,
                "enable_cancellation": True
            },
            timeout=10
        )
        
        if response.status_code != 200:
            print(colorize(f"❌ Fehler: {response.status_code}", "1;31"))
            print(response.text)
            return
        
        result = response.json()
        session_id = result.get('session_id')
        stream_url = result.get('stream_url')
        
        print(colorize(f"✅ Session gestartet: {session_id}", "1;32"))
        print(f"📡 Stream-URL: {stream_url}\n")
        
    except Exception as e:
        print(colorize(f"❌ Connection Error: {e}", "1;31"))
        return
    
    # 2. Monitor Progress Stream
    print(colorize("📊 2. Monitoring Progress-Stream (Brandenburg)...", "1;32"))
    print_separator()
    print()
    
    try:
        # SSE-Stream verbinden
        stream_response = requests.get(
            f"{BACKEND_URL}{stream_url}",
            stream=True,
            headers={'Accept': 'text/event-stream'},
            timeout=120
        )
        
        reflection_count = 0
        stage_count = 0
        thinking_count = 0
        reflections_by_stage = {}
        
        for line in stream_response.iter_lines(decode_unicode=True):
            if not line or not line.startswith('data: '):
                continue
            
            try:
                event_data = json.loads(line[6:])  # Entferne 'data: '
                event_type = event_data.get('type', '')
                stage = event_data.get('stage', '')
                message = event_data.get('message', '')
                
                timestamp = datetime.now().strftime("%H:%M:%S")
                
                # Stage-Updates
                if event_type == 'stage_update':
                    stage_count += 1
                    progress = event_data.get('progress', 0)
                    print(f"[{timestamp}] {colorize('📍', '1;34')} Stage: {colorize(stage.upper(), '1;34')} | Progress: {progress:.0f}%")
                
                # LLM-Thinking
                elif event_type == 'llm_thinking':
                    thinking_count += 1
                    thinking = event_data.get('llm_thinking', '')
                    print(f"[{timestamp}] {colorize('🧠', '1;36')} {thinking}")
                
                # 🆕 STAGE-REFLECTION
                elif event_type == 'stage_reflection':
                    reflection_count += 1
                    details = event_data.get('details', {})
                    
                    refl_stage = details.get('stage', 'unknown')
                    completion = details.get('completion_percent', 0)
                    status = details.get('fulfillment_status', 'unknown')
                    confidence = details.get('confidence', 0)
                    gaps = details.get('identified_gaps', [])
                    gathered = details.get('gathered_info', [])
                    actions = details.get('next_actions', [])
                    reasoning = details.get('llm_reasoning', '')
                    
                    # Speichere Reflection für Zusammenfassung
                    reflections_by_stage[refl_stage] = {
                        'completion': completion,
                        'status': status,
                        'confidence': confidence,
                        'gaps': gaps,
                        'gathered': gathered
                    }
                    
                    # Status-Emoji
                    status_emoji = {
                        "incomplete": "🔴",
                        "partial": "🟡",
                        "complete": "🟢"
                    }.get(status, "⚪")
                    
                    print()
                    print_separator("─")
                    print(colorize(f"{status_emoji} STAGE REFLECTION #{reflection_count}: {refl_stage.upper()}", "1;35"))
                    print_separator("─")
                    print(f"  Erfüllung: {colorize(f'{completion:.0f}%', '1;33')} | Status: {colorize(status, '1;33')} | Konfidenz: {colorize(f'{confidence:.2f}', '1;33')}")
                    
                    if gathered:
                        print(f"\n  {colorize('✅ Gesammelt:', '1;32')}")
                        for info in gathered[:5]:  # Zeige mehr Details
                            print(f"    • {info[:100]}{'...' if len(info) > 100 else ''}")
                    
                    if gaps:
                        print(f"\n  {colorize('⚠️ Lücken:', '1;33')}")
                        for gap in gaps[:5]:
                            print(f"    • {gap[:100]}{'...' if len(gap) > 100 else ''}")
                    
                    if actions:
                        print(f"\n  {colorize('🔜 Nächste Schritte:', '1;36')}")
                        for action in actions[:3]:
                            print(f"    • {action[:100]}{'...' if len(action) > 100 else ''}")
                    
                    if reasoning:
                        print(f"\n  {colorize('💭 LLM Reasoning:', '1;34')}")
                        print(f"    {reasoning[:300]}{'...' if len(reasoning) > 300 else ''}")
                    
                    print_separator("─")
                    print()
                
                # Intermediate Results
                elif event_type == 'intermediate_result':
                    agent = event_data.get('agent_type', 'unknown')
                    print(f"[{timestamp}] {colorize('🔄', '1;32')} Intermediate: {agent}")
                
                # Stream Complete
                elif event_type == 'stage_complete' and stage == 'completed':
                    print()
                    print_separator("=")
                    print(colorize("✅ STREAM ABGESCHLOSSEN", "1;32"))
                    print_separator("=")
                    
                    final_result = event_data.get('details', {}).get('final_result', {})
                    response_text = final_result.get('response_text', '')
                    sources = final_result.get('sources', [])
                    conf_score = final_result.get('confidence_score', 0)
                    
                    print(f"\n📊 Statistiken:")
                    print(f"  • Stage-Updates: {stage_count}")
                    print(f"  • LLM-Thinking-Steps: {thinking_count}")
                    print(f"  • {colorize(f'Stage-Reflections: {reflection_count}', '1;35')} {colorize('← MIT OLLAMA!', '1;33')}")
                    print(f"  • Quellen: {len(sources)}")
                    print(f"  • Finale Konfidenz: {conf_score:.2f}")
                    
                    # Reflection-Analyse
                    if reflections_by_stage:
                        print(f"\n🔍 Reflection-Analyse:")
                        for stage_name, refl in reflections_by_stage.items():
                            emoji = {"incomplete": "🔴", "partial": "🟡", "complete": "🟢"}.get(refl['status'], "⚪")
                            print(f"  {emoji} {stage_name.upper()}: {refl['completion']:.0f}% (Konfidenz: {refl['confidence']:.2f})")
                            if refl['gaps']:
                                print(f"      └─ {len(refl['gaps'])} Lücken identifiziert")
                    
                    if response_text:
                        print(f"\n📝 Finale Antwort (Auszug):")
                        print_separator("─")
                        print(response_text[:600])
                        if len(response_text) > 600:
                            print("...")
                        print_separator("─")
                    
                    break
                
                # Error
                elif event_type == 'error':
                    print(colorize(f"\n❌ Stream Error: {message}", "1;31"))
                    break
            
            except json.JSONDecodeError:
                continue
        
        print(f"\n⏰ Ende: {datetime.now().strftime('%H:%M:%S')}")
        
        # Zusammenfassung
        if reflection_count > 0:
            print(colorize(f"\n✅ SUCCESS! {reflection_count} Stage-Reflections empfangen!", "1;32"))
            print(colorize("   🎯 Dual-Prompt-System funktioniert mit Brandenburg-Query!", "1;32"))
            
            # Vergleiche mit erwarteten Stages
            expected_stages = {'hypothesis', 'agent_selection', 'retrieval', 'synthesis'}
            found_stages = set(reflections_by_stage.keys())
            missing_stages = expected_stages - found_stages
            
            if missing_stages:
                print(colorize(f"   ⚠️ Fehlende Stages: {', '.join(missing_stages)}", "1;33"))
            else:
                print(colorize("   🎉 Alle erwarteten Stages vorhanden!", "1;32"))
        else:
            print(colorize("\n⚠️ Keine Stage-Reflections empfangen.", "1;33"))
            print(colorize("   Prüfe Backend-Logs für Details", "1;33"))
    
    except Exception as e:
        print(colorize(f"\n❌ Stream Error: {e}", "1;31"))
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_streaming_with_reflections()
