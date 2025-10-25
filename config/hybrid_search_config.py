"""
Hybrid Search Configuration Module

Provides centralized configuration for the Hybrid Search system with support for:
- SearchWeights (Vector, Graph, Relational ratios)
- Ranking Strategies (RRF, Weighted, Borda)
- Re-Ranking settings (LLM model, batch size, scoring mode)
- Environment variable overrides
- Validation and best-practice defaults

Author: Veritas Development Team
Version: 1.0.0
Date: 2025-10-20
"""

import os
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS: Ranking Strategies & Scoring Modes
# ============================================================================

class RankingStrategy(str, Enum):
    """Available ranking strategies for hybrid search fusion."""
    RECIPROCAL_RANK_FUSION = "reciprocal_rank_fusion"  # RRF (Default)
    WEIGHTED_COMBINATION = "weighted_combination"      # Weighted average
    BORDA_COUNT = "borda_count"                        # Borda count method
    
    @classmethod
    def from_string(cls, value: str) -> "RankingStrategy":
        """Convert string to RankingStrategy enum."""
        try:
            return cls(value.lower())
        except ValueError:
            logger.warning(f"Unknown ranking strategy '{value}', defaulting to RRF")
            return cls.RECIPROCAL_RANK_FUSION


class ScoringMode(str, Enum):
    """Re-ranking scoring modes for LLM-based evaluation."""
    RELEVANCE_ONLY = "relevance_only"          # Focus on query relevance
    INFORMATIVENESS_ONLY = "informativeness"   # Focus on information quality
    COMBINED = "combined"                      # Balanced approach (Default)
    
    @classmethod
    def from_string(cls, value: str) -> "ScoringMode":
        """Convert string to ScoringMode enum."""
        try:
            return cls(value.lower())
        except ValueError:
            logger.warning(f"Unknown scoring mode '{value}', defaulting to COMBINED")
            return cls.COMBINED


# ============================================================================
# DATACLASSES: Configuration Objects
# ============================================================================

@dataclass
class SearchWeights:
    """
    Weights for hybrid search components.
    
    Must sum to 1.0 for consistent scoring.
    Defaults optimized for Verwaltungs-Domain (legal/regulatory documents).
    
    Attributes:
        vector: Dense retrieval weight (semantic similarity)
        graph: Knowledge graph retrieval weight (entity relationships)
        relational: Relational DB retrieval weight (structured queries)
    """
    vector: float = 0.6      # 60% - Primary for semantic search
    graph: float = 0.2       # 20% - Entity/relationship context
    relational: float = 0.2  # 20% - Structured metadata
    
    def __post_init__(self):
        """Validate weights sum to 1.0."""
        total = self.vector + self.graph + self.relational
        if not (0.99 <= total <= 1.01):  # Allow small floating point errors
            raise ValueError(
                f"SearchWeights must sum to 1.0, got {total}. "
                f"(vector={self.vector}, graph={self.graph}, relational={self.relational})"
            )
        if any(w < 0 for w in [self.vector, self.graph, self.relational]):
            raise ValueError("All weights must be non-negative")
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary for API serialization."""
        return {
            "vector": self.vector,
            "graph": self.graph,
            "relational": self.relational
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> "SearchWeights":
        """Create from dictionary."""
        return cls(
            vector=data.get("vector", 0.6),
            graph=data.get("graph", 0.2),
            relational=data.get("relational", 0.2)
        )


@dataclass
class SearchFilters:
    """
    Filters for hybrid search results.
    
    Attributes:
        max_results: Maximum number of results to return (per retriever)
        min_relevance: Minimum relevance score threshold (0.0-1.0)
        date_from: Optional start date filter (ISO 8601)
        date_to: Optional end date filter (ISO 8601)
        document_types: Optional list of document types to include
        source_types: Optional list of source types (vector/graph/relational)
    """
    max_results: int = 20
    min_relevance: float = 0.5
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    document_types: Optional[List[str]] = None
    source_types: Optional[List[str]] = None
    
    def __post_init__(self):
        """Validate filter values."""
        if self.max_results < 1:
            raise ValueError(f"max_results must be >= 1, got {self.max_results}")
        if not (0.0 <= self.min_relevance <= 1.0):
            raise ValueError(f"min_relevance must be in [0.0, 1.0], got {self.min_relevance}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API serialization."""
        return {
            "max_results": self.max_results,
            "min_relevance": self.min_relevance,
            "date_from": self.date_from,
            "date_to": self.date_to,
            "document_types": self.document_types,
            "source_types": self.source_types
        }


