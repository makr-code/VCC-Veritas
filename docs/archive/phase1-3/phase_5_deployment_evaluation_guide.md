# Phase 5 Deployment & Evaluation Guide

**Version:** 1.0  
**Datum:** 7. Oktober 2025  
**Strategie:** Staging (Phase 1 + Phase 2) + Evaluation mit echten Daten

---

## Übersicht

Dieser Guide beschreibt den kombinierten Ansatz **B+A**:
1. **Staging-Deployment** mit Feature-Toggles (Phase 1 → Phase 2)
2. **Evaluation** mit echten Daten parallel

**Zeitplan:**
- **Woche 1:** Staging Phase 1 (Hybrid Search)
- **Woche 1-2:** Ground-Truth Dataset erstellen
- **Woche 2:** Baseline Evaluation + Hybrid Evaluation
- **Woche 3:** Staging Phase 2 (+ Query Expansion)
- **Woche 3-4:** Full Pipeline Evaluation
- **Woche 4:** Production Rollout Plan

---

## Teil 1: Deployment-Konfiguration

### 1.1 Voraussetzungen

**Software:**
- Python 3.9+
- VERITAS Backend vollständig installiert
- Ollama mit llama2 Modell (für Phase 2)
- UDS3 Strategy funktionsfähig

**Komponenten-Check:**
```powershell
# Prüfe ob alle Phase 5 Komponenten vorhanden
ls backend/agents/veritas_sparse_retrieval.py
ls backend/agents/veritas_reciprocal_rank_fusion.py
ls backend/agents/veritas_hybrid_retrieval.py
ls backend/agents/veritas_query_expansion.py
ls config/phase5_config.py
ls backend/monitoring/phase5_monitoring.py
```

### 1.2 Konfiguration testen

```powershell
# Test Configuration
python config/phase5_config.py
```

**Erwartete Ausgabe:**
```
=== Phase 5 Configuration Test ===

1. Development Config:
   Phase5Config(stage=development, features=, rollout=0%)
   Features: Hybrid=False, QE=False

2. Staging Phase 1 Config:
   Phase5Config(stage=staging, features=Hybrid+ReRanking, rollout=10%)
   Features: Hybrid=True, QE=False

3. Staging Phase 2 Config:
   Phase5Config(stage=staging, features=Hybrid+QueryExpansion+ReRanking, rollout=10%)
   Features: Hybrid=True, QE=True

4. Production Config:
   Phase5Config(stage=production, features=Hybrid+QueryExpansion+ReRanking, rollout=100%)
   Features: Hybrid=True, QE=True

5. Current Environment Config:
   Phase5Config(stage=development, features=, rollout=0%)
   Validation: ✅ PASS
```

---

## Teil 2: Staging-Deployment Phase 1 (Hybrid Search)

### 2.1 Deployment durchführen

```powershell
# Ausführen des Deployment-Scripts
.\scripts\deploy_staging_phase1.ps1

# Oder mit custom Rollout
.\scripts\deploy_staging_phase1.ps1 -RolloutPercentage 25
```

**Das Script:**
1. ✅ Setzt Environment-Variablen
2. ✅ Validiert Konfiguration
3. ✅ Zeigt Monitoring-Commands
4. ✅ Zeigt Test-Commands

### 2.2 Backend starten

```powershell
# Mit Staging Phase 1 Config
python start_backend.py
```

**Prüfe Logs:**
```powershell
# Logs live verfolgen
Get-Content data/veritas_auto_server.log -Wait -Tail 50

# Suche nach Phase 5 Aktivität
Select-String -Path data/veritas_auto_server.log -Pattern "Phase5|Hybrid|BM25"
```

### 2.3 BM25 Index erstellen

**Python-Script:**
```python
from backend.agents.rag_context_service import RAGContextService
from config.phase5_config import get_config

# Initialize mit Staging Config
config = get_config()
rag_service = RAGContextService(uds3_strategy=uds3, **config.to_rag_query_options())

# Index Corpus
corpus = [
    # Ihre Dokumente hier
]
rag_service.index_corpus_for_hybrid_search(corpus)

print("✅ BM25 Index erstellt")
```

