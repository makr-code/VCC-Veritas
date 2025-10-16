# Phase 5: Advanced RAG - Bestands-Analyse

**Datum:** 6. Oktober 2025  
**Status:** 🔍 Analyse abgeschlossen

---

## 📊 Vorhandene RAG-Komponenten

### ✅ **Bereits Implementiert**

#### 1. **Re-Ranking Service** (`backend/agents/veritas_reranking_service.py`)
**Status:** ✅ Vollständig implementiert (468 Zeilen)

**Features:**
- ✅ Cross-Encoder Re-Ranking (`cross-encoder/ms-marco-MiniLM-L-6-v2`)
- ✅ ReRankingConfig (top_k, initial_k, batch_size, score_threshold)
- ✅ Cache-Unterstützung (optional)
- ✅ Graceful Degradation (funktioniert ohne sentence-transformers)
- ✅ Performance-Optimierung (Batch-Processing)

**Metriken:**
```python
- Latenz: ~50-100ms für 20 Dokumente (CPU)
- Latenz: ~10-20ms für 20 Dokumente (GPU)
- Memory: ~500MB für Modell
```

**Integration:**
- ✅ Bereits in `RAGContextService` integriert
- ✅ Enable/Disable via Config (`enable_reranking: bool`)
- ✅ Two-Stage Retrieval: UDS3 (Top-20) → Re-Ranking (Top-5)

**Code-Beispiel:**
```python
from backend.agents.veritas_reranking_service import (
    get_reranking_service,
    ReRankingConfig
)

# Service initialisieren
reranking_service = get_reranking_service()

# Dokumente re-ranken
reranked_docs = await reranking_service.rerank_documents(
    query="Bauvorhaben Umweltauflagen",
    documents=initial_docs,  # Top-20 von UDS3
    top_k=5
)
```

---

#### 2. **RAG Evaluator** (`backend/evaluation/veritas_rag_evaluator.py`)
**Status:** ✅ Vollständig implementiert (839 Zeilen)

**Features:**
- ✅ **Retrieval-Metriken:**
  - Precision@K, Recall@K
  - MRR (Mean Reciprocal Rank)
  - NDCG@K (Normalized Discounted Cumulative Gain)
- ✅ **Context-Metriken:**
  - Context Relevance Score (LLM-as-Judge)
  - Context Precision/Recall
  - Graph Enrichment Rate
- ✅ **Answer-Metriken:**
  - Faithfulness
  - Completeness
  - Hallucination Rate

**Evaluation-Workflow:**
```python
@dataclass
class RetrievalMetrics:
    precision_at_k: Dict[int, float]  # @1, @5, @10
    recall_at_k: Dict[int, float]
    mean_reciprocal_rank: float
    ndcg_at_k: Dict[int, float]

@dataclass
class EvaluationResult:
    test_case_id: str
    query: str
    passed: bool
    retrieval_passed: bool
    context_passed: bool
    answer_passed: bool
    retrieved_docs: List[str]
    expected_docs: List[str]
```

**Integration:**
- ✅ Golden Dataset Support
- ✅ Automatisierte Evaluations
- ✅ Detaillierte Metriken-Reports

---

#### 3. **RAG Context Service** (`backend/agents/rag_context_service.py`)
**Status:** ✅ Vollständig implementiert (359 Zeilen)

**Features:**
- ✅ Unified RAG Interface
- ✅ UDS3 Integration (Vector + Graph + Relational)
- ✅ Re-Ranking Integration (optional)
- ✅ Normalized Response Formats

**RAGQueryOptions:**
```python
@dataclass
class RAGQueryOptions:
    limit_documents: int = 5
    include_vector: bool = True
    include_graph: bool = True
    include_relational: bool = True
    
    # Re-Ranking
    enable_reranking: bool = True
    reranking_initial_k: int = 20  # Initial Retrieval
    reranking_final_k: int = 5     # Nach Re-Ranking
```

**Two-Stage Retrieval:**
```
Stage 1: UDS3 Vector Search → Top-20 (Recall-optimiert)
Stage 2: Cross-Encoder Re-Ranking → Top-5 (Precision-optimiert)
Stage 3: Graph Context Synthesis
```

---

### ❌ **Noch NICHT Implementiert**

#### 1. **Sparse Retrieval (BM25/SPLADE)**
**Status:** ❌ Fehlt komplett

**Was fehlt:**
- BM25 Lexikalisches Matching
- SPLADE (optional)
- Hybrid Search (Dense + Sparse)
- Reciprocal Rank Fusion (RRF)

