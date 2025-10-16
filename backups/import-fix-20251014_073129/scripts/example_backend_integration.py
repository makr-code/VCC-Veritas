"""
Phase 5 Hybrid Search - Backend Integration Example
Zeigt wie UDS3 Adapter in bestehenden Backend integriert wird
"""
import asyncio
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


async def example_basic_integration():
    """
    Example 1: Basic Integration
    Minimale Integration in bestehendes Backend
    """
    print("=" * 80)
    print("EXAMPLE 1: BASIC INTEGRATION")
    print("=" * 80)
    print()
    
    # 1. Import components
    from backend.agents.veritas_uds3_adapter import get_uds3_adapter
    from backend.agents.veritas_hybrid_retrieval import HybridRetriever
    from backend.agents.veritas_sparse_retrieval import SparseRetriever
    
    # 2. Initialize UDS3 Adapter
    print("🔄 Initializing UDS3 Adapter...")
    uds3_adapter = get_uds3_adapter()  # Auto-initializes UDS3
    print(f"   ✅ Adapter: {type(uds3_adapter).__name__}")
    
    # 3. Initialize BM25
    print("🔄 Initializing BM25...")
    bm25 = SparseRetriever()
    
    # 4. Index your corpus (example with demo docs)
    demo_corpus = [
        {
            "doc_id": "bgb_110",
            "content": "§ 110 BGB Taschengeldparagraph - Bewirken der Leistung mit eigenen Mitteln. Ein von dem Minderjährigen ohne Zustimmung des gesetzlichen Vertreters geschlossener Vertrag gilt als von Anfang an wirksam, wenn der Minderjährige die vertragsmäßige Leistung mit Mitteln bewirkt, die ihm zu diesem Zweck oder zu freier Verfügung von dem Vertreter oder mit dessen Zustimmung von einem Dritten überlassen worden sind.",
            "metadata": {"source": "BGB", "section": "110", "category": "Vertragsrecht"}
        },
        {
            "doc_id": "bgb_433",
            "content": "§ 433 BGB Vertragstypische Pflichten beim Kaufvertrag. (1) Durch den Kaufvertrag wird der Verkäufer einer Sache verpflichtet, dem Käufer die Sache zu übergeben und das Eigentum an der Sache zu verschaffen. Der Verkäufer hat dem Käufer die Sache frei von Sach- und Rechtsmängeln zu verschaffen. (2) Der Käufer ist verpflichtet, dem Verkäufer den vereinbarten Kaufpreis zu zahlen und die gekaufte Sache abzunehmen.",
            "metadata": {"source": "BGB", "section": "433", "category": "Kaufrecht"}
        },
        {
            "doc_id": "vwvfg_35",
            "content": "§ 35 VwVfG Begriff des Verwaltungsaktes. Verwaltungsakt ist jede Verfügung, Entscheidung oder andere hoheitliche Maßnahme, die eine Behörde zur Regelung eines Einzelfalls auf dem Gebiet des öffentlichen Rechts trifft und die auf unmittelbare Rechtswirkung nach außen gerichtet ist.",
            "metadata": {"source": "VwVfG", "section": "35", "category": "Verwaltungsrecht"}
        }
    ]
    
    bm25.index_documents(demo_corpus)
    print(f"   ✅ BM25 indexed: {len(demo_corpus)} documents")
    print()
    
    # 5. Create HybridRetriever
    print("🔄 Creating HybridRetriever...")
    hybrid = HybridRetriever(
        dense_retriever=uds3_adapter,  # UDS3 Adapter
        sparse_retriever=bm25,
        config=None  # Use defaults
    )
    print(f"   ✅ HybridRetriever initialized")
    print()
    
    # 6. Query
    query = "BGB Minderjährige Taschengeld Vertragsschluss"
    print(f"🔍 Query: \"{query}\"")
    print()
    
    results = await hybrid.retrieve(query, top_k=3)
    
    # 7. Display results
    print(f"📊 Results: {len(results)}")
    for i, result in enumerate(results, 1):
        dense_score = result.dense_score if result.dense_score else 0.0
        sparse_score = result.sparse_score if result.sparse_score else 0.0
        
        print(f"\n{i}. {result.doc_id}")
        print(f"   RRF Score: {result.score:.4f}")
        print(f"   Dense Score: {dense_score:.4f} (UDS3)")
        print(f"   Sparse Score: {sparse_score:.4f} (BM25)")
        print(f"   Content: {result.content[:100]}...")
    
    print()
    print("=" * 80)
    return hybrid


