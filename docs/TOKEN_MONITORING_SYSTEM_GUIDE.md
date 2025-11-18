# Token-Budget Monitoring System - Dokumentation 📊

**Version:** 1.0
**Datum:** 17. Oktober 2025
**Status:** ✅ PRODUCTION-READY

---

## 📋 Übersicht

Das Token-Budget Monitoring System sammelt, analysiert und visualisiert Token-Budget-Metriken aus dem VERITAS Backend. Es hilft dabei, die Performance des Token-Management-Systems zu überwachen und Optimierungspotenziale zu identifizieren.

### Features

- ✅ **Real-time Monitoring** - Live-Tracking von Queries und Token-Budgets
- ✅ **CSV/JSON Export** - Persistente Speicherung für Langzeit-Analyse
- ✅ **Statistik-Dashboard** - Umfassende Auswertung nach Intent, Complexity, Domain
- ✅ **Optimierungs-Empfehlungen** - Automatische Erkennung von Issues
- ✅ **Domain-spezifische Analyse** - Budget-Verteilung nach Rechtsgebieten
- ✅ **Performance-Korrelation** - Budget vs. Processing Time

---

## 🚀 Quick Start

### 1. Interaktives Monitoring

```powershell
python monitor_token_budgets.py
```

**Befehle:**
- Gib eine Query ein → Backend-Request + Tracking
- `stats` → Zeige Statistiken
- `domain` → Domain-spezifische Analyse
- `export` → CSV & JSON Export
- `rec` → Optimierungs-Empfehlungen
- `quit` → Beenden (mit automatischem Export)

### 2. Automatisiertes Monitoring (Batch)

```python
from monitor_token_budgets import TokenBudgetMonitor
import requests

monitor = TokenBudgetMonitor()

queries = [
    "Was ist ein Bauantrag?",
    "Wie beantrage ich eine Baugenehmigung?",
    "Erkläre das Ermessen der Behörde im Verwaltungsverfahren"
]

for query in queries:
    response = requests.post(
        "http://localhost:5000/v2/intelligent/query",
        json={"query": query, "model": "phi3"},
        timeout=120
    )

    if response.status_code == 200:
        monitor.record_query(query, response.json())

# Auswertung
monitor.print_statistics()
monitor.analyze_by_domain()
monitor.get_recommendations()

# Export
monitor.export_csv()
monitor.export_json()
```

### 3. Dashboard anzeigen

```powershell
# Neueste CSV automatisch laden
python dashboard_token_budgets.py

# Spezifische CSV laden
python dashboard_token_budgets.py data/token_monitoring/metrics_20251017_171315.csv
```

---

## 📊 Gesammelte Metriken

### Token Budget Metrics

| Metrik | Beschreibung | Quelle |
|--------|--------------|--------|
| `allocated` | Alloziertes Token-Budget | `processing_metadata.token_budget.allocated` |
| `actual_used` | Tatsächlich verwendete Tokens | `processing_metadata.token_budget.actual_used` |
| `intent` | Erkannter Intent | `processing_metadata.token_budget.intent.intent` |
| `intent_confidence` | Intent-Confidence (0-1) | `processing_metadata.token_budget.intent.confidence` |
| `intent_method` | Klassifikations-Methode | `processing_metadata.token_budget.intent.method` |
| `complexity_score` | Komplexitäts-Score (1-10) | `processing_metadata.token_budget.breakdown.complexity_score` |
| `agent_count` | Anzahl verwendeter Agents | `processing_metadata.token_budget.breakdown.agent_count` |
| `agent_factor` | Agent-Skalierungs-Faktor | `processing_metadata.token_budget.breakdown.agent_factor` |
| `intent_weight` | Intent-Gewichtung | `processing_metadata.token_budget.breakdown.intent_weight` |

### Performance Metrics

| Metrik | Beschreibung | Quelle |
|--------|--------------|--------|
| `processing_time` | Gesamt-Processing-Time (s) | `processing_time` |
| `agents_used` | Anzahl Agents in Response | `agents_used` |
| `confidence_score` | Antwort-Confidence | `confidence_score` |
| `sources_found` | Anzahl gefundener Quellen | `len(sources)` |

### Overflow Detection

