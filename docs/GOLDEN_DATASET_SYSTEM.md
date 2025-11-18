# Golden Dataset System für RAG Quality Improvement

**Version:** 2.0
**Datum:** 10. Oktober 2025
**Zweck:** Feedback-Schleife zur kontinuierlichen Verbesserung des Prompt-Designs

---

## 📋 Überblick

Das Golden Dataset System erweitert das RAG Quality Testing um:

1. **Alle Modelle testen** (nicht nur erste 3)
2. **Direkte Zitate** aus Rechtsquellen erkennen und bewerten
3. **Detaillierte Zeitmessung** (Retrieval, Generation, Network-Latenz)
4. **Feedback-Schleife** für iterative Prompt-Verbesserung
5. **Benchmark-Datensatz** für Modell-Vergleiche

---

## 🎯 Zielsetzung

### Problem
Nach erstem Test (v3.19.0):
- ❌ **0% IEEE-Zitationen** (0/15 Tests)
- ❌ **0% Follow-up-Vorschläge** (0/15 Tests)
- ❌ **32% Aspekt-Abdeckung** (zu niedrig)
- ❌ **Keine direkten Zitate** aus Rechtsquellen

### Lösung: Golden Dataset
1. **Baseline etablieren** (aktuelle Qualität dokumentieren)
2. **Prompt optimieren** (basierend auf Daten)
3. **Re-evaluieren** (Verbesserung messen)
4. **Iterieren** bis Ziel-Qualität erreicht

---

## 🏗️ Architektur

### Komponenten

```
┌─────────────────────────────────────────────────────────────┐
│  GOLDEN DATASET GENERATOR (test_rag_quality_v3_19_0.py)    │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  ALLE MODELLE TESTEN                                        │
│  - llama3.1:latest                                          │
│  - llama3.1:8b                                              │
│  - mistral:latest                                           │
│  - codellama:latest                                         │
│  - ... (alle verfügbaren)                                   │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  5 KOMPLEXE TESTFRAGEN (Multi-Aspekt)                      │
│  Q1: Baugenehmigung (Voraussetzungen, Fristen, Kosten)     │
│  Q2: Verfahrensarten (Unterschiede, Unterlagen)            │
│  Q3: § 58 LBO BW (Inhalt, Vergleich, Änderungen)           │
│  Q4: Brandschutz (Klassen, Wege, Stoffe, Normen)           │
│  Q5: Verfahrensablauf (Schritte, Behörden, Rechtsmittel)   │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  DETAILLIERTE ANALYSE                                       │
│  ✓ IEEE-Zitationen [1], [2], [3]                           │
│  ✓ Direkte Zitate "..."                                    │
│  ✓ Paragraphen-Referenzen (§ 58 LBO BW)                    │
│  ✓ Follow-up-Vorschläge                                    │
│  ✓ Aspekt-Abdeckung                                        │
│  ✓ Timing-Metriken (ms-Genauigkeit)                        │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  GOLDEN DATASET OUTPUT                                      │
│  golden_dataset_1760123456.json                             │
│  {                                                          │
│    "Q1": {                                                  │
│      "question": "...",                                     │
│      "expected_...",                                        │
│      "model_results": {                                     │
│        "llama3.1:latest": {...},                            │
│        "mistral:latest": {...}                              │
│      }                                                      │
│    }                                                        │
│  }                                                          │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  FEEDBACK-SCHLEIFE                                          │
│  1. Analyse: Welche Modelle performen am besten?           │
│  2. Identifikation: Welche Prompt-Aspekte fehlen?          │
│  3. Optimierung: Prompt-Anpassungen implementieren          │
│  4. Re-Test: Verbesserung validieren                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Datenstrukturen

### GoldenDatasetEntry

```python
@dataclass
class GoldenDatasetEntry:
    """
    Ein Eintrag im Golden Dataset
    Enthält Frage + erwartete Qualität + tatsächliche Ergebnisse pro Modell
    """
    question_id: str                    # "Q1", "Q2", ...
    question: str                        # Die komplexe Frage
    expected_aspects: List[str]          # ["Fristen", "Kosten", ...]
    expected_citations_min: int          # Mindestanzahl IEEE-Zitationen
    expected_quotes_min: int             # Mindestanzahl direkte Zitate
    expected_legal_refs_min: int         # Mindestanzahl Paragraphen

    model_results: Dict[str, Any]        # Ergebnisse pro Modell
    # {
    #   "llama3.1:latest": {
    #     "metrics": {...},
    #     "timing": {...},
    #     "quotes": [...],
    #     "rating": "GOOD"
    #   },
    #   "mistral:latest": {...}
    # }
