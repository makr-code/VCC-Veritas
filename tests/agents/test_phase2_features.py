"""
Tests for Phase 2 Features - Intelligence & Advanced Capabilities

Comprehensive test coverage for:
1. Self-Reflection Loops
2. Cross-Source Fact Verification
3. Query History Learning
4. Automatic Template Generation
5. Multi-Perspective Synthesis
"""

import pytest
import asyncio
from backend.agents.framework.phase2_features import (
    # Self-Reflection
    SelfReflectionEngine,
    ReflectionDimension,
    ReflectionCritique,
    
    # Cross-Source Verification
    CrossSourceVerifier,
    Claim,
    Contradiction,
    ContradictionSeverity,
    
    # Query History Learning
    QueryHistoryLearner,
    QueryPattern,
    UserProfile,
    
    # Template Generation
    AutomaticTemplateGenerator,
    QueryTemplate,
    TemplateMatch,
    
    # Multi-Perspective Synthesis
    MultiPerspectiveSynthesizer,
    PerspectiveDimension,
    PerspectiveAnalysis,
    
    # Coordinator
    Phase2FeatureCoordinator
)
from datetime import datetime


# ============================================================================
# MOCK CLASSES
# ============================================================================

class MockLLMClient:
    """Mock LLM client for testing"""
    
    def __init__(self):
        self.call_count = 0
    
    async def generate(self, prompt: str):
        self.call_count += 1
        
        # Return different responses based on prompt content
        if "critique" in prompt.lower():
            return {
                "score": 0.75,
                "issues": ["Could be more specific", "Missing examples"],
                "suggestions": ["Add concrete examples", "Provide more detail"],
                "confidence": 0.8
            }
        elif "refine" in prompt.lower():
            return {
                "text": "Refined answer with improvements based on feedback."
            }
        elif "contradiction" in prompt.lower():
            return {
                "contradiction": "NO_CONTRADICTION"
            }
        elif "claims" in prompt.lower():
            return {
                "claims": [
                    {
                        "text": "Test claim 1",
                        "confidence": 0.8,
                        "evidence": ["Evidence 1", "Evidence 2"]
                    }
                ]
            }
        elif "template" in prompt.lower() and "match" in prompt.lower():
            return {
                "match": "YES",
                "confidence": 0.85,
                "parameters": {"subject": "legal", "object": "requirements"}
            }
        elif "template" in prompt.lower():
            return {
                "name": "Test Template",
                "description": "A test query template",
                "pattern": "What are the {subject} requirements for {object}?",
                "parameters": ["subject", "object"]
            }
        elif "perspective" in prompt.lower():
            return {
                "key_points": ["Point 1", "Point 2"],
                "considerations": ["Consideration 1"],
                "trade_offs": ["Trade-off 1"],
                "confidence": 0.8
            }
        elif "synthesize" in prompt.lower():
            return {
                "answer": "Holistic synthesized answer.",
                "recommendations": ["Recommendation 1", "Recommendation 2"]
            }
        
        return {"text": "Default response"}


class MockStorage:
    """Mock storage for testing"""
    
    def __init__(self):
        self.data = {}
    
    async def append(self, key: str, value: dict):
        if key not in self.data:
            self.data[key] = []
        self.data[key].append(value)
    
    async def query(self, key: str, filter_dict: dict):
        if key not in self.data:
            return []
        
        # Simple filtering by user_id if present
        if "user_id" in filter_dict:
            return [
                item for item in self.data[key]
                if item.get("user_id") == filter_dict["user_id"]
            ]
        
        return self.data[key]
    
    async def save(self, key: str, value: dict):
        if key not in self.data:
            self.data[key] = []
        self.data[key].append(value)


# ============================================================================
# SELF-REFLECTION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_self_reflection_critique():
    """Test answer critique functionality"""
    engine = SelfReflectionEngine(MockLLMClient())
    
    critiques = await engine.critique_answer(
        "Test answer",
        "Test query"
    )
    
    assert len(critiques) == 5  # One per dimension
    assert all(isinstance(c, ReflectionCritique) for c in critiques)
    assert all(0.0 <= c.score <= 1.0 for c in critiques)


