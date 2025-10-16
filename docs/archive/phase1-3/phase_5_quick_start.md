# Phase 5 Deployment - Quick Start Guide

**Ziel:** Staging-Deployment + Evaluation in 4 Wochen

---

## 🚀 Woche 1: Staging Phase 1 (Hybrid Search)

### Tag 1: Setup & Deployment

```powershell
# 1. Deployment ausführen
.\scripts\deploy_staging_phase1.ps1

# 2. Backend starten
python start_backend.py

# 3. Tests durchführen
pytest tests/test_phase5_hybrid_search.py -v
pytest tests/test_phase5_integration.py::TestFullPipeline -v
```

### Tag 2-7: Monitoring

```powershell
# Logs überwachen
Get-Content data/veritas_auto_server.log -Wait -Tail 50

# Metriken prüfen
Select-String -Path data/veritas_auto_server.log -Pattern "Phase5.*latency"
```

**Success-Kriterien:**
- ✅ Latenz P95 <200ms
- ✅ Error Rate <1%
- ✅ BM25 Cache Hit Rate >60%

---

## 📊 Woche 2: Ground-Truth Dataset + Baseline Evaluation

### Tag 1-3: Dataset erstellen

```powershell
# Template öffnen
code tests/ground_truth_dataset_template.py

# TODO-Schritte:
# 1. Real Document IDs eintragen (20-30 Test-Cases)
# 2. Relevanz-Scores vergeben (0.0-1.0)
# 3. Validieren
python tests/ground_truth_dataset_template.py
```

**Zeit:** ~10-20 Stunden für 25 Test-Cases

### Tag 4-5: Baseline Evaluation

```python
# UDS3 Index vorbereiten
from backend.agents.rag_context_service import RAGContextService

rag_service = RAGContextService(
    uds3_strategy=uds3,
    enable_hybrid_search=False,
    enable_query_expansion=False
)

# Evaluation durchführen
from tests.test_phase5_evaluation import Phase5Evaluator
from tests.ground_truth_dataset import GROUND_TRUTH_DATASET

evaluator = Phase5Evaluator(rag_service)
evaluator.test_cases = GROUND_TRUTH_DATASET

baseline_result = await evaluator.evaluate_configuration(
    "Baseline (Dense-Only)",
    enable_hybrid=False,
    enable_query_expansion=False
)
```

### Tag 6-7: Hybrid Evaluation

```python
# Mit Hybrid Search
rag_service_hybrid = RAGContextService(
    uds3_strategy=uds3,
    enable_hybrid_search=True,
    enable_query_expansion=False
)

rag_service_hybrid.index_corpus_for_hybrid_search(corpus)

evaluator_hybrid = Phase5Evaluator(rag_service_hybrid)
hybrid_result = await evaluator_hybrid.evaluate_configuration(
    "Hybrid",
    enable_hybrid=True,
    enable_query_expansion=False
)

# Vergleich
evaluator_hybrid.print_comparison([baseline_result, hybrid_result])
```

**Erwartete Verbesserung:**
- NDCG@10: +15-25%
- MRR: +20-30%

---

## 🔬 Woche 3: Staging Phase 2 (Query Expansion)

### Tag 1: Ollama Setup

```powershell
# Ollama starten
ollama serve

# Modell prüfen
ollama pull llama2
```

### Tag 2: Deployment

```powershell
# Phase 2 deployen
.\scripts\deploy_staging_phase2.ps1

# Backend neu starten
python start_backend.py
```

### Tag 3-7: Monitoring + Evaluation

```powershell
# Query Expansion in Logs
Select-String -Path data/veritas_auto_server.log -Pattern "QueryExpansion|Ollama"
```

```python
# Full Pipeline Evaluation
rag_service_full = RAGContextService(
    uds3_strategy=uds3,
    enable_hybrid_search=True,
    enable_query_expansion=True
)

evaluator_full = Phase5Evaluator(rag_service_full)
full_result = await evaluator_full.evaluate_configuration(
    "Hybrid + QE",
    enable_hybrid=True,
    enable_query_expansion=True
)

# A/B/C Vergleich
evaluator_full.print_comparison([
    baseline_result,
    hybrid_result,
    full_result
])
```