**Impact:** 
- Kein lexikalisches Matching für exakte Begriffe (§ 242 BGB, DIN 18040-1)
- Keine Hybrid-Search-Vorteile

---

#### 2. **Semantic Chunking**
**Status:** ❌ Fehlt komplett

**Aktuell:** Vermutlich fixed-size Chunking in UDS3

**Was fehlt:**
- Semantic-basierte Chunk-Grenzen
- Sentence-Level Similarity
- Overlap-Strategien für Context-Preservation

**Impact:**
- Chunk-Grenzen schneiden Sätze/Absätze durch
- Kontext-Verlust an Chunk-Grenzen

---

#### 3. **Hierarchical Chunking**
**Status:** ❌ Fehlt komplett

**Was fehlt:**
- Multi-Level Chunks (Paragraph → Section → Document)
- Parent-Child-Relationen
- Context-Expansion bei Retrieval

**Impact:**
- Kein hierarchischer Kontext
- Keine automatische Context-Expansion

---

#### 4. **Query Expansion & Reformulation**
**Status:** ❌ Fehlt komplett

**Was fehlt:**
- LLM-basierte Query-Expansion
- Synonym-Expansion
- Multi-Query Generation
- Query-Rewriting

**Impact:**
- Single-Query Retrieval (keine Multi-Perspektive)
- Kein verbesserter Recall durch Query-Varianten

---

#### 5. **MMR Diversity Re-Ranking**
**Status:** ❌ Fehlt

**Aktuell:** Cross-Encoder Re-Ranking (relevance-only)

**Was fehlt:**
- Maximal Marginal Relevance (MMR)
- Diversity-basierte Re-Ranking
- Deduplication

**Impact:**
- Mögliche redundante Results
- Keine Diversity-Optimierung

---

## 🎯 Phase 5 - Angepasste Roadmap

### Was wir ÜBERSPRINGEN können:
- ✅ **Cross-Encoder Re-Ranking** - Bereits vollständig implementiert
- ✅ **Evaluation Framework** - Bereits vorhanden (NDCG, MRR, Precision@K, Recall@K)
- ✅ **RAG Integration Layer** - Bereits vorhanden (RAGContextService)

### Was wir IMPLEMENTIEREN sollten:

#### **Phase 5.1: Sparse Retrieval & Hybrid Search** (Priorität 1)
**Zeitaufwand:** 6-8 Stunden  
**Code:** 300-400 Zeilen

**Deliverables:**
1. BM25 Sparse Retriever
2. Reciprocal Rank Fusion (RRF)
3. Hybrid Search Pipeline (Dense + Sparse)
4. Integration in RAGContextService

**Neue Features:**
```python
class HybridRetriever:
    async def retrieve_hybrid(
        query: str,
        top_k: int = 50
    ) -> List[ScoredChunk]:
        # Dense Retrieval (UDS3 Embeddings)
        dense_results = await uds3.vector_search(query, k=50)
        
        # Sparse Retrieval (BM25)
        sparse_results = await bm25.search(query, k=50)
        
        # Reciprocal Rank Fusion
        fused_results = rrf.fuse(dense_results, sparse_results)
        
        return fused_results[:top_k]
```

---

#### **Phase 5.2: Query Expansion** (Priorität 2)
**Zeitaufwand:** 4-5 Stunden  
**Code:** 200-300 Zeilen

**Deliverables:**
1. LLM-basierte Query-Expansion
2. Multi-Query Generation
3. Query-Rewriting
4. Integration in RAGContextService

**Neue Features:**
```python
class QueryExpander:
    async def expand_query(
        query: str,
        num_expansions: int = 3
    ) -> List[str]:
        # LLM-basierte Expansion
        expansions = await llm.expand(query, n=num_expansions)
        
        return [query] + expansions

# Usage
expanded_queries = await expander.expand_query(
    "Bauvorhaben Umweltauflagen"
)
# → ["Bauvorhaben Umweltauflagen",
#    "Umweltrechtliche Genehmigungen Bauprojekte",
#    "Umweltverträglichkeitsprüfung Bauantrag"]
```

---

#### **Phase 5.3: MMR Diversity Re-Ranking** (Priorität 3)
**Zeitaufwand:** 3-4 Stunden  
**Code:** 150-250 Zeilen

**Deliverables:**
1. Maximal Marginal Relevance (MMR)
2. Integration mit bestehendem Cross-Encoder
3. Configurable Diversity-Parameter