@pytest.mark.asyncio
async def test_self_reflection_refinement():
    """Test answer refinement"""
    engine = SelfReflectionEngine(MockLLMClient())
    
    critiques = [
        ReflectionCritique(
            dimension=ReflectionDimension.ACCURACY,
            score=0.7,
            issues=["Issue 1"],
            suggestions=["Suggestion 1"],
            confidence=0.8
        )
    ]
    
    refined = await engine.refine_answer(
        "Original answer",
        critiques,
        "Test query"
    )
    
    assert isinstance(refined, str)
    assert len(refined) > 0


@pytest.mark.asyncio
async def test_self_reflection_loop_convergence():
    """Test reflection loop convergence"""
    engine = SelfReflectionEngine(MockLLMClient(), max_iterations=3)
    
    result = await engine.execute_reflection_loop(
        "Initial answer",
        "Test query"
    )
    
    assert result.iteration > 0
    assert result.overall_quality >= 0.0
    assert result.refined_answer != ""
    assert len(result.critiques) > 0


# ============================================================================
# CROSS-SOURCE VERIFICATION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_claim_extraction():
    """Test claim extraction from source"""
    verifier = CrossSourceVerifier(MockLLMClient())
    
    claims = await verifier.extract_claims(
        "Test source text with facts.",
        "source_1"
    )
    
    assert len(claims) > 0
    assert all(isinstance(c, Claim) for c in claims)
    assert all(c.source_id == "source_1" for c in claims)


@pytest.mark.asyncio
async def test_contradiction_detection():
    """Test contradiction detection between claims"""
    verifier = CrossSourceVerifier(MockLLMClient())
    
    claims = [
        Claim("Fact A", "source_1", 0.9, ["Evidence 1"]),
        Claim("Fact B", "source_2", 0.8, ["Evidence 2"])
    ]
    
    contradictions = await verifier.detect_contradictions(claims)
    
    # With mock LLM returning NO_CONTRADICTION
    assert isinstance(contradictions, list)


@pytest.mark.asyncio
async def test_fact_verification_full():
    """Test complete fact verification workflow"""
    verifier = CrossSourceVerifier(MockLLMClient(), min_sources=2)
    
    sources = [
        {"id": "s1", "text": "Source 1 text"},
        {"id": "s2", "text": "Source 2 text"}
    ]
    
    result = await verifier.verify_facts(sources)
    
    assert result.sources_analyzed == 2
    assert 0.0 <= result.consensus_level <= 1.0
    assert 0.0 <= result.reliability_score <= 1.0


@pytest.mark.asyncio
async def test_verification_min_sources():
    """Test minimum sources requirement"""
    verifier = CrossSourceVerifier(MockLLMClient(), min_sources=2)
    
    with pytest.raises(ValueError):
        await verifier.verify_facts([{"id": "s1", "text": "Only one source"}])


# ============================================================================
# QUERY HISTORY LEARNING TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_query_recording():
    """Test query recording"""
    storage = MockStorage()
    learner = QueryHistoryLearner(storage)
    
    await learner.record_query(
        user_id="user_1",
        query="Test query",
        response={"answer": "Test answer"},
        metrics={"css": 0.85, "cost_cu": 5.0, "time_seconds": 2.5, "satisfied": True}
    )
    
    history = await storage.query("query_history", {"user_id": "user_1"})
    assert len(history) == 1
    assert history[0]["query"] == "Test query"


@pytest.mark.asyncio
async def test_pattern_extraction():
    """Test pattern extraction from history"""
    storage = MockStorage()
    learner = QueryHistoryLearner(storage)
    
    # Record multiple similar queries
    for i in range(5):
        await learner.record_query(
            user_id="user_1",
            query=f"Legal requirements for construction {i}",
            response={},
            metrics={"css": 0.8, "cost_cu": 10.0, "time_seconds": 5.0, "satisfied": True}
        )
    
    patterns = await learner.extract_patterns("user_1", min_frequency=3)
    
    assert len(patterns) > 0
    assert all(isinstance(p, QueryPattern) for p in patterns)


