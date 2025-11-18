# Phase 5: Advanced RAG Pipeline - Design-Dokument

**Version:** 1.0
**Datum:** 6. Oktober 2025
**Status:** 🔄 In Planung
**Autor:** VERITAS Development Team

---

## 📋 Executive Summary

### Zielsetzung
Verbesserung der RAG-Pipeline mit state-of-the-art Retrieval-Techniken zur Steigerung der Antwort-Qualität und Relevanz.

### Motivation
Die aktuelle RAG-Pipeline nutzt **Dense Retrieval** (Embeddings + Cosine-Similarity). Moderne RAG-Systeme kombinieren jedoch:
- **Hybrid Search** (Dense + Sparse)
- **Multi-Stage Retrieval** mit Re-Ranking
- **Semantic Chunking** statt fixed-size
- **Query Expansion** für besseren Recall

### Erfolgs-Kriterien

| Metrik | Aktuell (Baseline) | Ziel (Phase 5) | Verbesserung |
|--------|-------------------|----------------|--------------|
| **NDCG@10** | 0.65 (geschätzt) | > 0.80 | +23% |
| **MRR** | 0.55 (geschätzt) | > 0.75 | +36% |
| **Recall@10** | 0.70 (geschätzt) | > 0.85 | +21% |
| **Retrieval-Latenz** | ~200ms | < 300ms | Max +50% |
| **Chunk-Quality** | Fixed-size | Semantic | Qualitativ |

---

## 🏗️ Architektur-Übersicht

### High-Level-Architektur

```
┌─────────────────────────────────────────────────────────────────┐
│                    ADVANCED RAG PIPELINE (Phase 5)              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  1. QUERY PROCESSING                                   │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐  │    │
│  │  │ Query        │  │ Multi-Query  │  │ Query       │  │    │
│  │  │ Expansion    │→ │ Generation   │→ │ Rewrite     │  │    │
│  │  └──────────────┘  └──────────────┘  └─────────────┘  │    │
│  │         ↓                                               │    │
│  │  Original Query + Expanded Queries + Reformulations    │    │
│  └────────────────────────────────────────────────────────┘    │
│                           ↓                                     │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  2. HYBRID RETRIEVAL                                   │    │
│  │  ┌──────────────┐          ┌──────────────┐            │    │
│  │  │ Dense        │          │ Sparse       │            │    │
│  │  │ Retrieval    │          │ Retrieval    │            │    │
│  │  │ (Embeddings) │          │ (BM25/SPLADE)│            │    │
│  │  └──────┬───────┘          └──────┬───────┘            │    │
│  │         │                         │                     │    │
│  │         └────────┬────────────────┘                     │    │
│  │                  ↓                                      │    │
│  │         ┌────────────────┐                              │    │
│  │         │ Result Fusion  │ (Reciprocal Rank Fusion)    │    │
│  │         └────────┬───────┘                              │    │
│  │                  ↓                                      │    │
│  │         Top-K Candidates (k=50-100)                     │    │
│  └────────────────────────────────────────────────────────┘    │
│                           ↓                                     │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  3. RE-RANKING                                         │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐  │    │
│  │  │ Cross-       │→ │ Diversity    │→ │ Relevance   │  │    │
│  │  │ Encoder      │  │ Re-Ranking   │  │ Feedback    │  │    │
│  │  └──────────────┘  └──────────────┘  └─────────────┘  │    │
│  │         ↓                                               │    │
│  │  Top-N Final Results (n=5-10)                          │    │
│  └────────────────────────────────────────────────────────┘    │
│                           ↓                                     │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  4. CONTEXT AUGMENTATION                               │    │
│  │  ┌──────────────┐  ┌──────────────┐                    │    │
│  │  │ Chunk        │  │ Metadata     │                    │    │
│  │  │ Expansion    │  │ Enrichment   │                    │    │
│  │  └──────────────┘  └──────────────┘                    │    │
│  │         ↓                                               │    │
│  │  Augmented Context → LLM                               │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Komponenten-Design

### 1. Query Processing Layer

#### 1.1 Query Expansion
**Ziel:** Erweitere Query um Synonyme, verwandte Begriffe, Kontextvariationen

**Implementierung:**
```python
class QueryExpander:
    """LLM-basierte Query-Expansion für besseren Recall"""

    def __init__(self, llm_client: OllamaClient):
        self.llm = llm_client

    async def expand_query(
        self,
        query: str,
        num_expansions: int = 3
    ) -> List[str]:
        """
        Generiert erweiterte Query-Varianten

        Returns:
            [original_query, expansion_1, expansion_2, ...]
        """
        prompt = f"""
        Original Query: "{query}"

        Generiere {num_expansions} semantisch ähnliche Umformulierungen:
        1. Verwende Synonyme
        2. Füge relevante Kontextbegriffe hinzu
        3. Behalte die Kernintention bei

        Format: Eine Umformulierung pro Zeile
        """

        response = await self.llm.generate_response(prompt)
        expansions = [query]  # Original immer dabei
        expansions.extend(response.strip().split('\n'))

        return expansions[:num_expansions + 1]
