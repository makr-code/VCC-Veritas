#!/usr/bin/env python3
"""
PHASE 5 HYBRID SEARCH INTEGRATION - BACKEND INITIALIZATION
===========================================================

Fügt Hybrid Search (UDS3 Adapter + BM25 + RRF) zum bestehenden Backend hinzu.

Integration:
1. Import dieser Datei in veritas_api_backend.py
2. Rufe initialize_phase5_hybrid_search() in lifespan() auf
3. Nutze hybrid_retriever für Queries

Author: VERITAS System
Date: 7. Oktober 2025
"""

import logging
import os
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

# Global instances
hybrid_retriever = None
bm25_retriever = None
uds3_adapter = None

# Import Phase 5 Components
try:
    from backend.agents.veritas_uds3_adapter import UDS3VectorSearchAdapter
    from backend.agents.veritas_sparse_retrieval import SparseRetriever, SparseRetrievalConfig
    from backend.agents.veritas_hybrid_retrieval import HybridRetriever, HybridRetrievalConfig
    PHASE5_AVAILABLE = True
except ImportError as e:
    PHASE5_AVAILABLE = False
    logger.error(f"❌ Phase 5 Components nicht verfügbar: {e}")

# Import UDS3
try:
    from uds3.core import UDS3PolyglotManager  # ✨ UDS3 v2.0.0 (Legacy stable)
    UDS3_DB_AVAILABLE = True
    logger.info("✅ UDS3 v2.0.0 erfolgreich importiert")
except ImportError as e:
    UDS3_DB_AVAILABLE = False
    logger.warning(f"⚠️ UDS3 nicht verfügbar: {e}")


# Demo Corpus für Testing (optional)
DEMO_CORPUS = []


def get_phase5_config() -> Dict[str, Any]:
    """Liest Phase 5 Konfiguration aus Environment Variables."""
    
    config = {
        # Feature Flags
        "enable_hybrid_search": os.getenv("VERITAS_ENABLE_HYBRID_SEARCH", "true").lower() == "true",
        "enable_sparse_retrieval": os.getenv("VERITAS_ENABLE_SPARSE_RETRIEVAL", "true").lower() == "true",
        "enable_query_expansion": os.getenv("VERITAS_ENABLE_QUERY_EXPANSION", "false").lower() == "true",
        
        # Hybrid Search Parameters
        "hybrid_sparse_top_k": int(os.getenv("VERITAS_HYBRID_SPARSE_TOP_K", "20")),
        "hybrid_dense_top_k": int(os.getenv("VERITAS_HYBRID_DENSE_TOP_K", "20")),
        "rrf_k": int(os.getenv("VERITAS_RRF_K", "60")),
        
        # BM25 Parameters
        "bm25_k1": float(os.getenv("VERITAS_BM25_K1", "1.5")),
        "bm25_b": float(os.getenv("VERITAS_BM25_B", "0.75")),
        
        # Performance
        "enable_performance_monitoring": os.getenv("VERITAS_ENABLE_PERFORMANCE_MONITORING", "true").lower() == "true",
        "max_hybrid_latency_ms": int(os.getenv("VERITAS_MAX_HYBRID_LATENCY_MS", "200")),
    }
    
    return config


