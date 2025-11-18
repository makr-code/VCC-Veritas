# Test: Frontend Conversation History Display
# Prüft ob der Gesprächskontext auch im echten Frontend angezeigt wird

import json
import time

import requests

print("🧪 Frontend Conversation History Display Test\n")
print("=" * 80)

# Backend URL
BASE_URL = "http://127.0.0.1:5000"

# 1. Health Check
print("\n1️⃣ Backend Health Check...")
try:
    health = requests.get(f"{BASE_URL}/health", timeout=5)
    print(f"✅ Backend: {health.json().get('status')}")
except Exception as e:
    print(f"❌ Backend nicht erreichbar: {e}")
    exit(1)

# 2. Sende Query OHNE conversation_history
print("\n2️⃣ Test 1: Query OHNE Conversation History")
print("-" * 80)

query_without_history = {
    "query": "Wie funktioniert das Baugenehmigungsverfahren in München?",
    "session_id": "test_no_history",
    "enable_streaming": True,
    "enable_intermediate_results": True,
    "enable_llm_thinking": True,
}

response = requests.post(f"{BASE_URL}/v2/query/stream", json=query_without_history, stream=True, timeout=60)

print("📡 Warte auf SSE Events...")
final_response_without_history = None

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
                    final_response_without_history = final_data.get("response_text", "")
                    print(f"✅ Antwort empfangen: {len(final_response_without_history)} Zeichen")
                    break
            except:
                pass

# 3. Sende Query MIT conversation_history
print("\n3️⃣ Test 2: Query MIT Conversation History")
print("-" * 80)

conversation_history = [
    {"role": "user", "content": "Wie funktioniert das Baugenehmigungsverfahren in München?"},
    {
        "role": "assistant",
        "content": "Das Baugenehmigungsverfahren in München umfasst mehrere Schritte: 1. Bauantrag stellen, 2. Prüfung durch Bauamt, 3. Genehmigung oder Ablehnung.",
    },
    {"role": "user", "content": "Welche Unterlagen benötige ich dafür?"},
]

query_with_history = {
    "query": "Welche Unterlagen benötige ich dafür?",
    "session_id": "test_with_history",
    "enable_streaming": True,
    "enable_intermediate_results": True,
    "enable_llm_thinking": True,
    "conversation_history": conversation_history,
}

print(f"📚 Sende Query mit {len(conversation_history)} Nachrichten Kontext...")

response = requests.post(f"{BASE_URL}/v2/query/stream", json=query_with_history, stream=True, timeout=60)

print("📡 Warte auf SSE Events...")
final_response_with_history = None

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
                    final_response_with_history = final_data.get("response_text", "")
                    print(f"✅ Antwort empfangen: {len(final_response_with_history)} Zeichen")
                    break
            except:
                pass

# 4. Vergleiche Antworten
print("\n" + "=" * 80)
print("📊 VERGLEICH DER ANTWORTEN")
print("=" * 80)

print("\n🔹 Antwort OHNE Conversation History:")
print("-" * 80)
if final_response_without_history:
    preview = final_response_without_history[:500]
    print(preview)
    if len(final_response_without_history) > 500:
        print(f"\n... ({len(final_response_without_history) - 500} weitere Zeichen)")

    has_context_section_1 = "**Gesprächskontext**" in final_response_without_history
    print(f"\n   Gesprächskontext-Abschnitt: {'✅ JA' if has_context_section_1 else '❌ NEIN'}")

print("\n🔹 Antwort MIT Conversation History:")
print("-" * 80)
if final_response_with_history:
    preview = final_response_with_history[:500]
    print(preview)
    if len(final_response_with_history) > 500:
        print(f"\n... ({len(final_response_with_history) - 500} weitere Zeichen)")

    has_context_section_2 = "**Gesprächskontext**" in final_response_with_history
    print(f"\n   Gesprächskontext-Abschnitt: {'✅ JA' if has_context_section_2 else '❌ NEIN'}")

# 5. Finale Bewertung
print("\n" + "=" * 80)
print("🎯 TEST-ERGEBNIS")
print("=" * 80)

if final_response_with_history and has_context_section_2:
    print("✅ ERFOLGREICH!")
    print("   - Conversation History wird korrekt verarbeitet")
    print("   - Gesprächskontext-Abschnitt wird in Antwort eingefügt")
    print("   - Frontend sollte den Kontext anzeigen")

    # Extrahiere Kontext-Abschnitt
    if "**Gesprächskontext**" in final_response_with_history:
        start = final_response_with_history.find("**Gesprächskontext**")
        end = final_response_with_history.find("\n\n**", start + 5)
        if end == -1:
            end = start + 300
        context_section = final_response_with_history[start:end]
        print("\n   📝 Kontext-Abschnitt:")
        print("   " + "─" * 76)
        for line in context_section.split("\n"):
            print(f"   {line}")
        print("   " + "─" * 76)
elif final_response_with_history and not has_context_section_2:
    print("⚠️  TEILWEISE ERFOLGREICH")
    print("   - Antwort wurde empfangen")
    print("   - ABER: Gesprächskontext-Abschnitt fehlt!")
    print("   - Problem möglicherweise in _synthesize_final_response()")
else:
    print("❌ FEHLGESCHLAGEN")
    print("   - Keine Antwort empfangen")

print("\n" + "=" * 80)