```

**Beispiel:**
```
Original: "Bauvorhaben Umweltauflagen Berlin"
Expansion 1: "Umweltrechtliche Genehmigungen für Bauprojekte in Berlin"
Expansion 2: "Umweltverträglichkeitsprüfung Bauantrag Berlin"
Expansion 3: "Ökologische Auflagen Hochbau Berlin-Mitte"
```

---

#### 1.2 Multi-Query Generation
**Ziel:** Generiere multiple Perspektiven der Query für umfassendere Retrieval

**Implementierung:**
```python
class MultiQueryGenerator:
    """Generiert multiple Query-Perspektiven"""

    async def generate_multi_queries(
        self,
        query: str,
        num_queries: int = 3
    ) -> List[str]:
        """
        Generiert verschiedene Perspektiven/Aspekte der Query

        Returns:
            Liste von Queries aus verschiedenen Perspektiven
        """
        prompt = f"""
        User-Query: "{query}"

        Generiere {num_queries} verschiedene Such-Perspektiven:
        1. Rechtliche Perspektive
        2. Technische Perspektive
        3. Prozessuale Perspektive

        Jede Perspektive als separate Query.
        """

        response = await self.llm.generate_response(prompt)
        queries = [query]  # Original
        queries.extend(response.strip().split('\n'))

        return queries[:num_queries + 1]
```

---

### 2. Hybrid Retrieval Layer

#### 2.1 Dense Retrieval (Embeddings)
**Aktuell:** Sentence-Transformers Embeddings + Cosine-Similarity
**Neu:** Erweitert um Multi-Query Support

**Komponenten:**
```python
class DenseRetriever:
    """Embedding-basierte Dense Retrieval"""

    def __init__(
        self,
        embedding_model: str = "all-MiniLM-L6-v2",
        vector_store: VectorStore
    ):
        self.model = SentenceTransformer(embedding_model)
        self.vector_store = vector_store

    async def retrieve(
        self,
        queries: List[str],  # Multi-Query Support
        top_k: int = 50
    ) -> List[ScoredChunk]:
        """
        Dense Retrieval für multiple Queries

        Returns:
            Top-K Chunks mit Dense-Scores
        """
        all_results = []

        for query in queries:
            query_embedding = self.model.encode(query)
            results = await self.vector_store.similarity_search(
                query_embedding,
                k=top_k
            )
            all_results.extend(results)

        # Dedupliziere & merge Scores
        return self._merge_results(all_results, top_k)
```

---

#### 2.2 Sparse Retrieval (BM25/SPLADE)
**Ziel:** Lexikalisches Matching für exakte Begriffe, Akronyme, Zahlen

**BM25 Implementation:**
```python
from rank_bm25 import BM25Okapi

class SparseRetriever:
    """BM25-basierte Sparse Retrieval"""

    def __init__(self, corpus: List[str]):
        # Tokenize Corpus
        self.tokenized_corpus = [
            self._tokenize(doc) for doc in corpus
        ]
        self.bm25 = BM25Okapi(self.tokenized_corpus)
        self.corpus = corpus

    def _tokenize(self, text: str) -> List[str]:
        """Einfache Tokenization (kann erweitert werden)"""
        return text.lower().split()

    async def retrieve(
        self,
        queries: List[str],
        top_k: int = 50
    ) -> List[ScoredChunk]:
        """
        BM25 Retrieval für multiple Queries

        Returns:
            Top-K Chunks mit BM25-Scores
        """
        all_scores = []

        for query in queries:
            tokenized_query = self._tokenize(query)
            scores = self.bm25.get_scores(tokenized_query)
            all_scores.append(scores)

        # Merge Scores (Max, Sum, oder Average)
        merged_scores = np.max(all_scores, axis=0)

        # Top-K Indizes
        top_indices = np.argsort(merged_scores)[-top_k:][::-1]

        return [
            ScoredChunk(
                chunk=self.corpus[idx],
                score=merged_scores[idx],
                source="bm25"
            )
            for idx in top_indices
        ]