### 2.4 Tests durchführen

```powershell
# Unit Tests
pytest tests/test_phase5_hybrid_search.py -v

# Integration Tests (nur Hybrid, ohne QE)
pytest tests/test_phase5_integration.py::TestFullPipeline::test_hybrid_search_pipeline -v

# A/B Vergleich Baseline vs Hybrid
pytest tests/test_phase5_integration.py::TestABComparison -v
```

### 2.5 Monitoring (24-48 Stunden)

**Metriken beobachten:**

1. **Latenz:**
   ```powershell
   # Latenz-Statistiken
   Select-String -Path data/veritas_auto_server.log -Pattern "Phase5.*latency" | Select-Object -Last 20
   ```
   
   **Targets:**
   - Hybrid Total: <120ms (Avg), <200ms (P95)
   - Sparse Retrieval: <50ms
   - RRF Fusion: <5ms

2. **Success Rate:**
   ```powershell
   # Error Rate
   Select-String -Path data/veritas_auto_server.log -Pattern "ERROR.*Phase5"
   ```
   
   **Target:** <1% Error Rate

3. **BM25 Cache Hit Rate:**
   ```powershell
   # Cache Performance
   Select-String -Path data/veritas_auto_server.log -Pattern "cache_hit_rate"
   ```
   
   **Target:** >60% Cache Hit Rate (nach Warmup)

### 2.6 Success-Kriterien Phase 1

✅ **Go to Phase 2 wenn:**
- Latenz P95 <200ms
- Error Rate <1%
- BM25 Index erfolgreich erstellt
- Integration Tests bestanden
- Keine kritischen Bugs in 24h

❌ **Rollback wenn:**
- Latenz P95 >250ms
- Error Rate >5%
- Kritische Fehler in BM25 oder RRF

**Rollback:**
```powershell
$env:VERITAS_ENABLE_HYBRID_SEARCH = "false"
# Backend neu starten
```

---

## Teil 3: Ground-Truth Dataset erstellen (Parallel zu Phase 1)

### 3.1 Template öffnen

```powershell
code tests/ground_truth_dataset_template.py
```

### 3.2 Dokument-IDs aus Corpus holen

```python
# Liste aller Dokument-IDs
from your_corpus_module import get_all_documents

docs = get_all_documents()
for doc in docs:
    print(f"ID: {doc.id}, Title: {doc.title}")
```

### 3.3 Test-Cases erstellen

**Für jede Kategorie 5-7 Queries:**

1. **Legal (5-7 Queries):**
   - Exakte Paragraphen (§ 242 BGB)
   - Multi-Keyword (Baurecht BGB VOB)
   - Rechtsprinzipien (Treu und Glauben)

2. **Technical (5-7 Queries):**
   - Exakte Normen (DIN 18040-1)
   - Semantic (Barrierefreiheit öffentliche Gebäude)
   - Abbreviations (DIN, VOB, UVPG)

3. **Environmental (3-5 Queries):**
   - UVP-bezogen
   - Umweltrecht
   - Nachhaltigkeit

4. **Multi-Topic (5-7 Queries):**
   - Kombinationen (Nachhaltiges barrierefreies Bauen)
   - Natural Language (Wie baue ich ein energieeffizientes Haus?)

**Insgesamt: 20-30 Test-Cases**

### 3.4 Relevanz-Scores vergeben

**Manuelle Review:**

Für jeden Test-Case:
1. Führe Query in aktuellem System aus
2. Review Top-10 Ergebnisse
3. Vergebe Scores:
   - 1.0 = Perfekt
   - 0.8-0.9 = Sehr relevant
   - 0.6-0.7 = Relevant
   - 0.4-0.5 = Etwas relevant
   - <0.4 = Kaum/Nicht relevant

**Zeitaufwand:** ~30-60 Minuten pro Test-Case → 10-30 Stunden total

### 3.5 Dataset validieren

```powershell
python tests/ground_truth_dataset_template.py
```

**Erwartete Ausgabe:**
```
=== Ground-Truth Dataset Validation ===

✅ Dataset validation passed!

📊 Dataset Statistics:
   Total queries: 25
   Categories: {'legal': 7, 'technical': 7, 'environmental': 4, 'multi_topic': 7}
   Avg docs per query: 4.5
   Avg relevance score: 0.78
```