**Erwartete Gesamt-Verbesserung:**
- NDCG@10: +23% (0.65 → 0.80)
- MRR: +36% (0.55 → 0.75)

---

## 📈 Woche 4: Evaluation Report + Production Rollout

### Tag 1-2: Report schreiben

```markdown
# Phase 5 Evaluation Report

## Executive Summary
- Baseline NDCG@10: 0.65
- Hybrid NDCG@10: 0.75 (+15%)
- Full Pipeline NDCG@10: 0.80 (+23%)

**Empfehlung:** GO für Production Rollout

[Weitere Details siehe Template in deployment guide]
```

### Tag 3-7: Production Rollout

**Tag 3: 10% Rollout**
```powershell
$env:VERITAS_ROLLOUT_PERCENTAGE = "10"
$env:VERITAS_ENABLE_HYBRID_SEARCH = "true"
```

**Tag 4: 25% Rollout** (wenn OK)
```powershell
$env:VERITAS_ROLLOUT_PERCENTAGE = "25"
```

**Tag 5: 50% Rollout + Query Expansion**
```powershell
$env:VERITAS_ROLLOUT_PERCENTAGE = "50"
$env:VERITAS_ENABLE_QUERY_EXPANSION = "true"
```

**Tag 6-7: 100% Rollout**
```powershell
$env:VERITAS_ROLLOUT_PERCENTAGE = "100"
```

---

## ✅ Checkliste

### Voraussetzungen
- [ ] Phase 5 Code vollständig (2730 Zeilen)
- [ ] Tests laufen durch (43 Tests)
- [ ] Ollama installiert + llama2 Modell
- [ ] UDS3 funktionsfähig

### Woche 1
- [ ] Staging Phase 1 deployed
- [ ] BM25 Index erstellt
- [ ] 24h Monitoring OK
- [ ] Latenz <200ms

### Woche 2
- [ ] 20-30 Ground-Truth Test-Cases
- [ ] Baseline Evaluation durchgeführt
- [ ] Hybrid Evaluation durchgeführt
- [ ] Verbesserung +15-25% NDCG

### Woche 3
- [ ] Ollama Setup
- [ ] Staging Phase 2 deployed
- [ ] Full Pipeline Evaluation
- [ ] Gesamt-Verbesserung +23% NDCG

### Woche 4
- [ ] Evaluation Report geschrieben
- [ ] 10% Rollout erfolgreich
- [ ] 25% Rollout erfolgreich
- [ ] 50% Rollout erfolgreich
- [ ] 100% Rollout erfolgreich

---

## 🆘 Troubleshooting

**Problem:** Tests schlagen fehl
```powershell
# Dependencies prüfen
pip install rank-bm25 httpx

# Einzelne Tests debuggen
pytest tests/test_phase5_hybrid_search.py::TestSparseRetrieval -v
```

**Problem:** BM25 zu langsam
- Cache-TTL erhöhen: `$env:VERITAS_BM25_CACHE_TTL = "7200"`
- Top-K reduzieren: `$env:VERITAS_HYBRID_SPARSE_TOP_K = "15"`

**Problem:** Query Expansion Timeout
- Timeout erhöhen: `$env:VERITAS_OLLAMA_TIMEOUT = "60"`
- Oder QE temporär deaktivieren

**Problem:** Metriken schlechter als erwartet
- Ground-Truth Scores prüfen
- Top-5 Ergebnisse manuell reviewen
- Ggf. mehr Test-Cases hinzufügen

---

## 📚 Weitere Ressourcen

- **Vollständiger Guide:** `docs/phase_5_deployment_evaluation_guide.md`
- **Implementation Report:** `docs/phase_5_implementation_report.md`
- **Evaluation Guide:** `docs/phase_5_evaluation_guide.md`
- **Konfiguration:** `config/phase5_config.py`
- **Monitoring:** `backend/monitoring/phase5_monitoring.py`

---

**Viel Erfolg! 🚀**
