"""
Test Rich Media JSON Responses
===============================

Testet ob LLM Rich Media (Maps, Charts, Tables) generieren kann
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import json
import re

from backend.agents.veritas_json_citation_formatter import JSONCitationFormatter
from backend.agents.veritas_ollama_client import OllamaRequest, VeritasOllamaClient
from backend.agents.veritas_rich_media_schema import get_rich_media_prompt


async def test_rich_media():
    """
    Test Rich Media Capabilities
    """

    print("=" * 80)
    print("🎨 TEST: RICH MEDIA JSON RESPONSES")
    print("=" * 80)
    print("\nTeste ob LLM Rich Media generieren kann:")
    print("  📊 Charts (Statistiken)")
    print("  🗺️  Maps (Geolokationen)")
    print("  📋 Tables (Vergleiche)")
    print("  📄 Documents (Downloads)\n")

    test_cases = [
        {
            "name": "Baukosten-Vergleich (Table Expected)",
            "query": "Vergleiche die Baugenehmigungskosten in Berlin, München und Stuttgart",
            "sources": ["[1] Gebührenordnung Berlin", "[2] Gebührenordnung München", "[3] Gebührenordnung Stuttgart"],
            "context": "Kosten variieren je nach Stadt: Berlin 250€, München 350€, Stuttgart 200€ Grundgebühr",
            "expected_media": ["tables"],
        },
        {
            "name": "Luftqualität (Map + Chart Expected)",
            "query": "Wie ist die Luftqualität in Berlin? Zeige Messstationen.",
            "sources": ["[1] Berliner Luftgütemessnetz", "[2] Umweltbundesamt"],
            "context": "Messwerte: Alexanderplatz PM10 18μg/m³, Charlottenburg 15μg/m³, Neukölln 22μg/m³",
            "expected_media": ["maps", "charts"],
        },
        {
            "name": "Bauantrag-Unterlagen (Documents + Image Expected)",
            "query": "Welche Unterlagen brauche ich für einen Bauantrag?",
            "sources": ["[1] Bauordnungsamt Merkblatt", "[2] LBO BW § 58"],
            "context": "Erforderlich: Formular, Lageplan, Bauzeichnungen, Statik",
            "expected_media": ["documents", "images"],
        },
    ]

    ollama_client = VeritasOllamaClient()
    results = []

    for i, test in enumerate(test_cases, 1):
        print(f"\n{'='*80}")
        print(f"🧪 TEST {i}/3: {test['name']}")
        print(f"{'='*80}")
        print(f"Query: {test['query']}")
        print(f"Expected Media: {', '.join(test['expected_media'])}")

        # Build Rich Media prompt
        rich_prompts = get_rich_media_prompt()

        system_prompt = rich_prompts["system"]
        user_prompt = rich_prompts["user_template"].format(
            query=test["query"],
            source_list="\n".join(test["sources"]),
            rag_context=test["context"],
            agent_results="Agent: " + test["context"],
        )

        full_prompt = f"{system_prompt}\n\n{user_prompt}"

        print(f"\n⏳ Sende an Ollama (Prompt: {len(full_prompt)} chars)...")

        # Send to Ollama
        request = OllamaRequest(
            model="llama3.2:latest",
            prompt=full_prompt,
            temperature=0.6,  # Etwas höher für kreative Media-Generierung
            max_tokens=3000,  # Mehr Tokens für Rich Media
        )

        response = await ollama_client.generate_response(request)
        raw_output = response.response

        print(f"\n✅ Antwort erhalten ({len(raw_output)} chars)")

        # Parse JSON
        try:
            # Extract JSON
            json_start = raw_output.find("{")
            json_end = raw_output.rfind("}") + 1
            json_str = raw_output[json_start:json_end]

            # Fix common escapes
            json_str = json_str.replace("\\_", "_")

            data = json.loads(json_str)

            print("✅ JSON parsed successfully")
            print(f"\n📋 JSON Keys: {list(data.keys())}")

            # Check for media types
            media_found = []
            for media_type in ["images", "maps", "charts", "tables", "documents", "videos"]:
                if media_type in data and data[media_type]:
                    media_found.append(media_type)
                    print(f"   ✅ {media_type}: {len(data[media_type])} items")

            if not media_found:
                print("   ⚠️  No rich media generated")

            # Format to IEEE
            formatted, success = JSONCitationFormatter.format_with_fallback(raw_output)

            # Count citations
            citations = re.findall(r"\[(\d+)\]", formatted)

            print(f"\n📊 ANALYSIS:")
            print(f"   Citations: {len(citations)}")
            print(f"   Media Types: {', '.join(media_found) if media_found else 'None'}")
            print(f"   Expected: {', '.join(test['expected_media'])}")

            match = all(media in media_found for media in test["expected_media"])
            print(f"   Match: {'✅' if match else '❌'}")

            # Show formatted output
            print(f"\n📄 FORMATIERTE ANTWORT:")
            print("-" * 80)
            print(formatted[:1000])  # First 1000 chars
            if len(formatted) > 1000:
                print("...\n(gekürzt)")
            print("-" * 80)

            results.append(
                {
                    "name": test["name"],
                    "success": True,
                    "media_found": media_found,
                    "media_expected": test["expected_media"],
                    "match": match,
                    "citations": len(citations),
                }
            )

        except Exception as e:
            print(f"❌ Error: {e}")
            print(f"\nRaw output preview:")
            print(raw_output[:300])

            results.append(
                {
                    "name": test["name"],
                    "success": False,
                    "media_found": [],
                    "media_expected": test["expected_media"],
                    "match": False,
                    "citations": 0,
                }
            )

    # Summary
    print("\n" + "=" * 80)
    print("📊 ZUSAMMENFASSUNG")
    print("=" * 80)

    total = len(results)
    success = sum(1 for r in results if r["success"])
    matches = sum(1 for r in results if r["match"])
    avg_citations = sum(r["citations"] for r in results) / total if total > 0 else 0

    print(f"\n✅ JSON Parsing: {success}/{total} ({success/total*100:.0f}%)")
    print(f"✅ Media Matching: {matches}/{total} ({matches/total*100:.0f}%)")
    print(f"📊 Avg Citations: {avg_citations:.1f}")

    print("\n📋 Details:")
    for r in results:
        status = "✅" if r["match"] else ("⚠️" if r["success"] else "❌")
        print(f"{status} {r['name']}")
        if r["media_found"]:
            print(f"     Generated: {', '.join(r['media_found'])}")
        print(f"     Expected: {', '.join(r['media_expected'])}")

    print("\n" + "=" * 80)
    print("🎯 FAZIT")
    print("=" * 80)

    if matches == total:
        print("\n✅ PERFEKT!")
        print("   LLM generiert alle erwarteten Rich Media Typen!")
        print("   → Rich Media System voll funktionsfähig!")
    elif matches >= total * 0.6:
        print("\n✅ GUT!")
        print(f"   {matches}/{total} Tests mit korrekten Media-Typen")
        print("   → System funktioniert, Prompt-Tuning kann helfen")
    else:
        print("\n⚠️ TEILWEISE")
        print(f"   {matches}/{total} Tests erfolgreich")
        print("   → LLM braucht klarere Anweisungen für Rich Media")

    print("\n💡 NEXT STEPS:")
    print("   1. Backend neu starten mit Rich Media Support")
    print("   2. Frontend erweitern für Map/Chart Rendering")
    print("   3. API-Endpoint für Media-Assets erstellen")
    print("   4. Golden Dataset v2 mit Rich Media Tests")


if __name__ == "__main__":
    asyncio.run(test_rich_media())
