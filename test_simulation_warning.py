# Test: Simulation Warning in Response
# Prüft ob die neue Demo-Modus Warnung in Antworten erscheint

import json

import requests

print("🧪 Simulation Warning Test\n")
print("=" * 80)

BASE_URL = "http://127.0.0.1:5000"

# Health Check
print("\n1️⃣ Backend Health Check...")
try:
    health = requests.get(f"{BASE_URL}/health", timeout=5)
    print(f"✅ Backend: {health.json().get('status')}")
except Exception as e:
    print(f"❌ Backend nicht erreichbar: {e}")
    exit(1)

# Sende Query
print("\n2️⃣ Sende Test-Query...")
query = {
    "query": "Wie beantrage ich eine Baugenehmigung in München?",
    "session_id": "test_simulation_warning",
    "enable_streaming": True,
    "enable_intermediate_results": True,
    "enable_llm_thinking": True,
}

response = requests.post(f"{BASE_URL}/v2/query/stream", json=query, stream=True, timeout=60)

print("📡 Warte auf SSE Events...")
final_response = None

for line in response.iter_lines():
    if line:
        line = line.decode("utf-8")
        if line.startswith("data: "):
            data_str = line[6:]
            if data_str.strip() == "[DONE]":
                break
            try:
                event = json.loads(data_str)
                if event.get("type") == "stream_complete":
                    final_data = event.get("data", {}).get("final_result", {})
                    final_response = final_data.get("response_text", "")
                    metadata = final_data.get("processing_metadata", {})
                    print(f"✅ Antwort empfangen: {len(final_response)} Zeichen")
                    print(f"📊 Metadata: has_simulation={metadata.get('has_simulation')}")
                    break
            except:
                pass

# Analysiere Antwort
print("\n" + "=" * 80)
print("📄 FINALE ANTWORT (Auszug):")
print("=" * 80)

if final_response:
    # Zeige ersten Teil
    print(final_response[:800])

    if len(final_response) > 800:
        print(f"\n... ({len(final_response) - 800} weitere Zeichen)")

    print("\n" + "=" * 80)
    print("🔍 PRÜFUNG: Simulation-Warnung")
    print("=" * 80)

    # Prüfe auf Demo-Modus Warnung
    has_demo_warning = "DEMO-MODUS" in final_response or "⚠️" in final_response
    has_simulation_text = "simuliert" in final_response.lower() or "simulation" in final_response.lower()
    has_uds3_warning = "UDS3" in final_response and ("nicht verfügbar" in final_response or "not available" in final_response)

    print(f"\n   Demo-Modus Warnung gefunden: {'✅ JA' if has_demo_warning else '❌ NEIN'}")
    print(f"   'Simuliert' Text gefunden: {'✅ JA' if has_simulation_text else '❌ NEIN'}")
    print(f"   UDS3 Warnung gefunden: {'✅ JA' if has_uds3_warning else '❌ NEIN'}")

    # Extrahiere Warnung falls vorhanden
    if "⚠️" in final_response:
        # Finde Warnung-Abschnitt
        warning_start = final_response.find("⚠️")
        warning_section = final_response[warning_start : warning_start + 500]

        print(f"\n   📝 Warnung-Abschnitt gefunden:")
        print("   " + "-" * 76)
        for line in warning_section.split("\n")[:10]:
            print(f"   {line}")
        print("   " + "-" * 76)

    print("\n" + "=" * 80)
    print("🎯 ERGEBNIS")
    print("=" * 80)

    if has_demo_warning and has_simulation_text:
        print("✅ ERFOLGREICH!")
        print("   - Simulation-Warnung ist in der Antwort enthalten")
        print("   - User wird über Demo-Modus informiert")
        print("   - Transparenz hergestellt")
    elif has_simulation_text:
        print("⚠️  TEILWEISE ERFOLGREICH")
        print("   - Simulation erwähnt, aber ohne klare Demo-Warnung")
    else:
        print("❌ WARNUNG FEHLT")
        print("   - Keine Simulation-Warnung gefunden")
        print("   - User wird NICHT informiert über Demo-Daten")
else:
    print("❌ Keine Antwort empfangen")

print("\n" + "=" * 80)
