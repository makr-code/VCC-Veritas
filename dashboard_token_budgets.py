#!/usr/bin/env python3
"""
Token-Budget Dashboard - Visualisierung & Analyse

Liest CSV-Exports aus dem Monitoring und erstellt:
- Budget-Verteilung nach Intent
- Complexity vs. Budget Korrelation
- Zeitliche Entwicklung
- Domain-spezifische Analyse
"""

import csv
import json
from pathlib import Path
from collections import defaultdict, Counter
import statistics
from datetime import datetime
from typing import List, Dict, Any

def load_monitoring_data(csv_path: str) -> List[Dict[str, Any]]:
    """Lädt Monitoring-Daten aus CSV."""
    
    data = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric fields
            row['allocated'] = int(row['allocated']) if row['allocated'] else 0
            row['complexity_score'] = float(row['complexity_score']) if row['complexity_score'] else 0
            row['agent_count'] = int(row['agent_count']) if row['agent_count'] else 0
            row['processing_time'] = float(row['processing_time']) if row['processing_time'] else 0
            row['intent_confidence'] = float(row['intent_confidence']) if row['intent_confidence'] else 0
            data.append(row)
    
    return data

def analyze_budget_by_intent(data: List[Dict]) -> Dict:
    """Analysiert Budget-Verteilung nach Intent."""
    
    by_intent = defaultdict(list)
    
    for row in data:
        intent = row['intent']
        budget = row['allocated']
        if budget > 0:
            by_intent[intent].append(budget)
    
    results = {}
    for intent, budgets in by_intent.items():
        results[intent] = {
            'count': len(budgets),
            'min': min(budgets),
            'max': max(budgets),
            'avg': statistics.mean(budgets),
            'median': statistics.median(budgets),
            'stdev': statistics.stdev(budgets) if len(budgets) > 1 else 0
        }
    
    return results

def analyze_complexity_correlation(data: List[Dict]) -> Dict:
    """Analysiert Korrelation zwischen Complexity und Budget."""
    
    complexity_bins = {
        'Low (1-3)': [],
        'Medium (4-6)': [],
        'High (7-10)': []
    }
    
    for row in data:
        complexity = row['complexity_score']
        budget = row['allocated']
        
        if budget == 0:
            continue
        
        if complexity <= 3:
            complexity_bins['Low (1-3)'].append(budget)
        elif complexity <= 6:
            complexity_bins['Medium (4-6)'].append(budget)
        else:
            complexity_bins['High (7-10)'].append(budget)
    
    results = {}
    for bin_name, budgets in complexity_bins.items():
        if budgets:
            results[bin_name] = {
                'count': len(budgets),
                'avg': statistics.mean(budgets),
                'min': min(budgets),
                'max': max(budgets)
            }
        else:
            results[bin_name] = {'count': 0, 'avg': 0, 'min': 0, 'max': 0}
    
    return results

