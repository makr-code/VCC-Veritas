# Baseline-Evaluation Integration Complete

**Status:** ✅ **READY FOR TESTING**  
**Datum:** 06.10.2025  
**Komponenten:** run_baseline_evaluation.py + RAG Evaluator Integration  

---

## 📋 Zusammenfassung

Die Baseline-Evaluation ist **fertig implementiert** und bereit für den ersten echten Testlauf mit UDS3 + Ollama + IntelligentMultiAgentPipeline.

### Was wurde implementiert?

| Komponente | Status | Details |
|-----------|--------|---------|
| **RAG Evaluator - Pipeline Integration** | ✅ Complete | `_run_pipeline()` nutzt jetzt `IntelligentPipelineRequest` |
| **Response Mapping** | ✅ Complete | Konvertiert `IntelligentPipelineResponse` → Standard-Format |
| **Entity Extraction** | ✅ Complete | `_extract_entities_from_response()` für Pipeline-Output |
| **Baseline Script** | ✅ Complete | `backend/evaluation/run_baseline_evaluation.py` (194 Zeilen) |
| **Auto-Initialization** | ✅ Complete | Pipeline initialisiert UDS3/Ollama/Agents automatisch |
| **CLI Interface** | ✅ Complete | `--mode {baseline,comparative}` |

---

## 🚀 Verwendung

### 1. Baseline-Evaluation durchführen

```powershell
cd c:\VCC\veritas
python backend/evaluation/run_baseline_evaluation.py --mode baseline
```

**Output:**
- Console-Summary mit Metriken
- JSON-Report: `backend/evaluation/baseline_evaluation_report.json`

**Erwartete Metriken:**
- Precision@5: ~60-75%
- Recall@20: ~70%
- MRR: ~0.65-0.80
- Hallucination Rate: ~5%
- Pass Rate: ~60-75%

### 2. Comparative Evaluation (temporär deaktiviert)

```powershell
python backend/evaluation/run_baseline_evaluation.py --mode comparative
```

**Status:** Leitet zur Standard-Baseline um.  
**Grund:** Re-Ranking-Toggle muss in RAGContextService noch verifiziert werden.  
**Roadmap:** Phase 3+

---

## 🔧 Implementierungsdetails

### RAG Evaluator - Pipeline Integration

**Datei:** `backend/evaluation/veritas_rag_evaluator.py`

**Neue/Geänderte Methoden:**

#### `_run_pipeline(query: str)` - Zeilen 360-427
```python
async def _run_pipeline(self, query: str) -> Dict[str, Any]:
    """
    Führt Pipeline aus (echte Pipeline oder Mock für Testing).
    """
    if self.pipeline:
        # Echte Pipeline-Ausführung
        from backend.agents.veritas_intelligent_pipeline import IntelligentPipelineRequest
        
        request = IntelligentPipelineRequest(
            query_id=f"eval_{hash(query)}",
            query_text=query,
            user_id="evaluator",
            session_id="baseline_evaluation"
        )
        
        response = await self.pipeline.process_intelligent_query(request)
        
        # Konvertiere Response zu Standard-Format
        return {
            "answer": response.response_text,
            "documents": response.sources,
            "entities": self._extract_entities_from_response(response),
            "graph": {
                "related_entities": response.rag_context.get("entities", []),
                "relationships": response.rag_context.get("relationships", [])
            },
            "meta": {
                "reranking_applied": response.rag_context.get("reranking_applied", False),
                "duration_ms": response.total_processing_time * 1000,
                "confidence_score": response.confidence_score,
                "agents_used": list(response.agent_results.keys())
            }
        }
    
    # Fallback: Mock-Response
    return {...}
```

#### `_extract_entities_from_response(response)` - NEU
```python
def _extract_entities_from_response(self, response) -> List[str]:
    """
    Extrahiert Entities aus Pipeline-Response.
    
    Quellen:
    - response.rag_context.get("entities", [])
    - agent_result.get("entities", []) für alle Agents
    
    Returns: Deduplizierte Liste
    """
```

---

### Baseline-Evaluation-Script

**Datei:** `backend/evaluation/run_baseline_evaluation.py` (194 Zeilen)

**Funktionen:**

#### `async def initialize_pipeline()`
- Erstellt `IntelligentMultiAgentPipeline(max_workers=5)`
- Ruft `pipeline.initialize()` auf
  - Initialisiert intern: Ollama, UDS3, VERITAS Agents, RAG Service
- Validiert `pipeline.uds3_strategy` (hard requirement)
- Wirft `RuntimeError` bei Fehlern

#### `async def run_baseline_evaluation()`
**Workflow:**
1. Pipeline initialisieren
2. RAG Evaluator erstellen
3. Golden Dataset laden (5 Test-Cases)
4. Evaluation durchführen
5. Report speichern (`baseline_evaluation_report.json`)
6. Console-Summary ausgeben

**Cleanup:**
- `pipeline.executor.shutdown(wait=True)` in `finally`-Block

#### `async def run_comparative_evaluation()`
**Status:** Temporär deaktiviert  
**Redirect:** Ruft `run_baseline_evaluation()` auf  
**Warnung:** "Re-Ranking toggle needs to be implemented in RAGContextService"

---

## 🧪 Nächste Schritte

### IMMEDIATE: Ersten echten Testlauf durchführen