**Neue Features:**
```python
class MMRReranker:
    async def rerank_with_diversity(
        query: str,
        candidates: List[Chunk],
        top_k: int = 10,
        lambda_param: float = 0.5  # 0.5 = Balance Relevance/Diversity
    ) -> List[Chunk]:
        # MMR Iterative Selection
        selected = []
        remaining = candidates.copy()
        
        for _ in range(top_k):
            mmr_scores = [
                lambda_param * relevance(q, c) - 
                (1 - lambda_param) * max_similarity(c, selected)
                for c in remaining
            ]
            best = remaining[argmax(mmr_scores)]
            selected.append(best)
            remaining.remove(best)
        
        return selected
```

---

#### **Phase 5.4: Semantic Chunking** (Priorität 4 - Optional)
**Zeitaufwand:** 4-6 Stunden  
**Code:** 300-400 Zeilen

**Deliverables:**
1. Semantic-basierte Chunking-Strategie
2. Sentence-Level Similarity
3. Overlap-Strategien
4. Integration in UDS3 Preprocessing

**Hinweis:** Benötigt Änderungen in UDS3 Document-Preprocessing

---

## 📊 Angepasste Code-Schätzung

| Komponente | Original (Design) | Angepasst (Realität) | Status |
|------------|-------------------|----------------------|--------|
| **Re-Ranking (Cross-Encoder)** | 250-350 | **0** (bereits vorhanden) | ✅ SKIP |
| **Evaluation Framework** | 250-350 | **0** (bereits vorhanden) | ✅ SKIP |
| **Hybrid Search (BM25 + RRF)** | 300-400 | **350** | 🔄 TODO |
| **Query Expansion** | 200-300 | **250** | 🔄 TODO |
| **MMR Diversity** | 150-250 | **200** | 🔄 TODO |
| **Semantic Chunking** | 300-400 | **350** (optional) | ⏸️ OPTIONAL |
| **Integration & Config** | 150-200 | **100** | 🔄 TODO |
| **Tests** | 400-500 | **200** | 🔄 TODO |
| **Dokumentation** | 500-600 | **300** | 🔄 TODO |
| **GESAMT** | **2350-3100** | **1450-1750** | **-40%** |

**Zeitersparnis:** ~1 Tag (weil Re-Ranking & Evaluation bereits fertig)

---

## 🚀 Empfohlene Nächste Schritte

### **Option A: Minimaler Impact (Hybrid Search only)**
**Zeitaufwand:** 1 Tag  
**Code:** ~550 Zeilen

**Implementiere:**
1. ✅ Sparse Retrieval (BM25)
2. ✅ Reciprocal Rank Fusion
3. ✅ Hybrid Search Integration

**Vorteile:**
- Größter Impact/Aufwand-Ratio
- Lexikalisches Matching für exakte Begriffe
- Komplementär zu bestehendem Dense-Retrieval

---

### **Option B: Moderate Impact (Hybrid + Query Expansion)**
**Zeitaufwand:** 1.5 Tage  
**Code:** ~850 Zeilen

**Implementiere:**
1. ✅ Sparse Retrieval + Hybrid Search
2. ✅ Query Expansion (LLM-basiert)
3. ✅ Multi-Query Generation

**Vorteile:**
- Hybrid Search + verbesserte Recall
- Multi-Perspektive Retrieval
- LLM-basierte Query-Verbesserung

---

### **Option C: Vollständig (All Features)**
**Zeitaufwand:** 2-2.5 Tage  
**Code:** ~1450-1750 Zeilen

**Implementiere:**
1. ✅ Hybrid Search
2. ✅ Query Expansion
3. ✅ MMR Diversity Re-Ranking
4. ⏸️ Semantic Chunking (optional)

**Vorteile:**
- Vollständiges Advanced RAG System
- Alle State-of-the-Art Techniken
- Maximale Retrieval-Qualität

---

## 🗳️ Empfehlung

**Ich empfehle: Option B - Moderate Impact**

**Begründung:**
1. ✅ Hybrid Search ist **Must-Have** (größter Impact)
2. ✅ Query Expansion ist **High-Value** (besserer Recall)
3. ❌ MMR ist **Nice-to-Have** (Cross-Encoder bereits sehr gut)
4. ❌ Semantic Chunking ist **UDS3-Dependent** (größerer Scope)

**Nächster Schritt:**
Sollen wir mit **Phase 5.1: Hybrid Search (BM25 + RRF)** starten?

- **Ja** → Implementiere BM25 Sparse Retriever
- **Alternative** → Wähle andere Option (A oder C)
- **Review** → Design nochmal reviewen