```

**Warum BM25?**
- ✅ Gut für exakte Begriffe (z.B. "§ 242 BGB", "DIN 18040-1")
- ✅ Akronyme & Abkürzungen (z.B. "UVP", "VOB")
- ✅ Zahlen & Daten (z.B. "2024", "50.000 EUR")
- ✅ Komplementär zu Dense-Retrieval

---

#### 2.3 Result Fusion (Reciprocal Rank Fusion)
**Ziel:** Kombiniere Dense + Sparse Results optimal

**RRF Formula:**
```
RRF_score(d) = Σ_{r ∈ R} 1 / (k + rank_r(d))

Wobei:
- R = Liste der Retriever (Dense, Sparse)
- rank_r(d) = Rang von Dokument d in Retriever r
- k = Konstante (typisch 60)
```

**Implementation:**
```python
class ReciprocalRankFusion:
    """Reciprocal Rank Fusion für Hybrid-Results"""

    def __init__(self, k: int = 60):
        self.k = k

    def fuse(
        self,
        dense_results: List[ScoredChunk],
        sparse_results: List[ScoredChunk],
        top_k: int = 50
    ) -> List[ScoredChunk]:
        """
        Fusioniert Dense + Sparse Results via RRF

        Returns:
            Top-K fusionierte Results mit RRF-Scores
        """
        # Chunk-ID → RRF-Score Mapping
        rrf_scores = {}

        # Dense Results
        for rank, chunk in enumerate(dense_results):
            chunk_id = chunk.chunk_id
            rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0) + \
                1 / (self.k + rank + 1)

        # Sparse Results
        for rank, chunk in enumerate(sparse_results):
            chunk_id = chunk.chunk_id
            rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0) + \
                1 / (self.k + rank + 1)

        # Sortiere nach RRF-Score
        sorted_chunks = sorted(
            rrf_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return [
            ScoredChunk(
                chunk_id=chunk_id,
                score=score,
                source="rrf"
            )
            for chunk_id, score in sorted_chunks[:top_k]
        ]
```

**Warum RRF?**
- ✅ Rank-basiert (nicht score-basiert) → robuster gegen unterschiedliche Score-Skalen
- ✅ Einfach & effektiv
- ✅ State-of-the-Art in Multi-Retriever-Fusion

---

### 3. Re-Ranking Layer

#### 3.1 Cross-Encoder Re-Ranker
**Ziel:** Präzise Relevanz-Bewertung für Top-K Kandidaten

**Modell:** `cross-encoder/ms-marco-MiniLM-L-6-v2` (22M params, schnell)

**Implementation:**
```python
from sentence_transformers import CrossEncoder

class CrossEncoderReranker:
    """Cross-Encoder basiertes Re-Ranking"""

    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    ):
        self.model = CrossEncoder(model_name)

    async def rerank(
        self,
        query: str,
        candidates: List[ScoredChunk],
        top_k: int = 10
    ) -> List[ScoredChunk]:
        """
        Re-rankt Kandidaten via Cross-Encoder

        Returns:
            Top-K re-ranked Chunks
        """
        # Prepare Query-Chunk Pairs
        pairs = [
            [query, candidate.chunk_text]
            for candidate in candidates
        ]

        # Cross-Encoder Scores
        scores = self.model.predict(pairs)

        # Merge mit Original-Candidates
        for candidate, score in zip(candidates, scores):
            candidate.rerank_score = score

        # Sortiere nach Rerank-Score
        reranked = sorted(
            candidates,
            key=lambda x: x.rerank_score,
            reverse=True
        )

        return reranked[:top_k]
```

**Performance:**
- **Latenz:** ~10ms pro Chunk (GPU), ~50ms (CPU)
- **Accuracy:** +15-20% NDCG@10 vs Bi-Encoder

---

#### 3.2 Diversity Re-Ranking (MMR)
**Ziel:** Maximiere Diversity in Results (vermeide redundante Chunks)

**MMR Formula:**
```
MMR = argmax_{D_i ∈ R \ S} [
    λ * Similarity(Q, D_i) - (1-λ) * max_{D_j ∈ S} Similarity(D_i, D_j)
]

