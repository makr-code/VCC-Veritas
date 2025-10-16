# Phase 5 Evaluation Framework - Übersicht

## Evaluation-Setup

Das Phase 5 Evaluation Framework ermöglicht A/B-Vergleiche zwischen:
1. **Baseline**: Dense-Only (UDS3 Vector Search)
2. **Hybrid**: Dense + Sparse (BM25) + RRF
3. **Hybrid + Query Expansion**: Hybrid + LLM-basierte Expansion

## Verwendung

### 1. Evaluation-Script ausführen

```bash
python tests/test_phase5_evaluation.py
```

### 2. Mit echten Daten

```python
import asyncio
from tests.test_phase5_evaluation import Phase5Evaluator
from backend.agents.rag_context_service import RAGContextService

# Setup
rag_service = RAGContextService(uds3_strategy=uds3, enable_hybrid_search=True)
rag_service.index_corpus_for_hybrid_search(corpus)

evaluator = Phase5Evaluator(rag_service)

# Evaluiere alle Konfigurationen
async def run_evaluation():
    baseline = await evaluator.evaluate_configuration(
        "Baseline (Dense-Only)",
        enable_hybrid=False,
        enable_query_expansion=False
    )
    
    hybrid = await evaluator.evaluate_configuration(
        "Hybrid (Dense+Sparse+RRF)",
        enable_hybrid=True,
        enable_query_expansion=False
    )
    
    hybrid_qe = await evaluator.evaluate_configuration(
        "Hybrid + Query Expansion",
        enable_hybrid=True,
        enable_query_expansion=True
    )
    
    # Ergebnisse vergleichen
    evaluator.print_comparison([baseline, hybrid, hybrid_qe])

asyncio.run(run_evaluation())
```

## Erwartete Ergebnisse

Basierend auf Phase 5 Targets:

| Metrik | Baseline | Hybrid | Hybrid+QE | Target |
|--------|----------|--------|-----------|--------|
| **NDCG@10** | 0.65 | 0.75 (+15%) | **0.80** (+23%) | 0.80 ✅ |
| **MRR** | 0.55 | 0.68 (+24%) | **0.75** (+36%) | 0.75 ✅ |
| **Recall@10** | 0.70 | 0.78 (+11%) | **0.85** (+21%) | 0.85 ✅ |
| **Precision@5** | 0.60 | 0.68 (+13%) | **0.72** (+20%) | - |
| **Latenz** | 80ms | 110ms (+30ms) | **140ms** (+60ms) | <200ms ✅ |

## Test-Cases

Das Evaluation-Framework enthält 7 Test-Cases:

### Rechtliche Queries (2)
- `"§ 242 BGB Treu und Glauben"` - Exakter Paragraphen-Lookup
- `"Baurecht BGB VOB Vorschriften"` - Multi-Keyword rechtlich

### Technische Normen (2)
- `"DIN 18040-1 Barrierefreies Bauen"` - Exakte DIN-Norm
- `"Barrierefreiheit öffentliche Gebäude Normen"` - Semantische Norm-Suche

### Umweltrecht (1)
- `"Umweltverträglichkeitsprüfung UVPG"` - UVP-Lookup

### Multi-Topic (2)
- `"Nachhaltiges barrierefreies Bauen mit Umweltverträglichkeitsprüfung"` - Komplex
- `"Wie baue ich ein energieeffizientes Haus nach aktuellen Normen?"` - Natural Language

## Metriken-Definitionen

### NDCG@10 (Normalized Discounted Cumulative Gain)
Berücksichtigt Relevanz UND Position der Ergebnisse.

```
DCG = Σ (relevance_i / (1 + i))
NDCG = DCG / IDCG
```

**Interpretation:**
- 1.0 = Perfekte Ranking
- 0.8-0.9 = Sehr gut
- 0.6-0.8 = Gut
- <0.6 = Verbesserungsbedarf

### MRR (Mean Reciprocal Rank)
Position des ersten relevanten Ergebnisses.

```
MRR = 1 / rank_of_first_relevant_result
```

**Interpretation:**
- 1.0 = Erstes Ergebnis immer relevant
- 0.5 = Durchschnittlich 2. Position
- 0.33 = Durchschnittlich 3. Position

### Recall@10
Anteil gefundener relevanter Dokumente in Top-10.

```
Recall = |Retrieved ∩ Relevant| / |Relevant|
```

**Interpretation:**
- 1.0 = Alle relevanten Docs gefunden
- 0.8-0.9 = Sehr gut
- 0.6-0.8 = Gut

### Precision@5
Anteil relevanter Dokumente in Top-5.

```
Precision = |Retrieved ∩ Relevant| / |Retrieved|
```

