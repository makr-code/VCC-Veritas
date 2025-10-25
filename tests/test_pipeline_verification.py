#!/usr/bin/env python3
"""
VOLLSTÄNDIGER PIPELINE VERIFIKATIONS-TEST
==========================================

Testet die Intelligent Pipeline Integration im Streaming-Endpoint:
1. Backend Health Check
2. Streaming Query mit realer Frage
3. Progress Events überwachen
4. Agent Count verifizieren (8+ erwartet)
5. Confidence Score prüfen (>0.85 erwartet)
6. Response Quality bewerten
7. Processing Time messen
"""
import requests
import json
import time
from datetime import datetime

print("=" * 80)
print("VERITAS INTELLIGENT PIPELINE - VOLLSTÄNDIGER VERIFIKATIONS-TEST")
print("=" * 80)
print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)

# Testdaten
TEST_QUERIES = [
    {
        "query": "Welche Baugenehmigung brauche ich für ein Einfamilienhaus in München?",
        "expected_agents": 8,
        "expected_confidence": 0.85
    },
    {
        "query": "Welche Umweltauflagen gelten für den Bau einer Windkraftanlage?",
        "expected_agents": 8,
        "expected_confidence": 0.85
    }
]

results = []

for test_idx, test_data in enumerate(TEST_QUERIES, 1):
    print(f"\n{'=' * 80}")
    print(f"TEST {test_idx}/{len(TEST_QUERIES)}: {test_data['query'][:60]}...")
    print("=" * 80)
    
    test_result = {
        "query": test_data["query"],
        "success": False,
        "agent_count": 0,
        "confidence": 0.0,
        "processing_time": 0.0,
        "answer_length": 0,
        "stages": [],
        "errors": []
    }
    
    # 1. Backend Health Check
    print("\n[1/7] Backend Health Check...")
    try:
        response = requests.get("http://localhost:5000/health", timeout=5)
        health = response.json()
        
        print(f"  ✓ Backend Status: {response.status_code}")
        print(f"  ✓ Pipeline Available: {health.get('intelligent_pipeline_available')}")
        print(f"  ✓ Ollama Available: {health.get('ollama_available')}")
        print(f"  ✓ UDS3 Available: {health.get('uds3_available', 'N/A')}")
        
        if not health.get('intelligent_pipeline_available'):
            print("  ✗ ERROR: Intelligent Pipeline nicht verfügbar!")
            test_result["errors"].append("Pipeline not available")
            continue
            
    except Exception as e:
        print(f"  ✗ ERROR: Backend nicht erreichbar: {e}")
        test_result["errors"].append(f"Backend unreachable: {e}")
        continue
    
    # 2. Streaming Query starten
    print("\n[2/7] Starte Streaming Query...")
    query_data = {
        "query": test_data["query"],
        "enable_intermediate_results": True,
        "enable_reflection": True
    }
    
    try:
        start_time = time.time()
        
        response = requests.post(
            "http://localhost:5000/v2/query/stream",
            json=query_data,
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"  ✗ HTTP {response.status_code}: {response.text}")
            test_result["errors"].append(f"HTTP {response.status_code}")
            continue
        
        result = response.json()
        session_id = result.get("session_id")
        
        if not session_id:
            print(f"  ✗ Keine Session ID: {result}")
            test_result["errors"].append("No session ID")
            continue
        
        print(f"  ✓ Session ID: {session_id}")
        print(f"  ✓ Stream URL: {result.get('stream_url')}")
        
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        test_result["errors"].append(f"Query failed: {e}")
        continue
    
    # 3. Progress Events überwachen
    print("\n[3/7] Überwache Progress Events...")
    print("  " + "-" * 76)
    
    agent_count = 0
    agents_seen = set()
    stages_seen = []
    last_stage = None
    final_answer = ""
    max_confidence = 0.0
    stream_complete = False
    
    for i in range(120):  # Max 2 Minuten
        try:
            progress_response = requests.get(
                f"http://localhost:5000/progress/{session_id}",
                headers={"Accept": "text/event-stream"},
                stream=True,
                timeout=2
            )
            
            for line in progress_response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]
                        try:
                            event = json.loads(data_str)
                            event_type = event.get('type')
                            
                            # Stage Changes
                            if event_type == 'stage_start':
                                stage = event.get('stage')
                                if stage != last_stage:
                                    stages_seen.append(stage)
                                    print(f"  📍 STAGE: {stage}")
                                    last_stage = stage
                            
                            # Agent Events
                            elif event_type == 'AGENT_START' or event_type == 'agent_start':
                                agent_name = event.get('agent_name', 'unknown')
                                agents_seen.add(agent_name)
                                print(f"    → {agent_name}")
                            
                            elif event_type == 'AGENT_COMPLETE' or event_type == 'agent_complete':
                                # Parse agent name from message if not in event
                                agent_name = event.get('agent_name', 'unknown')
                                if agent_name == 'unknown':
                                    # Try to parse from message: "✅ Geo-Kontext Agent abgeschlossen"
                                    message = event.get('message', '')
                                    if 'Geo-Kontext' in message:
                                        agent_name = 'geo_context'
                                    elif 'Dokument-Retrieval' in message:
                                        agent_name = 'document_retrieval'
                                    elif 'Rechts-Framework' in message:
                                        agent_name = 'legal_framework'
                                    elif 'Umwelt' in message:
                                        agent_name = 'environmental'
                                    elif 'Verkehr' in message:
                                        agent_name = 'traffic'
                                    elif 'Finanz' in message:
                                        agent_name = 'financial'
                                
                                agents_seen.add(agent_name)
                                agent_count += 1
                                
                                # Confidence aus message parsen: "(Confidence: 0.82)"
                                message = event.get('message', '')
                                confidence = 0.0
                                if '(Confidence:' in message or '(Conf:' in message:
                                    import re
                                    match = re.search(r'\(Conf(?:idence)?:\s*([\d.]+)\)', message)
                                    if match:
                                        confidence = float(match.group(1))
                                
                                max_confidence = max(max_confidence, confidence)
                                print(f"    ✓ {agent_name} (Conf: {confidence:.2f})")
                            
                            # Stream Complete
                            elif event_type == 'STREAM_COMPLETE' or event_type == 'stage_complete':
                                final_answer = event.get('answer', '')
                                stream_complete = True
                                
                                end_time = time.time()
                                processing_time = end_time - start_time
                                
                                test_result["agent_count"] = agent_count
                                test_result["confidence"] = max_confidence
                                test_result["processing_time"] = processing_time
                                test_result["answer_length"] = len(final_answer)
                                test_result["stages"] = stages_seen
                                test_result["success"] = True
                                
                                print(f"\n  " + "=" * 76)
                                print(f"  ✅ STREAM COMPLETE")
                                print(f"  " + "=" * 76)
                                break
                        
                        except json.JSONDecodeError:
                            pass
            
            if stream_complete:
                break
                
            time.sleep(0.1)
        
        except requests.exceptions.RequestException:
            time.sleep(0.5)
    
    if not stream_complete:
        print(f"\n  ⏱️ Timeout nach 120 Sekunden")
        test_result["errors"].append("Timeout after 120s")
        continue
    
    # 4. Agent Count verifizieren
    print(f"\n[4/7] Agent Count Verifikation")
    print(f"  Agents gesehen: {len(agents_seen)}")
    print(f"  Agents komplett: {agent_count}")
    print(f"  Erwartet: >= {test_data['expected_agents']}")
    
    if agent_count >= test_data['expected_agents']:
        print(f"  ✅ PASS: {agent_count} >= {test_data['expected_agents']}")
    else:
        print(f"  ⚠️ WARNING: Nur {agent_count} Agents (erwartet: {test_data['expected_agents']})")
        test_result["errors"].append(f"Low agent count: {agent_count}")
    
    print(f"\n  Agent-Liste: {', '.join(sorted(agents_seen))}")
    
    # 5. Confidence Score prüfen
    print(f"\n[5/7] Confidence Score Prüfung")
    print(f"  Max Confidence: {max_confidence:.3f}")
    print(f"  Erwartet: >= {test_data['expected_confidence']:.2f}")
    
    if max_confidence >= test_data['expected_confidence']:
        print(f"  ✅ PASS: {max_confidence:.3f} >= {test_data['expected_confidence']}")
    else:
        print(f"  ⚠️ WARNING: Niedrige Confidence {max_confidence:.3f}")
        test_result["errors"].append(f"Low confidence: {max_confidence}")
    
    # 6. Response Quality bewerten
    print(f"\n[6/7] Response Quality Bewertung")
    print(f"  Antwort-Länge: {len(final_answer)} Zeichen")
    print(f"  Stages durchlaufen: {len(stages_seen)}")
    print(f"  Stages: {' → '.join(stages_seen)}")
    
    # Qualitäts-Checks
    quality_score = 0
    
    if len(final_answer) > 200:
        print(f"  ✓ Ausreichende Länge (>200 Zeichen)")
        quality_score += 1
    else:
        print(f"  ✗ Antwort zu kurz (<200 Zeichen)")
    
    if "Baugenehmigung" in final_answer or "Umwelt" in final_answer or "München" in final_answer:
        print(f"  ✓ Relevante Keywords gefunden")
        quality_score += 1
    else:
        print(f"  ✗ Keine relevanten Keywords")
    
    if len(stages_seen) >= 3:
        print(f"  ✓ Mehrere Stages durchlaufen")
        quality_score += 1
    else:
        print(f"  ✗ Wenige Stages")
    
    print(f"\n  Quality Score: {quality_score}/3")
    
    # 7. Processing Time messen
    print(f"\n[7/7] Processing Time Analyse")
    print(f"  Gesamt-Zeit: {processing_time:.2f}s")
    
    if processing_time < 30:
        print(f"  ✅ Schnell (<30s)")
    elif processing_time < 60:
        print(f"  ⚠️ Akzeptabel (<60s)")
    else:
        print(f"  ⚠️ Langsam (>60s)")
    
    # Antwort-Preview
    print(f"\n{'─' * 80}")
    print(f"ANTWORT-PREVIEW ({len(final_answer)} Zeichen):")
    print(f"{'─' * 80}")
    print(final_answer[:500] + ("..." if len(final_answer) > 500 else ""))
    print(f"{'─' * 80}")
    
    results.append(test_result)

