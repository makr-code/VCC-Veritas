"""
🧪 Token Budget Test Session - Interaktive Datensammlung

Durchführt eine strukturierte Test-Session mit 20 vordefinierten Queries
und trackt alle Token-Budget-Metriken.
"""

import csv
import json
import statistics
import time
from datetime import datetime
from pathlib import Path

import requests

BACKEND_URL = "http://localhost:5000"
ENDPOINT = "/v2/intelligent/query"

# Test-Queries nach Komplexität
TEST_QUERIES = {
    "Block 1: Simple Queries (quick_answer)": [
        ("Was ist ein Bauantrag?", "Baurecht", "~250"),
        ("Wo beantrage ich eine Baugenehmigung?", "Baurecht", "~300"),
        ("Was bedeutet Lärmschutz?", "Umweltrecht", "~250"),
        ("Wer ist für Verkehrsschilder zuständig?", "Verkehrsrecht", "~300"),
        ("Was ist ein Verwaltungsakt?", "Verwaltungsrecht", "~350"),
    ],
    "Block 2: Medium Queries (explanation)": [
        ("Wie beantrage ich eine Baugenehmigung in Stuttgart?", "Baurecht", "~800"),
        ("Welche Unterlagen brauche ich für einen Bauantrag?", "Baurecht", "~700"),
        ("Wie funktioniert die Lärmschutzverordnung?", "Umweltrecht", "~850"),
        ("Wie kann ich gegen einen Bußgeldbescheid vorgehen?", "Verkehrsrecht", "~750"),
        ("Wie läuft ein Widerspruchsverfahren ab?", "Verwaltungsrecht", "~900"),
    ],
    "Block 3: Complex Queries (analysis)": [
        ("Erkläre das Ermessen der Behörde im Verwaltungsverfahren", "Verwaltungsrecht", "~1200"),
        ("Was bedeutet Verhältnismäßigkeitsprinzip in der Verwaltung?", "Verwaltungsrecht", "~1300"),
        ("Wie wird die Abwägung bei Bebauungsplänen durchgeführt?", "Baurecht", "~1400"),
        ("Erkläre die Lärmgrenzwerte für Wohngebiete und Gewerbegebiete", "Umweltrecht", "~1100"),
        ("Was sind die Voraussetzungen für eine Fahrerlaubnisentziehung?", "Verkehrsrecht", "~1000"),
    ],
    "Block 4: Edge Cases": [
        (
            "Erkläre mir ausführlich die gesamte Verwaltungsgerichtsordnung mit allen Verfahrensarten",
            "Verwaltungsrecht",
            "Overflow?",
        ),
        ("Vergleiche Baurecht, Umweltrecht und Verkehrsrecht", "Multi-Domain", "Analysis?"),
        ("Was ist der Unterschied zwischen Ermessen und Beurteilungsspielraum?", "Verwaltungsrecht", "~1200"),
        ("Liste alle Behörden in Stuttgart auf", "General", "Unknown?"),
        ("Wie funktioniert der Bebauungsplan?", "Baurecht", "~800"),
    ],
}