```

### TimingMetrics

```python
@dataclass
class TimingMetrics:
    """Detaillierte Performance-Messung"""
    total_time: float              # Gesamtzeit (Client-seitig)
    retrieval_time: float          # RAG-Retrieval (Backend)
    generation_time: float         # LLM-Generierung (Backend)
    post_processing_time: float    # Citation-Extraktion etc.
    network_latency: float         # HTTP Round-Trip
```

### QuoteMetrics

```python
@dataclass
class QuoteMetrics:
    """Zitat-Qualität"""
    direct_quotes_count: int       # Anzahl "..." Zitate
    quote_length_avg: float        # Durchschnittliche Länge
    quotes_with_source: int        # Zitate mit [1] Referenz
    quotes: List[str]              # Die tatsächlichen Zitate
```

---

## 🔍 Erweiterte Metriken

### Neue Metriken in v2.0

| Metrik | Beschreibung | Ziel | Aktuell (v1) |
|--------|--------------|------|--------------|
| **direct_quotes_count** | Anzahl direkter Zitate aus Quellen | ≥2 | 0 |
| **quotes_with_source** | Zitate mit [1] Referenz | 100% | 0% |
| **quote_length_avg** | Ø Länge der Zitate (Zeichen) | 50-150 | 0 |
| **legal_references** | § 58 LBO BW, Art. 14 GG | ≥3 | ~5% |
| **retrieval_time** | RAG-Retrieval-Zeit (ms) | <500ms | - |
| **generation_time** | LLM-Generation-Zeit (ms) | <5000ms | - |
| **quote_source_ratio** | % Zitate mit Quelle | >80% | 0% |

### Timing-Analyse

**Zweck:** Identifiziere Performance-Bottlenecks

```
Total Time:     18.2s
  ├─ Network Latency:     0.3s  (2%)
  ├─ Retrieval Time:      1.2s  (7%)   ← ChromaDB + Neo4j
  ├─ Generation Time:    15.8s (87%)  ← LLM Inference
  └─ Post-Processing:     0.9s  (4%)   ← Citation Extraction
```

**Optimierungspotential:**
- Generation Time: Model-Auswahl (kleineres Modell?)
- Retrieval Time: Index-Optimierung, Caching
- Post-Processing: Parallel-Processing

---

## 📝 Direkte Zitate - Anforderungen

### Was sind "direkte Zitate"?

```python
# BEISPIEL 1: Gutes direktes Zitat
"Nach § 58 Abs. 1 LBO BW ist die Baugenehmigung schriftlich zu beantragen [1].
Der Antrag muss enthalten: 'Angaben zur Person des Bauherrn, Beschreibung des
Bauvorhabens und Lage des Baugrundstücks' [1]."
                            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                            Direktes Zitat aus LBO BW mit Quelle [1]

# BEISPIEL 2: Schlechtes "Paraphrase"
"Der Bauantrag muss Informationen zum Bauherrn und Grundstück enthalten."
 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
 Keine Anführungszeichen = Paraphrase (weniger belastbar)
```

### Erkennungskriterien

```python
def extract_direct_quotes(answer: str) -> List[str]:
    """
    Erkennt:
    - "Text in Anführungszeichen"
    - „Text in deutschen Anführungszeichen"
    - Mindestlänge: 20 Zeichen (um Kurz-Zitate zu filtern)
    """
    patterns = [
        r'"([^"]{20,})"',        # "langes Zitat"
        r'„([^"]{20,})"',        # „deutsches Zitat"
    ]
    ...
```

### Zitat-Qualität bewerten

```python
# EXZELLENT (Quote + Source + Legal Ref)
"Gemäß § 59 Abs. 2 LBO BW gilt: 'Die Baugenehmigungsbehörde hat über
den Bauantrag innerhalb von drei Monaten zu entscheiden' [1]."
                                  ^^^^^^^^^^^^^^^^^^^^^^^^^^
                                  Zitat mit [1] + § 59 Abs. 2

# GUT (Quote + Source)
"Die Frist beträgt 'drei Monate' [1]."