---

## Teil 4: Baseline Evaluation

### 4.1 UDS3 Index vorbereiten

```python
from backend.agents.rag_context_service import RAGContextService
from uds3.your_strategy import YourUDS3Strategy

# Initialize UDS3
uds3 = YourUDS3Strategy()

# Index Corpus
corpus = [...]  # Ihre Dokumente
uds3.index_documents(corpus)

print("✅ UDS3 Index bereit")
```

### 4.2 Baseline Evaluation durchführen

```python
import asyncio
from tests.test_phase5_evaluation import Phase5Evaluator
from tests.ground_truth_dataset import GROUND_TRUTH_DATASET  # Ihr finales Dataset

# Initialize RAG Service (Baseline: nur Dense)
rag_service = RAGContextService(
    uds3_strategy=uds3,
    enable_hybrid_search=False,
    enable_query_expansion=False,
    enable_reranking=True  # Phase 4 Re-Ranking behalten
)

# Initialize Evaluator
evaluator = Phase5Evaluator(rag_service)
evaluator.test_cases = GROUND_TRUTH_DATASET  # Ihr Dataset

# Run Baseline Evaluation
async def run_baseline():
    result = await evaluator.evaluate_configuration(
        "Baseline (Dense-Only)",
        enable_hybrid=False,
        enable_query_expansion=False
    )
    return result

baseline_result = asyncio.run(run_baseline())
```

### 4.3 Baseline-Metriken dokumentieren

**Erwartete Werte (basierend auf Erfahrung):**
- NDCG@10: ~0.60-0.70
- MRR: ~0.50-0.60
- Recall@10: ~0.65-0.75
- Precision@5: ~0.55-0.65
- Latenz: ~80-100ms

**Speichern:**
```python
import json

with open('docs/baseline_evaluation_results.json', 'w') as f:
    json.dump({
        'configuration': 'Baseline (Dense-Only)',
        'ndcg_at_10': baseline_result.ndcg_at_10,
        'mrr': baseline_result.mrr,
        'recall_at_10': baseline_result.recall_at_10,
        'precision_at_5': baseline_result.precision_at_5,
        'avg_latency_ms': baseline_result.avg_latency_ms,
        'p95_latency_ms': baseline_result.p95_latency_ms,
        'pass_rate': baseline_result.pass_rate,
    }, f, indent=2)
```

---

## Teil 5: Hybrid Evaluation (Nach Phase 1 Deployment)

### 5.1 Hybrid Search aktivieren

```python
# Re-initialize mit Hybrid
rag_service_hybrid = RAGContextService(
    uds3_strategy=uds3,
    enable_hybrid_search=True,
    enable_query_expansion=False,
    enable_reranking=True
)

# Index BM25
rag_service_hybrid.index_corpus_for_hybrid_search(corpus)
```

### 5.2 Hybrid Evaluation durchführen

```python
evaluator_hybrid = Phase5Evaluator(rag_service_hybrid)
evaluator_hybrid.test_cases = GROUND_TRUTH_DATASET

async def run_hybrid():
    result = await evaluator_hybrid.evaluate_configuration(
        "Hybrid (Dense+Sparse+RRF)",
        enable_hybrid=True,
        enable_query_expansion=False
    )
    return result

hybrid_result = asyncio.run(run_hybrid())
```

### 5.3 Vergleich Baseline vs Hybrid

```python
from tests.test_phase5_evaluation import Phase5Evaluator

# Print Comparison
evaluator_hybrid.print_comparison([baseline_result, hybrid_result])
```

**Erwartete Verbesserung:**
- NDCG@10: +15-25%
- MRR: +20-30%
- Recall@10: +10-15%
- Latenz: +20-40ms

**Success-Kriterien:**
✅ NDCG@10 >0.75
✅ MRR >0.65
✅ Latenz <150ms

---

## Teil 6: Staging-Deployment Phase 2 (Query Expansion)

### 6.1 Ollama vorbereiten

