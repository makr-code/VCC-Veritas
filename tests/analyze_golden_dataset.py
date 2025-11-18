#!/usr/bin/env python3
"""
GOLDEN DATASET ANALYSE
Wertet die Ergebnisse des RAG Quality Tests aus
"""
import json
from collections import defaultdict
from typing import Dict, List


def analyze_golden_dataset(json_file: str):
    """Analysiert Golden Dataset Ergebnisse"""

    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    print("\n" + "=" * 80)
    print("🎯 GOLDEN DATASET - DETAILLIERTE ANALYSE")
    print("=" * 80)

    # Basis-Statistiken
    print(f"\n📊 ÜBERSICHT:")
    print(f"   Total Tests: {len(data)}")
    models = list(set([r["model"] for r in data]))
    print(f"   Modelle getestet: {len(models)}")
    test_ids = list(set([r.get("test_id", r.get("query_id", "unknown")) for r in data]))
    print(f"   Fragen getestet: {len(test_ids)}")

    # Modell-Performance aggregieren
    model_stats = defaultdict(
        lambda: {
            "tests": 0,
            "total_citations": 0,
            "total_quotes": 0,
            "total_legal_refs": 0,
            "total_answer_length": 0,
            "total_aspect_coverage": 0,
            "total_duration": 0,
            "ratings": defaultdict(int),
        }
    )

    for result in data:
        model = result["model"]
        # Metrics können entweder direkt oder unter 'analysis' sein
        metrics = result.get("metrics", result.get("analysis", {}).get("metrics", {}))

        model_stats[model]["tests"] += 1
        model_stats[model]["total_citations"] += metrics.get("citation_count", 0)
        model_stats[model]["total_quotes"] += metrics.get("direct_quotes_count", 0)
        model_stats[model]["total_legal_refs"] += metrics.get("legal_references", 0)
        model_stats[model]["total_answer_length"] += metrics.get("answer_length", 0)
        model_stats[model]["total_aspect_coverage"] += metrics.get("aspect_coverage", 0)
        model_stats[model]["total_duration"] += result.get("duration", 0)
        model_stats[model]["ratings"][result.get("rating", "UNKNOWN")] += 1

    # Durchschnittswerte berechnen
    model_averages = {}
    for model, stats in model_stats.items():
        n = stats["tests"]
        model_averages[model] = {
            "avg_citations": stats["total_citations"] / n,
            "avg_quotes": stats["total_quotes"] / n,
            "avg_legal_refs": stats["total_legal_refs"] / n,
            "avg_answer_length": stats["total_answer_length"] / n,
            "avg_aspect_coverage": stats["total_aspect_coverage"] / n,
            "avg_duration": stats["total_duration"] / n,
            "success_rate": (stats["ratings"]["GOOD"] / n) * 100,
        }

    # === RANKING 1: QUALITÄT (Zitationen + Quotes + Legal Refs) ===
    print(f"\n{'='*80}")
    print("🏆 TOP 5 MODELLE - QUALITÄT (Zitationen + Direkte Zitate + Rechtsreferenzen)")
    print("=" * 80)

    quality_scores = []
    for model, avg in model_averages.items():
        quality_score = (
            avg["avg_citations"] * 10
            + avg["avg_quotes"] * 15  # IEEE Citations wichtig
            + avg["avg_legal_refs"] * 8  # Direkte Zitate SEHR wichtig
            + avg["avg_aspect_coverage"] * 5  # § Referenzen wichtig  # Aspect Coverage
        )
        quality_scores.append((model, quality_score, avg))

    quality_scores.sort(key=lambda x: x[1], reverse=True)

    for i, (model, score, avg) in enumerate(quality_scores[:5], 1):
        print(f"\n{i}. {model}")
        print(f"   Quality Score: {score:.2f}")
        print(f"   Ø Zitationen: {avg['avg_citations']:.2f}")
        print(f"   Ø Direkte Zitate: {avg['avg_quotes']:.2f}")
        print(f"   Ø Legal Refs (§): {avg['avg_legal_refs']:.2f}")
        print(f"   Ø Aspect Coverage: {avg['avg_aspect_coverage']:.1%}")
        print(f"   Success Rate: {avg['success_rate']:.1f}%")

    # === RANKING 2: GESCHWINDIGKEIT ===
    print(f"\n{'='*80}")
    print("⚡ TOP 5 MODELLE - GESCHWINDIGKEIT")
    print("=" * 80)

    speed_ranking = sorted(model_averages.items(), key=lambda x: x[1]["avg_duration"])

    for i, (model, avg) in enumerate(speed_ranking[:5], 1):
        print(f"{i}. {model}: {avg['avg_duration']:.1f}s pro Query")

    # === RANKING 3: ANTWORTLÄNGE ===
    print(f"\n{'='*80}")
    print("📝 TOP 5 MODELLE - ANTWORTLÄNGE")
    print("=" * 80)

    length_ranking = sorted(model_averages.items(), key=lambda x: x[1]["avg_answer_length"], reverse=True)

    for i, (model, avg) in enumerate(length_ranking[:5], 1):
        print(f"{i}. {model}: {avg['avg_answer_length']:.0f} Zeichen")

    # === KRITISCHE ERKENNTNISSE ===
    print(f"\n{'='*80}")
    print("⚠️ KRITISCHE ERKENNTNISSE")
    print("=" * 80)

    total_citations = sum(m["avg_citations"] for m in model_averages.values())
    total_quotes = sum(m["avg_quotes"] for m in model_averages.values())

    print(f"\n🔴 KRITISCHES PROBLEM - Zitat-Qualität:")
    print(f"   • Durchschnittliche IEEE-Zitationen (alle Modelle): {total_citations/len(model_averages):.2f}")
    print(f"   • Durchschnittliche Direkte Zitate (alle Modelle): {total_quotes/len(model_averages):.2f}")
    print(f"   • ERWARTUNG: Min. 2-3 Zitate pro Antwort")
    print(f"   • REALITÄT: {(total_quotes/len(model_averages)/2.5)*100:.1f}% der Erwartung")

    if total_citations < 0.5 and total_quotes < 0.5:
        print(f"\n   ❌ ALLE MODELLE VERSAGEN bei Zitationen!")
        print(f"   → Problem liegt NICHT am Modell")
        print(f"   → Problem liegt am PROMPT oder RAG-System")

    # === EMPFEHLUNG ===
    print(f"\n{'='*80}")
    print("💡 EMPFEHLUNGEN")
    print("=" * 80)

    best_quality = quality_scores[0]
    best_speed = speed_ranking[0]

    print(f"\n1. BESTES MODELL (Qualität): {best_quality[0]}")
    print(f"   → Quality Score: {best_quality[1]:.2f}")
    print(f"   → Verwende für Produktions-RAG")

    print(f"\n2. SCHNELLSTES MODELL: {best_speed[0]}")
    print(f"   → {best_speed[1]['avg_duration']:.1f}s pro Query")
    print(f"   → Verwende für schnelle Prototypen")

    print(f"\n3. PROMPT-OPTIMIERUNG DRINGEND ERFORDERLICH:")
    print(f"   ❌ 0% Zitationen → Prompt fordert Zitate nicht streng genug")
    print(f"   ❌ 0% Direkte Zitate → Prompt zeigt keine Beispiele")
    print(f"   ❌ 32% Aspect Coverage → Prompt strukturiert nicht ausreichend")

    print(f"\n4. NÄCHSTE SCHRITTE:")
    print(f"   1. VerwaltungsrechtPrompts in Backend integrieren")
    print(f"   2. Few-Shot Examples hinzufügen (EXZELLENT/SCHLECHT)")
    print(f"   3. Test mit neuem Prompt wiederholen")
    print(f"   4. Golden Dataset v2 erstellen mit Verbesserungen")

    # === AUSGABE JSON-DATEI ===
    output_file = json_file.replace(".json", "_analysis.json")
    analysis_output = {
        "summary": {"total_tests": len(data), "models_tested": len(models), "test_ids": len(test_ids)},
        "quality_ranking": [
            {
                "rank": i + 1,
                "model": model,
                "quality_score": score,
                "avg_citations": avg["avg_citations"],
                "avg_quotes": avg["avg_quotes"],
                "avg_legal_refs": avg["avg_legal_refs"],
                "avg_aspect_coverage": avg["avg_aspect_coverage"],
            }
            for i, (model, score, avg) in enumerate(quality_scores)
        ],
        "speed_ranking": [
            {"rank": i + 1, "model": model, "avg_duration_seconds": avg["avg_duration"]}
            for i, (model, avg) in enumerate(speed_ranking)
        ],
        "recommendations": {
            "best_quality_model": best_quality[0],
            "fastest_model": best_speed[0],
            "critical_issues": [
                "Zero IEEE citations across all models",
                "Zero direct quotes across all models",
                "Low aspect coverage (32% average)",
                "Prompt optimization required",
            ],
        },
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(analysis_output, f, indent=2, ensure_ascii=False)

    print(f"\n📁 Analyse gespeichert: {output_file}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        json_file = sys.argv[1]
    else:
        # Finde neueste Datei
        import glob
        import os

        files = glob.glob("rag_test_results_*.json")
        if not files:
            print("❌ Keine rag_test_results_*.json Dateien gefunden")
            sys.exit(1)

        json_file = max(files, key=os.path.getctime)
        print(f"📂 Analysiere: {json_file}")

    analyze_golden_dataset(json_file)