# VERBESSERUNGSWÜRDIG (Quote ohne Source)
"Es gilt eine Frist von 'drei Monaten'."
                         ^^^^^^^^^^^^^
                         Zitat ohne [1] Referenz

# SCHLECHT (Keine Zitate)
"Die Bearbeitungsfrist beträgt drei Monate."
```

---

## 🔄 Feedback-Schleife - Workflow

### Iteration 1: Baseline

```bash
# Schritt 1: Baseline-Test durchführen
python tests/test_rag_quality_v3_19_0.py

# Output: golden_dataset_baseline.json
# Ergebnis:
#   - 0% Zitationen
#   - 0% Direkte Zitate
#   - 32% Aspekt-Abdeckung
```

### Iteration 2: Prompt-Optimierung

```bash
# Schritt 2: Prompt verbessern
# File: backend/agents/veritas_enhanced_prompts.py

# HINZUFÜGEN:
# - "Verwende ZWINGEND direkte Zitate aus den Quellen"
# - "Setze Zitate in Anführungszeichen: '...'"
# - "Nach jedem Zitat: Quellenangabe [1]"
```

### Iteration 3: Re-Evaluation

```bash
# Schritt 3: Erneut testen mit optimiertem Prompt
python tests/test_rag_quality_v3_19_0.py

# Output: golden_dataset_iteration2.json
# Vergleich mit Baseline:
#   - Zitationen: 0% → 80% ✅
#   - Direkte Zitate: 0% → 65% ✅
#   - Aspekt-Abdeckung: 32% → 58% ✅
```

### Iteration 4: Fine-Tuning

```bash
# Schritt 4: Modell-spezifische Optimierungen
# Erkenntnis aus Dataset:
#   - llama3.1:8b: Beste Zitation-Rate (90%)
#   - mistral:latest: Beste Aspekt-Abdeckung (72%)
#   - llama3.1:latest: Balance (80% / 65%)

# Entscheidung: llama3.1:latest als Standard-Modell
```

---

## 📈 Beispiel-Analyse

### Golden Dataset Entry - Q1 (Baugenehmigung)

```json
{
  "question_id": "Q1",
  "question": "Welche rechtlichen Voraussetzungen, Fristen und Kosten...",

  "expected_aspects": [
    "Rechtliche Voraussetzungen (§§ LBO BW)",
    "Fristen (Bearbeitungsdauer)",
    "Kosten (Gebühren)",
    "Ausnahmen (Genehmigungsfreistellung)",
    "Vereinfachtes Verfahren"
  ],

  "expected_citations_min": 3,
  "expected_quotes_min": 2,
  "expected_legal_refs_min": 3,

  "model_results": {

    "llama3.1:latest": {
      "metrics": {
        "answer_length": 770,
        "citation_count": 0,          // ❌ FEHLT
        "direct_quotes_count": 0,     // ❌ FEHLT
        "legal_references": [],       // ❌ FEHLT
        "aspect_coverage": 0.20       // ❌ NUR 20%
      },
      "timing": {
        "total_time": 18.2,
        "retrieval_time": 1.1,
        "generation_time": 16.3,
        "network_latency": 0.3
      },
      "rating": "GOOD",               // Trotzdem "GOOD" wg. Länge
      "issues": [
        "⚠️ Zu wenig Zitationen: 0/3",
        "⚠️ Keine direkten Zitate: 0/2",
        "⚠️ Aspekt-Abdeckung zu niedrig: 1/5 (20%)"
      ]
    },

    "mistral:latest": {
      "metrics": {
        "answer_length": 821,
        "citation_count": 0,
        "direct_quotes_count": 0,
        "legal_references": [],
        "aspect_coverage": 0.00       // ❌ 0%!
      },
      "timing": {
        "total_time": 17.6,
        "retrieval_time": 1.0,
        "generation_time": 15.9,
        "network_latency": 0.2
      },
      "rating": "GOOD",
      "issues": [
        "⚠️ Zu wenig Zitationen: 0/3",
        "⚠️ Keine direkten Zitate: 0/2",
        "⚠️ Aspekt-Abdeckung: 0/5 (0%)"  // ❌ KRITISCH
      ]
    }
  }
}
```

### Erkenntnisse aus diesem Entry

1. **ALLE Modelle** haben 0 Zitationen → **Prompt-Problem**, nicht modell-spezifisch
2. **Aspekt-Abdeckung variiert** (20% vs. 0%) → Modell-Unterschiede
3. **Timing ähnlich** (~17-18s) → LLM-Inferenz dominiert
4. **Rating "GOOD"** trotz fehlender Zitate → **Metriken anpassen**

---

## 🎯 Ziel-Metriken (Golden Standard)

### Nach Prompt-Optimierung

| Metrik | Baseline | Ziel | Status |
|--------|----------|------|--------|
| **IEEE-Zitationen** | 0.0 | ≥3.5 | ⏳ In Arbeit |
| **Direkte Zitate** | 0.0 | ≥2.0 | ⏳ In Arbeit |
| **Zitate mit Quelle** | 0% | ≥80% | ⏳ In Arbeit |
| **Paragraphen-Refs** | ~5% | ≥80% | ⏳ In Arbeit |
| **Aspekt-Abdeckung** | 32% | ≥65% | ⏳ In Arbeit |
| **Follow-up-Vorschläge** | 0.0 | ≥4.0 | ⏳ In Arbeit |
| **Rating "EXCELLENT"** | 33% | ≥60% | ⏳ In Arbeit |

### Performance-Ziele

| Metrik | Aktuell | Ziel | Optimierung |
|--------|---------|------|-------------|
| **Total Time** | 18s | <10s | Kleineres Modell |
| **Retrieval Time** | 1.1s | <500ms | Index-Optimierung |
| **Generation Time** | 16s | <8s | llama3.1:8b statt :latest |

---

## 🚀 Nutzung

### Test durchführen

```bash
# ALLE Modelle testen (Golden Dataset)
python tests/test_rag_quality_v3_19_0.py