```powershell
# Ollama starten
ollama serve

# Modell prüfen/pullen
ollama list
ollama pull llama2  # Falls nicht vorhanden
```

### 6.2 Deployment durchführen

```powershell
.\scripts\deploy_staging_phase2.ps1

# Mit custom Model
.\scripts\deploy_staging_phase2.ps1 -OllamaModel "mistral"
```

### 6.3 Backend neu starten

```powershell
python start_backend.py
```

**Prüfe Query Expansion in Logs:**
```powershell
Select-String -Path data/veritas_auto_server.log -Pattern "QueryExpansion|Ollama"
```

### 6.4 Tests durchführen

```powershell
# Query Expansion Unit Tests
pytest tests/test_phase5_hybrid_search.py::TestQueryExpansion -v

# Full Pipeline Integration
pytest tests/test_phase5_integration.py::TestFullPipeline -v
```

### 6.5 Monitoring (24-48 Stunden)

**Neue Metriken:**
- Query Expansion Latenz: <2000ms (LLM)
- Total Pipeline: <200ms Target (aber <250ms acceptable)
- QE Variant Count: ~2-3 per query

**Kritische Checks:**
- Ollama Errors: Should be 0
- Query Expansion Fallback Rate: <10% (falls Ollama down)

---

## Teil 7: Full Pipeline Evaluation

### 7.1 Hybrid + Query Expansion Evaluation

```python
# Re-initialize mit allen Features
rag_service_full = RAGContextService(
    uds3_strategy=uds3,
    enable_hybrid_search=True,
    enable_query_expansion=True,
    enable_reranking=True
)

rag_service_full.index_corpus_for_hybrid_search(corpus)

evaluator_full = Phase5Evaluator(rag_service_full)
evaluator_full.test_cases = GROUND_TRUTH_DATASET

async def run_full():
    result = await evaluator_full.evaluate_configuration(
        "Hybrid + Query Expansion",
        enable_hybrid=True,
        enable_query_expansion=True
    )
    return result

full_result = asyncio.run(run_full())
```

### 7.2 A/B/C Vergleich

```python
# Alle Konfigurationen vergleichen
evaluator_full.print_comparison([
    baseline_result,
    hybrid_result,
    full_result
])
```

**Erwartete Gesamt-Verbesserung:**
- NDCG@10: 0.65 → 0.75 → **0.80** (+23%)
- MRR: 0.55 → 0.68 → **0.75** (+36%)
- Recall@10: 0.70 → 0.78 → **0.85** (+21%)
- Latenz: 80ms → 110ms → **140ms** (+60ms)

---

## Teil 8: Evaluation Report erstellen

### 8.1 Report-Template

```markdown
# Phase 5 Evaluation Report

**Datum:** [Datum]
**Evaluator:** [Name]

## Executive Summary

- **Baseline NDCG@10:** [Wert]
- **Hybrid NDCG@10:** [Wert] (+[%])
- **Full Pipeline NDCG@10:** [Wert] (+[%])

**Empfehlung:** [Go/No-Go für Production]

## Test-Dataset

- Total Queries: [Anzahl]
- Kategorien: Legal ([X]), Technical ([X]), Environmental ([X]), Multi-Topic ([X])
- Avg Relevance Score: [Wert]

## Evaluation-Ergebnisse

### Baseline (Dense-Only)

| Metrik | Wert |
|--------|------|
| NDCG@10 | [X] |
| MRR | [X] |
| Recall@10 | [X] |
| Precision@5 | [X] |
| Latenz Avg | [X]ms |
| Latenz P95 | [X]ms |

### Hybrid (Dense+Sparse+RRF)

[Gleiche Tabelle]

**Delta vs Baseline:**
- NDCG@10: +[%]
- MRR: +[%]

### Full Pipeline (Hybrid + QE)

[Gleiche Tabelle]

**Delta vs Baseline:**
- NDCG@10: +[%]
- MRR: +[%]

## Kategorien-Analyse

[Breakdown nach Legal, Technical, etc.]

## Latenz-Analyse

[P50/P95/P99 Latency breakdown]

## Empfehlungen

1. [Go/No-Go]
2. [Rollout-Strategy]
3. [Weitere Optimierungen]

## ROI-Berechnung

[Wenn möglich: Business Value der Verbesserung]
```