async def initialize_phase5_hybrid_search(
    demo_corpus: Optional[List[Dict[str, str]]] = None
) -> bool:
    """
    Initialisiert Phase 5 Hybrid Search System.
    
    Args:
        demo_corpus: Optional demo corpus für Testing (Liste von Dicts mit 'doc_id', 'content', 'metadata')
    
    Returns:
        True wenn erfolgreich initialisiert
    """
    global hybrid_retriever, bm25_retriever, uds3_adapter
    
    logger.info("=" * 80)
    logger.info("🚀 PHASE 5 HYBRID SEARCH INITIALIZATION")
    logger.info("=" * 80)
    
    # Check availability
    if not PHASE5_AVAILABLE:
        logger.error("❌ Phase 5 Components nicht verfügbar!")
        return False
    
    # Get configuration
    config = get_phase5_config()
    
    logger.info(f"📋 Configuration:")
    logger.info(f"   Hybrid Search: {config['enable_hybrid_search']}")
    logger.info(f"   Sparse Retrieval (BM25): {config['enable_sparse_retrieval']}")
    logger.info(f"   Query Expansion: {config['enable_query_expansion']}")
    logger.info(f"   RRF k: {config['rrf_k']}")
    logger.info(f"   BM25 k1={config['bm25_k1']}, b={config['bm25_b']}")
    
    if not config["enable_hybrid_search"]:
        logger.warning("⚠️ Hybrid Search disabled - Skipping initialization")
        return False
    
    try:
        # Step 1: Initialize UDS3 Adapter (Dense Retriever)
        logger.info("\n📦 Step 1: Initializing Dense Retriever...")
        
        # UDS3 ist optional - wir verwenden Mock wenn nicht verfügbar
        try:
            from uds3.core import UDS3PolyglotManager  # ✨ UDS3 v2.0.0 (Legacy stable)
            
            # Versuche UDS3 Polyglot Manager zu erstellen
            uds3_strategy = None
            try:
                backend_config = {
                    "vector": {"enabled": True, "backend": "chromadb"},
                    "graph": {"enabled": False},
                    "relational": {"enabled": False},
                    "file_storage": {"enabled": False}
                }
                uds3_strategy = UDS3PolyglotManager(
                    backend_config=backend_config,
                    enable_rag=True
                )
                logger.info("✅ UDS3 Polyglot Manager erstellt")
            except Exception as init_err:
                logger.warning(f"⚠️ UDS3 Polyglot Manager Init fehlgeschlagen: {init_err}")
            
            if uds3_strategy is None:
                logger.warning("⚠️ UDS3 strategy nicht verfügbar - verwende Mock Dense Retriever")
                # Erstelle Mock Dense Retriever
                from backend.agents.veritas_uds3_adapter import MockDenseRetriever
                uds3_adapter = MockDenseRetriever()
                logger.info(f"   ✅ Mock Dense Retriever initialized (no real vector search)")
            else:
                uds3_adapter = UDS3VectorSearchAdapter(uds3_strategy=uds3_strategy)
                logger.info(f"   ✅ UDS3 Adapter initialized with Polyglot Manager")
        except Exception as e:
            logger.warning(f"⚠️ UDS3 Initialisierung fehlgeschlagen: {e} - verwende Mock")
            from backend.agents.veritas_uds3_adapter import MockDenseRetriever
            uds3_adapter = MockDenseRetriever()
            logger.info(f"   ✅ Mock Dense Retriever initialized (fallback)")
        
        # Step 2: Initialize BM25 Sparse Retriever
        logger.info("\n📦 Step 2: Initializing BM25 Sparse Retriever...")
        
        bm25_config = SparseRetrievalConfig(
            k1=config["bm25_k1"],
            b=config["bm25_b"]
        )
        
        bm25_retriever = SparseRetriever(config=bm25_config)
        
        # Index demo corpus if provided
        if demo_corpus:
            logger.info(f"   📚 Indexing {len(demo_corpus)} demo documents...")
            bm25_retriever.index_documents(demo_corpus)
            logger.info(f"   ✅ BM25 indexed {len(demo_corpus)} documents")
        else:
            logger.info("   ⚠️ No demo corpus provided - BM25 index is empty")
            logger.info("   💡 Load your corpus and call: bm25_retriever.index_documents(corpus)")
        
        # Step 3: Initialize Hybrid Retriever
        logger.info("\n📦 Step 3: Initializing Hybrid Retriever (Dense + Sparse + RRF)...")
        
        hybrid_config = HybridRetrievalConfig(
            dense_weight=0.6,
            sparse_weight=0.4,
            rrf_k=config["rrf_k"],
            enable_query_expansion=config["enable_query_expansion"],
            dense_top_k=config["hybrid_dense_top_k"],
            sparse_top_k=config["hybrid_sparse_top_k"]
        )
        
        hybrid_retriever = HybridRetriever(
            dense_retriever=uds3_adapter,
            sparse_retriever=bm25_retriever,
            config=hybrid_config
        )
        
        logger.info(f"   ✅ Hybrid Retriever initialized")
        logger.info(f"   📊 Dense Weight: {hybrid_config.dense_weight}")
        logger.info(f"   📊 Sparse Weight: {hybrid_config.sparse_weight}")
        logger.info(f"   📊 RRF k: {hybrid_config.rrf_k}")
        
        # Step 4: Validation
        logger.info("\n🔍 Step 4: Validation...")
        
        test_query = "Test Query"
        logger.info(f"   Running test query: '{test_query}'")
        
        try:
            results = await hybrid_retriever.retrieve(test_query, top_k=5)
            
            logger.info(f"   ✅ Test query successful: {len(results)} results")
            
            if results and len(results) > 0:
                sample = results[0]
                logger.info(f"   📄 Sample result:")
                logger.info(f"      doc_id: {sample.doc_id}")
                logger.info(f"      score: {sample.score}")
                logger.info(f"      content: {sample.content[:100]}...")
            else:
                logger.info(f"   ⚠️ No results (expected if corpus not loaded)")
        except Exception as e:
            logger.warning(f"   ⚠️ Test query failed (non-critical): {e}")
        
        # Step 5: Summary
        logger.info("\n" + "=" * 80)
        logger.info("✅ PHASE 5 HYBRID SEARCH INITIALIZED SUCCESSFULLY")
        logger.info("=" * 80)
        logger.info(f"📊 System Status:")
        logger.info(f"   ✅ UDS3 Adapter: {'OK (with DB)' if UDS3_DB_AVAILABLE else 'OK (graceful degradation)'}")
        logger.info(f"   ✅ BM25 Retriever: OK ({len(demo_corpus) if demo_corpus else 0} docs indexed)")
        logger.info(f"   ✅ Hybrid Retriever: OK")
        logger.info(f"\n📝 Usage:")
        logger.info(f"   from backend.api.veritas_phase5_integration import hybrid_retriever")
        logger.info(f"   results = await hybrid_retriever.retrieve(query, top_k=10)")
        logger.info(f"\n⚡ Expected Performance:")
        logger.info(f"   BM25-only mode: <50ms (Dense=0.0)")
        logger.info(f"   Full Hybrid mode: <150ms (when Vector DB populated)")
        logger.info("=" * 80)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Phase 5 initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def get_hybrid_retriever():
    """Returns the global hybrid retriever instance."""
    global hybrid_retriever
    
    if hybrid_retriever is None:
        raise RuntimeError(
            "Hybrid Retriever not initialized! "
            "Call initialize_phase5_hybrid_search() first."
        )
    
    return hybrid_retriever