**Voraussetzungen prüfen:**
```powershell
# 1. Ollama läuft?
ollama list

# 2. PostgreSQL läuft? (UDS3 Backend)
# Check in Task Manager oder Services

# 3. Neo4j läuft? (UDS3 Graph)
# Check in Task Manager oder Services

# 4. ChromaDB konfiguriert?
# Check config/config.py
```

**Evaluation starten:**
```powershell
cd c:\VCC\veritas
python backend/evaluation/run_baseline_evaluation.py --mode baseline
```

**Expected Issues (mögliche Fehler):**

1. **UDS3 nicht verfügbar:**
   ```
   RuntimeError: RAG Integration (UDS3) ist nicht verfügbar!
   ```
   **Lösung:** UDS3-Backend (PostgreSQL, Neo4j, ChromaDB) starten

2. **Ollama nicht erreichbar:**
   ```
   RuntimeError: Ollama Client Initialisierung fehlgeschlagen
   ```
   **Lösung:** `ollama serve` im Terminal starten

3. **Keine Dokumente in UDS3:**
   ```
   Pass Rate: 0% (keine expected_documents gefunden)
   ```
   **Lösung:** Normal für erste Evaluation - Golden Dataset muss mit echten Doc-IDs aktualisiert werden

4. **Pipeline-Timeout:**
   ```
   Agent execution timed out
   ```
   **Lösung:** `max_workers` erhöhen oder `timeout` in Pipeline-Config anpassen

---

## 📊 Expected Baseline Results

### Scenario 1: UDS3 leer (keine Dokumente)
```
Pass Rate: 0-10%
Precision@5: 0%
Hallucination Rate: >50% (LLM generiert ohne Context)
```
**Normal:** Datenbank muss erst befüllt werden

### Scenario 2: UDS3 teilweise befüllt
```
Pass Rate: 30-50%
Precision@5: 40-60%
Hallucination Rate: 10-20%
```
**Erwartbar:** Einige Test-Cases finden Dokumente

### Scenario 3: UDS3 gut befüllt
```
Pass Rate: 60-75%
Precision@5: 60-75%
Hallucination Rate: 3-8%
MRR: 0.65-0.80
```
**Target:** Dies sollte der Production-Baseline entsprechen

---

## 🔍 Debugging

### Evaluator-Logs aktivieren

**In:** `backend/evaluation/veritas_rag_evaluator.py` (Zeile 34)

```python
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Detailliertes Logging
```

### Pipeline-Logs aktivieren

**In:** `backend/agents/veritas_intelligent_pipeline.py`

```python
logger.setLevel(logging.DEBUG)
```

### Testlauf mit einzelnem Test-Case

**Golden Dataset temporär reduzieren:**

```python
# In run_baseline_evaluation.py nach load_golden_dataset():
evaluator.test_cases = evaluator.test_cases[:1]  # Nur erster Test-Case
```

---

## 📄 Generierte Dateien

### Baseline Report

**Datei:** `backend/evaluation/baseline_evaluation_report.json`

**Struktur:**
```json
{
  "summary": {
    "total_test_cases": 5,
    "passed_test_cases": 3,
    "failed_test_cases": 2,
    "pass_rate": 0.6,
    "avg_retrieval_score": 0.72,
    "avg_context_score": 0.68,
    "avg_answer_score": 0.75,
    "avg_overall_score": 0.71,
    "performance_by_category": {
      "legal": 0.80,
      "building": 0.65,
      "environmental": 0.70,
      "social": 0.60
    },
    "performance_by_complexity": {
      "simple": 0.85,
      "medium": 0.70,
      "complex": 0.55,
      "multi_hop": 0.50
    }
  },
  "detailed_results": [...]
}
```

---

## ✅ Checklist vor erstem Testlauf

- [ ] **Ollama läuft:** `ollama list` zeigt Modelle
- [ ] **PostgreSQL läuft:** Port 5432 erreichbar
- [ ] **Neo4j läuft:** Port 7474/7687 erreichbar (optional)
- [ ] **ChromaDB konfiguriert:** Path existiert
- [ ] **Golden Dataset existiert:** `backend/evaluation/golden_dataset_examples.json`
- [ ] **Python Dependencies:** `sentence-transformers` installiert (Re-Ranking)
- [ ] **Backup erstellt:** Git commit vor Testlauf

---

## 🎯 Success Criteria

### Minimum (Phase 1):
✅ Script läuft durch ohne Crash  
✅ Report wird generiert  
✅ Console-Summary wird ausgegeben  

### Good (Phase 2):
✅ Pass Rate > 0% (mindestens 1 Test-Case passed)  
✅ Keine RuntimeErrors  
✅ Alle Metriken berechnet (Precision@K, Recall@K, MRR)  

### Excellent (Phase 3):
✅ Pass Rate > 60%  
✅ Precision@5 > 60%  
✅ Hallucination Rate < 10%  
✅ MRR > 0.65  

---

## 🚦 Status

**Current State:**  
- ✅ Code implementiert
- ✅ Script getestet (Help-Output funktioniert)
- ⏳ **READY FOR FIRST RUN**

**Next Action:**  
```powershell
python backend/evaluation/run_baseline_evaluation.py --mode baseline
```

**Expected Duration:** 2-5 Minuten (je nach Pipeline-Performance)

---

**Author:** VERITAS System  
**Version:** 1.0  
**Last Updated:** 06.10.2025