async def example_with_environment_config():
    """
    Example 2: With Environment Configuration
    Verwendet Environment Variables für Feature Toggles
    """
    print("\n")
    print("=" * 80)
    print("EXAMPLE 2: WITH ENVIRONMENT CONFIGURATION")
    print("=" * 80)
    print()
    
    import os
    
    # Read environment
    enable_hybrid = os.getenv('VERITAS_ENABLE_HYBRID_SEARCH', 'false').lower() == 'true'
    enable_sparse = os.getenv('VERITAS_ENABLE_SPARSE_RETRIEVAL', 'true').lower() == 'true'
    
    print(f"🔧 Configuration:")
    print(f"   HYBRID_SEARCH: {enable_hybrid}")
    print(f"   SPARSE_RETRIEVAL: {enable_sparse}")
    print()
    
    if not enable_hybrid:
        print("⚠️ Hybrid Search disabled - using default retriever")
        return None
    
    # Same as Example 1
    from backend.agents.veritas_uds3_adapter import get_uds3_adapter
    from backend.agents.veritas_hybrid_retrieval import HybridRetriever
    from backend.agents.veritas_sparse_retrieval import SparseRetriever
    
    uds3_adapter = get_uds3_adapter()
    bm25 = SparseRetriever()
    
    # Your corpus loading logic here
    # corpus = load_corpus_from_database()
    # bm25.index_documents(corpus)
    
    hybrid = HybridRetriever(
        dense_retriever=uds3_adapter,
        sparse_retriever=bm25 if enable_sparse else None,
        config=None
    )
    
    print("✅ Hybrid Search initialized from environment config")
    return hybrid


async def example_rag_context_service_integration():
    """
    Example 3: Integration in RAGContextService
    Zeigt wie Hybrid in bestehende RAGContextService integriert wird
    """
    print("\n")
    print("=" * 80)
    print("EXAMPLE 3: RAG CONTEXT SERVICE INTEGRATION")
    print("=" * 80)
    print()
    
    print("Pseudo-Code für RAGContextService Integration:")
    print()
    
    code = """
# In backend/agents/rag_context_service.py

class RAGContextService:
    def __init__(self, ...):
        # Existing initialization
        self.uds3 = get_optimized_unified_strategy()
        
        # NEW: Phase 5 Hybrid Search
        if os.getenv('VERITAS_ENABLE_HYBRID_SEARCH', 'false').lower() == 'true':
            from backend.agents.veritas_uds3_adapter import UDS3VectorSearchAdapter
            from backend.agents.veritas_hybrid_retrieval import HybridRetriever
            from backend.agents.veritas_sparse_retrieval import SparseRetriever
            
            # Initialize components
            uds3_adapter = UDS3VectorSearchAdapter(self.uds3)
            self.bm25 = SparseRetriever()
            
            # Load corpus and index
            corpus = self._load_corpus()
            self.bm25.index_documents(corpus)
            
            # Create hybrid retriever
            self.hybrid_retriever = HybridRetriever(
                dense_retriever=uds3_adapter,
                sparse_retriever=self.bm25,
                config=None
            )
            
            logger.info("✅ Phase 5 Hybrid Search initialized")
        else:
            self.hybrid_retriever = None
            logger.info("ℹ️ Phase 5 Hybrid Search disabled")
    
    async def retrieve_context(self, query: str, top_k: int = 5):
        # Use Hybrid if enabled, otherwise fall back to UDS3
        if self.hybrid_retriever:
            results = await self.hybrid_retriever.retrieve(query, top_k)
            # Convert HybridResult to your internal format
            return self._convert_hybrid_results(results)
        else:
            # Existing UDS3 retrieval
            result = self.uds3.query_across_databases(
                vector_params={"query_text": query, "top_k": top_k},
                ...
            )
            return self._convert_uds3_results(result)
    """
    
    print(code)
    print()
    print("Key Points:")
    print("1. Check VERITAS_ENABLE_HYBRID_SEARCH environment variable")
    print("2. Initialize UDS3VectorSearchAdapter with existing UDS3 instance")
    print("3. Load corpus and index with BM25")
    print("4. Use hybrid_retriever if enabled, else fallback to UDS3")
    print()


