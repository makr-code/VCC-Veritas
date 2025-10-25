#!/usr/bin/env python3
"""
DEBUG: SSE Event Stream Inspector
Schaut sich die RAW Events an um zu verstehen was gesendet wird
"""
import requests
import time

print("=" * 80)
print("SSE EVENT STREAM INSPECTOR")
print("=" * 80)

# 1. Query starten
print("\n1. Starte Query...")
response = requests.post(
    "http://localhost:5000/v2/query/stream",
    json={"query": "Test Frage", "enable_intermediate_results": True},
    timeout=5
)

result = response.json()
session_id = result["session_id"]
print(f"Session ID: {session_id}")

# 2. Stream beobachten
print("\n2. Beobachte Stream...")
print("-" * 80)

event_count = 0
start_time = time.time()

try:
    response = requests.get(
        f"http://localhost:5000/progress/{session_id}",
        headers={"Accept": "text/event-stream"},
        stream=True,
        timeout=30
    )
    
    for line in response.iter_lines():
        if line:
            line_str = line.decode('utf-8')
            event_count += 1
            elapsed = time.time() - start_time
            
            print(f"[{elapsed:6.2f}s] Event #{event_count:3d}: {line_str[:120]}")
            
            if event_count >= 50:  # Max 50 Events zeigen
                print("\n... (mehr als 50 Events, stoppe)")
                break

except Exception as e:
    print(f"\nStream Error: {e}")

print(f"\n" + "=" * 80)
print(f"Total Events: {event_count}")
print(f"Total Time: {time.time() - start_time:.2f}s")
print("=" * 80)