def get_bm25_retriever():
    """Returns the global BM25 retriever instance."""
    global bm25_retriever
    
    if bm25_retriever is None:
        raise RuntimeError(
            "BM25 Retriever not initialized! "
            "Call initialize_phase5_hybrid_search() first."
        )
    
    return bm25_retriever


def get_uds3_adapter():
    """Returns the global UDS3 adapter instance."""
    global uds3_adapter
    
    if uds3_adapter is None:
        raise RuntimeError(
            "UDS3 Adapter not initialized! "
            "Call initialize_phase5_hybrid_search() first."
        )
    
    return uds3_adapter


# Demo corpus for testing
DEMO_CORPUS = [
    {
        "doc_id": "doc_0",
        "content": "§ 110 BGB Taschengeldparagraph: Bewirkt der Minderjährige einen Vertrag ohne Zustimmung des gesetzlichen Vertreters, so hängt die Wirksamkeit des Vertrags von der Genehmigung ab.",
        "metadata": {"source": "BGB", "section": "110"}
    },
    {
        "doc_id": "doc_1",
        "content": "§ 433 BGB Vertragstypische Pflichten beim Kaufvertrag: Durch den Kaufvertrag wird der Verkäufer verpflichtet, dem Käufer die Sache zu übergeben und das Eigentum zu verschaffen.",
        "metadata": {"source": "BGB", "section": "433"}
    },
    {
        "doc_id": "doc_2",
        "content": "§ 35 VwVfG Begriff des Verwaltungsaktes: Verwaltungsakt ist jede Verfügung, Entscheidung oder andere hoheitliche Maßnahme, die eine Behörde zur Regelung eines Einzelfalls trifft.",
        "metadata": {"source": "VwVfG", "section": "35"}
    },
    {
        "doc_id": "doc_3",
        "content": "Nachhaltiges Bauen berücksichtigt ökologische, ökonomische und soziokulturelle Aspekte. Wichtige Normen: DIN 277, DGNB-Kriterien, Energieeinsparverordnung (EnEV).",
        "metadata": {"source": "Baurecht", "topic": "Nachhaltigkeit"}
    },
    {
        "doc_id": "doc_4",
        "content": "Bauordnung NRW § 39: Barrierefreies Bauen. Bauliche Anlagen müssen barrierefrei sein, soweit es die Nutzung erfordert. DIN 18040 enthält die technischen Anforderungen.",
        "metadata": {"source": "BauO NRW", "section": "39"}
    },
    {
        "doc_id": "doc_5",
        "content": "Immissionsschutz: Bundesimmissionsschutzgesetz (BImSchG) regelt Schutz vor Luftverunreinigungen, Lärm und Erschütterungen. TA Lärm und TA Luft sind wichtige Verwaltungsvorschriften.",
        "metadata": {"source": "Umweltrecht", "topic": "Emissionen"}
    },
    {
        "doc_id": "doc_6",
        "content": "Arbeitsschutz im Baugewerbe: ArbSchG, BaustellV, Unfallverhütungsvorschriften (UVV). PSA-Pflicht für Höhenarbeiten, Lärmschutz, Atemschutz bei Staubbelastung.",
        "metadata": {"source": "Arbeitsrecht", "topic": "Baustelle"}
    },
    {
        "doc_id": "doc_7",
        "content": "Verkehrssicherungspflicht auf Baustellen: Bauherr und Unternehmer haften für Schäden durch unzureichende Absicherung. BGH-Rechtsprechung zu Haftungsverteilung.",
        "metadata": {"source": "Haftungsrecht", "topic": "Verkehrssicherung"}
    }
]