# Output:
# - Konsolen-Output mit Zwischenergebnissen
# - golden_dataset_1760123456.json (vollständige Daten)
# - rag_test_results_1760123456.json (Flat-Format)
```

### Dataset analysieren

```python
import json

# Golden Dataset laden
with open('golden_dataset_1760123456.json') as f:
    dataset = json.load(f)

# Bestes Modell für Zitationen finden
for question_id, entry in dataset.items():
    print(f"\n{question_id}: {entry['question'][:50]}...")

    best_model = None
    best_citations = 0

    for model, results in entry['model_results'].items():
        citations = results['metrics']['citation_count']
        if citations > best_citations:
            best_citations = citations
            best_model = model

    print(f"  Bestes Modell: {best_model} ({best_citations} Zitationen)")
```

### Prompt-Verbesserung testen

```bash
# 1. Baseline
python tests/test_rag_quality_v3_19_0.py
mv golden_dataset_*.json golden_dataset_baseline.json

# 2. Prompt ändern
# backend/agents/veritas_enhanced_prompts.py bearbeiten

# 3. Re-Test
python tests/test_rag_quality_v3_19_0.py
mv golden_dataset_*.json golden_dataset_iteration2.json

# 4. Vergleichen
python tests/compare_golden_datasets.py \
    golden_dataset_baseline.json \
    golden_dataset_iteration2.json
```

---

## 📚 Verwandte Dokumentation

- `RAG_QUALITY_ANALYSIS_AND_PROMPT_IMPROVEMENTS.md` - Detaillierte Analyse v1.0
- `veritas_enhanced_prompts.py` - Verbesserte Prompt-Templates
- `test_rag_quality_v3_19_0.py` - Test-Script (mit Golden Dataset)

---

## 🔮 Nächste Schritte

### Kurzfristig (diese Woche)
1. ✅ Golden Dataset System dokumentieren
2. ⏳ Verwaltungsrecht-Prompts integrieren (aus `veritas_enhanced_prompts.py`)
3. ⏳ Vollständigen Test durchführen (ALLE Modelle)
4. ⏳ Baseline Golden Dataset erstellen

### Mittelfristig (nächste Woche)
1. Prompt-Optimierungen implementieren (direkte Zitate erzwingen)
2. Re-Test nach Optimierung
3. Modell-Auswahl finalisieren (basierend auf Daten)
4. Performance-Optimierung (kleineres Modell?)

### Langfristig (nächsten Monat)
1. Automatische Feedback-Schleife (CI/CD Integration)
2. Kontinuierliches Golden Dataset Update
3. A/B-Testing verschiedener Prompt-Varianten
4. Fine-Tuning eines eigenen Modells (optional)

---

**Erstellt von:** GitHub Copilot
**Datum:** 10. Oktober 2025
**Version:** 2.0