def print_dashboard(csv_path: str):
    """Zeigt umfassendes Dashboard der Token-Budget-Metriken."""
    
    print("\n" + "🎨 "*40)
    print("TOKEN-BUDGET DASHBOARD")
    print("🎨 "*40)
    
    # Load data
    print(f"\n📁 Lade Daten: {csv_path}")
    data = load_monitoring_data(csv_path)
    
    if not data:
        print("❌ Keine Daten gefunden")
        return
    
    print(f"✅ {len(data)} Einträge geladen\n")
    
    # 1. Budget by Intent
    print("="*80)
    print("📊 BUDGET-VERTEILUNG NACH INTENT")
    print("="*80 + "\n")
    
    intent_stats = analyze_budget_by_intent(data)
    
    for intent in sorted(intent_stats.keys()):
        stats = intent_stats[intent]
        print(f"🎯 {intent.upper()}")
        print(f"   Queries: {stats['count']}")
        print(f"   Budget: {stats['min']}-{stats['max']} tokens")
        print(f"   Durchschnitt: {stats['avg']:.0f} ± {stats['stdev']:.0f} tokens")
        print(f"   Median: {stats['median']:.0f} tokens\n")
    
    # 2. Complexity Correlation
    print("="*80)
    print("🔍 COMPLEXITY VS. BUDGET KORRELATION")
    print("="*80 + "\n")
    
    complexity_stats = analyze_complexity_correlation(data)
    
    for bin_name in ['Low (1-3)', 'Medium (4-6)', 'High (7-10)']:
        stats = complexity_stats[bin_name]
        if stats['count'] > 0:
            print(f"📈 {bin_name}")
            print(f"   Queries: {stats['count']}")
            print(f"   Avg Budget: {stats['avg']:.0f} tokens")
            print(f"   Range: {stats['min']}-{stats['max']} tokens\n")
    
    # 3. Performance Analysis
    print("="*80)
    print("⚡ PERFORMANCE-ANALYSE")
    print("="*80 + "\n")
    
    times = [row['processing_time'] for row in data if row['processing_time'] > 0]
    budgets = [row['allocated'] for row in data if row['allocated'] > 0]
    
    if times and budgets:
        # Korrelation Budget vs. Time
        fast_queries = [row for row in data if row['processing_time'] < 30]
        slow_queries = [row for row in data if row['processing_time'] >= 30]
        
        if fast_queries:
            avg_budget_fast = statistics.mean([r['allocated'] for r in fast_queries if r['allocated'] > 0])
            print(f"⚡ Schnelle Queries (<30s): {len(fast_queries)}")
            print(f"   Durchschn. Budget: {avg_budget_fast:.0f} tokens\n")
        
        if slow_queries:
            avg_budget_slow = statistics.mean([r['allocated'] for r in slow_queries if r['allocated'] > 0])
            print(f"🐌 Langsame Queries (≥30s): {len(slow_queries)}")
            print(f"   Durchschn. Budget: {avg_budget_slow:.0f} tokens\n")
    
    # 4. Agent Usage
    print("="*80)
    print("🤖 AGENT-NUTZUNG")
    print("="*80 + "\n")
    
    agent_counts = Counter(row['agent_count'] for row in data if row['agent_count'] > 0)
    
    for agent_count in sorted(agent_counts.keys()):
        count = agent_counts[agent_count]
        avg_budget = statistics.mean([
            row['allocated'] for row in data 
            if row['agent_count'] == agent_count and row['allocated'] > 0
        ])
        print(f"   {agent_count} Agents: {count:3d} queries | Avg Budget: {avg_budget:6.0f} tokens")
    
    # 5. Top Queries
    print("\n" + "="*80)
    print("🏆 TOP 5 QUERIES (höchstes Budget)")
    print("="*80 + "\n")
    
    sorted_data = sorted(data, key=lambda x: x['allocated'], reverse=True)[:5]
    
    for i, row in enumerate(sorted_data, 1):
        print(f"{i}. {row['query'][:70]}...")
        print(f"   Budget: {row['allocated']} tokens | "
              f"Complexity: {row['complexity_score']:.1f}/10 | "
              f"Intent: {row['intent']} | "
              f"Time: {row['processing_time']:.1f}s\n")
    
    # 6. Recommendations
    print("="*80)
    print("💡 EMPFEHLUNGEN")
    print("="*80 + "\n")
    
    avg_budget = statistics.mean(budgets)
    max_budget = max(budgets)
    overflow_count = sum(1 for b in budgets if b >= 3500)
    overflow_rate = (overflow_count / len(budgets)) * 100
    
    if avg_budget < 500:
        print("🟢 Budget-Effizienz: GUT")
        print("   Durchschnittliches Budget niedrig, System arbeitet effizient\n")
    elif avg_budget > 2000:
        print("🟡 Budget-Effizienz: HOCH")
        print("   Durchschnittliches Budget hoch, evtl. Domain-Weights prüfen\n")
    
    if overflow_rate > 10:
        print("🔴 Overflow-Rate KRITISCH")
        print(f"   {overflow_rate:.1f}% der Queries nahe Maximum")
        print("   → Base Budget oder max_tokens erhöhen\n")
    elif overflow_rate > 5:
        print("🟡 Overflow-Rate ERHÖHT")
        print(f"   {overflow_rate:.1f}% der Queries nahe Maximum")
        print("   → Monitoring fortsetzen\n")
    
    if max_budget == 4000:
        print("⚠️  Maximum Budget erreicht")
        print("   Evtl. Context-Window-Limit zu niedrig für sehr komplexe Queries\n")
    
    print("="*80 + "\n")

def main():
    """Main Dashboard Runner."""
    
    import sys
    
    if len(sys.argv) < 2:
        # Suche neueste CSV
        data_dir = Path("data/token_monitoring")
        if data_dir.exists():
            csv_files = list(data_dir.glob("*.csv"))
            if csv_files:
                latest_csv = max(csv_files, key=lambda p: p.stat().st_mtime)
                print(f"📁 Verwende neueste CSV: {latest_csv}")
                print_dashboard(str(latest_csv))
            else:
                print("❌ Keine CSV-Dateien gefunden in data/token_monitoring/")
        else:
            print("❌ Verzeichnis nicht gefunden: data/token_monitoring/")
    else:
        csv_path = sys.argv[1]
        print_dashboard(csv_path)

if __name__ == "__main__":
    main()