| Metrik | Beschreibung | Berechnung |
|--------|--------------|------------|
| `overflow_detected` | Overflow-Flag | `allocated >= 3500` oder `overflow_strategy_used` |

---

## 📈 Statistik-Auswertungen

### 1. Budget-Verteilung nach Intent

**Zeigt:**
- Durchschnittliches Budget pro Intent-Type
- Min/Max/Median Budget
- Standardabweichung
- Anzahl Queries pro Intent

**Interpretation:**
- `quick_answer`: Sollte ~250 tokens sein (Minimum)
- `explanation`: 800-1500 tokens
- `analysis`: 1500-3000 tokens
- `research`: 2500-4000 tokens

**Beispiel:**
```
🎯 EXPLANATION
   Queries: 15
   Budget: 800-1800 tokens
   Durchschnitt: 1250 ± 300 tokens
   Median: 1200 tokens
```

### 2. Complexity vs. Budget Korrelation

**Zeigt:**
- Budget-Verteilung nach Complexity-Bins
- Low (1-3), Medium (4-6), High (7-10)

**Erwartete Korrelation:**
- Low → 250-600 tokens
- Medium → 600-1500 tokens
- High → 1500-4000 tokens

**Beispiel:**
```
📈 High (7-10)
   Queries: 8
   Avg Budget: 1850 tokens
   Range: 1200-3500 tokens
```

### 3. Domain-spezifische Analyse

**Zeigt:**
- Budget-Verteilung nach erkannten Domänen
- Verwaltungsrecht, Baurecht, Umweltrecht, etc.

**Keywords für Domain-Erkennung:**
- **Verwaltungsrecht:** verwaltung, behörde, ermessen, vwvfg
- **Baurecht:** bauantrag, baugenehmigung, bebauungsplan
- **Umweltrecht:** umwelt, immission, emission, naturschutz
- **Verkehrsrecht:** verkehr, straße, fahrzeug
- **Strafrecht:** straftat, delikt, verurteilung

**Beispiel:**
```
📊 Budget nach Domain:

   Verwaltungsrecht    :  12 queries | Avg:   1450 tokens | Max:   3200 tokens
   Baurecht            :   8 queries | Avg:    980 tokens | Max:   2100 tokens
   Sonstige            :   5 queries | Avg:    620 tokens | Max:   1200 tokens
```

### 4. Performance-Korrelation

**Zeigt:**
- Budget vs. Processing Time
- Schnelle (<30s) vs. Langsame Queries (≥30s)

**Erwartung:**
- Höheres Budget → Längere Processing Time (mehr Agents, mehr Synthesis)

### 5. Agent-Nutzung

**Zeigt:**
- Budget-Verteilung nach Agent-Anzahl
- Korrelation Agent-Count vs. Budget

**Erwartung:**
- Mehr Agents → Höheres Budget (+15% pro Agent)

---

## 💡 Optimierungs-Empfehlungen

### Automatische Issue-Erkennung

Das System erkennt automatisch folgende Issues:

#### 🔴 HIGH Priority

**Overflow-Rate > 15%**
```
Issue: Overflow-Rate zu hoch (18.5%)
Action: Base Budget erhöhen (600 → 800) oder max_tokens erhöhen (4000 → 6000)
```

**Viele langsame Queries (>20% über 60s)**
```
Issue: Viele langsame Queries (25.0% >60s)
Action: Agent-Timeouts prüfen, evtl. parallel execution optimieren
```

#### 🟡 MEDIUM Priority

**Overflow-Rate > 5%**
```
Issue: Overflow-Rate erhöht (8.2%)
Action: Monitoring fortsetzen, evtl. Context-Window-Limits prüfen
```

**Viele unbekannte Intents (>10%)**
```
Issue: Viele unbekannte Intents (12.5%)
Action: Mehr Regeln zu intent_classifier.py hinzufügen
```

**Durchschnittliches Budget sehr hoch (>2000)**
```
Issue: Durchschnittliches Budget sehr hoch (2150)
Action: Prüfen ob Domain-Weights zu aggressiv sind
```

#### 🟢 LOW Priority

**Durchschnittliches Budget sehr niedrig (<400)**
```
Issue: Durchschnittliches Budget sehr niedrig (380)
Action: Evtl. Base Budget zu konservativ, könnte erhöht werden
```