@dataclass
class RRFConfig:
    """
    Reciprocal Rank Fusion (RRF) algorithm configuration.
    
    RRF Formula: score(doc) = Σ[1 / (k + rank_i)]
    where rank_i is the rank in the i-th result list.
    
    Attributes:
        k: RRF constant (default=60, recommended range: 10-100)
           Higher k → more emphasis on top-ranked results
           Lower k → flatter score distribution
    """
    k: int = 60
    
    def __post_init__(self):
        """Validate RRF parameters."""
        if not (1 <= self.k <= 1000):
            raise ValueError(f"RRF k must be in [1, 1000], got {self.k}")


@dataclass
class ReRankingConfig:
    """
    LLM-based re-ranking configuration.
    
    Attributes:
        enabled: Whether to enable re-ranking (default: True)
        model_name: Ollama model name (default: llama3.1:8b)
        scoring_mode: Scoring mode (RELEVANCE_ONLY, INFORMATIVENESS_ONLY, COMBINED)
        temperature: LLM temperature for scoring consistency (0.0-1.0, default: 0.1)
        batch_size: Number of documents to rerank per batch (default: 5)
        timeout_seconds: Timeout per batch in seconds (default: 30)
        max_retries: Max retry attempts on LLM failure (default: 2)
    """
    enabled: bool = True
    model_name: str = "llama3.1:8b"
    scoring_mode: ScoringMode = ScoringMode.COMBINED
    temperature: float = 0.1
    batch_size: int = 5
    timeout_seconds: int = 30
    max_retries: int = 2
    
    def __post_init__(self):
        """Validate re-ranking parameters."""
        if not (0.0 <= self.temperature <= 1.0):
            raise ValueError(f"temperature must be in [0.0, 1.0], got {self.temperature}")
        if self.batch_size < 1:
            raise ValueError(f"batch_size must be >= 1, got {self.batch_size}")
        if self.timeout_seconds < 1:
            raise ValueError(f"timeout_seconds must be >= 1, got {self.timeout_seconds}")
        if self.max_retries < 0:
            raise ValueError(f"max_retries must be >= 0, got {self.max_retries}")


