"""
Unit Tests for Hybrid Search Configuration Module

Tests all configuration classes, validation logic, environment variable
loading, and preset configurations.

Run with: pytest tests/backend/test_hybrid_search_config.py -v
"""

import pytest
import os
from unittest.mock import patch

from config.hybrid_search_config import (
    SearchWeights,
    SearchFilters,
    RRFConfig,
    ReRankingConfig,
    HybridSearchConfig,
    RankingStrategy,
    ScoringMode,
    load_config_from_env,
    get_preset_config
)


# ============================================================================
# TEST: SearchWeights
# ============================================================================

class TestSearchWeights:
    """Test SearchWeights validation and serialization."""
    
    def test_default_weights_sum_to_one(self):
        """Test that default weights sum to 1.0."""
        weights = SearchWeights()
        total = weights.vector + weights.graph + weights.relational
        assert abs(total - 1.0) < 0.01
    
    def test_custom_weights_valid(self):
        """Test custom weights that sum to 1.0."""
        weights = SearchWeights(vector=0.7, graph=0.2, relational=0.1)
        assert weights.vector == 0.7
        assert weights.graph == 0.2
        assert weights.relational == 0.1
    
    def test_weights_invalid_sum(self):
        """Test that weights not summing to 1.0 raise ValueError."""
        with pytest.raises(ValueError, match="must sum to 1.0"):
            SearchWeights(vector=0.5, graph=0.3, relational=0.3)  # Sum = 1.1
    
    def test_weights_negative_values(self):
        """Test that negative weights raise ValueError."""
        with pytest.raises(ValueError, match="non-negative"):
            SearchWeights(vector=-0.1, graph=0.6, relational=0.5)
    
    def test_to_dict_serialization(self):
        """Test SearchWeights.to_dict() serialization."""
        weights = SearchWeights(vector=0.6, graph=0.2, relational=0.2)
        data = weights.to_dict()
        
        assert data == {
            "vector": 0.6,
            "graph": 0.2,
            "relational": 0.2
        }
    
    def test_from_dict_deserialization(self):
        """Test SearchWeights.from_dict() deserialization."""
        data = {"vector": 0.7, "graph": 0.2, "relational": 0.1}
        weights = SearchWeights.from_dict(data)
        
        assert weights.vector == 0.7
        assert weights.graph == 0.2
        assert weights.relational == 0.1


# ============================================================================
# TEST: SearchFilters
# ============================================================================

class TestSearchFilters:
    """Test SearchFilters validation and serialization."""
    
    def test_default_filters(self):
        """Test default filter values."""
        filters = SearchFilters()
        assert filters.max_results == 20
        assert filters.min_relevance == 0.5
        assert filters.date_from is None
        assert filters.document_types is None
    
    def test_custom_filters(self):
        """Test custom filter values."""
        filters = SearchFilters(
            max_results=10,
            min_relevance=0.7,
            document_types=["pdf", "docx"]
        )
        assert filters.max_results == 10
        assert filters.min_relevance == 0.7
        assert filters.document_types == ["pdf", "docx"]
    
    def test_invalid_max_results(self):
        """Test that max_results < 1 raises ValueError."""
        with pytest.raises(ValueError, match="max_results must be >= 1"):
            SearchFilters(max_results=0)
    
    def test_invalid_min_relevance(self):
        """Test that min_relevance outside [0, 1] raises ValueError."""
        with pytest.raises(ValueError, match="min_relevance must be in"):
            SearchFilters(min_relevance=1.5)
        
        with pytest.raises(ValueError, match="min_relevance must be in"):
            SearchFilters(min_relevance=-0.1)
    
    def test_to_dict_serialization(self):
        """Test SearchFilters.to_dict() serialization."""
        filters = SearchFilters(max_results=15, min_relevance=0.6)
        data = filters.to_dict()
        
        assert data["max_results"] == 15
        assert data["min_relevance"] == 0.6
        assert data["date_from"] is None


# ============================================================================
# TEST: RRFConfig
# ============================================================================

class TestRRFConfig:
    """Test RRF configuration validation."""
    
    def test_default_rrf_k(self):
        """Test default RRF k value."""
        rrf = RRFConfig()
        assert rrf.k == 60
    
    def test_custom_rrf_k(self):
        """Test custom RRF k value."""
        rrf = RRFConfig(k=100)
        assert rrf.k == 100
    
    def test_invalid_rrf_k_too_low(self):
        """Test that k < 1 raises ValueError."""
        with pytest.raises(ValueError, match="RRF k must be in"):
            RRFConfig(k=0)
    
    def test_invalid_rrf_k_too_high(self):
        """Test that k > 1000 raises ValueError."""
        with pytest.raises(ValueError, match="RRF k must be in"):
            RRFConfig(k=1001)


