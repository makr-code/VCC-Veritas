"""
FINAL TEST: JSON Citation Approach - End-to-End
================================================

Demonstriert dass der JSON-Approach perfekt funktioniert:
1. LLM generiert strukturiertes JSON
2. JSONCitationFormatter fügt [1],[2],[3] ein
3. Ergebnis: IEEE-konforme Antworten mit Citations!
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.agents.veritas_json_citation_formatter import JSONCitationFormatter
from backend.agents.veritas_ollama_client import VeritasOllamaClient, OllamaRequest
import asyncio
import re

async def final_test():
    """
    End-to-End Test mit 3 Fragen
    """
    
    print("="*80)
    print("🎯 FINAL TEST: JSON CITATION APPROACH")
    print("="*80)
    print("\nBeweis dass der Approach funktioniert:")
    print("  1. LLM generiert JSON")
    print("  2. Formatter fügt IEEE Citations [N] ein")
    print("  3. Ergebnis: Perfekte Citations!\n")
    
    test_questions = [
        {
            "query": "Was regelt § 58 LBO BW?",
            "sources": [
                "[1] LBO BW Gesetzestext § 58",
                "[2] Bauordnungsamt Leitfaden 2024"
            ],
            "context": "§ 58 LBO BW behandelt Bauanträge und Genehmigungsverfahren"
        },
        {
            "query": "Welche Kosten entstehen bei einer Baugenehmigung?",
            "sources": [
                "[1] Gebührenordnung BauO BW",
                "[2] Kostenrechner Stadt Stuttgart",
                "[3] Verwaltungsportal Baden-Württemberg"
            ],
            "context": "Kosten richten sich nach Gebührenordnung, ca. 0,5% der Bausumme"
        },
        {
            "query": "Wie ist die Luftqualität in Berlin?",
            "sources": [
                "[1] Berliner Luftgütemessnetz",
                "[2] Umweltbundesamt Bericht 2024"
            ],
            "context": "Aktuelle Messwerte zeigen Feinstaub 18 μg/m³, NO₂ 22 μg/m³"
        }
    ]
    
    ollama_client = VeritasOllamaClient()
    results = []
    
    for i, test in enumerate(test_questions, 1):
        print(f"\n{'='*80}")
        print(f"📝 TEST {i}/3: {test['query']}")
        print(f"{'='*80}")
        
        # Build JSON prompt
        json_prompts = JSONCitationFormatter.get_json_prompt_template()
        
        system_prompt = json_prompts["system"]
        user_prompt = json_prompts["user_template"].format(
            query=test["query"],
            source_list="\n".join(test["sources"]),
            rag_context=test["context"],
            agent_results="BuildingAgent: " + test["context"]
        )
        
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        
        print(f"\n⏳ Sende an Ollama (Prompt: {len(full_prompt)} chars)...")
        
        # Send to Ollama
        request = OllamaRequest(
            model="llama3.2:latest",
            prompt=full_prompt,
            temperature=0.5,
            max_tokens=2000
        )
        
        response = await ollama_client.generate_response(request)
        raw_output = response.response
        
        # Check if JSON
        is_json = raw_output.strip().startswith('{')
        
        print(f"\n✅ Antwort erhalten ({len(raw_output)} chars)")
        print(f"   JSON generated: {'✅' if is_json else '❌'}")
        
        if is_json:
            # Format to IEEE
            formatted, success = JSONCitationFormatter.format_with_fallback(raw_output)
            
            # Count citations
            citations = re.findall(r'\[(\d+)\]', formatted)
            citation_count = len(citations)
            unique_citations = len(set(citations))
            
            print(f"   Formatter success: {'✅' if success else '❌'}")
            print(f"   Citations [N]: {citation_count} total, {unique_citations} unique")
            
            # Show formatted answer
            print(f"\n📄 FORMATIERTE ANTWORT:")
            print("-"*80)
            print(formatted)
            print("-"*80)
            
            results.append({
                "question": test["query"],
                "json_generated": is_json,
                "formatted": success,
                "citations": citation_count,
                "unique_citations": unique_citations
            })
        else:
            print("   ❌ LLM generierte kein JSON!")
            print(f"\n   Raw output: {raw_output[:200]}...")
            results.append({
                "question": test["query"],
                "json_generated": False,
                "formatted": False,
                "citations": 0,
                "unique_citations": 0
            })
    
    # Summary
    print("\n" + "="*80)
    print("📊 ZUSAMMENFASSUNG")
    print("="*80)
    
    total_tests = len(results)
    json_success = sum(1 for r in results if r["json_generated"])
    format_success = sum(1 for r in results if r["formatted"])
    avg_citations = sum(r["citations"] for r in results) / total_tests if total_tests > 0 else 0
    
    print(f"\n✅ JSON Generated: {json_success}/{total_tests} ({json_success/total_tests*100:.0f}%)")
    print(f"✅ Formatting Success: {format_success}/{total_tests} ({format_success/total_tests*100:.0f}%)")
    print(f"📊 Avg Citations: {avg_citations:.1f} pro Antwort")
    
    print("\n" + "="*80)
    print("🎯 FAZIT")
    print("="*80)
    
    if json_success == total_tests and format_success == total_tests and avg_citations >= 2:
        print("\n✅ EXZELLENT!")
        print("   JSON Citation Approach funktioniert PERFEKT!")
        print("   LLM generiert strukturiertes JSON")
        print("   Formatter fügt IEEE Citations [1],[2],[3] ein")
        print("   → Bereit für Integration ins Backend!")
    elif json_success >= total_tests * 0.7:
        print("\n✅ GUT!")
        print(f"   {json_success}/{total_tests} Tests erfolgreich")
        print("   Approach ist grundsätzlich funktionsfähig")
        print("   → Prompt-Tuning könnte Erfolgsrate verbessern")
    else:
        print("\n⚠️ TEILWEISE ERFOLGREICH")
        print(f"   {json_success}/{total_tests} Tests mit JSON")
        print("   LLM hat Schwierigkeiten mit JSON-Format")
        print("   → Alternative Ansätze erwägen")
    
    print("\n" + "="*80)
    print("📋 NÄCHSTE SCHRITTE")
    print("="*80)
    print("\n1. Backend neu starten (alle Python-Prozesse beenden)")
    print("2. Python-Cache löschen:")
    print("   find backend -name '*.pyc' -delete")
    print("   find backend -name '__pycache__' -type d -exec rm -rf {} +")
    print("3. Backend starten: python start_backend.py")
    print("4. Test: cd tests && python test_json_citations.py")
    print("5. Erwartung: [1],[2],[3] Citations in allen Antworten! 🎉")

if __name__ == "__main__":
    asyncio.run(final_test())
