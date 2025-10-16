# VERITAS RAG Evaluation Framework

Automatisierte Qualitätsbewertung für RAG-Pipeline mit Golden Dataset.

---

## 📦 Komponenten

| Datei | Zweck | Zeilen |
|-------|-------|--------|
| `veritas_rag_evaluator.py` | RAG Evaluator mit Metriken | 850 |
| `run_baseline_evaluation.py` | Baseline-Evaluation-Script | 194 |
| `golden_dataset_schema.json` | JSON-Schema für Test-Cases | 120 |
| `golden_dataset_examples.json` | 5 Beispiel-Test-Cases | 180 |

---

## 🚀 Quick Start

### Baseline-Evaluation durchführen

```powershell
cd c:\VCC\veritas
python backend/evaluation/run_baseline_evaluation.py --mode baseline
```

**Output:**
- Console-Summary mit Metriken
- JSON-Report: `baseline_evaluation_report.json`

---

## 📊 Metriken

### Retrieval
- **Precision@K:** Anteil relevanter Dokumente in Top-K
- **Recall@K:** Anteil gefundener relevanter Dokumente
- **MRR:** Mean Reciprocal Rank
- **NDCG:** Normalized Discounted Cumulative Gain

### Context
- **Relevance Score:** LLM-basierte Kontext-Bewertung
- **Graph Enrichment:** Anzahl gefundener Relations

### Answer
- **Faithfulness:** Treue zum Context
- **Hallucination Rate:** Anteil halluzinierter Fakten
- **Completeness:** Vollständigkeit der Antwort

---

## 📁 Golden Dataset

### Schema

```json
{
  "id": "test_001",
  "category": "legal",
  "complexity": "simple",
  "question": "Was regelt § 110 BGB?",
  "expected_retrieval": {
    "documents": ["doc_bgb_110"],
    "entities": ["BGB", "§ 110"],
    "min_relevance_score": 0.7
  },
  "expected_answer": {
    "must_contain": ["Taschengeld"],
    "must_not_contain": ["Geldtransport"]
  },
  "hallucination_triggers": ["Geldtransport"]
}
```

### Test-Cases (aktuell: 5)

1. **bgb_110_basic** - Taschengeldparagraph (legal/simple)
2. **bgb_110_practical** - Praktische Anwendung (legal/medium)
3. **baurecht_baugenehmigung** - Baugenehmigung (building/medium)
4. **umweltrecht_emissionsgrenzwerte** - Emissionsschutz (environmental/complex)
5. **sozialrecht_wohngeld** - Wohngeld (social/multi_hop)

**Erweitern auf 50+:** Siehe `TODO.md`

---

## 📈 Expected Results

### Mit Re-Ranking (Standard)
```
Precision@5: ~75%
Recall@20: ~70%
MRR: ~0.80
Hallucination Rate: ~5%
Pass Rate: ~75%
```

### Ohne Re-Ranking (Baseline)
```
Precision@5: ~60%
MRR: ~0.65
Pass Rate: ~60%
```

**Re-Ranking Impact:** +15% Precision@5

---

## 🔧 Konfiguration

### RAG Evaluator

```python
from backend.evaluation.veritas_rag_evaluator import RAGEvaluator

evaluator = RAGEvaluator(
    pipeline=my_pipeline,         # IntelligentMultiAgentPipeline
    ollama_client=my_client,      # Ollama AsyncClient
    strict_mode=False             # True für strengere Bewertung
)
```

### Pipeline Integration

```python
# Automatische Initialisierung
from backend.agents.veritas_intelligent_pipeline import IntelligentMultiAgentPipeline

pipeline = IntelligentMultiAgentPipeline(max_workers=5)
await pipeline.initialize()  # Lädt UDS3, Ollama, Agents

# Evaluator nutzt Pipeline automatisch
evaluator = RAGEvaluator(pipeline=pipeline, ollama_client=pipeline.ollama_client)
```

---

## 🧪 Testing

### Mock-Pipeline (ohne UDS3)

```python
evaluator = RAGEvaluator(pipeline=None)  # Nutzt Mock-Data
summary = await evaluator.run_evaluation()
```

### Filtered Evaluation

```python
# Nur legal Test-Cases
summary = await evaluator.run_evaluation(filter_category="legal")

# Nur simple Test-Cases
summary = await evaluator.run_evaluation(filter_complexity="simple")

# Spezifische IDs
summary = await evaluator.run_evaluation(filter_ids=["bgb_110_basic"])
```

---

## 📊 Report-Format

### Console-Output

```
════════════════════════════════════════
VERITAS RAG EVALUATION SUMMARY
════════════════════════════════════════
📊 Gesamt-Statistik
────────────────────────────────────────
  Total Test Cases: 5
  Passed: 3 ✅
  Failed: 2 ❌
  Pass Rate: 60.0%

📈 Performance nach Kategorie
────────────────────────────────────────
  legal: 80.0%
  building: 65.0%

🎯 Retrieval-Metriken
────────────────────────────────────────
  Precision@5: 72.3%
  Recall@20: 68.5%
  MRR: 0.78
```

### JSON-Report

```json
{
  "summary": {...},
  "detailed_results": [
    {
      "test_id": "bgb_110_basic",
      "passed": true,
      "retrieval_score": 0.85,
      "context_score": 0.78,
      "answer_score": 0.82,
      "overall_score": 0.81,
      "duration_ms": 1250
    }
  ]
}
```

---

## 🐛 Troubleshooting

### UDS3 nicht verfügbar
```
RuntimeError: RAG Integration (UDS3) ist nicht verfügbar!
```
**Lösung:** PostgreSQL, Neo4j, ChromaDB starten

### Ollama nicht erreichbar
```
RuntimeError: Ollama Client Initialisierung fehlgeschlagen
```
**Lösung:** `ollama serve` starten

### Keine Dokumente gefunden
```
Pass Rate: 0% - Alle retrieval_scores = 0
```
**Lösung:** UDS3-Datenbank befüllen oder Golden Dataset mit echten Doc-IDs aktualisieren

---

## 📚 Dokumentation

- **Implementation Guide:** `docs/RERANKING_EVALUATION_IMPLEMENTATION.md` (600+ Zeilen)
- **Phase 2 Complete:** `docs/PHASE_2_EVALUATION_COMPLETE.md`
- **Integration Complete:** `docs/BASELINE_EVALUATION_INTEGRATION_COMPLETE.md`
- **Hyperscaler Comparison:** Siehe Implementation Guide

---

## 🎯 Roadmap

### Phase 1: Re-Ranking ✅ DONE
- Cross-Encoder-Modell (ms-marco-MiniLM-L-6-v2)
- Zwei-Stufen-Retrieval (Recall → Precision)

### Phase 2: Evaluation ✅ DONE
- Golden Dataset Framework
- RAG Evaluator mit 8 Metriken
- Baseline-Evaluation-Script

### Phase 3: Supervisor-Agent ⏳ NEXT
- Hierarchische Orchestrierung
- Query-Dekomposition
- Intelligente Agent-Selektion

### Phase 4: Agent Communication ⏳ PLANNED
- AgentMessage-Schema
- Event Bus
- Agent Registry

---

## ⚙️ Dependencies

```bash
# Core
pip install asyncio logging dataclasses

# Re-Ranking
pip install sentence-transformers

# Ollama
pip install ollama

# Optional: Jupyter (für interaktive Evaluation)
pip install jupyter notebook
```

---

## 📝 License

Internal VERITAS Project - Proprietary

---

**Version:** 1.0  
**Last Updated:** 06.10.2025  
**Author:** VERITAS System
