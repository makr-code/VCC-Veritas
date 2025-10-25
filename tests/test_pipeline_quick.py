#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PIPELINE QUICK TEST - ASCII Only
"""
import requests
import json
import time
import re

print("="*80)
print("VERITAS PIPELINE QUICK TEST")
print("="*80)

# Test Query
query = "Welche Baugenehmigung brauche ich fur ein Einfamilienhaus?"

print("\n1. Backend Check...")
health = requests.get("http://localhost:5000/health").json()
print(f"   Pipeline: {health.get('intelligent_pipeline_available')}")
print(f"   Ollama: {health.get('ollama_available')}")

print("\n2. Start Query...")
resp = requests.post(
    "http://localhost:5000/v2/query/stream",
    json={"query": query, "enable_intermediate_results": True}
).json()

session_id = resp["session_id"]
print(f"   Session: {session_id}")

print("\n3. Monitor Events...")
print("-"*80)

agents = set()
stages = []
last_stage = None
start_time = time.time()

for i in range(60):  # 60 seconds max
    try:
        r = requests.get(
            f"http://localhost:5000/progress/{session_id}",
            headers={"Accept": "text/event-stream"},
            stream=True,
            timeout=2
        )
        
        for line in r.iter_lines():
            if line and line.decode('utf-8').startswith('data: '):
                try:
                    event = json.loads(line.decode('utf-8')[6:])
                    event_type = event.get('type')
                    
                    if event_type == 'stage_start':
                        stage = event.get('stage')
                        if stage != last_stage:
                            stages.append(stage)
                            print(f"   [{time.time()-start_time:5.1f}s] Stage: {stage}")
                            last_stage = stage
                    
                    elif event_type == 'agent_complete':
                        msg = event.get('message', '')
                        # Parse agent name
                        if 'Geo-Kontext' in msg:
                            agents.add('geo_context')
                        elif 'Dokument' in msg:
                            agents.add('document_retrieval')
                        elif 'Rechts' in msg:
                            agents.add('legal_framework')
                        elif 'Umwelt' in msg:
                            agents.add('environmental')
                        elif 'Verkehr' in msg:
                            agents.add('traffic')
                        elif 'Finanz' in msg:
                            agents.add('financial')
                        
                        # Parse confidence
                        conf_match = re.search(r'Conf.*?:\s*([\d.]+)', msg)
                        conf = float(conf_match.group(1)) if conf_match else 0.0
                        
                        print(f"   [{time.time()-start_time:5.1f}s] Agent done (conf={conf:.2f})")
                    
                    elif event_type == 'stage_complete' and event.get('stage') == 'completed':
                        print(f"\n   [{time.time()-start_time:5.1f}s] COMPLETE!")
                        break
                
                except:
                    pass
        
        if event.get('stage') == 'completed':
            break
            
        time.sleep(0.2)
    except:
        time.sleep(0.5)

end_time = time.time()
duration = end_time - start_time

print("\n" + "="*80)
print("RESULTS:")
print("="*80)
print(f"Agents: {len(agents)} - {', '.join(sorted(agents))}")
print(f"Stages: {len(stages)} - {' -> '.join(stages)}")
print(f"Time: {duration:.1f}s")

if len(agents) >= 3 and len(stages) >= 5:
    print("\n[PASS] Pipeline is working!")
    exit(0)
else:
    print("\n[FAIL] Not enough agents or stages")
    exit(1)