# ============================================================================
# TEST: ReRankingConfig
# ============================================================================

class TestReRankingConfig:
    """Test re-ranking configuration validation."""
    
    def test_default_reranking_config(self):
        """Test default re-ranking values."""
        config = ReRankingConfig()
        assert config.enabled is True
        assert config.model_name == "llama3.1:8b"
        assert config.scoring_mode == ScoringMode.COMBINED
        assert config.temperature == 0.1
        assert config.batch_size == 5
        assert config.timeout_seconds == 30
    
    def test_custom_reranking_config(self):
        """Test custom re-ranking values."""
        config = ReRankingConfig(
            enabled=False,
            model_name="llama3.2:3b",
            temperature=0.2,
            batch_size=10
        )
        assert config.enabled is False
        assert config.model_name == "llama3.2:3b"
        assert config.temperature == 0.2
        assert config.batch_size == 10
    
    def test_invalid_temperature(self):
        """Test that temperature outside [0, 1] raises ValueError."""
        with pytest.raises(ValueError, match="temperature must be in"):
            ReRankingConfig(temperature=1.5)
    
    def test_invalid_batch_size(self):
        """Test that batch_size < 1 raises ValueError."""
        with pytest.raises(ValueError, match="batch_size must be >= 1"):
            ReRankingConfig(batch_size=0)
    
    def test_invalid_timeout(self):
        """Test that timeout < 1 raises ValueError."""
        with pytest.raises(ValueError, match="timeout_seconds must be >= 1"):
            ReRankingConfig(timeout_seconds=0)


# ============================================================================
# TEST: RankingStrategy Enum
# ============================================================================

class TestRankingStrategy:
    """Test RankingStrategy enum."""
    
    def test_from_string_valid(self):
        """Test RankingStrategy.from_string() with valid values."""
        assert RankingStrategy.from_string("reciprocal_rank_fusion") == RankingStrategy.RECIPROCAL_RANK_FUSION
        assert RankingStrategy.from_string("weighted_combination") == RankingStrategy.WEIGHTED_COMBINATION
        assert RankingStrategy.from_string("borda_count") == RankingStrategy.BORDA_COUNT
    
    def test_from_string_case_insensitive(self):
        """Test case-insensitive parsing."""
        assert RankingStrategy.from_string("RECIPROCAL_RANK_FUSION") == RankingStrategy.RECIPROCAL_RANK_FUSION
        assert RankingStrategy.from_string("Weighted_Combination") == RankingStrategy.WEIGHTED_COMBINATION
    
    def test_from_string_invalid_defaults_to_rrf(self):
        """Test that invalid strategy defaults to RRF."""
        assert RankingStrategy.from_string("unknown") == RankingStrategy.RECIPROCAL_RANK_FUSION


# ============================================================================
# TEST: ScoringMode Enum
# ============================================================================

class TestScoringMode:
    """Test ScoringMode enum."""
    
    def test_from_string_valid(self):
        """Test ScoringMode.from_string() with valid values."""
        assert ScoringMode.from_string("relevance_only") == ScoringMode.RELEVANCE_ONLY
        assert ScoringMode.from_string("informativeness") == ScoringMode.INFORMATIVENESS_ONLY
        assert ScoringMode.from_string("combined") == ScoringMode.COMBINED
    
    def test_from_string_invalid_defaults_to_combined(self):
        """Test that invalid mode defaults to COMBINED."""
        assert ScoringMode.from_string("unknown") == ScoringMode.COMBINED


# ============================================================================
# TEST: HybridSearchConfig
# ============================================================================