async def example_performance_monitoring():
    """
    Example 4: Performance Monitoring
    Zeigt wie man Performance Metriken trackt
    """
    print("\n")
    print("=" * 80)
    print("EXAMPLE 4: PERFORMANCE MONITORING")
    print("=" * 80)
    print()
    
    import time
    from backend.agents.veritas_uds3_adapter import get_uds3_adapter
    from backend.agents.veritas_hybrid_retrieval import HybridRetriever
    from backend.agents.veritas_sparse_retrieval import SparseRetriever
    
    # Initialize
    uds3_adapter = get_uds3_adapter()
    bm25 = SparseRetriever()
    
    # Index demo docs
    demo_docs = [
        {"doc_id": "test_1", "content": "Test document one about contracts"},
        {"doc_id": "test_2", "content": "Test document two about administrative law"},
    ]
    bm25.index_documents(demo_docs)
    
    hybrid = HybridRetriever(
        dense_retriever=uds3_adapter,
        sparse_retriever=bm25,
        config=None
    )
    
    # Query with timing
    query = "contract law"
    
    start = time.time()
    results = await hybrid.retrieve(query, top_k=2)
    latency = (time.time() - start) * 1000
    
    print(f"⏱️ Performance Metrics:")
    print(f"   Query: \"{query}\"")
    print(f"   Latency: {latency:.1f}ms")
    print(f"   Results: {len(results)}")
    print()
    
    # Adapter stats
    adapter_stats = uds3_adapter.get_stats()
    print(f"📊 Adapter Statistics:")
    for key, value in adapter_stats.items():
        print(f"   {key}: {value}")
    print()
    
    # Check if meets SLA
    sla_latency = 200  # ms
    if latency < sla_latency:
        print(f"✅ Performance: WITHIN SLA (<{sla_latency}ms)")
    else:
        print(f"⚠️ Performance: EXCEEDS SLA (>{sla_latency}ms)")
    
    print()


async def main():
    """Run all examples"""
    print("\n")
    print("*" * 80)
    print("PHASE 5 HYBRID SEARCH - BACKEND INTEGRATION EXAMPLES")
    print("*" * 80)
    print()
    
    # Example 1: Basic Integration
    await example_basic_integration()
    
    # Example 2: With Environment Config
    await example_with_environment_config()
    
    # Example 3: RAG Context Service (pseudo-code)
    await example_rag_context_service_integration()
    
    # Example 4: Performance Monitoring
    await example_performance_monitoring()
    
    print("\n")
    print("*" * 80)
    print("✅ ALL EXAMPLES COMPLETE")
    print("*" * 80)
    print()
    print("Next Steps:")
    print("1. Choose integration pattern (Example 1, 2, or 3)")
    print("2. Adapt to your backend structure")
    print("3. Load your actual corpus for BM25 indexing")
    print("4. Test with real queries")
    print("5. Monitor performance metrics")
    print()


if __name__ == "__main__":
    asyncio.run(main())
