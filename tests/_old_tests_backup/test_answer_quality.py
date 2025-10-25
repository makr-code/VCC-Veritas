#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check Final Answer Quality
"""
import requests
import json
import time

query = "Welche Baugenehmigung brauche ich fur ein Einfamilienhaus in Munchen?"

print("Starte Query...")
resp = requests.post(
    "http://localhost:5000/v2/query/stream",
    json={"query": query}
).json()

session_id = resp["session_id"]
print(f"Session: {session_id}\n")

# Wait for completion
time.sleep(30)

# Get final state
print("Hole finale Antwort...")
try:
    r = requests.get(
        f"http://localhost:5000/progress/{session_id}",
        headers={"Accept": "text/event-stream"},
        stream=True,
        timeout=2
    )
    
    answer = None
    for line in r.iter_lines():
        if line:
            try:
                event = json.loads(line.decode('utf-8')[6:])
                if event.get('type') == 'stage_complete' and event.get('stage') == 'completed':
                    answer = event.get('answer') or event.get('message')
                    break
            except:
                pass
    
    if answer:
        print("\n" + "="*80)
        print("FINALE ANTWORT:")
        print("="*80)
        print(answer)
        print("="*80)
        print(f"\nLange: {len(answer)} Zeichen")
        
        # Quality checks
        quality = 0
        if len(answer) > 200:
            print("[OK] Ausreichend lang")
            quality += 1
        if "Baugenehmigung" in answer or "Baurecht" in answer or "München" in answer or "Munchen" in answer:
            print("[OK] Relevante Keywords")
            quality += 1
        if not ("Simulation" in answer or "Mock" in answer or "Demo" in answer):
            print("[OK] Keine Mock-Warnung")
            quality += 1
        
        print(f"\nQuality Score: {quality}/3")
        
        if quality >= 2:
            print("\n[PASS] Gute Antwort-Qualitat!")
            exit(0)
    else:
        print("[FAIL] Keine Antwort erhalten")
except Exception as e:
    print(f"Error: {e}")

exit(1)
