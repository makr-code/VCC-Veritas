# Phase 5 Deployment - START HERE

**Status:** ✅ Code Complete | 🚀 Ready for Deployment  
**Datum:** 7. Oktober 2025

---

## 🎯 Quick Decision Guide

**Haben Sie bereits:**
- [ ] Produktiv-Daten in UDS3 indexiert?
- [ ] 20+ repräsentative Dokumente im Corpus?
- [ ] Ollama installiert mit llama2 Modell?

### ➡️ JA zu allen → [Sofort deployen](#sofort-deployment)
### ➡️ NEIN → [Mit Tests beginnen](#mit-tests-beginnen)

---

## 🧪 Mit Tests beginnen

### Schritt 1: Unit Tests ausführen

```powershell
# Alle Phase 5 Unit Tests
pytest tests/test_phase5_hybrid_search.py -v

# Erwartung: 25 Tests PASSED
```

**Was wird getestet:**
- ✅ BM25 Sparse Retrieval (9 Tests)
- ✅ RRF Fusion (8 Tests)
- ✅ Hybrid Retrieval (4 Tests)
- ✅ Query Expansion (4 Tests)

### Schritt 2: Integration Tests ausführen

```powershell
# Integration Tests mit Mock-Daten
pytest tests/test_phase5_integration.py -v

# Erwartung: 18 Tests PASSED
```

**Was wird getestet:**
- ✅ Full Pipeline End-to-End
- ✅ Real-World Queries (Legal, Technical, Environmental)
- ✅ Edge Cases
- ✅ A/B Comparison Dense vs Hybrid

### Schritt 3: Konfigurations-Test

```powershell
# Test Phase5Config
python config/phase5_config.py

# Erwartung: ✅ Validation PASS für alle Configs
```

### Schritt 4: Monitoring-Test

```powershell
# Test Phase5Monitor
python backend/monitoring/phase5_monitoring.py

# Erwartung: Stats werden korrekt geloggt
```

---

## 🚀 Sofort-Deployment

### Voraussetzungen prüfen

```powershell
# 1. Python Dependencies
pip list | Select-String "rank-bm25|httpx"

# Falls fehlt:
pip install rank-bm25 httpx

# 2. Ollama (nur für Phase 2)
curl http://localhost:11434/api/tags

# Falls fehlt:
# Download: https://ollama.ai
ollama serve
ollama pull llama2
```

### Staging Phase 1 deployen

```powershell
# Deployment ausführen
.\scripts\deploy_staging_phase1.ps1

# Output zeigt:
# ✅ Environment konfiguriert
# ✅ Configuration valid
# 🚀 Ready to start backend
```

### Backend starten

```powershell
# Backend mit Phase 5 Config starten
python start_backend.py
```

**Logs überwachen:**
```powershell
# In separatem Terminal
Get-Content data/veritas_auto_server.log -Wait -Tail 50
```

**Suche nach Phase 5 Aktivität:**
```powershell
Select-String -Path data/veritas_auto_server.log -Pattern "Phase5|Hybrid|BM25" | Select-Object -Last 10
```

---

## 📊 Evaluation (mit echten Daten)

### Schritt 1: Ground-Truth Dataset erstellen

```powershell
# Template öffnen
code tests/ground_truth_dataset_template.py
```

**TODO in der Datei:**
1. Ersetze `"TODO: Replace with actual document IDs"` mit echten Doc-IDs
2. Füge 15-20 weitere Test-Cases hinzu (insgesamt 25-30)
3. Vergib Relevanz-Scores (0.0-1.0) basierend auf manueller Review

**Zeitaufwand:** ~10-20 Stunden für 25 hochwertige Test-Cases

### Schritt 2: Dataset validieren

```powershell
# Nach Fertigstellung
python tests/ground_truth_dataset_template.py

# Erwartung:
# ✅ Dataset validation passed!
# 📊 Total queries: 25+
```

### Schritt 3: Baseline Evaluation

```python
# In Python Console oder Jupyter Notebook
import asyncio
from backend.agents.rag_context_service import RAGContextService
from tests.test_phase5_evaluation import Phase5Evaluator
from tests.ground_truth_dataset import GROUND_TRUTH_DATASET

# Initialize (Baseline: nur Dense)
rag_service = RAGContextService(
    uds3_strategy=your_uds3_strategy,  # Ihre UDS3 Instanz
    enable_hybrid_search=False,
    enable_query_expansion=False
)

evaluator = Phase5Evaluator(rag_service)
evaluator.test_cases = GROUND_TRUTH_DATASET

# Run Baseline
baseline = await evaluator.evaluate_configuration(
    "Baseline",
    enable_hybrid=False,
    enable_query_expansion=False
)

print(f"Baseline NDCG@10: {baseline.ndcg_at_10:.3f}")
print(f"Baseline MRR: {baseline.mrr:.3f}")
```

