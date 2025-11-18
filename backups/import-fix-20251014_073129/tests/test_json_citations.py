"""
Test JSON Citation Approach
============================

Testet ob LLM JSON generiert und wir es zu IEEE formatieren können.
"""

import json
import re

import requests

BACKEND_URL = "http://localhost:5000"


def test_json_citation_approach():
    """
    Test: JSON-strukturierte Antwort → IEEE-Formatierung
    """

    print("=" * 80)
    print("🧪 TEST: JSON CITATION APPROACH")
    print("=" * 80)

    question = "Was regelt § 58 LBO BW?"

    print(f"\n📝 Frage: {question}")
    print(f"\n⏳ Sende Query an Backend...")

    payload = {"question": question, "mode": "intelligent", "session_id": "test-json-citations"}

    try:
        response = requests.post(f"{BACKEND_URL}/ask", json=payload, timeout=60)

        if response.status_code == 200:
            data = response.json()
            answer = data.get("answer", "")

            print(f"\n✅ Antwort erhalten ({len(answer)} Zeichen)\n")

            # Zeige Antwort
            print("=" * 80)
            print("📄 ANTWORT:")
            print("=" * 80)
            print(answer)
            print("=" * 80)

            # Analysiere Antwort
            print("\n📊 CITATION ANALYSIS:")
            print("=" * 80)

            # Check for IEEE citations
            citations = re.findall(r"\[(\d+)\]", answer)
            print(f"\n✅ IEEE Citations [N] gefunden: {len(citations)}")
            if citations:
                print(f"   → {', '.join([f'[{c}]' for c in sorted(set(citations))])}")
            else:
                print("   ❌ KEINE Citations gefunden!")

            # Check for structure
            has_direct_answer = "**Direkte Antwort**" in answer or "**Direkte Antwort:**" in answer
            has_details = "**Details**" in answer or "**Details:**" in answer
            has_sources = "**Quellen**" in answer or "**Quellen:**" in answer
            has_follow_ups = "💡" in answer or "**Vorschläge**" in answer

            print(f"\n📋 STRUKTUR:")
            print(f"   {'✅' if has_direct_answer else '❌'} Direkte Antwort")
            print(f"   {'✅' if has_details else '❌'} Details")
            print(f"   {'✅' if has_sources else '❌'} Quellen")
            print(f"   {'✅' if has_follow_ups else '❌'} Follow-ups (💡)")

            # Check for legal references
            legal_refs = re.findall(r"§\s*\d+", answer)
            print(f"\n⚖️ Legal References (§): {len(legal_refs)}")
            if legal_refs:
                print(f"   → {', '.join(set(legal_refs))}")

            # Overall score
            print("\n" + "=" * 80)
            print("🎯 BEWERTUNG:")
            print("=" * 80)

            criteria_met = sum([len(citations) >= 2, has_direct_answer, has_details, has_sources, len(legal_refs) >= 1])

            print(f"\n   Zitationen [N]: {'✅' if len(citations) >= 2 else '❌'} ({len(citations)}/2+)")
            print(f"   Struktur vollständig: {'✅' if all([has_direct_answer, has_details, has_sources]) else '❌'}")
            print(f"   Legal Refs: {'✅' if len(legal_refs) >= 1 else '❌'} ({len(legal_refs)}/1+)")
            print(f"   Follow-ups: {'✅' if has_follow_ups else '❌'}")

            print(f"\n📊 GESAMT: {criteria_met}/5 Kriterien erfüllt ({criteria_met/5*100:.0f}%)")

            if criteria_met >= 4:
                print("\n✅ EXZELLENT - JSON Citation Approach funktioniert!")
            elif criteria_met >= 3:
                print("\n✅ GUT - Deutliche Verbesserung!")
            elif criteria_met >= 2:
                print("\n⚠️ BEFRIEDIGEND - Teilweise Verbesserung")
            else:
                print("\n❌ UNZUREICHEND - Approach funktioniert nicht")

            # Check if answer looks like JSON (debugging)
            if answer.strip().startswith("{"):
                print("\n⚠️ WARNUNG: Antwort sieht wie raw JSON aus (Formatter nicht ausgeführt?)")
                try:
                    parsed = json.loads(answer)
                    print(f"   → Valid JSON mit keys: {list(parsed.keys())}")
                except:
                    print("   → Ungültiges JSON")

        else:
            print(f"\n❌ Fehler: {response.status_code}")
            print(response.text)

    except Exception as e:
        print(f"\n❌ Exception: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_json_citation_approach()