# ===== ZUSAMMENFASSUNG =====
print(f"\n{'=' * 80}")
print("TEST-ZUSAMMENFASSUNG")
print("=" * 80)

total_tests = len(TEST_QUERIES)
passed_tests = sum(1 for r in results if r["success"] and not r["errors"])
failed_tests = total_tests - passed_tests

print(f"\nTests Gesamt: {total_tests}")
print(f"Tests Passed: {passed_tests}")
print(f"Tests Failed: {failed_tests}")
print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")

print(f"\n{'─' * 80}")
print("DETAIL-ERGEBNISSE:")
print("─" * 80)

for idx, result in enumerate(results, 1):
    status = "✅ PASS" if result["success"] and not result["errors"] else "❌ FAIL"
    print(f"\nTest {idx}: {status}")
    print(f"  Query: {result['query'][:60]}...")
    print(f"  Agents: {result['agent_count']}")
    print(f"  Confidence: {result['confidence']:.3f}")
    print(f"  Time: {result['processing_time']:.2f}s")
    print(f"  Answer: {result['answer_length']} chars")
    
    if result["errors"]:
        print(f"  Errors: {', '.join(result['errors'])}")

print(f"\n{'=' * 80}")

# FINALE BEWERTUNG
if passed_tests == total_tests:
    print("🎉 ALLE TESTS ERFOLGREICH! INTELLIGENT PIPELINE LÄUFT PERFEKT!")
    exit(0)
elif passed_tests > 0:
    print("⚠️ TEILWEISE ERFOLGREICH - Weitere Untersuchung empfohlen")
    exit(1)
else:
    print("❌ ALLE TESTS FEHLGESCHLAGEN - Pipeline-Problem!")
    exit(2)