### Schritt 4: Hybrid Evaluation

```python
# Mit Hybrid Search
rag_hybrid = RAGContextService(
    uds3_strategy=your_uds3_strategy,
    enable_hybrid_search=True,
    enable_query_expansion=False
)

# Index für BM25
rag_hybrid.index_corpus_for_hybrid_search(your_corpus)

evaluator_hybrid = Phase5Evaluator(rag_hybrid)
evaluator_hybrid.test_cases = GROUND_TRUTH_DATASET

hybrid = await evaluator_hybrid.evaluate_configuration(
    "Hybrid",
    enable_hybrid=True,
    enable_query_expansion=False
)

# Vergleich
evaluator_hybrid.print_comparison([baseline, hybrid])
```

---

## 🔧 Troubleshooting

### Problem: Tests schlagen fehl

```powershell
# Dependencies prüfen
pip install -r requirements.txt

# Einzelne Test-Komponente debuggen
pytest tests/test_phase5_hybrid_search.py::TestSparseRetrieval::test_initialization -v
```

### Problem: "rank-bm25 not found"

```powershell
pip install rank-bm25
```

### Problem: Ollama Timeout

```powershell
# Ollama Status prüfen
curl http://localhost:11434/api/tags

# Timeout erhöhen (in PowerShell)
$env:VERITAS_OLLAMA_TIMEOUT = "60"
```

### Problem: BM25 zu langsam

```powershell
# Cache TTL erhöhen
$env:VERITAS_BM25_CACHE_TTL = "7200"

# Oder Top-K reduzieren
$env:VERITAS_HYBRID_SPARSE_TOP_K = "15"
```

### Problem: Keine UDS3 Strategie

Falls Sie UDS3 noch nicht haben, können Sie Phase 5 trotzdem testen:

```python
# Mock UDS3 für Testing
from tests.test_phase5_integration import mock_uds3_strategy

# Verwenden in Tests
rag_service = RAGContextService(
    uds3_strategy=mock_uds3_strategy(),
    enable_hybrid_search=True
)
```

---

## 📁 Wichtige Dateien

### Konfiguration
- `config/phase5_config.py` - Feature-Toggles, Environment-Variables
- `scripts/deploy_staging_phase1.ps1` - Phase 1 Deployment
- `scripts/deploy_staging_phase2.ps1` - Phase 2 Deployment

### Tests
- `tests/test_phase5_hybrid_search.py` - 25 Unit Tests
- `tests/test_phase5_integration.py` - 18 Integration Tests
- `tests/test_phase5_evaluation.py` - Evaluation Framework
- `tests/ground_truth_dataset_template.py` - Dataset Template

### Dokumentation
- `docs/phase_5_quick_start.md` - Kompakte Anleitung
- `docs/phase_5_deployment_evaluation_guide.md` - Vollständiger Guide
- `docs/phase_5_summary.md` - Gesamtübersicht

### Monitoring
- `backend/monitoring/phase5_monitoring.py` - Performance Tracking
- Logs: `data/veritas_auto_server.log`

---

## ✅ Nächste Schritte - Ihre Wahl

### Option A: Tests ausführen (5 Minuten)
```powershell
pytest tests/test_phase5*.py -v
```
→ Validiert dass alles funktioniert

### Option B: Staging Phase 1 deployen (10 Minuten)
```powershell
.\scripts\deploy_staging_phase1.ps1
python start_backend.py
```
→ Hybrid Search im Staging testen

### Option C: Ground-Truth Dataset erstellen (10-20 Stunden)
```powershell
code tests/ground_truth_dataset_template.py
```
→ Vorbereitung für Evaluation

### Option D: Alle Dokumentation lesen (30 Minuten)
- `docs/phase_5_quick_start.md`
- `docs/phase_5_deployment_evaluation_guide.md`
→ Vollständiges Verständnis

---

## 🎯 Empfohlener Workflow

**Heute (30 Minuten):**
1. ✅ Tests ausführen → Validierung
2. ✅ Deployment-Script testen (ohne Backend-Start)
3. ✅ Dokumentation überfliegen

**Diese Woche:**
1. Staging Phase 1 deployen
2. 24h Monitoring
3. Mit Ground-Truth Dataset beginnen

**Nächste Woche:**
1. Baseline + Hybrid Evaluation
2. Staging Phase 2 (Query Expansion)
3. Full Pipeline Evaluation

**Übernächste Woche:**
1. Evaluation Report
2. Production Rollout Plan
3. Gradual Rollout starten (10% → 25% → 50% → 100%)

---

**WICHTIG:** Sie müssen NICHTS sofort tun. Alle Komponenten sind fertig und warten auf Sie! 🎉

Wählen Sie einfach den nächsten Schritt der zu Ihrer Situation passt.

**Fragen? Siehe Dokumentation in `docs/` oder führen Sie Tests aus für Hands-On Verständnis!**
