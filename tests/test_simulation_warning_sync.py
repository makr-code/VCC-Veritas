# Test: Direkter Synchroner Test der Simulation-Warnung
# Nutzt synchronen Endpoint statt Streaming

import requests

print("🧪 Direkter Simulation Warning Test (Synchron)\n")
print("=" * 80)

BASE_URL = "http://127.0.0.1:5000"

# Sende synchrone Query
print("\n📤 Sende synchrone Query...")
query = {"query": "Wie beantrage ich eine Baugenehmigung in München?", "enable_streaming": False}  # Synchron!

try:
    response = requests.post(f"{BASE_URL}/v2/query", json=query, timeout=60)

    if response.status_code == 200:
        data = response.json()

        print("✅ Antwort empfangen")
        print("\n" + "=" * 80)
        print("📄 ANTWORT:")
        print("=" * 80)

        # Extrahiere Antwort-Text
        answer = data.get("answer", "")
        metadata = data.get("metadata", {})

        # Zeige Antwort
        print(answer[:1000])
        if len(answer) > 1000:
            print(f"\n... ({len(answer) - 1000} weitere Zeichen)")

        # Prüfe Metadata
        print("\n" + "=" * 80)
        print("📊 METADATA:")
        print("=" * 80)
        print(f"  has_simulation: {metadata.get('has_simulation', 'N/A')}")
        print(f"  simulated_agents: {metadata.get('simulated_agents', [])}")
        print(f"  simulation_count: {metadata.get('simulation_count', 0)}")

        # Prüfe Worker Results
        worker_results = data.get("worker_results", {})
        simulated_workers = [name for name, result in worker_results.items() if result.get("is_simulation", False)]

        print(f"\n  Worker Results: {len(worker_results)} gesamt")
        print(f"  Simulierte Workers: {len(simulated_workers)}")
        if simulated_workers:
            print(f"  Namen: {', '.join(simulated_workers)}")

        # Prüfe auf Warnung im Text
        print("\n" + "=" * 80)
        print("🔍 WARNUNG-ANALYSE:")
        print("=" * 80)

        has_demo_warning = "DEMO-MODUS" in answer
        has_simulation = "simuliert" in answer.lower()
        has_uds3_warning = "UDS3" in answer and "nicht verfügbar" in answer

        print(f"  ⚠️  DEMO-MODUS gefunden: {'✅ JA' if has_demo_warning else '❌ NEIN'}")
        print(f"  📝 'simuliert' erwähnt: {'✅ JA' if has_simulation else '❌ NEIN'}")
        print(f"  🔌 UDS3 Warnung: {'✅ JA' if has_uds3_warning else '❌ NEIN'}")

        # Extrahiere Warnung
        if has_demo_warning:
            demo_start = answer.find("⚠️")
            demo_section = answer[demo_start : demo_start + 600]
            print("\n  📋 Warnung-Abschnitt:")
            print("  " + "-" * 76)
            for line in demo_section.split("\n")[:15]:
                print(f"  {line}")
            print("  " + "-" * 76)

        print("\n" + "=" * 80)
        print("🎯 ERGEBNIS:")
        print("=" * 80)

        if has_demo_warning:
            print("✅ ERFOLGREICH!")
            print("   - Demo-Modus Warnung wird angezeigt")
            print("   - User wird über simulierte Daten informiert")
            print("   - Transparenz gewährleistet")
        else:
            print("⚠️  WARNUNG FEHLT IM TEXT")
            print("   - Metadata enthält Simulation-Info")
            print("   - Aber keine sichtbare User-Warnung")
    else:
        print(f"❌ Fehler: HTTP {response.status_code}")
        print(response.text)

except Exception as e:
    print(f"❌ Fehler: {e}")
    import traceback

    traceback.print_exc()

print("\n" + "=" * 80)