Wobei:
- Q = Query
- R = Kandidaten-Set
- S = Bereits ausgewählte Chunks
- λ = Diversity-Parameter (0.5 = Balance)
```

**Implementation:**
```python
class MaximalMarginalRelevance:
    """MMR-basierte Diversity Re-Ranking"""

    def __init__(self, lambda_param: float = 0.5):
        self.lambda_param = lambda_param

    async def rerank(
        self,
        query_embedding: np.ndarray,
        candidates: List[ScoredChunk],
        top_k: int = 10
    ) -> List[ScoredChunk]:
        """
        MMR Re-Ranking für Diversity

        Returns:
            Top-K diverse Chunks
        """
        selected = []
        remaining = candidates.copy()

        # Iterativ auswählen
        for _ in range(min(top_k, len(remaining))):
            mmr_scores = []

            for candidate in remaining:
                # Relevanz-Score
                relevance = self._cosine_similarity(
                    query_embedding,
                    candidate.embedding
                )

                # Diversity-Score (max similarity zu bereits gewählten)
                if selected:
                    diversity = max([
                        self._cosine_similarity(
                            candidate.embedding,
                            s.embedding
                        )
                        for s in selected
                    ])
                else:
                    diversity = 0

                # MMR Score
                mmr = self.lambda_param * relevance - \
                      (1 - self.lambda_param) * diversity

                mmr_scores.append((candidate, mmr))

            # Wähle besten MMR-Score
            best_candidate, best_score = max(
                mmr_scores,
                key=lambda x: x[1]
            )

            selected.append(best_candidate)
            remaining.remove(best_candidate)

        return selected
```

---

### 4. Advanced Chunking Strategies

#### 4.1 Semantic Chunking
**Problem mit Fixed-Size Chunking:**
- Schneidet Sätze/Absätze mitten durch
- Verliert semantischen Kontext
- Chunk-Grenzen willkürlich

**Semantic Chunking Ansatz:**
```python
class SemanticChunker:
    """Semantic-basiertes Chunking (nicht fixed-size)"""

    def __init__(
        self,
        embedding_model: SentenceTransformer,
        similarity_threshold: float = 0.7
    ):
        self.model = embedding_model
        self.threshold = similarity_threshold

    async def chunk_document(
        self,
        text: str,
        min_chunk_size: int = 100,
        max_chunk_size: int = 500
    ) -> List[str]:
        """
        Chunked Dokument semantisch

        Returns:
            Liste semantisch kohärenter Chunks
        """
        # Split in Sätze
        sentences = self._split_sentences(text)

        # Embed Sentences
        embeddings = self.model.encode(sentences)

        chunks = []
        current_chunk = [sentences[0]]
        current_embedding = embeddings[0]

        for i in range(1, len(sentences)):
            sentence = sentences[i]
            embedding = embeddings[i]

            # Similarity zum aktuellen Chunk
            similarity = self._cosine_similarity(
                current_embedding,
                embedding
            )

            # Wenn ähnlich & nicht zu groß → hinzufügen
            if (similarity >= self.threshold and
                len(' '.join(current_chunk)) < max_chunk_size):
                current_chunk.append(sentence)
                # Update Chunk-Embedding (Mean)
                current_embedding = np.mean([current_embedding, embedding], axis=0)
            else:
                # Neuer Chunk
                chunks.append(' '.join(current_chunk))
                current_chunk = [sentence]
                current_embedding = embedding

        # Letzter Chunk
        if current_chunk:
            chunks.append(' '.join(current_chunk))

        return chunks
```

**Vorteile:**
- ✅ Semantisch kohärente Chunks
- ✅ Keine abgeschnittenen Sätze
- ✅ Bessere Kontext-Preservation

---

#### 4.2 Hierarchical Chunking
**Ziel:** Multi-Level Chunks (Paragraph → Section → Document)

**Implementation:**
```python
class HierarchicalChunker:
    """Hierarchical Chunking mit Parent-Child-Relationen"""

    async def chunk_hierarchical(
        self,
        text: str
    ) -> List[HierarchicalChunk]:
        """
        Erstellt hierarchische Chunk-Struktur

        Returns:
            Liste von Chunks mit Parent-Child-Links
        """
        # Level 1: Document
        doc_chunk = HierarchicalChunk(
            text=text,
            level=1,
            parent_id=None
        )

        # Level 2: Sections (via Headers)
        sections = self._split_by_headers(text)
        section_chunks = []

        for section in sections:
            section_chunk = HierarchicalChunk(
                text=section,
                level=2,
                parent_id=doc_chunk.chunk_id
            )
            section_chunks.append(section_chunk)

            # Level 3: Paragraphs
            paragraphs = self._split_paragraphs(section)
            for para in paragraphs:
                para_chunk = HierarchicalChunk(
                    text=para,
                    level=3,
                    parent_id=section_chunk.chunk_id
                )
                section_chunks.append(para_chunk)

        return [doc_chunk] + section_chunks