class TestSessionMonitor:
    def __init__(self):
        self.results = []
        self.start_time = datetime.now()
        self.data_dir = Path("data/token_monitoring")
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def send_query(self, query_text):
        """Sendet Query an Backend und extrahiert Token-Budget-Info"""
        try:
            payload = {"query": query_text}
            start = time.time()
            response = requests.post(f"{BACKEND_URL}{ENDPOINT}", json=payload, timeout=60)
            duration = time.time() - start

            if response.status_code == 200:
                data = response.json()
                pm = data.get("processing_metadata", {})
                tb = pm.get("token_budget", {})

                if tb:
                    result = {
                        "timestamp": datetime.now().isoformat(),
                        "query": query_text,
                        "allocated": tb.get("allocated", 0),
                        "intent": tb.get("intent", {}).get("intent", "unknown"),
                        "intent_confidence": tb.get("intent", {}).get("confidence", 0.0),
                        "intent_method": tb.get("intent", {}).get("method", "unknown"),
                        "complexity_score": tb.get("breakdown", {}).get("complexity_score", 0),
                        "agent_count": tb.get("breakdown", {}).get("agent_count", 0),
                        "agent_factor": tb.get("breakdown", {}).get("agent_factor", 0),
                        "intent_weight": tb.get("breakdown", {}).get("intent_weight", 1.0),
                        "chunk_count": tb.get("breakdown", {}).get("chunk_count", 0),
                        "source_diversity": tb.get("breakdown", {}).get("source_diversity", 1.0),
                        "processing_time": round(duration, 2),
                        "overflow_detected": tb.get("allocated", 0) >= 3500,
                        "response_length": len(data.get("result", "")),
                    }
                    return result, None
                else:
                    return None, "Token budget nicht in Response gefunden"
            else:
                return None, f"HTTP {response.status_code}: {response.text[:100]}"
        except Exception as e:
            return None, f"Error: {str(e)}"

    def detect_domain(self, query):
        """Einfache Domain-Erkennung"""
        query_lower = query.lower()
        domains = []

        if any(kw in query_lower for kw in ["verwaltung", "behörde", "ermessen", "verhältnismäßigkeit", "widerspruch"]):
            domains.append("Verwaltungsrecht")
        if any(kw in query_lower for kw in ["bau", "bebauung", "genehmigung", "bauantrag"]):
            domains.append("Baurecht")
        if any(kw in query_lower for kw in ["lärm", "umwelt", "emission", "grenzwert"]):
            domains.append("Umweltrecht")
        if any(kw in query_lower for kw in ["verkehr", "bußgeld", "fahrerlaubnis", "straße"]):
            domains.append("Verkehrsrecht")

        return domains if domains else ["Unknown"]

    def run_session(self, auto_mode=False):
        """Führt Test-Session durch"""
        print("\n" + "=" * 80)
        print("🧪 TOKEN BUDGET TEST SESSION")
        print("=" * 80)
        print(f"\nStart: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Backend: {BACKEND_URL}")
        print(f"Geplante Queries: {sum(len(queries) for queries in TEST_QUERIES.values())}")
        print("\n" + "=" * 80)

        query_num = 0

        for block_name, queries in TEST_QUERIES.items():
            print(f"\n\n{'='*80}")
            print(f"📦 {block_name}")
            print(f"{'='*80}\n")

            for query, expected_domain, expected_budget in queries:
                query_num += 1
                print(f'\n[{query_num}/{sum(len(q) for q in TEST_QUERIES.values())}] Query: "{query}"')
                print(f"   Erwartete Domain: {expected_domain} | Budget: {expected_budget}")
                print(f"   🔄 Sende Request...", end=" ", flush=True)

                result, error = self.send_query(query)

                if result:
                    print(f"✅ OK ({result['processing_time']}s)")

                    # Domains erkennen
                    detected_domains = self.detect_domain(query)
                    result["detected_domains"] = ",".join(detected_domains)
                    result["expected_domain"] = expected_domain
                    result["expected_budget"] = expected_budget

                    self.results.append(result)

                    # Ergebnis anzeigen
                    print(f"   📊 Budget: {result['allocated']} tokens")
                    print(
                        f"   🎯 Intent: {result['intent']} (conf: {result['intent_confidence']:.2f}, method: {result['intent_method']})"
                    )
                    print(f"   🔢 Complexity: {result['complexity_score']:.1f}/10")
                    print(f"   🤖 Agents: {result['agent_count']}")
                    print(f"   🌍 Domain erkannt: {result['detected_domains']}")

                    if result["overflow_detected"]:
                        print(f"   ⚠️  OVERFLOW DETECTED!")

                    # Vergleich mit Erwartung
                    expected_num = expected_budget.replace("~", "").replace("tokens", "").strip()
                    if expected_num.isdigit():
                        diff_pct = ((result["allocated"] - int(expected_num)) / int(expected_num)) * 100
                        if abs(diff_pct) > 20:
                            print(f"   ⚡ Abweichung: {diff_pct:+.0f}% von Erwartung")
                else:
                    print(f"❌ FEHLER")
                    print(f"   Error: {error}")

                if not auto_mode and query_num < sum(len(q) for q in TEST_QUERIES.values()):
                    input(f"\n   ⏸  Drücke Enter für nächste Query...")

        print(f"\n\n{'='*80}")
        print("✅ SESSION ABGESCHLOSSEN")
        print(f"{'='*80}\n")

        self.print_summary()
        self.export_results()

    def print_summary(self):
        """Zeigt Session-Zusammenfassung"""
        if not self.results:
            print("⚠️  Keine Ergebnisse gesammelt")
            return

        budgets = [r["allocated"] for r in self.results]
        times = [r["processing_time"] for r in self.results]
        complexities = [r["complexity_score"] for r in self.results]
        confidences = [r["intent_confidence"] for r in self.results]

        print("\n📊 SESSION SUMMARY")
        print("=" * 80)
        print(f"\n📈 BUDGET-STATISTIK:")
        print(f"   Queries: {len(self.results)}")
        print(f"   Range: {min(budgets)} - {max(budgets)} tokens")
        print(f"   Average: {statistics.mean(budgets):.0f} tokens")
        print(f"   Median: {statistics.median(budgets):.0f} tokens")
        print(f"   StdDev: {statistics.stdev(budgets) if len(budgets) > 1 else 0:.0f}")

        print(f"\n🎯 INTENT-VERTEILUNG:")
        intents = {}
        for r in self.results:
            intent = r["intent"]
            intents[intent] = intents.get(intent, 0) + 1
        for intent, count in sorted(intents.items(), key=lambda x: -x[1]):
            pct = (count / len(self.results)) * 100
            print(f"   {intent}: {count} ({pct:.1f}%)")

        print(f"\n🔢 COMPLEXITY-VERTEILUNG:")
        complexity_bins = {"Low (0-3)": 0, "Medium (4-6)": 0, "High (7-10)": 0}
        for c in complexities:
            if c <= 3:
                complexity_bins["Low (0-3)"] += 1
            elif c <= 6:
                complexity_bins["Medium (4-6)"] += 1
            else:
                complexity_bins["High (7-10)"] += 1
        for bin_name, count in complexity_bins.items():
            pct = (count / len(self.results)) * 100 if self.results else 0
            print(f"   {bin_name}: {count} ({pct:.1f}%)")

        print(f"\n🌍 DOMAIN-VERTEILUNG:")
        all_domains = []
        for r in self.results:
            all_domains.extend(r["detected_domains"].split(","))
        domain_counts = {}
        for d in all_domains:
            domain_counts[d] = domain_counts.get(d, 0) + 1
        for domain, count in sorted(domain_counts.items(), key=lambda x: -x[1]):
            print(f"   {domain}: {count}")

        print(f"\n⚡ PERFORMANCE:")
        print(f"   Avg Processing Time: {statistics.mean(times):.1f}s")
        print(f"   Range: {min(times):.1f}s - {max(times):.1f}s")

        print(f"\n💡 QUALITÄT:")
        print(f"   Avg Confidence: {statistics.mean(confidences):.2f}")
        print(
            f"   High Confidence (>0.8): {sum(1 for c in confidences if c > 0.8)} ({(sum(1 for c in confidences if c > 0.8)/len(confidences)*100):.1f}%)"
        )

        overflow_count = sum(1 for r in self.results if r["overflow_detected"])
        print(f"\n⚠️  OVERFLOW:")
        print(f"   Overflow Detected: {overflow_count} ({(overflow_count/len(self.results)*100):.1f}%)")

        print("\n" + "=" * 80)

    def export_results(self):
        """Exportiert Ergebnisse als CSV und JSON"""
        if not self.results:
            return

        timestamp = self.start_time.strftime("%Y%m%d_%H%M%S")
        csv_path = self.data_dir / f"session_{timestamp}.csv"
        json_path = self.data_dir / f"session_{timestamp}.json"

        # CSV Export
        fieldnames = [
            "timestamp",
            "query",
            "allocated",
            "intent",
            "intent_confidence",
            "intent_method",
            "complexity_score",
            "agent_count",
            "agent_factor",
            "intent_weight",
            "chunk_count",
            "source_diversity",
            "processing_time",
            "overflow_detected",
            "response_length",
            "detected_domains",
            "expected_domain",
            "expected_budget",
        ]

        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.results)

        print(f"\n💾 CSV Export: {csv_path}")

        # JSON Export
        export_data = {
            "session_info": {
                "start_time": self.start_time.isoformat(),
                "end_time": datetime.now().isoformat(),
                "query_count": len(self.results),
                "backend_url": BACKEND_URL,
            },
            "queries": self.results,
        }

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        print(f"💾 JSON Export: {json_path}")
        print(f"\n✅ Export abgeschlossen!")
        print(f"\n📊 Dashboard generieren mit:")
        print(f"   python dashboard_token_budgets.py {csv_path}")


if __name__ == "__main__":
    import sys

    print("\n🧪 TOKEN BUDGET TEST SESSION")
    print("=" * 80)
    print("\nModus wählen:")
    print("  [1] Interaktiv (Pause nach jeder Query)")
    print("  [2] Automatisch (alle Queries ohne Pause)")
    print()

    auto_mode = False
    if len(sys.argv) > 1 and sys.argv[1] == "auto":
        auto_mode = True
        print("▶️  Automatischer Modus aktiviert")
    else:
        choice = input("Wahl [1/2]: ").strip()
        if choice == "2":
            auto_mode = True
            print("▶️  Automatischer Modus aktiviert")
        else:
            print("▶️  Interaktiver Modus aktiviert")

    monitor = TestSessionMonitor()
    monitor.run_session(auto_mode=auto_mode)

    print("\n" + "=" * 80)
    print("🎉 SESSION COMPLETE!")
    print("=" * 80)