class TestHybridSearchConfig:
    """Test master HybridSearchConfig."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = HybridSearchConfig()
        
        assert config.weights.vector == 0.6
        assert config.ranking_strategy == RankingStrategy.RECIPROCAL_RANK_FUSION
        assert config.reranking_config.enabled is True
        assert config.enable_hybrid_search is True
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = HybridSearchConfig(
            weights=SearchWeights(vector=0.7, graph=0.2, relational=0.1),
            ranking_strategy=RankingStrategy.BORDA_COUNT,
            reranking_config=ReRankingConfig(enabled=False)
        )
        
        assert config.weights.vector == 0.7
        assert config.ranking_strategy == RankingStrategy.BORDA_COUNT
        assert config.reranking_config.enabled is False
    
    def test_to_dict_serialization(self):
        """Test HybridSearchConfig.to_dict() serialization."""
        config = HybridSearchConfig()
        data = config.to_dict()
        
        assert "weights" in data
        assert "filters" in data
        assert "ranking_strategy" in data
        assert "reranking" in data
        assert data["ranking_strategy"] == "reciprocal_rank_fusion"
        assert data["reranking"]["enabled"] is True


# ============================================================================
# TEST: Environment Variable Loading
# ============================================================================

class TestLoadConfigFromEnv:
    """Test load_config_from_env() with mocked environment variables."""
    
    @patch.dict(os.environ, {}, clear=True)
    def test_load_default_config(self):
        """Test loading with no environment variables (defaults)."""
        config = load_config_from_env()
        
        assert config.weights.vector == 0.6
        assert config.reranking_config.enabled is True
        assert config.enable_hybrid_search is True
    
    @patch.dict(os.environ, {
        "HYBRID_SEARCH_ENABLED": "false",
        "HYBRID_WEIGHT_VECTOR": "0.8",
        "HYBRID_WEIGHT_GRAPH": "0.1",
        "HYBRID_WEIGHT_RELATIONAL": "0.1",
        "HYBRID_RANKING_STRATEGY": "weighted_combination"
    }, clear=True)
    def test_load_custom_weights(self):
        """Test loading custom weights from environment."""
        config = load_config_from_env()
        
        assert config.enable_hybrid_search is False
        assert config.weights.vector == 0.8
        assert config.weights.graph == 0.1
        assert config.weights.relational == 0.1
        assert config.ranking_strategy == RankingStrategy.WEIGHTED_COMBINATION
    
    @patch.dict(os.environ, {
        "RERANKING_ENABLED": "false",
        "RERANKING_MODEL": "llama3.2:3b",
        "RERANKING_BATCH_SIZE": "10",
        "RERANKING_TEMPERATURE": "0.2"
    }, clear=True)
    def test_load_custom_reranking(self):
        """Test loading custom re-ranking config from environment."""
        config = load_config_from_env()
        
        assert config.reranking_config.enabled is False
        assert config.reranking_config.model_name == "llama3.2:3b"
        assert config.reranking_config.batch_size == 10
        assert config.reranking_config.temperature == 0.2
    
    @patch.dict(os.environ, {
        "HYBRID_MAX_RESULTS": "30",
        "HYBRID_MIN_RELEVANCE": "0.7",
        "HYBRID_RRF_K": "100"
    }, clear=True)
    def test_load_custom_filters_and_rrf(self):
        """Test loading custom filters and RRF config."""
        config = load_config_from_env()
        
        assert config.filters.max_results == 30
        assert config.filters.min_relevance == 0.7
        assert config.rrf_config.k == 100
    
    @patch.dict(os.environ, {
        "HYBRID_WEIGHT_VECTOR": "0.5",
        "HYBRID_WEIGHT_GRAPH": "0.3",
        "HYBRID_WEIGHT_RELATIONAL": "0.3"  # Sum = 1.1 (invalid)
    }, clear=True)
    def test_load_invalid_weights_fallback_to_default(self):
        """Test that invalid weights fall back to default config."""
        config = load_config_from_env()
        
        # Should fall back to defaults (0.6, 0.2, 0.2)
        assert config.weights.vector == 0.6
        assert config.weights.graph == 0.2


# ============================================================================
# TEST: Preset Configurations
# ============================================================================

class TestPresetConfigs:
    """Test get_preset_config() presets."""
    
    def test_balanced_preset(self):
        """Test 'balanced' preset."""
        config = get_preset_config("balanced")
        
        assert config.weights.vector == 0.6
        assert config.weights.graph == 0.2
        assert config.weights.relational == 0.2
        assert config.reranking_config.enabled is True
    
    def test_vector_heavy_preset(self):
        """Test 'vector_heavy' preset."""
        config = get_preset_config("vector_heavy")
        
        assert config.weights.vector == 0.8
        assert config.weights.graph == 0.1
        assert config.weights.relational == 0.1
        assert config.ranking_strategy == RankingStrategy.WEIGHTED_COMBINATION
    
    def test_graph_heavy_preset(self):
        """Test 'graph_heavy' preset."""
        config = get_preset_config("graph_heavy")
        
        assert config.weights.vector == 0.4
        assert config.weights.graph == 0.4
        assert config.weights.relational == 0.2
    
    def test_fast_preset(self):
        """Test 'fast' preset (no re-ranking)."""
        config = get_preset_config("fast")
        
        assert config.reranking_config.enabled is False
        assert config.filters.max_results == 10
        assert config.ranking_strategy == RankingStrategy.WEIGHTED_COMBINATION
    
    def test_accurate_preset(self):
        """Test 'accurate' preset (more candidates, larger batches)."""
        config = get_preset_config("accurate")
        
        assert config.filters.max_results == 30
        assert config.filters.min_relevance == 0.3
        assert config.reranking_config.batch_size == 10
        assert config.reranking_config.enabled is True
    
    def test_production_preset(self):
        """Test 'production' preset."""
        config = get_preset_config("production")
        
        assert config.weights.vector == 0.6
        assert config.rrf_config.k == 60
        assert config.reranking_config.batch_size == 5
        assert config.reranking_config.max_retries == 2
    
    def test_preset_case_insensitive(self):
        """Test that preset names are case-insensitive."""
        config1 = get_preset_config("BALANCED")
        config2 = get_preset_config("Balanced")
        
        assert config1.weights.vector == config2.weights.vector
    
    def test_unknown_preset_raises_error(self):
        """Test that unknown preset raises ValueError."""
        with pytest.raises(ValueError, match="Unknown preset"):
            get_preset_config("unknown_preset")


# ============================================================================
# TEST: Integration Scenarios
# ============================================================================

class TestIntegrationScenarios:
    """Test realistic usage scenarios."""
    
    def test_production_config_from_env_variables(self):
        """Test production-like configuration with environment variables."""
        env_vars = {
            "HYBRID_SEARCH_ENABLED": "true",
            "HYBRID_RANKING_STRATEGY": "reciprocal_rank_fusion",
            "HYBRID_WEIGHT_VECTOR": "0.6",
            "HYBRID_WEIGHT_GRAPH": "0.2",
            "HYBRID_WEIGHT_RELATIONAL": "0.2",
            "HYBRID_MAX_RESULTS": "20",
            "HYBRID_MIN_RELEVANCE": "0.5",
            "HYBRID_RRF_K": "60",
            "RERANKING_ENABLED": "true",
            "RERANKING_MODEL": "llama3.1:8b",
            "RERANKING_SCORING_MODE": "combined",
            "RERANKING_BATCH_SIZE": "5",
            "RERANKING_TIMEOUT": "30"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            config = load_config_from_env()
            
            assert config.enable_hybrid_search is True
            assert config.weights.vector == 0.6
            assert config.reranking_config.enabled is True
            assert config.rrf_config.k == 60
    
    def test_fast_mode_for_low_latency(self):
        """Test 'fast' preset for low-latency requirements."""
        config = get_preset_config("fast")
        
        # Fast mode should disable re-ranking
        assert config.reranking_config.enabled is False
        
        # And reduce result count
        assert config.filters.max_results <= 10
        
        # Use faster ranking strategy
        assert config.ranking_strategy == RankingStrategy.WEIGHTED_COMBINATION
    
    def test_accurate_mode_for_best_quality(self):
        """Test 'accurate' preset for maximum quality."""
        config = get_preset_config("accurate")
        
        # Accurate mode should enable re-ranking
        assert config.reranking_config.enabled is True
        
        # Larger candidate pool
        assert config.filters.max_results >= 30
        
        # Lower relevance threshold for more candidates
        assert config.filters.min_relevance <= 0.3
        
        # Larger batch size
        assert config.reranking_config.batch_size >= 10


# ============================================================================
# TEST: Validation Edge Cases
# ============================================================================

class TestValidationEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_weights_with_floating_point_precision(self):
        """Test weights that sum to 1.0 within floating point tolerance."""
        # Should be valid (within 0.99-1.01 tolerance)
        weights = SearchWeights(vector=0.333333, graph=0.333333, relational=0.333334)
        assert weights.vector + weights.graph + weights.relational >= 0.99
    
    def test_min_relevance_boundaries(self):
        """Test min_relevance at boundaries (0.0 and 1.0)."""
        filters1 = SearchFilters(min_relevance=0.0)
        assert filters1.min_relevance == 0.0
        
        filters2 = SearchFilters(min_relevance=1.0)
        assert filters2.min_relevance == 1.0
    
    def test_rrf_k_boundaries(self):
        """Test RRF k at boundaries (1 and 1000)."""
        rrf1 = RRFConfig(k=1)
        assert rrf1.k == 1
        
        rrf2 = RRFConfig(k=1000)
        assert rrf2.k == 1000
    
    def test_temperature_boundaries(self):
        """Test temperature at boundaries (0.0 and 1.0)."""
        config1 = ReRankingConfig(temperature=0.0)
        assert config1.temperature == 0.0
        
        config2 = ReRankingConfig(temperature=1.0)
        assert config2.temperature == 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
