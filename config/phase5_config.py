"""
Phase 5 Hybrid Search & Query Expansion Configuration

Manages feature toggles, environment-specific settings, and performance parameters
for the Advanced RAG Pipeline (Phase 5).

Environment Variables:
    VERITAS_ENABLE_HYBRID_SEARCH: Enable hybrid search (Dense + Sparse + RRF)
    VERITAS_ENABLE_QUERY_EXPANSION: Enable LLM-based query expansion
    VERITAS_ENABLE_RERANKING: Enable cross-encoder re-ranking
    VERITAS_HYBRID_SPARSE_TOP_K: Number of BM25 results to retrieve
    VERITAS_HYBRID_DENSE_TOP_K: Number of Dense results to retrieve
    VERITAS_RRF_K: RRF constant parameter (default: 60)
    VERITAS_QUERY_EXPANSION_VARIANTS: Number of query variants to generate
    VERITAS_OLLAMA_BASE_URL: Ollama API base URL for query expansion

Usage:
    from config.phase5_config import Phase5Config
    
    config = Phase5Config.from_environment()
    print(f"Hybrid Search: {config.enable_hybrid_search}")
"""

import os
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from enum import Enum


class DeploymentStage(str, Enum):
    """Deployment stages for gradual rollout."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class ExpansionStrategy(str, Enum):
    """Query expansion strategies."""
    SYNONYM = "synonym"
    CONTEXT = "context"
    MULTI_PERSPECTIVE = "multi_perspective"
    TECHNICAL = "technical"
    SIMPLE = "simple"


@dataclass
class Phase5Config:
    """Configuration for Phase 5 Advanced RAG Pipeline.
    
    Feature Toggles:
        enable_hybrid_search: Enable Dense + Sparse + RRF hybrid retrieval
        enable_query_expansion: Enable LLM-based query expansion
        enable_reranking: Enable cross-encoder re-ranking
    
    Hybrid Search Parameters:
        hybrid_sparse_top_k: Top-K for BM25 sparse retrieval (default: 20)
        hybrid_dense_top_k: Top-K for dense UDS3 retrieval (default: 20)
        rrf_k: RRF constant parameter (default: 60)
        dense_weight: Weight for dense retriever in RRF (default: 0.6)
        sparse_weight: Weight for sparse retriever in RRF (default: 0.4)
    
    BM25 Parameters:
        bm25_k1: BM25 term frequency saturation (default: 1.5)
        bm25_b: BM25 document length normalization (default: 0.75)
        bm25_cache_ttl: BM25 query cache TTL in seconds (default: 3600)
    
    Query Expansion Parameters:
        query_expansion_variants: Number of variants to generate (default: 2)
        query_expansion_strategy: Strategy to use (default: MULTI_PERSPECTIVE)
        ollama_base_url: Ollama API URL (default: http://localhost:11434)
        ollama_model: Model for query expansion (default: llama2)
        ollama_timeout: Request timeout in seconds (default: 30)
    
    Performance Limits:
        max_hybrid_latency_ms: Maximum allowed hybrid retrieval latency (default: 200)
        max_query_expansion_latency_ms: Maximum query expansion latency (default: 2000)
        enable_performance_monitoring: Log performance metrics (default: True)
    
    Deployment:
        deployment_stage: Current deployment stage
        rollout_percentage: Percentage of traffic using Phase 5 features (0-100)
    """
    
    # Feature Toggles
    enable_hybrid_search: bool = False
    enable_query_expansion: bool = False
    enable_reranking: bool = True  # Already implemented in Phase 4
    
    # Hybrid Search Parameters
    hybrid_sparse_top_k: int = 20
    hybrid_dense_top_k: int = 20
    rrf_k: int = 60
    dense_weight: float = 0.6
    sparse_weight: float = 0.4
    
    # BM25 Parameters
    bm25_k1: float = 1.5
    bm25_b: float = 0.75
    bm25_cache_ttl: int = 3600  # 1 hour
    
    # Query Expansion Parameters
    query_expansion_variants: int = 2
    query_expansion_strategy: ExpansionStrategy = ExpansionStrategy.MULTI_PERSPECTIVE
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama2"
    ollama_timeout: int = 30
    
    # Performance Limits
    max_hybrid_latency_ms: int = 200
    max_query_expansion_latency_ms: int = 2000
    enable_performance_monitoring: bool = True
    
    # Deployment
    deployment_stage: DeploymentStage = DeploymentStage.DEVELOPMENT
    rollout_percentage: int = 0  # 0-100, for gradual rollout
    
    # Advanced Options
    enable_multi_query: bool = True  # Use multi-query retrieval
    multi_query_aggregation: str = "max"  # max, sum, avg
    enable_fusion_stats: bool = True  # Log fusion statistics
    
    @classmethod
    def from_environment(cls) -> 'Phase5Config':
        """Create configuration from environment variables.
        
        Returns:
            Phase5Config instance with values from environment
        
        Example:
            export VERITAS_ENABLE_HYBRID_SEARCH=true
            export VERITAS_DEPLOYMENT_STAGE=staging
            
            config = Phase5Config.from_environment()
        """
        def get_bool(key: str, default: bool) -> bool:
            value = os.getenv(key, str(default)).lower()
            return value in ('true', '1', 'yes', 'on')
        
        def get_int(key: str, default: int) -> int:
            try:
                return int(os.getenv(key, str(default)))
            except ValueError:
                return default
        
        def get_float(key: str, default: float) -> float:
            try:
                return float(os.getenv(key, str(default)))
            except ValueError:
                return default
        
        def get_str(key: str, default: str) -> str:
            return os.getenv(key, default)
        
        return cls(
            # Feature Toggles
            enable_hybrid_search=get_bool('VERITAS_ENABLE_HYBRID_SEARCH', False),
            enable_query_expansion=get_bool('VERITAS_ENABLE_QUERY_EXPANSION', False),
            enable_reranking=get_bool('VERITAS_ENABLE_RERANKING', True),
            
            # Hybrid Search Parameters
            hybrid_sparse_top_k=get_int('VERITAS_HYBRID_SPARSE_TOP_K', 20),
            hybrid_dense_top_k=get_int('VERITAS_HYBRID_DENSE_TOP_K', 20),
            rrf_k=get_int('VERITAS_RRF_K', 60),
            dense_weight=get_float('VERITAS_DENSE_WEIGHT', 0.6),
            sparse_weight=get_float('VERITAS_SPARSE_WEIGHT', 0.4),
            
            # BM25 Parameters
            bm25_k1=get_float('VERITAS_BM25_K1', 1.5),
            bm25_b=get_float('VERITAS_BM25_B', 0.75),
            bm25_cache_ttl=get_int('VERITAS_BM25_CACHE_TTL', 3600),
            
            # Query Expansion Parameters
            query_expansion_variants=get_int('VERITAS_QUERY_EXPANSION_VARIANTS', 2),
            query_expansion_strategy=ExpansionStrategy(
                get_str('VERITAS_QUERY_EXPANSION_STRATEGY', 'multi_perspective')
            ),
            ollama_base_url=get_str('VERITAS_OLLAMA_BASE_URL', 'http://localhost:11434'),
            ollama_model=get_str('VERITAS_OLLAMA_MODEL', 'llama2'),
            ollama_timeout=get_int('VERITAS_OLLAMA_TIMEOUT', 30),
            
            # Performance Limits
            max_hybrid_latency_ms=get_int('VERITAS_MAX_HYBRID_LATENCY_MS', 200),
            max_query_expansion_latency_ms=get_int('VERITAS_MAX_QE_LATENCY_MS', 2000),
            enable_performance_monitoring=get_bool('VERITAS_ENABLE_PERFORMANCE_MONITORING', True),
            
            # Deployment
            deployment_stage=DeploymentStage(
                get_str('VERITAS_DEPLOYMENT_STAGE', 'development')
            ),
            rollout_percentage=get_int('VERITAS_ROLLOUT_PERCENTAGE', 0),
            
            # Advanced Options
            enable_multi_query=get_bool('VERITAS_ENABLE_MULTI_QUERY', True),
            multi_query_aggregation=get_str('VERITAS_MULTI_QUERY_AGGREGATION', 'max'),
            enable_fusion_stats=get_bool('VERITAS_ENABLE_FUSION_STATS', True),
        )
    
    @classmethod
    def for_development(cls) -> 'Phase5Config':
        """Configuration for local development.
        
        All features disabled, safe defaults for testing.
        """
        return cls(
            deployment_stage=DeploymentStage.DEVELOPMENT,
            enable_hybrid_search=False,
            enable_query_expansion=False,
            enable_reranking=False,
            enable_performance_monitoring=True,
        )
    
    @classmethod
    def for_staging_phase1(cls) -> 'Phase5Config':
        """Configuration for Staging Phase 1: Hybrid Search only.
        
        Enable Dense + Sparse + RRF, disable Query Expansion.
        Monitor latency and quality metrics.
        """
        return cls(
            deployment_stage=DeploymentStage.STAGING,
            enable_hybrid_search=True,
            enable_query_expansion=False,
            enable_reranking=True,
            enable_performance_monitoring=True,
            rollout_percentage=10,  # Start with 10% traffic
        )
    
    @classmethod
    def for_staging_phase2(cls) -> 'Phase5Config':
        """Configuration for Staging Phase 2: Hybrid + Query Expansion.
        
        Enable all Phase 5 features. Full pipeline testing.
        """
        return cls(
            deployment_stage=DeploymentStage.STAGING,
            enable_hybrid_search=True,
            enable_query_expansion=True,
            enable_reranking=True,
            enable_performance_monitoring=True,
            rollout_percentage=10,  # Keep at 10% for initial testing
        )
    
    @classmethod
    def for_production(cls, rollout_percentage: int = 100) -> 'Phase5Config':
        """Configuration for Production deployment.
        
        Args:
            rollout_percentage: Percentage of traffic (0-100)
        
        Returns:
            Production-ready configuration
        """
        return cls(
            deployment_stage=DeploymentStage.PRODUCTION,
            enable_hybrid_search=True,
            enable_query_expansion=True,
            enable_reranking=True,
            enable_performance_monitoring=True,
            rollout_percentage=min(100, max(0, rollout_percentage)),
        )
    
    def to_rag_query_options(self) -> Dict[str, Any]:
        """Convert to RAGQueryOptions dictionary.
        
        Returns:
            Dictionary compatible with RAGQueryOptions initialization
        
        Example:
            config = Phase5Config.for_staging_phase1()
            options = RAGQueryOptions(**config.to_rag_query_options())
        """
        return {
            'enable_hybrid_search': self.enable_hybrid_search,
            'enable_query_expansion': self.enable_query_expansion,
            'enable_reranking': self.enable_reranking,
            'hybrid_sparse_top_k': self.hybrid_sparse_top_k,
            'hybrid_dense_top_k': self.hybrid_dense_top_k,
            'rrf_k': self.rrf_k,
            'dense_weight': self.dense_weight,
            'sparse_weight': self.sparse_weight,
            'query_expansion_variants': self.query_expansion_variants,
            'query_expansion_strategy': self.query_expansion_strategy.value,
        }
    
    def validate(self) -> list[str]:
        """Validate configuration parameters.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Validate weights sum to 1.0
        total_weight = self.dense_weight + self.sparse_weight
        if abs(total_weight - 1.0) > 0.01:
            errors.append(
                f"Dense + Sparse weights must sum to 1.0, got {total_weight:.2f}"
            )
        
        # Validate rollout percentage
        if not 0 <= self.rollout_percentage <= 100:
            errors.append(
                f"Rollout percentage must be 0-100, got {self.rollout_percentage}"
            )
        
        # Validate top-k values
        if self.hybrid_sparse_top_k < 1:
            errors.append(f"hybrid_sparse_top_k must be >= 1, got {self.hybrid_sparse_top_k}")
        if self.hybrid_dense_top_k < 1:
            errors.append(f"hybrid_dense_top_k must be >= 1, got {self.hybrid_dense_top_k}")
        
        # Validate BM25 parameters
        if not 0.5 <= self.bm25_k1 <= 3.0:
            errors.append(f"bm25_k1 should be 0.5-3.0, got {self.bm25_k1}")
        if not 0.0 <= self.bm25_b <= 1.0:
            errors.append(f"bm25_b should be 0.0-1.0, got {self.bm25_b}")
        
        # Validate query expansion
        if self.query_expansion_variants < 1:
            errors.append(
                f"query_expansion_variants must be >= 1, got {self.query_expansion_variants}"
            )
        
        return errors
    
    def __repr__(self) -> str:
        """Human-readable configuration summary."""
        features = []
        if self.enable_hybrid_search:
            features.append("Hybrid")
        if self.enable_query_expansion:
            features.append("QueryExpansion")
        if self.enable_reranking:
            features.append("ReRanking")
        
        features_str = "+".join(features) if features else "Baseline"
        
        return (
            f"Phase5Config("
            f"stage={self.deployment_stage.value}, "
            f"features={features_str}, "
            f"rollout={self.rollout_percentage}%)"
        )


# Preset configurations for easy access
DEVELOPMENT_CONFIG = Phase5Config.for_development()
STAGING_PHASE1_CONFIG = Phase5Config.for_staging_phase1()
STAGING_PHASE2_CONFIG = Phase5Config.for_staging_phase2()
PRODUCTION_CONFIG = Phase5Config.for_production()


def get_config() -> Phase5Config:
    """Get configuration based on current environment.
    
    Priority:
        1. Environment variables (VERITAS_*)
        2. VERITAS_DEPLOYMENT_STAGE environment variable
        3. Default to development
    
    Returns:
        Phase5Config instance
    
    Example:
        from config.phase5_config import get_config
        
        config = get_config()
        print(config)
    """
    # Check if any environment variables are set
    has_env_vars = any(
        key.startswith('VERITAS_')
        for key in os.environ.keys()
    )
    
    if has_env_vars:
        config = Phase5Config.from_environment()
    else:
        # Use preset based on deployment stage
        stage = os.getenv('VERITAS_DEPLOYMENT_STAGE', 'development')
        
        if stage == 'staging':
            # Check which staging phase
            if os.getenv('VERITAS_ENABLE_QUERY_EXPANSION', '').lower() == 'true':
                config = STAGING_PHASE2_CONFIG
            else:
                config = STAGING_PHASE1_CONFIG
        elif stage == 'production':
            rollout = int(os.getenv('VERITAS_ROLLOUT_PERCENTAGE', '100'))
            config = Phase5Config.for_production(rollout)
        else:
            config = DEVELOPMENT_CONFIG
    
    # Validate configuration
    errors = config.validate()
    if errors:
        raise ValueError(f"Invalid Phase 5 configuration:\n" + "\n".join(f"  - {e}" for e in errors))
    
    return config


if __name__ == "__main__":
    """Test configuration setup."""
    print("=== Phase 5 Configuration Test ===\n")
    
    print("1. Development Config:")
    print(f"   {DEVELOPMENT_CONFIG}")
    print(f"   Features: Hybrid={DEVELOPMENT_CONFIG.enable_hybrid_search}, "
          f"QE={DEVELOPMENT_CONFIG.enable_query_expansion}\n")
    
    print("2. Staging Phase 1 Config:")
    print(f"   {STAGING_PHASE1_CONFIG}")
    print(f"   Features: Hybrid={STAGING_PHASE1_CONFIG.enable_hybrid_search}, "
          f"QE={STAGING_PHASE1_CONFIG.enable_query_expansion}\n")
    
    print("3. Staging Phase 2 Config:")
    print(f"   {STAGING_PHASE2_CONFIG}")
    print(f"   Features: Hybrid={STAGING_PHASE2_CONFIG.enable_hybrid_search}, "
          f"QE={STAGING_PHASE2_CONFIG.enable_query_expansion}\n")
    
    print("4. Production Config:")
    print(f"   {PRODUCTION_CONFIG}")
    print(f"   Features: Hybrid={PRODUCTION_CONFIG.enable_hybrid_search}, "
          f"QE={PRODUCTION_CONFIG.enable_query_expansion}\n")
    
    print("5. Current Environment Config:")
    try:
        current_config = get_config()
        print(f"   {current_config}")
        print(f"   Validation: {'✅ PASS' if not current_config.validate() else '❌ FAIL'}")
    except ValueError as e:
        print(f"   ❌ {e}")