---

## Teil 9: Production Rollout Plan

### 9.1 Gradual Rollout Strategy

**Woche 1: 10% Rollout**
```powershell
$env:VERITAS_ROLLOUT_PERCENTAGE = "10"
$env:VERITAS_ENABLE_HYBRID_SEARCH = "true"
$env:VERITAS_ENABLE_QUERY_EXPANSION = "false"  # Noch nicht QE
```

**Monitoring:** Latenz, Error Rate, User Feedback

**Woche 2: 25% Rollout** (wenn 10% OK)
```powershell
$env:VERITAS_ROLLOUT_PERCENTAGE = "25"
```

**Woche 3: 50% Rollout**
```powershell
$env:VERITAS_ROLLOUT_PERCENTAGE = "50"
$env:VERITAS_ENABLE_QUERY_EXPANSION = "true"  # QE aktivieren
```

**Woche 4: 100% Rollout**
```powershell
$env:VERITAS_ROLLOUT_PERCENTAGE = "100"
```

### 9.2 Success-Kriterien pro Stufe

✅ **Fortfahren wenn:**
- Latenz P95 <200ms
- Error Rate <1%
- User Satisfaction ≥ Baseline

❌ **Rollback wenn:**
- Latenz P95 >250ms
- Error Rate >5%
- Kritische Bugs

### 9.3 Rollback-Procedure

```powershell
# Sofortiger Rollback
$env:VERITAS_ENABLE_HYBRID_SEARCH = "false"
$env:VERITAS_ENABLE_QUERY_EXPANSION = "false"

# Backend neu starten
python start_backend.py
```

---

## Checkliste

### Staging Phase 1
- [ ] Config validiert
- [ ] Deployment-Script ausgeführt
- [ ] Backend gestartet
- [ ] BM25 Index erstellt
- [ ] Unit Tests bestanden
- [ ] Integration Tests bestanden
- [ ] 24h Monitoring OK
- [ ] Latenz <200ms
- [ ] Error Rate <1%

### Ground-Truth Dataset
- [ ] 20-30 Test-Cases erstellt
- [ ] Alle Kategorien abgedeckt
- [ ] Relevanz-Scores vergeben
- [ ] Dataset validiert
- [ ] In test_phase5_evaluation.py integriert

### Baseline Evaluation
- [ ] UDS3 Index erstellt
- [ ] Baseline Evaluation durchgeführt
- [ ] Metriken dokumentiert
- [ ] JSON-Report gespeichert

### Staging Phase 2
- [ ] Ollama läuft
- [ ] llama2 Modell verfügbar
- [ ] Deployment-Script ausgeführt
- [ ] Backend gestartet
- [ ] Query Expansion in Logs sichtbar
- [ ] Tests bestanden
- [ ] 24h Monitoring OK

### Full Evaluation
- [ ] Hybrid Evaluation durchgeführt
- [ ] Full Pipeline Evaluation durchgeführt
- [ ] A/B/C Vergleich erstellt
- [ ] Evaluation Report geschrieben
- [ ] Empfehlung dokumentiert

### Production Rollout
- [ ] Rollout-Plan erstellt
- [ ] 10% Rollout erfolgreich
- [ ] 25% Rollout erfolgreich
- [ ] 50% Rollout erfolgreich
- [ ] 100% Rollout erfolgreich

---

## Support & Troubleshooting

**Problem:** BM25 Index schlägt fehl
```python
# Check rank-bm25 Installation
pip install rank-bm25

# Prüfe Dokumente
print(f"Corpus size: {len(corpus)}")
```

**Problem:** Ollama nicht erreichbar
```powershell
# Test Ollama
curl http://localhost:11434/api/tags
```

**Problem:** Evaluation dauert zu lange
- Reduziere Test-Dataset auf 10-15 Queries für schnelle Iteration
- Verwende Cache wo möglich

**Problem:** Metriken nicht wie erwartet
- Prüfe Ground-Truth Relevanz-Scores
- Vergleiche mit manueller Review der Top-5 Ergebnisse

---

**Ende des Deployment & Evaluation Guide**