```

**Retrieval-Strategie:**
1. Retrieve auf Paragraph-Level (Level 3)
2. Bei Match: Hole Parent-Section für mehr Kontext
3. Bei Bedarf: Hole gesamtes Document

---

## 📊 Evaluation-Framework

### Retrieval-Metriken

#### 1. NDCG@K (Normalized Discounted Cumulative Gain)
```python
def ndcg_at_k(
    relevant_docs: List[str],
    retrieved_docs: List[str],
    k: int = 10
) -> float:
    """
    NDCG@K: Misst Ranking-Qualität mit Position-Discount

    Returns:
        NDCG Score (0.0 - 1.0)
    """
    dcg = sum([
        1 / np.log2(i + 2)
        for i, doc in enumerate(retrieved_docs[:k])
        if doc in relevant_docs
    ])

    idcg = sum([
        1 / np.log2(i + 2)
        for i in range(min(k, len(relevant_docs)))
    ])

    return dcg / idcg if idcg > 0 else 0.0
```

---

#### 2. MRR (Mean Reciprocal Rank)
```python
def mean_reciprocal_rank(
    relevant_docs: List[str],
    retrieved_docs: List[str]
) -> float:
    """
    MRR: Position des ersten relevanten Dokuments

    Returns:
        MRR Score (0.0 - 1.0)
    """
    for i, doc in enumerate(retrieved_docs):
        if doc in relevant_docs:
            return 1 / (i + 1)
    return 0.0
```

---

#### 3. Recall@K
```python
def recall_at_k(
    relevant_docs: List[str],
    retrieved_docs: List[str],
    k: int = 10
) -> float:
    """
    Recall@K: Anteil relevanter Docs in Top-K

    Returns:
        Recall (0.0 - 1.0)
    """
    retrieved_set = set(retrieved_docs[:k])
    relevant_set = set(relevant_docs)

    if not relevant_set:
        return 0.0

    return len(retrieved_set & relevant_set) / len(relevant_set)
```

---

### Benchmark-Dataset

**Erstelle Test-Set:**
```python
class RAGBenchmark:
    """Benchmark für RAG-Evaluation"""

    def __init__(self):
        self.test_queries = [
            {
                "query": "Umweltauflagen für Bauvorhaben in Berlin",
                "relevant_chunks": ["chunk_123", "chunk_456", ...],
                "ideal_ranking": ["chunk_123", "chunk_456", ...]
            },
            # ... mehr Test-Queries
        ]

    async def evaluate_pipeline(
        self,
        pipeline: RAGPipeline
    ) -> Dict[str, float]:
        """
        Evaluiert RAG-Pipeline auf Test-Set

        Returns:
            {"ndcg@10": 0.78, "mrr": 0.65, "recall@10": 0.82}
        """
        ndcg_scores = []
        mrr_scores = []
        recall_scores = []

        for test_case in self.test_queries:
            query = test_case["query"]
            relevant = test_case["relevant_chunks"]

            # Retrieve
            results = await pipeline.retrieve(query, top_k=10)
            retrieved = [r.chunk_id for r in results]

            # Metriken
            ndcg_scores.append(ndcg_at_k(relevant, retrieved, k=10))
            mrr_scores.append(mean_reciprocal_rank(relevant, retrieved))
            recall_scores.append(recall_at_k(relevant, retrieved, k=10))

        return {
            "ndcg@10": np.mean(ndcg_scores),
            "mrr": np.mean(mrr_scores),
            "recall@10": np.mean(recall_scores)
        }
