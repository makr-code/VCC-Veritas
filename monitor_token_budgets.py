#!/usr/bin/env python3
"""
Token-Budget Monitoring Tool
Sammelt und analysiert Token-Budget-Metriken aus dem VERITAS Backend

Features:
- Real-time budget tracking
- CSV export für Analyse
- Statistiken nach Intent-Type
- Domain-spezifische Auswertung
- Overflow-Detection
"""

import csv
import json
import time
from datetime import datetime
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Any
import statistics

class TokenBudgetMonitor:
    """Monitor für Token-Budget-Metriken."""
    
    def __init__(self, data_dir: str = "data/token_monitoring"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.queries: List[Dict[str, Any]] = []
        self.start_time = datetime.now()
        
        print(f"📊 Token Budget Monitor gestartet")
        print(f"📁 Daten-Verzeichnis: {self.data_dir}")
    
    def record_query(self, query: str, response: Dict[str, Any]):
        """Zeichnet eine Query und ihre Token-Budget-Metriken auf."""
        
        pm = response.get("processing_metadata", {})
        tb = pm.get("token_budget", {})
        
        if not tb or not tb.get("allocated"):
            print(f"⚠️  Query ohne Token-Budget: {query[:50]}")
            return
        
        # Extract metrics
        record = {
            "timestamp": datetime.now().isoformat(),
            "query": query[:100],  # Erste 100 Zeichen
            "query_length": len(query),
            
            # Token Budget
            "allocated": tb.get("allocated", 0),
            "actual_used": tb.get("actual_used"),
            
            # Intent
            "intent": tb.get("intent", {}).get("intent", "unknown"),
            "intent_confidence": tb.get("intent", {}).get("confidence", 0.0),
            "intent_method": tb.get("intent", {}).get("method", "unknown"),
            
            # Complexity & Breakdown
            "complexity_score": tb.get("breakdown", {}).get("complexity_score", 0.0),
            "agent_count": tb.get("breakdown", {}).get("agent_count", 0),
            "agent_factor": tb.get("breakdown", {}).get("agent_factor", 1.0),
            "intent_weight": tb.get("breakdown", {}).get("intent_weight", 1.0),
            "chunk_count": tb.get("breakdown", {}).get("chunk_count", 0),
            "source_diversity": tb.get("breakdown", {}).get("source_diversity", 1.0),
            
            # Performance
            "processing_time": response.get("processing_time", 0.0),
            "agents_used": response.get("agents_used", 0),
            
            # Quality
            "confidence_score": response.get("confidence_score", 0.0),
            "sources_found": len(response.get("sources", [])),
            
            # Overflow Detection
            "overflow_detected": self._detect_overflow(tb, response)
        }
        
        self.queries.append(record)
        
        # Log
        print(f"✅ Recorded: {record['intent']} | "
              f"{record['allocated']} tokens | "
              f"{record['complexity_score']:.1f}/10 | "
              f"{record['processing_time']:.1f}s")
    
    def _detect_overflow(self, tb: Dict, response: Dict) -> bool:
        """Erkennt, ob Overflow-Strategien aktiviert wurden."""
        pm = response.get("processing_metadata", {})
        overflow_used = pm.get("overflow_strategy_used", False)
        return overflow_used or tb.get("allocated", 0) >= 3500  # Near max
    
    def export_csv(self, filename: str = None) -> str:
        """Exportiert alle Metriken als CSV."""
        
        if not self.queries:
            print("⚠️  Keine Daten zum Exportieren")
            return None
        
        if filename is None:
            filename = f"token_budget_metrics_{datetime.now():%Y%m%d_%H%M%S}.csv"
        
        filepath = self.data_dir / filename
        
        # CSV schreiben
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.queries[0].keys())
            writer.writeheader()
            writer.writerows(self.queries)
        
        print(f"✅ CSV exportiert: {filepath} ({len(self.queries)} Einträge)")
        return str(filepath)
    
    def export_json(self, filename: str = None) -> str:
        """Exportiert alle Metriken als JSON."""
        
        if not self.queries:
            print("⚠️  Keine Daten zum Exportieren")
            return None
        
        if filename is None:
            filename = f"token_budget_metrics_{datetime.now():%Y%m%d_%H%M%S}.json"
        
        filepath = self.data_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                "metadata": {
                    "export_time": datetime.now().isoformat(),
                    "monitoring_start": self.start_time.isoformat(),
                    "total_queries": len(self.queries)
                },
                "queries": self.queries
            }, f, indent=2, ensure_ascii=False)
        
        print(f"✅ JSON exportiert: {filepath} ({len(self.queries)} Einträge)")
        return str(filepath)
    
    def print_statistics(self):
        """Zeigt Statistiken über gesammelte Metriken."""
        
        if not self.queries:
            print("⚠️  Keine Daten für Statistiken")
            return
        
        print("\n" + "="*80)
        print("📊 TOKEN BUDGET MONITORING - STATISTIKEN")
        print("="*80)
        
        # Basic Stats
        total_queries = len(self.queries)
        duration = (datetime.now() - self.start_time).total_seconds()
        
        print(f"\n📈 Übersicht:")
        print(f"   Zeitraum: {self.start_time:%Y-%m-%d %H:%M:%S} - {datetime.now():%Y-%m-%d %H:%M:%S}")
        print(f"   Dauer: {duration:.0f}s ({duration/60:.1f} min)")
        print(f"   Queries: {total_queries}")
        print(f"   Durchsatz: {total_queries/(duration/60):.1f} queries/min")
        
        # Token Budget Stats
        budgets = [q["allocated"] for q in self.queries if q["allocated"]]
        if budgets:
            print(f"\n💰 Token Budget:")
            print(f"   Minimum: {min(budgets)} tokens")
            print(f"   Maximum: {max(budgets)} tokens")
            print(f"   Durchschnitt: {statistics.mean(budgets):.0f} tokens")
            print(f"   Median: {statistics.median(budgets):.0f} tokens")
            if len(budgets) > 1:
                print(f"   Std.Abweichung: {statistics.stdev(budgets):.0f} tokens")
        
        # Intent Distribution
        intent_counts = Counter(q["intent"] for q in self.queries)
        print(f"\n🎯 Intent-Verteilung:")
        for intent, count in intent_counts.most_common():
            percentage = (count / total_queries) * 100
            avg_budget = statistics.mean([q["allocated"] for q in self.queries if q["intent"] == intent])
            print(f"   {intent:15s}: {count:3d} ({percentage:5.1f}%) | Avg Budget: {avg_budget:6.0f} tokens")
        
        # Complexity Stats
        complexities = [q["complexity_score"] for q in self.queries if q["complexity_score"]]
        if complexities:
            print(f"\n🔍 Komplexität:")
            print(f"   Niedrig (1-3): {sum(1 for c in complexities if c <= 3)} queries")
            print(f"   Mittel (4-6):  {sum(1 for c in complexities if 3 < c <= 6)} queries")
            print(f"   Hoch (7-10):   {sum(1 for c in complexities if c > 6)} queries")
            print(f"   Durchschnitt:  {statistics.mean(complexities):.1f}/10")
        
        # Agent Usage
        agent_counts = [q["agent_count"] for q in self.queries if q["agent_count"]]
        if agent_counts:
            print(f"\n🤖 Agent-Nutzung:")
            print(f"   Min Agents: {min(agent_counts)}")
            print(f"   Max Agents: {max(agent_counts)}")
            print(f"   Avg Agents: {statistics.mean(agent_counts):.1f}")
        
        # Performance
        times = [q["processing_time"] for q in self.queries if q["processing_time"]]
        if times:
            print(f"\n⚡ Performance:")
            print(f"   Schnellste Query: {min(times):.1f}s")
            print(f"   Langsamste Query: {max(times):.1f}s")
            print(f"   Durchschnitt: {statistics.mean(times):.1f}s")
        
        # Overflow Detection
        overflow_count = sum(1 for q in self.queries if q["overflow_detected"])
        if overflow_count > 0:
            overflow_rate = (overflow_count / total_queries) * 100
            print(f"\n⚠️  Overflow:")
            print(f"   Overflow-Queries: {overflow_count} ({overflow_rate:.1f}%)")
            if overflow_rate > 5:
                print(f"   ⚠️  WARNING: Overflow-Rate > 5%!")
        
        # Confidence Stats
        confidences = [q["confidence_score"] for q in self.queries if q["confidence_score"]]
        if confidences:
            print(f"\n🎯 Confidence:")
            print(f"   Durchschnitt: {statistics.mean(confidences):.2f}")
            print(f"   Hoch (>0.8): {sum(1 for c in confidences if c > 0.8)} queries")
            print(f"   Niedrig (<0.5): {sum(1 for c in confidences if c < 0.5)} queries")
        
        print(f"\n{'='*80}\n")
    
    def analyze_by_domain(self):
        """Analysiert Token-Budget nach erkannten Domänen."""
        
        print("\n" + "="*80)
        print("🏢 DOMAIN-SPEZIFISCHE ANALYSE")
        print("="*80)
        
        # Keywords für Domain-Erkennung
        domain_keywords = {
            "Verwaltungsrecht": ["verwaltung", "behörde", "ermessen", "vwvfg", "verwaltungsakt"],
            "Baurecht": ["bauantrag", "baugenehmigung", "bauvorhaben", "bebauungsplan"],
            "Umweltrecht": ["umwelt", "immission", "emission", "naturschutz", "gewässer"],
            "Verkehrsrecht": ["verkehr", "straße", "fahrzeug", "führerschein"],
            "Strafrecht": ["straftat", "delikt", "verurteilung", "strafe"],
        }
        
        domain_stats = defaultdict(list)
        
        for query_record in self.queries:
            query_lower = query_record["query"].lower()
            
            # Erkenne Domain
            detected_domain = "Sonstige"
            for domain, keywords in domain_keywords.items():
                if any(keyword in query_lower for keyword in keywords):
                    detected_domain = domain
                    break
            
            domain_stats[detected_domain].append(query_record["allocated"])
        
        # Ausgabe
        print(f"\n📊 Budget nach Domain:\n")
        for domain in sorted(domain_stats.keys()):
            budgets = domain_stats[domain]
            if budgets:
                print(f"   {domain:20s}: {len(budgets):3d} queries | "
                      f"Avg: {statistics.mean(budgets):6.0f} tokens | "
                      f"Max: {max(budgets):6.0f} tokens")
        
        print(f"\n{'='*80}\n")
    
    def get_recommendations(self):
        """Gibt Optimierungs-Empfehlungen basierend auf Daten."""
        
        if len(self.queries) < 10:
            print("⚠️  Zu wenig Daten für Empfehlungen (min. 10 Queries)")
            return
        
        print("\n" + "="*80)
        print("💡 OPTIMIERUNGS-EMPFEHLUNGEN")
        print("="*80 + "\n")
        
        recommendations = []
        
        # Check Overflow Rate
        overflow_count = sum(1 for q in self.queries if q["overflow_detected"])
        overflow_rate = (overflow_count / len(self.queries)) * 100
        
        if overflow_rate > 15:
            recommendations.append({
                "priority": "HIGH",
                "issue": f"Overflow-Rate zu hoch ({overflow_rate:.1f}%)",
                "action": "Base Budget erhöhen (600 → 800) oder max_tokens erhöhen (4000 → 6000)"
            })
        elif overflow_rate > 5:
            recommendations.append({
                "priority": "MEDIUM",
                "issue": f"Overflow-Rate erhöht ({overflow_rate:.1f}%)",
                "action": "Monitoring fortsetzen, evtl. Context-Window-Limits prüfen"
            })
        
        # Check Intent Classification
        unknown_intent = sum(1 for q in self.queries if q["intent"] == "unknown")
        unknown_rate = (unknown_intent / len(self.queries)) * 100
        
        if unknown_rate > 10:
            recommendations.append({
                "priority": "MEDIUM",
                "issue": f"Viele unbekannte Intents ({unknown_rate:.1f}%)",
                "action": "Mehr Regeln zu intent_classifier.py hinzufügen"
            })
        
        # Check Budget Efficiency
        budgets = [q["allocated"] for q in self.queries]
        avg_budget = statistics.mean(budgets)
        
        if avg_budget < 400:
            recommendations.append({
                "priority": "LOW",
                "issue": f"Durchschnittliches Budget sehr niedrig ({avg_budget:.0f})",
                "action": "Evtl. Base Budget zu konservativ, könnte erhöht werden"
            })
        elif avg_budget > 2000:
            recommendations.append({
                "priority": "MEDIUM",
                "issue": f"Durchschnittliches Budget sehr hoch ({avg_budget:.0f})",
                "action": "Prüfen ob Domain-Weights zu aggressiv sind"
            })
        
        # Check Performance
        times = [q["processing_time"] for q in self.queries]
        slow_queries = sum(1 for t in times if t > 60)
        slow_rate = (slow_queries / len(self.queries)) * 100
        
        if slow_rate > 20:
            recommendations.append({
                "priority": "HIGH",
                "issue": f"Viele langsame Queries ({slow_rate:.1f}% >60s)",
                "action": "Agent-Timeouts prüfen, evtl. parallel execution optimieren"
            })
        
        # Output
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                priority_emoji = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}[rec["priority"]]
                print(f"{priority_emoji} {rec['priority']} Priority:")
                print(f"   Issue: {rec['issue']}")
                print(f"   Action: {rec['action']}\n")
        else:
            print("✅ Keine kritischen Issues gefunden!")
            print("   System läuft im optimalen Bereich.\n")
        
        print("="*80 + "\n")


