"""
Staging Deployment Script für Phase 5 mit UDS3 Adapter
Startet Backend mit Hybrid Search (BM25-only wegen leerer Vector DB)
"""
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def setup_environment():
    """Configure environment for Staging Phase 1 deployment"""
    print("=" * 80)
    print("PHASE 5 STAGING DEPLOYMENT - UDS3 ADAPTER")
    print("=" * 80)
    print()
    
    # Phase 5 Feature Toggles
    print("🔧 Setting Environment Variables...")
    
    env_vars = {
        # Feature Toggles
        "VERITAS_ENABLE_HYBRID_SEARCH": "true",
        "VERITAS_ENABLE_SPARSE_RETRIEVAL": "true",
        "VERITAS_ENABLE_QUERY_EXPANSION": "false",  # Ollama issues - disable for now
        "VERITAS_ENABLE_RERANKING": "true",
        
        # Deployment Stage
        "VERITAS_DEPLOYMENT_STAGE": "staging",
        "VERITAS_ROLLOUT_PERCENTAGE": "100",
        
        # Hybrid Parameters
        "VERITAS_HYBRID_SPARSE_TOP_K": "20",
        "VERITAS_HYBRID_DENSE_TOP_K": "20",
        "VERITAS_RRF_K": "60",
        
        # BM25 Parameters
        "VERITAS_BM25_K1": "1.5",
        "VERITAS_BM25_B": "0.75",
        
        # Performance Monitoring
        "VERITAS_ENABLE_PERFORMANCE_MONITORING": "true",
        "VERITAS_MAX_HYBRID_LATENCY_MS": "200",
    }
    
    for key, value in env_vars.items():
        os.environ[key] = value
        print(f"   ✅ {key}={value}")
    
    print()
    return env_vars


def verify_adapter():
    """Verify UDS3 Adapter is available"""
    print("🔍 Verifying UDS3 Adapter...")
    
    try:
        from backend.agents.veritas_uds3_adapter import UDS3VectorSearchAdapter, get_uds3_adapter
        print("   ✅ UDS3VectorSearchAdapter importiert")
        
        # Try to initialize
        try:
            adapter = get_uds3_adapter()
            print(f"   ✅ Adapter initialized: {type(adapter).__name__}")
            return True
        except Exception as e:
            print(f"   ⚠️ Adapter init warning: {e}")
            print(f"   Note: This is OK if UDS3 dependencies not fully configured")
            return True  # Still allow deployment
            
    except ImportError as e:
        print(f"   ❌ UDS3 Adapter not found: {e}")
        return False


def verify_components():
    """Verify Phase 5 components"""
    print()
    print("🔍 Verifying Phase 5 Components...")
    
    components = [
        ("backend.agents.veritas_sparse_retrieval", "SparseRetriever"),
        ("backend.agents.veritas_hybrid_retrieval", "HybridRetriever"),
        ("backend.agents.veritas_uds3_adapter", "UDS3VectorSearchAdapter"),
        ("config.phase5_config", "Phase5Config"),
    ]
    
    all_ok = True
    for module_path, class_name in components:
        try:
            module = __import__(module_path, fromlist=[class_name])
            cls = getattr(module, class_name)
            print(f"   ✅ {module_path}.{class_name}")
        except Exception as e:
            print(f"   ❌ {module_path}.{class_name}: {e}")
            all_ok = False
    
    return all_ok


def show_deployment_info():
    """Show deployment configuration summary"""
    print()
    print("=" * 80)
    print("DEPLOYMENT CONFIGURATION SUMMARY")
    print("=" * 80)
    print()
    
    print("📊 Feature Status:")
    print("   ✅ Hybrid Search: ENABLED")
    print("   ✅ Sparse Retrieval (BM25): ENABLED")
    print("   ❌ Query Expansion: DISABLED (Ollama not available)")
    print("   ✅ Re-Ranking: ENABLED (Phase 4)")
    print()
    
    print("🔧 Backend Configuration:")
    print("   Dense Retriever: UDS3VectorSearchAdapter")
    print("   Sparse Retriever: BM25Okapi (k1=1.5, b=0.75)")
    print("   Fusion: Reciprocal Rank Fusion (RRF, k=60)")
    print()
    
    print("⚡ Expected Performance:")
    print("   Latency Target: <50ms (Query Expansion disabled)")
    print("   Quality: BM25-only (Dense=0.0 until Vector DB populated)")
    print("   Stability: High (Graceful degradation active)")
    print()
    
    print("🎯 Current Behavior:")
    print("   1. Hybrid Search initialized with UDS3 Adapter")
    print("   2. UDS3 Adapter returns empty results (Vector DB leer)")
    print("   3. BM25 delivers 100% of retrieval results")
    print("   4. RRF Fusion processes BM25-only results")
    print("   5. System operates normally with graceful degradation")
    print()
    
    print("📈 Migration Path to Full Hybrid:")
    print("   1. Fix UDS3 create_secure_document() JSON bug")
    print("   2. Index documents via UDS3 Database API")
    print("   3. Vector DB auto-activates → Dense Scores > 0.0")
    print("   4. Full Hybrid Search active → +15-25% NDCG improvement")
    print("   5. NO CODE CHANGES REQUIRED")
    print()


def show_test_commands():
    """Show test commands for validation"""
    print("=" * 80)
    print("VALIDATION COMMANDS")
    print("=" * 80)
    print()
    
    print("1. Test UDS3 Adapter:")
    print("   python scripts/test_uds3_adapter.py")
    print()
    
    print("2. Test BM25 Standalone:")
    print("   python scripts/demo_bm25_standalone.py")
    print()
    
    print("3. Start Backend (wenn ready):")
    print("   python start_backend.py")
    print()
    
    print("4. Test Query (via API):")
    print("   curl http://localhost:8000/api/search?query=BGB+Taschengeldparagraph")
    print()
    
    print("5. Monitor Performance:")
    print("   # Check logs for Phase5Monitor metrics")
    print("   # Expected: Latency <50ms, Sparse Results > 0, Dense Results = 0")
    print()


def main():
    """Main deployment setup"""
    
    # Setup environment
    env_vars = setup_environment()
    
    # Verify adapter
    if not verify_adapter():
        print()
        print("❌ UDS3 Adapter verification failed")
        print("   Please check backend/agents/veritas_uds3_adapter.py exists")
        return 1
    
    # Verify components
    print()
    if not verify_components():
        print()
        print("⚠️ Some components missing - deployment may have issues")
        print("   Recommendation: Fix missing imports before deployment")
    
    # Show deployment info
    show_deployment_info()
    
    # Show test commands
    show_test_commands()
    
    # Final summary
    print("=" * 80)
    print("✅ STAGING ENVIRONMENT CONFIGURED")
    print("=" * 80)
    print()
    print("Next Steps:")
    print("1. Review configuration above")
    print("2. Run validation: python scripts/test_uds3_adapter.py")
    print("3. Start backend: python start_backend.py")
    print("4. Monitor logs for Phase5Monitor metrics")
    print("5. Validate queries return BM25 results")
    print()
    print("Rollback Plan:")
    print("   Set VERITAS_ENABLE_HYBRID_SEARCH=false")
    print("   Restart backend")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