```

---

## 🔄 Implementation-Roadmap

### Phase 5.1: Hybrid Search (Tag 1)
**Dauer:** 6-8 Stunden

**Todos:**
1. ✅ Design-Dokument finalisieren
2. ⏳ Sparse Retrieval (BM25) implementieren
3. ⏳ Reciprocal Rank Fusion implementieren
4. ⏳ Integration in VeritasRAGPipeline
5. ⏳ Unit-Tests für Hybrid-Retrieval

**Code-Schätzung:** 300-400 Zeilen

---

### Phase 5.2: Re-Ranking System (Tag 1-2)
**Dauer:** 6-8 Stunden

**Todos:**
1. ⏳ Cross-Encoder Integration
2. ⏳ MMR Diversity Re-Ranking
3. ⏳ Konfigurierbare Re-Ranking-Pipeline
4. ⏳ Performance-Tests (Latenz)

**Code-Schätzung:** 250-350 Zeilen

---

### Phase 5.3: Advanced Chunking (Tag 2)
**Dauer:** 4-6 Stunden

**Todos:**
1. ⏳ Semantic Chunker implementieren
2. ⏳ Hierarchical Chunker implementieren
3. ⏳ Backward-Kompatibilität (Feature-Flag)
4. ⏳ Chunk-Quality Tests

**Code-Schätzung:** 300-400 Zeilen

---

### Phase 5.4: Query Expansion (Tag 2)
**Dauer:** 4-5 Stunden

**Todos:**
1. ⏳ Query Expander (LLM-basiert)
2. ⏳ Multi-Query Generator
3. ⏳ Integration in Query-Pipeline
4. ⏳ A/B Tests (mit/ohne Expansion)

**Code-Schätzung:** 200-300 Zeilen

---

### Phase 5.5: Evaluation & Benchmarks (Tag 3)
**Dauer:** 6-8 Stunden

**Todos:**
1. ⏳ Benchmark-Dataset erstellen (20-30 Test-Queries)
2. ⏳ Evaluation-Framework implementieren
3. ⏳ Baseline-Messung (aktuelles RAG)
4. ⏳ Advanced-RAG Messung
5. ⏳ Performance-Report erstellen

**Code-Schätzung:** 250-350 Zeilen

---

### Phase 5.6: Documentation & Integration (Tag 3)
**Dauer:** 3-4 Stunden

**Todos:**
1. ⏳ Implementation-Report
2. ⏳ API-Dokumentation
3. ⏳ Migration-Guide
4. ⏳ Performance-Dashboard

**Code-Schätzung:** Dokumentation (500-600 Zeilen)

---

## 📦 Deliverables

| Komponente | Zeilen (geschätzt) | Status |
|------------|-------------------|--------|
| **Hybrid Search** (Dense + Sparse + Fusion) | 300-400 | 🔄 |
| **Re-Ranking** (Cross-Encoder + MMR) | 250-350 | 🔄 |
| **Advanced Chunking** (Semantic + Hierarchical) | 300-400 | 🔄 |
| **Query Expansion** (LLM + Multi-Query) | 200-300 | 🔄 |
| **Evaluation Framework** (Benchmarks) | 250-350 | 🔄 |
| **Integration & Config** | 150-200 | 🔄 |
| **Tests** (Unit + Integration) | 400-500 | 🔄 |
| **Dokumentation** (Implementation-Report) | 500-600 | 🔄 |
| **GESAMT** | **2350-3100 Zeilen** | 🔄 |

---

## 🎯 Success-Kriterien

### Must-Have
- [x] Design-Dokument vollständig
- [ ] Hybrid Search (Dense + Sparse) ✅
- [ ] Re-Ranking (Cross-Encoder) ✅
- [ ] Evaluation-Framework (NDCG@10, MRR, Recall@K) ✅
- [ ] NDCG@10 > 0.80 (vs Baseline 0.65)
- [ ] Backward-Kompatibilität 100%

### Should-Have
- [ ] MMR Diversity Re-Ranking
- [ ] Semantic Chunking
- [ ] Query Expansion (LLM-basiert)
- [ ] Performance-Dashboard

### Nice-to-Have
- [ ] Hierarchical Chunking
- [ ] Multi-Query Generation
- [ ] A/B Testing Infrastructure
- [ ] Caching-Layer für Embeddings

---

## 🚀 Getting Started

**Nächster Schritt:** Phase 5.1 - Hybrid Search Implementation

**Ready?** Lassen Sie uns mit der BM25 Sparse Retrieval Implementation beginnen! 🎯