---

## 📁 Datenstruktur

### CSV-Export Format

```csv
timestamp,query,query_length,allocated,actual_used,intent,intent_confidence,intent_method,complexity_score,agent_count,agent_factor,intent_weight,chunk_count,source_diversity,processing_time,agents_used,confidence_score,sources_found,overflow_detected
2025-10-17T17:15:30,Was ist ein Bauantrag?,22,250,,quick_answer,1.0,rule_based,3.5,6,1.9,0.5,0,1.0,28.7,6,0.92,3,False
2025-10-17T17:16:05,Wie beantrage ich...,45,1029,,explanation,0.8,hybrid_llm,7.8,8,2.1,1.0,2,1.2,27.6,8,0.88,5,False
```

### JSON-Export Format

```json
{
  "metadata": {
    "export_time": "2025-10-17T17:20:00",
    "monitoring_start": "2025-10-17T17:15:00",
    "total_queries": 25
  },
  "queries": [
    {
      "timestamp": "2025-10-17T17:15:30",
      "query": "Was ist ein Bauantrag?",
      "allocated": 250,
      "intent": "quick_answer",
      "complexity_score": 3.5,
      ...
    }
  ]
}
```

---

## 🎯 Best Practices

### Monitoring-Strategie

**Week 1-2: Datensammlung**
- Mindestens 50-100 Queries sammeln
- Verschiedene Query-Typen testen
- Verschiedene Domänen abdecken
- Normale Produktions-Queries + Edge-Cases

**Week 3-4: Analyse**
- CSV-Exports analysieren
- Dashboard regelmäßig prüfen
- Empfehlungen umsetzen
- Domain-Weights anpassen

**Week 5+: Optimierung**
- Basierend auf Daten entscheiden
- Iterative Verbesserungen
- A/B-Testing (alte vs. neue Weights)

### Metriken-Ziele (KPIs)

| Metrik | Ziel | Warnung | Kritisch |
|--------|------|---------|----------|
| **Overflow-Rate** | <5% | 5-15% | >15% |
| **Avg Budget** | 800-1500 | 1500-2500 | >2500 |
| **Intent Unknown Rate** | <5% | 5-10% | >10% |
| **Processing Time** | <40s avg | 40-60s | >60s |
| **Confidence Score** | >0.8 avg | 0.6-0.8 | <0.6 |

### Export-Schedule

```powershell
# Täglich: Quick Stats
python monitor_token_budgets.py  # Interactive session mit 10-20 Queries

# Wöchentlich: Full Export
monitor.export_csv(f"weekly_report_{datetime.now():%Y%m%d}.csv")
monitor.export_json(f"weekly_report_{datetime.now():%Y%m%d}.json")

# Monatlich: Dashboard-Review
python dashboard_token_budgets.py weekly_report_*.csv
```

---

## 🔧 Troubleshooting

### Problem 1: "Keine Token-Budget-Daten in Response"

**Symptom:** `⚠️ Query ohne Token-Budget`

**Ursache:**
- Backend verwendet nicht `/v2/intelligent/query` Endpoint
- Token-Budget-System nicht initialisiert
- `processing_metadata` fehlt

**Lösung:**
```powershell
# Check Backend-Logs
Get-Content data\veritas_auto_server.log | Select-String "Token Budget Calculator"

# Expected: "✅ Token Budget Calculator initialisiert"
```

### Problem 2: "CSV-Export leer"

**Symptom:** `⚠️ Keine Daten zum Exportieren`

**Ursache:** Keine Queries erfolgreich getrackt

**Lösung:**
```python
# Check ob Queries aufgezeichnet werden
print(f"Getrackter Queries: {len(monitor.queries)}")

# Manual test
response = requests.post(...)
monitor.record_query("test", response.json())
```

### Problem 3: "Dashboard zeigt keine Daten"

**Symptom:** `❌ Keine Daten gefunden`

**Ursache:** CSV-Datei nicht gefunden oder leer

**Lösung:**
```powershell
# Check CSV-Verzeichnis
ls data\token_monitoring\*.csv

# Check CSV-Inhalt
Get-Content data\token_monitoring\test_monitoring.csv | Measure-Object -Line
```