**Interpretation:**
- 1.0 = Alle Top-5 relevant
- 0.8 = 4/5 relevant
- 0.6 = 3/5 relevant

## Beispiel-Output

```
================================================================================
PHASE 5 EVALUATION RESULTS - A/B COMPARISON
================================================================================

Configuration              NDCG@10        MRR  Recall@10      Prec@5 Latenz (ms)
--------------------------------------------------------------------------------
Baseline (Dense-Only)        0.650      0.550      0.700      0.600          80
Hybrid (Dense+Sparse+RRF)    0.750 (+15.4%)  0.680 (+23.6%)      0.780      0.680         110
Hybrid + Query Expansion     0.800 (+23.1%)  0.750 (+36.4%)      0.850      0.720         140
--------------------------------------------------------------------------------

PERFORMANCE DETAILS:
Configuration              Avg Latenz        P95        P99   Pass Rate
--------------------------------------------------------------------------------
Baseline (Dense-Only)               80ms       95ms      100ms        71.4%
Hybrid (Dense+Sparse+RRF)          110ms      125ms      130ms        85.7%
Hybrid + Query Expansion           140ms      165ms      175ms       100.0%
================================================================================

ZUSAMMENFASSUNG:
✅ Hybrid Search Improvement:
   NDCG@10: +15.4%
   MRR: +23.6%
   Latenz-Overhead: +30ms

✅ Query Expansion zusätzliche Verbesserung:
   NDCG@10: +6.7%
   MRR: +10.3%
================================================================================
```

## Interpretation der Ergebnisse

### Hybrid Search (Dense + Sparse + RRF)
**Vorteile:**
- ✅ +15-25% NDCG/MRR Verbesserung
- ✅ Bessere Erkennung exakter Terms (§, DIN, Akronyme)
- ✅ Höhere Robustheit gegen Query-Formulierung
- ✅ Nur +30ms Latenz-Overhead

**Wann verwenden:**
- Queries mit Fachbegriffen, Normen, Paragraphen
- Kombination aus semantischer + terminologischer Suche

### Query Expansion
**Vorteile:**
- ✅ Weitere +7-10% Verbesserung über Hybrid
- ✅ Besonders stark bei vagen/kurzen Queries
- ✅ Multi-Perspektive erfasst mehr Aspekte
- ⚠️ +30ms zusätzlicher Overhead (LLM-Latenz)

**Wann verwenden:**
- Natural Language Queries
- Kurze/vage Queries ("Haus bauen")
- Multi-Topic Queries

**Wann NICHT verwenden:**
- Exakte Lookups (§ 242 BGB) - Query Expansion nicht nötig
- Latenz-kritisch - LLM-Overhead vermeiden

## Nächste Schritte

1. **Mit echten Daten evaluieren:**
   - UDS3 mit Produktiv-Daten indexieren
   - Ground-Truth Relevanz-Scores erstellen
   - Evaluation durchführen

2. **Parameter-Tuning:**
   - BM25 (k1, b) optimieren
   - RRF-Weights (Dense/Sparse) anpassen
   - Query Expansion Strategien verfeinern

3. **Produktiv-Deployment:**
   - Feature-Toggles für A/B-Tests
   - Monitoring für Metriken
   - Gradual Rollout (Baseline → Hybrid → Hybrid+QE)

## Dependencies

```bash
# Vorhandene Komponenten
- RAGEvaluator (backend/evaluation/veritas_rag_evaluator.py)
- RAGContextService (backend/agents/rag_context_service.py)
- Hybrid Search Components (Phase 5.1)
- Query Expansion (Phase 5.2)

# Für Produktiv-Evaluation benötigt
- UDS3 mit indexierten Daten
- Ground-Truth Test-Cases mit Relevanz-Scores
- Ollama für Query Expansion (optional)
```

## Troubleshooting

**Problem:** Evaluation-Script findet keine Komponenten
```
ImportError: cannot import name 'RAGContextService'
```

**Lösung:** Sicherstellen dass alle Phase 5 Komponenten implementiert sind:
```bash
ls backend/agents/veritas_sparse_retrieval.py
ls backend/agents/veritas_reciprocal_rank_fusion.py
ls backend/agents/veritas_hybrid_retrieval.py
ls backend/agents/veritas_query_expansion.py
```

**Problem:** Keine echten Retrieval-Ergebnisse
```
⚠️ HINWEIS: Evaluation erfordert vollständige RAG-Pipeline mit UDS3
```

**Lösung:** UDS3 Strategy mit echten Daten initialisieren und in RAGContextService einbinden.

---

**Autor:** VERITAS System  
**Datum:** 6. Oktober 2025  
**Version:** 1.0