def main():
    """Demo: Monitoring mit manueller Query-Eingabe."""
    
    monitor = TokenBudgetMonitor()
    
    print("\n" + "="*80)
    print("TOKEN BUDGET MONITORING - INTERACTIVE MODE")
    print("="*80)
    print("\nBefehle:")
    print("  stats    - Zeige Statistiken")
    print("  domain   - Domain-Analyse")
    print("  export   - Exportiere CSV & JSON")
    print("  rec      - Zeige Empfehlungen")
    print("  quit     - Beenden")
    print("\nOder: Gib eine Query ein zum Testen")
    print("="*80 + "\n")
    
    try:
        import requests
        BACKEND_URL = "http://localhost:5000"
        
        while True:
            cmd = input("\n> ").strip()
            
            if not cmd:
                continue
            
            if cmd.lower() == "quit":
                break
            elif cmd.lower() == "stats":
                monitor.print_statistics()
            elif cmd.lower() == "domain":
                monitor.analyze_by_domain()
            elif cmd.lower() == "export":
                monitor.export_csv()
                monitor.export_json()
            elif cmd.lower() == "rec":
                monitor.get_recommendations()
            else:
                # Query ausführen
                print(f"🔍 Sende Query: {cmd[:50]}...")
                try:
                    response = requests.post(
                        f"{BACKEND_URL}/v2/intelligent/query",
                        json={"query": cmd, "model": "phi3"},
                        timeout=120
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        monitor.record_query(cmd, data)
                        
                        # Kurze Zusammenfassung
                        tb = data.get("processing_metadata", {}).get("token_budget", {})
                        print(f"   ✅ Allocated: {tb.get('allocated')} tokens")
                        print(f"   Intent: {tb.get('intent', {}).get('intent')}")
                        print(f"   Processing: {data.get('processing_time', 0):.1f}s")
                    else:
                        print(f"   ❌ Error: {response.status_code}")
                
                except Exception as e:
                    print(f"   ❌ Error: {e}")
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Monitoring unterbrochen")
    
    finally:
        # Final Export
        if monitor.queries:
            print("\n" + "="*80)
            monitor.print_statistics()
            monitor.analyze_by_domain()
            monitor.get_recommendations()
            
            monitor.export_csv()
            monitor.export_json()
            print("\n✅ Monitoring beendet")
        else:
            print("\n⚠️  Keine Daten gesammelt")


if __name__ == "__main__":
    main()
