#!/usr/bin/env python3
"""
MULTI-MODEL CITATION TEST
=========================
Testet verschiedene Modelle auf IEEE-Citation-Fähigkeit

Hypothese: codellama ignoriert [N] Citations, aber andere Modelle nicht
"""

import re
import time

import requests

BACKEND_URL = "http://localhost:5000"
QUESTION = "Was regelt § 58 LBO BW?"

# Teste diese Modelle
TEST_MODELS = [
    "llama3:latest",  # 4.3GB - General Purpose
    "mixtral:latest",  # 24.6GB - Large, sollte gut sein
    "gemma3:latest",  # 3.1GB - Google
    "phi3:latest",  # 2.0GB - Microsoft
    "codellama:latest",  # Baseline
]


def test_model(model_name: str):
    """Testet ein Modell auf Citation-Fähigkeit"""
    print(f"\n{'='*80}")
    print(f"🤖 TESTE: {model_name}")
    print(f"{'='*80}")

    payload = {"question": QUESTION, "mode": "intelligent", "model": model_name, "temperature": 0.7, "max_tokens": 800}

    start_time = time.time()
    response = requests.post(f"{BACKEND_URL}/ask", json=payload, timeout=90)
    duration = time.time() - start_time

    if response.status_code != 200:
        print(f"❌ Error: HTTP {response.status_code}")
        return None

    data = response.json()
    answer = data.get("answer", "")

    # Analyse
    citations = re.findall(r"\[(\d+)\]", answer)
    has_followups = "💡" in answer or "Vorschläge:" in answer
    has_structure = "**" in answer or "###" in answer

    print(f"⏱️  Dauer: {duration:.1f}s")
    print(f"📝 Antwort: {len(answer)} Zeichen")
    print(f"📊 Struktur: {'✅' if has_structure else '❌'}")
    print(f"🔢 [N] Zitationen: {len(set(citations))} {'✅' if citations else '❌'}")
    if citations:
        print(f"   → Zitate: {sorted(set(citations))}")
    print(f"💡 Follow-ups: {'✅' if has_followups else '❌'}")

    # Zeige ersten Teil der Antwort
    print(f"\n📄 Antwort (erste 300 Zeichen):")
    print("-" * 80)
    print(answer[:300] + ("..." if len(answer) > 300 else ""))
    print("-" * 80)

    return {
        "model": model_name,
        "duration": duration,
        "answer_length": len(answer),
        "citations_count": len(set(citations)),
        "has_followups": has_followups,
        "has_structure": has_structure,
        "score": len(set(citations)) + (1 if has_followups else 0) + (1 if has_structure else 0),
    }


def main():
    print("=" * 80)
    print("🧪 MULTI-MODEL CITATION TEST")
    print("=" * 80)
    print(f"\nFrage: {QUESTION}")
    print(f"Modelle: {len(TEST_MODELS)}")
    print(f"Erwartung: ≥3 [N] Zitationen + Follow-ups")

    results = []
    for model in TEST_MODELS:
        result = test_model(model)
        if result:
            results.append(result)
        time.sleep(2)  # Pause zwischen Modellen

    # Ranking
    print(f"\n{'='*80}")
    print("🏆 MODELL-RANKING (Nach Citation-Fähigkeit)")
    print(f"{'='*80}\n")

    results.sort(key=lambda x: x["score"], reverse=True)

    for i, result in enumerate(results, 1):
        print(f"{i}. {result['model']}")
        print(
            f"   Score: {result['score']}/5 | Zitationen: {result['citations_count']} | "
            f"Follow-ups: {'✅' if result['has_followups'] else '❌'} | "
            f"Struktur: {'✅' if result['has_structure'] else '❌'}"
        )
        print()

    # Beste Empfehlung
    if results and results[0]["citations_count"] > 0:
        best = results[0]
        print(f"💡 EMPFEHLUNG: Nutze '{best['model']}' für bessere Zitat-Qualität")
        print(f"   → {best['citations_count']} Zitationen vs. 0 bei anderen")
    else:
        print(f"⚠️  PROBLEM: ALLE Modelle versagen bei [N] Zitationen!")
        print(f"   → Problem liegt NICHT am Modell")
        print(f"   → Problem liegt am PROMPT-DELIVERY oder LLM-Training")
        print(f"\n   Nächste Schritte:")
        print(f"   1. Prüfe Backend-Logs: Wird Enhanced Prompt wirklich gesendet?")
        print(f"   2. Few-Shot Examples hinzufügen (zeige 2-3 Beispiel-Antworten MIT [N])")
        print(f"   3. Constraint-based Generation (Force [N] nach jedem Satz)")


if __name__ == "__main__":
    main()