@pytest.mark.asyncio
async def test_user_profile_building():
    """Test user profile building"""
    storage = MockStorage()
    learner = QueryHistoryLearner(storage)
    
    # Add some history
    await learner.record_query(
        user_id="user_1",
        query="Test query",
        response={},
        metrics={"css": 0.85, "cost_cu": 5.0, "time_seconds": 2.0, "satisfied": True}
    )
    
    profile = await learner.build_user_profile("user_1")
    
    assert isinstance(profile, UserProfile)
    assert profile.user_id == "user_1"
    assert 0.0 <= profile.preferred_speed_quality_tradeoff <= 1.0


@pytest.mark.asyncio
async def test_recommendations():
    """Test recommendation generation"""
    storage = MockStorage()
    learner = QueryHistoryLearner(storage)
    
    recommendations = await learner.generate_recommendations(
        "user_1",
        "Current query"
    )
    
    assert isinstance(recommendations, list)


# ============================================================================
# TEMPLATE GENERATION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_template_candidate_identification():
    """Test identification of template candidates"""
    storage = MockStorage()
    generator = AutomaticTemplateGenerator(storage, MockLLMClient(), min_quality=0.85)
    
    # Add high-quality queries
    await storage.append("query_history", {
        "user_id": "user_1",
        "query": "Test query",
        "response_quality": 0.90,
        "user_satisfied": True,
        "cost_cu": 5.0
    })
    
    candidates = await generator.identify_template_candidates("user_1")
    
    assert len(candidates) > 0


@pytest.mark.asyncio
async def test_template_generation():
    """Test template generation from candidates"""
    storage = MockStorage()
    generator = AutomaticTemplateGenerator(storage, MockLLMClient())
    
    candidates = [
        {"query": "What are the legal requirements for building?", "response_quality": 0.9, "cost_cu": 10.0, "user_satisfied": True},
        {"query": "What are the safety requirements for construction?", "response_quality": 0.88, "cost_cu": 9.0, "user_satisfied": True}
    ]
    
    template = await generator.generate_template(candidates)
    
    assert isinstance(template, QueryTemplate)
    assert template.pattern != ""
    assert len(template.parameters) > 0


@pytest.mark.asyncio
async def test_template_matching():
    """Test template matching"""
    storage = MockStorage()
    generator = AutomaticTemplateGenerator(storage, MockLLMClient())
    
    template = QueryTemplate(
        template_id="tpl_1",
        name="Requirements Template",
        description="Template for requirement queries",
        pattern="What are the {subject} requirements for {object}?",
        parameters=["subject", "object"],
        success_rate=0.9,
        avg_quality_score=0.85,
        avg_cost_cu=10.0,
        usage_count=5,
        created_at=datetime.utcnow()
    )
    
    match = await generator.match_template(
        "What are the legal requirements for building?",
        [template]
    )
    
    assert match is not None
    assert match.confidence > 0.0


@pytest.mark.asyncio
async def test_template_application():
    """Test template application"""
    storage = MockStorage()
    generator = AutomaticTemplateGenerator(storage, MockLLMClient())
    
    template = QueryTemplate(
        template_id="tpl_1",
        name="Test Template",
        description="Test",
        pattern="{query}",
        parameters=["query"],
        success_rate=0.9,
        avg_quality_score=0.85,
        avg_cost_cu=10.0,
        usage_count=5,
        created_at=datetime.utcnow()
    )
    
    template_match = TemplateMatch(
        template=template,
        confidence=0.85,
        parameter_values={"query": "test"}
    )
    
    plan = await generator.apply_template(template_match)
    
    assert plan["template_id"] == "tpl_1"
    assert "estimated_cost_cu" in plan


# ============================================================================
# MULTI-PERSPECTIVE SYNTHESIS TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_perspective_analysis():
    """Test analysis from single perspective"""
    synthesizer = MultiPerspectiveSynthesizer(MockLLMClient())
    
    analysis = await synthesizer.analyze_perspective(
        query="Should we build a new factory?",
        context="Context about factory construction",
        dimension=PerspectiveDimension.ECONOMIC
    )
    
    assert isinstance(analysis, PerspectiveAnalysis)
    assert analysis.dimension == PerspectiveDimension.ECONOMIC
    assert len(analysis.key_points) > 0