---

## 📚 API Reference

### TokenBudgetMonitor Class

```python
class TokenBudgetMonitor:
    def __init__(self, data_dir: str = "data/token_monitoring")

    def record_query(self, query: str, response: Dict[str, Any])
        """Zeichnet Query + Token-Budget-Metriken auf."""

    def export_csv(self, filename: str = None) -> str
        """Exportiert Metriken als CSV."""

    def export_json(self, filename: str = None) -> str
        """Exportiert Metriken als JSON."""

    def print_statistics(self)
        """Zeigt umfassende Statistiken."""

    def analyze_by_domain(self)
        """Domain-spezifische Budget-Analyse."""

    def get_recommendations(self)
        """Automatische Optimierungs-Empfehlungen."""
```

### Dashboard Functions

```python
def load_monitoring_data(csv_path: str) -> List[Dict[str, Any]]
    """Lädt Monitoring-Daten aus CSV."""

def analyze_budget_by_intent(data: List[Dict]) -> Dict
    """Budget-Verteilung nach Intent."""

def analyze_complexity_correlation(data: List[Dict]) -> Dict
    """Complexity vs. Budget Korrelation."""

def print_dashboard(csv_path: str)
    """Vollständiges Dashboard mit allen Analysen."""
```

---

## 📊 Beispiel-Workflow

### Kompletter Monitoring-Zyklus

```python
from monitor_token_budgets import TokenBudgetMonitor
import requests
from datetime import datetime

# 1. Setup
monitor = TokenBudgetMonitor()
BACKEND_URL = "http://localhost:5000"

# 2. Datensammlung (1-2 Wochen)
test_queries = [
    # Simple Queries
    "Was ist ein Bauantrag?",
    "Wo beantrage ich einen Personalausweis?",

    # Medium Queries
    "Wie beantrage ich eine Baugenehmigung in Stuttgart?",
    "Welche Unterlagen brauche ich für eine Gewerbeanmeldung?",

    # Complex Queries (Verwaltungsrecht)
    "Erkläre das Ermessen der Behörde im Verwaltungsverfahren nach VwVfG",
    "Wie ist die Verhältnismäßigkeit bei belastenden Verwaltungsakten zu prüfen?",

    # Domain-spezifisch
    "Was regelt das BImSchG für Industrieanlagen?",
    "Welche Verkehrssicherungspflichten hat ein Bauherr?",
]

for query in test_queries:
    response = requests.post(
        f"{BACKEND_URL}/v2/intelligent/query",
        json={"query": query, "model": "phi3"},
        timeout=120
    )

    if response.status_code == 200:
        monitor.record_query(query, response.json())

# 3. Analyse
print("\n📊 STATISTIKEN:")
monitor.print_statistics()

print("\n🏢 DOMAIN-ANALYSE:")
monitor.analyze_by_domain()

print("\n💡 EMPFEHLUNGEN:")
monitor.get_recommendations()

# 4. Export
csv_file = monitor.export_csv(f"monitoring_report_{datetime.now():%Y%m%d}.csv")
json_file = monitor.export_json(f"monitoring_report_{datetime.now():%Y%m%d}.json")

# 5. Dashboard
import subprocess
subprocess.run(["python", "dashboard_token_budgets.py", csv_file])
```

---

## 🎯 Zusammenfassung

**Das Monitoring-System bietet:**

✅ **Real-time Tracking** - Sofortiges Feedback zu Token-Budgets
✅ **Langzeit-Analyse** - CSV/JSON-Exports für historische Auswertung
✅ **Automatische Empfehlungen** - Issue-Erkennung mit Lösungsvorschlägen
✅ **Domain-Awareness** - Rechtsgebiets-spezifische Auswertungen
✅ **Performance-Monitoring** - Budget vs. Time Korrelation

**Nächste Schritte:**
1. ✅ Monitoring-Tools bereit
2. 🔄 Datensammlung starten (50-100 Queries)
3. 📊 Wöchentliche Dashboard-Reviews
4. 🎯 Optimierungen basierend auf Daten

---

**Status:** ✅ PRODUCTION-READY
**Version:** 1.0
**Erstellt:** 17. Oktober 2025
