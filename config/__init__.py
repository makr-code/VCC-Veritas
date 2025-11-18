"""
Config Package for VERITAS Framework

This package contains all configuration modules for the VERITAS system.
"""

# Import main configuration classes
from .config import CovinaConfig

# Import hybrid search configuration
from .hybrid_search_config import (
    DEFAULT_CONFIG,
    HybridSearchConfig,
    RankingStrategy,
    ReRankingConfig,
    RRFConfig,
    ScoringMode,
    SearchFilters,
    SearchWeights,
    get_preset_config,
    load_config_from_env,
)

__all__ = [
    # Main config
    "CovinaConfig",
    # Hybrid search config
    "HybridSearchConfig",
    "SearchWeights",
    "SearchFilters",
    "RRFConfig",
    "ReRankingConfig",
    "RankingStrategy",
    "ScoringMode",
    "load_config_from_env",
    "get_preset_config",
    "DEFAULT_CONFIG",
]
