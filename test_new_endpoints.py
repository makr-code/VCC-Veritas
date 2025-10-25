import requests

print("Test 1: Dokumente (alt endpoint)")
try:
    resp = requests.get("http://localhost:5001/statistik/overview")
    print(f"✅ Status: {resp.status_code}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\nTest 2: Dokumente (neu)")
try:
    resp = requests.get("http://localhost:5001/dokumente/search?limit=3")
    print(f"Status: {resp.status_code}")
    if resp.status_code != 200:
        print(f"Error: {resp.text}")
    else:
        print(f"✅ Erfolg: {resp.json()['count']} Dokumente")
except Exception as e:
    print(f"❌ Error: {e}")

print("\nTest 3: Ansprechpartner")
try:
    resp = requests.get("http://localhost:5001/ansprechpartner/search?limit=3")
    print(f"Status: {resp.status_code}")
    if resp.status_code != 200:
        print(f"Error: {resp.text}")
    else:
        print(f"✅ Erfolg: {resp.json()['count']} Ansprechpartner")
except Exception as e:
    print(f"❌ Error: {e}")

print("\nTest 4: Wartung")
try:
    resp = requests.get("http://localhost:5001/wartung/search?limit=3")
    print(f"Status: {resp.status_code}")
    if resp.status_code != 200:
        print(f"Error: {resp.text}")
    else:
        print(f"✅ Erfolg: {resp.json()['count']} Wartungen")
except Exception as e:
    print(f"❌ Error: {e}")

print("\nTest 5: Messreihen")
try:
    resp = requests.get("http://localhost:5001/messreihen/search?limit=3")
    print(f"Status: {resp.status_code}")
    if resp.status_code != 200:
        print(f"Error: {resp.text}")
    else:
        print(f"✅ Erfolg: {resp.json()['count']} Messreihen")
except Exception as e:
    print(f"❌ Error: {e}")

print("\nTest 6: Behörden")
try:
    resp = requests.get("http://localhost:5001/behoerden/search?limit=3")
    print(f"Status: {resp.status_code}")
    if resp.status_code != 200:
        print(f"Error: {resp.text}")
    else:
        print(f"✅ Erfolg: {resp.json()['count']} Kontakte")
except Exception as e:
    print(f"❌ Error: {e}")

print("\nTest 7: Compliance")
try:
    resp = requests.get("http://localhost:5001/compliance/search?limit=3")
    print(f"Status: {resp.status_code}")
    if resp.status_code != 200:
        print(f"Error: {resp.text}")
    else:
        print(f"✅ Erfolg: {resp.json()['count']} Historie-Einträge")
except Exception as e:
    print(f"❌ Error: {e}")