@dataclass
class HybridSearchConfig:
    """
    Master configuration for Hybrid Search system.
    
    Combines all sub-configurations with environment variable support.
    """
    # Sub-configurations
    weights: SearchWeights = field(default_factory=SearchWeights)
    filters: SearchFilters = field(default_factory=SearchFilters)
    rrf_config: RRFConfig = field(default_factory=RRFConfig)
    reranking_config: ReRankingConfig = field(default_factory=ReRankingConfig)
    
    # Top-level settings
    ranking_strategy: RankingStrategy = RankingStrategy.RECIPROCAL_RANK_FUSION
    enable_hybrid_search: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/debugging."""
        return {
            "weights": self.weights.to_dict(),
            "filters": self.filters.to_dict(),
            "ranking_strategy": self.ranking_strategy.value,
            "rrf_k": self.rrf_config.k,
            "reranking": {
                "enabled": self.reranking_config.enabled,
                "model": self.reranking_config.model_name,
                "scoring_mode": self.reranking_config.scoring_mode.value,
                "temperature": self.reranking_config.temperature,
                "batch_size": self.reranking_config.batch_size
            },
            "enable_hybrid_search": self.enable_hybrid_search
        }


# ============================================================================
# ENVIRONMENT VARIABLE LOADER
# ============================================================================

def load_config_from_env() -> HybridSearchConfig:
    """
    Load HybridSearchConfig from environment variables.
    
    Environment Variables:
        HYBRID_SEARCH_ENABLED: Enable hybrid search (default: true)
        HYBRID_RANKING_STRATEGY: Ranking strategy (rrf/weighted/borda, default: rrf)
        
        # Search Weights (must sum to 1.0)
        HYBRID_WEIGHT_VECTOR: Vector search weight (default: 0.6)
        HYBRID_WEIGHT_GRAPH: Graph search weight (default: 0.2)
        HYBRID_WEIGHT_RELATIONAL: Relational search weight (default: 0.2)
        
        # Search Filters
        HYBRID_MAX_RESULTS: Max results per retriever (default: 20)
        HYBRID_MIN_RELEVANCE: Min relevance threshold (default: 0.5)
        
        # RRF Configuration
        HYBRID_RRF_K: RRF k parameter (default: 60)
        
        # Re-Ranking Configuration
        RERANKING_ENABLED: Enable LLM re-ranking (default: true)
        RERANKING_MODEL: Ollama model name (default: llama3.1:8b)
        RERANKING_SCORING_MODE: Scoring mode (default: combined)
        RERANKING_TEMPERATURE: LLM temperature (default: 0.1)
        RERANKING_BATCH_SIZE: Batch size (default: 5)
        RERANKING_TIMEOUT: Timeout in seconds (default: 30)
        RERANKING_MAX_RETRIES: Max retry attempts (default: 2)
    
    Returns:
        HybridSearchConfig: Fully configured instance
    
    Raises:
        ValueError: If configuration is invalid (e.g., weights don't sum to 1.0)
    """
    try:
        # Top-level settings
        enable_hybrid_search = os.getenv("HYBRID_SEARCH_ENABLED", "true").lower() == "true"
        ranking_strategy = RankingStrategy.from_string(
            os.getenv("HYBRID_RANKING_STRATEGY", "reciprocal_rank_fusion")
        )
        
        # Search Weights
        weights = SearchWeights(
            vector=float(os.getenv("HYBRID_WEIGHT_VECTOR", "0.6")),
            graph=float(os.getenv("HYBRID_WEIGHT_GRAPH", "0.2")),
            relational=float(os.getenv("HYBRID_WEIGHT_RELATIONAL", "0.2"))
        )
        
        # Search Filters
        filters = SearchFilters(
            max_results=int(os.getenv("HYBRID_MAX_RESULTS", "20")),
            min_relevance=float(os.getenv("HYBRID_MIN_RELEVANCE", "0.5"))
        )
        
        # RRF Configuration
        rrf_config = RRFConfig(
            k=int(os.getenv("HYBRID_RRF_K", "60"))
        )
        
        # Re-Ranking Configuration
        reranking_config = ReRankingConfig(
            enabled=os.getenv("RERANKING_ENABLED", "true").lower() == "true",
            model_name=os.getenv("RERANKING_MODEL", "llama3.1:8b"),
            scoring_mode=ScoringMode.from_string(
                os.getenv("RERANKING_SCORING_MODE", "combined")
            ),
            temperature=float(os.getenv("RERANKING_TEMPERATURE", "0.1")),
            batch_size=int(os.getenv("RERANKING_BATCH_SIZE", "5")),
            timeout_seconds=int(os.getenv("RERANKING_TIMEOUT", "30")),
            max_retries=int(os.getenv("RERANKING_MAX_RETRIES", "2"))
        )
        
        config = HybridSearchConfig(
            weights=weights,
            filters=filters,
            rrf_config=rrf_config,
            reranking_config=reranking_config,
            ranking_strategy=ranking_strategy,
            enable_hybrid_search=enable_hybrid_search
        )
        
        logger.info("Hybrid Search configuration loaded successfully")
        logger.debug(f"Config: {config.to_dict()}")
        
        return config
        
    except Exception as e:
        logger.error(f"Failed to load Hybrid Search config from environment: {e}")
        logger.warning("Using default configuration")
        return HybridSearchConfig()


# ============================================================================
# PRESET CONFIGURATIONS
# ============================================================================

def get_preset_config(preset: str) -> HybridSearchConfig:
    """
    Get pre-configured settings for common use cases.
    
    Available Presets:
        - "balanced": Default balanced weights (60/20/20)
        - "vector_heavy": Emphasize semantic search (80/10/10)
        - "graph_heavy": Emphasize entity relationships (40/40/20)
        - "fast": Disable re-ranking for low-latency (< 2s)
        - "accurate": Enable all features for best quality (< 10s)
        - "production": Production-ready defaults with monitoring
    
    Args:
        preset: Preset name (case-insensitive)
    
    Returns:
        HybridSearchConfig: Pre-configured instance
    
    Raises:
        ValueError: If preset name is unknown
    """
    preset = preset.lower()
    
    if preset == "balanced":
        return HybridSearchConfig()  # Default is already balanced
    
    elif preset == "vector_heavy":
        return HybridSearchConfig(
            weights=SearchWeights(vector=0.8, graph=0.1, relational=0.1),
            ranking_strategy=RankingStrategy.WEIGHTED_COMBINATION
        )
    
    elif preset == "graph_heavy":
        return HybridSearchConfig(
            weights=SearchWeights(vector=0.4, graph=0.4, relational=0.2),
            ranking_strategy=RankingStrategy.RECIPROCAL_RANK_FUSION
        )
    
    elif preset == "fast":
        return HybridSearchConfig(
            weights=SearchWeights(vector=0.7, graph=0.2, relational=0.1),
            filters=SearchFilters(max_results=10),  # Fewer results
            reranking_config=ReRankingConfig(enabled=False),  # Skip re-ranking
            ranking_strategy=RankingStrategy.WEIGHTED_COMBINATION  # Faster than RRF
        )
    
    elif preset == "accurate":
        return HybridSearchConfig(
            weights=SearchWeights(vector=0.6, graph=0.2, relational=0.2),
            filters=SearchFilters(max_results=30, min_relevance=0.3),  # More candidates
            reranking_config=ReRankingConfig(
                enabled=True,
                batch_size=10,  # Larger batches
                scoring_mode=ScoringMode.COMBINED
            ),
            ranking_strategy=RankingStrategy.RECIPROCAL_RANK_FUSION
        )
    
    elif preset == "production":
        return HybridSearchConfig(
            weights=SearchWeights(vector=0.6, graph=0.2, relational=0.2),
            filters=SearchFilters(max_results=20, min_relevance=0.5),
            rrf_config=RRFConfig(k=60),
            reranking_config=ReRankingConfig(
                enabled=True,
                batch_size=5,
                timeout_seconds=30,
                max_retries=2
            ),
            ranking_strategy=RankingStrategy.RECIPROCAL_RANK_FUSION
        )
    
    else:
        raise ValueError(
            f"Unknown preset '{preset}'. Available: "
            "balanced, vector_heavy, graph_heavy, fast, accurate, production"
        )


# ============================================================================
# GLOBAL CONFIGURATION INSTANCE
# ============================================================================

# Initialize from environment variables on module import
DEFAULT_CONFIG = load_config_from_env()


# ============================================================================
# USAGE EXAMPLES (for documentation)
# ============================================================================

if __name__ == "__main__":
    """
    Example usage of HybridSearchConfig.
    
    Run with: python -m config.hybrid_search_config
    """
    print("=" * 80)
    print("HYBRID SEARCH CONFIGURATION EXAMPLES")
    print("=" * 80)
    
    # Example 1: Default configuration
    print("\n1. Default Configuration (from environment):")
    default_config = load_config_from_env()
    print(f"   Weights: {default_config.weights.to_dict()}")
    print(f"   Strategy: {default_config.ranking_strategy.value}")
    print(f"   Re-ranking: {default_config.reranking_config.enabled}")
    
    # Example 2: Custom configuration
    print("\n2. Custom Configuration:")
    custom_config = HybridSearchConfig(
        weights=SearchWeights(vector=0.7, graph=0.2, relational=0.1),
        ranking_strategy=RankingStrategy.BORDA_COUNT,
        reranking_config=ReRankingConfig(enabled=False)
    )
    print(f"   Config: {custom_config.to_dict()}")
    
    # Example 3: Preset configurations
    print("\n3. Preset Configurations:")
    for preset in ["balanced", "vector_heavy", "fast", "accurate"]:
        preset_config = get_preset_config(preset)
        print(f"   {preset.upper()}:")
        print(f"      Weights: {preset_config.weights.to_dict()}")
        print(f"      Re-ranking: {preset_config.reranking_config.enabled}")
    
    # Example 4: Environment variable simulation
    print("\n4. Environment Variable Examples:")
    print("   # Enable hybrid search with custom weights")
    print("   export HYBRID_SEARCH_ENABLED=true")
    print("   export HYBRID_WEIGHT_VECTOR=0.7")
    print("   export HYBRID_WEIGHT_GRAPH=0.2")
    print("   export HYBRID_WEIGHT_RELATIONAL=0.1")
    print()
    print("   # Configure re-ranking")
    print("   export RERANKING_ENABLED=true")
    print("   export RERANKING_MODEL=llama3.1:8b")
    print("   export RERANKING_BATCH_SIZE=10")
    
    print("\n" + "=" * 80)