@pytest.mark.asyncio
async def test_multi_perspective_synthesis():
    """Test synthesis from multiple perspectives"""
    synthesizer = MultiPerspectiveSynthesizer(MockLLMClient())
    
    perspectives = [
        PerspectiveAnalysis(
            dimension=PerspectiveDimension.LEGAL,
            key_points=["Legal point 1"],
            considerations=["Legal consideration"],
            trade_offs=["Legal trade-off"],
            confidence=0.8
        ),
        PerspectiveAnalysis(
            dimension=PerspectiveDimension.TECHNICAL,
            key_points=["Technical point 1"],
            considerations=["Technical consideration"],
            trade_offs=["Technical trade-off"],
            confidence=0.85
        )
    ]
    
    result = await synthesizer.synthesize_perspectives(
        perspectives,
        "Test query"
    )
    
    assert result.holistic_answer != ""
    assert len(result.perspectives) == 2
    assert 0.0 <= result.overall_confidence <= 1.0


@pytest.mark.asyncio
async def test_full_multi_perspective_analysis():
    """Test complete multi-perspective analysis"""
    synthesizer = MultiPerspectiveSynthesizer(MockLLMClient())
    
    result = await synthesizer.execute_multi_perspective_analysis(
        query="Should we implement new environmental regulations?",
        context="Context about regulations",
        dimensions=[
            PerspectiveDimension.LEGAL,
            PerspectiveDimension.ENVIRONMENTAL,
            PerspectiveDimension.ECONOMIC
        ]
    )
    
    assert len(result.perspectives) == 3
    assert result.holistic_answer != ""
    assert isinstance(result.recommendations, list)


# ============================================================================
# COORDINATOR TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_coordinator_integration():
    """Test Phase2FeatureCoordinator integration"""
    llm = MockLLMClient()
    storage = MockStorage()
    
    coordinator = Phase2FeatureCoordinator(
        reflection_engine=SelfReflectionEngine(llm),
        verifier=CrossSourceVerifier(llm),
        history_learner=QueryHistoryLearner(storage),
        template_generator=AutomaticTemplateGenerator(storage, llm),
        synthesizer=MultiPerspectiveSynthesizer(llm)
    )
    
    result = await coordinator.process_query_with_intelligence(
        query="Test query",
        user_id="user_1",
        sources=[
            {"id": "s1", "text": "Source 1"},
            {"id": "s2", "text": "Source 2"}
        ],
        initial_answer="Initial answer"
    )
    
    assert "final_answer" in result
    assert "features_used" in result
    assert len(result["features_used"]) > 0


@pytest.mark.asyncio
async def test_coordinator_selective_features():
    """Test coordinator with selective feature usage"""
    llm = MockLLMClient()
    storage = MockStorage()
    
    coordinator = Phase2FeatureCoordinator(
        reflection_engine=SelfReflectionEngine(llm),
        verifier=CrossSourceVerifier(llm),
        history_learner=QueryHistoryLearner(storage),
        template_generator=AutomaticTemplateGenerator(storage, llm),
        synthesizer=MultiPerspectiveSynthesizer(llm)
    )
    
    result = await coordinator.process_query_with_intelligence(
        query="Test query",
        user_id="user_1",
        sources=[{"id": "s1", "text": "Source"}],
        initial_answer="Answer",
        use_reflection=True,
        use_verification=False,
        use_learning=False,
        use_templates=False,
        use_multi_perspective=False
    )
    
    assert "self_reflection" in result["features_used"]
    assert "cross_source_verification" not in result["features_used"]


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_reflection_performance():
    """Test self-reflection performance"""
    engine = SelfReflectionEngine(MockLLMClient(), max_iterations=2)
    
    import time
    start = time.time()
    
    result = await engine.execute_reflection_loop(
        "Test answer",
        "Test query"
    )
    
    elapsed = time.time() - start
    
    assert elapsed < 5.0  # Should complete in < 5 seconds
    assert result.iteration <= 2


@pytest.mark.asyncio
async def test_verification_performance():
    """Test verification performance"""
    verifier = CrossSourceVerifier(MockLLMClient())
    
    sources = [
        {"id": f"s{i}", "text": f"Source {i} text"}
        for i in range(5)
    ]
    
    import time
    start = time.time()
    
    result = await verifier.verify_facts(sources)
    
    elapsed = time.time() - start
    
    assert elapsed < 10.0  # Should complete in < 10 seconds


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
