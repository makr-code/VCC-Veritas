"""
Tests for Phase 1 Feature Implementations

Tests all 4 high-priority features:
1. Multi-hop reasoning chains
2. Proactive clarification
3. Web search integration
4. Conversational memory

Author: VERITAS Development Team
Created: 2025-12-03
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from backend.agents.framework.phase1_features import (
    # Multi-hop reasoning
    ReasoningStep,
    ReasoningChain,
    ReasoningStepStatus,
    MultiHopReasoningEngine,
    
    # Proactive clarification
    ClarificationQuestion,
    ClarificationType,
    ProactiveClarificationEngine,
    
    # Web search
    WebSearchResult,
    WebSearchEngine,
    
    # Conversational memory
    ConversationTurn,
    ConversationSession,
    ConversationalMemoryManager,
    
    # Integration
    Phase1FeatureCoordinator
)


# ============================================================================
# MULTI-HOP REASONING TESTS
# ============================================================================

class TestMultiHopReasoning:
    """Test suite for multi-hop reasoning chains."""
    
    @pytest.fixture
    def mock_llm(self):
        """Mock LLM client."""
        llm = AsyncMock()
        llm.generate = AsyncMock(return_value={
            "steps": [
                {
                    "question": "What is the legal framework?",
                    "hypothesis": "BGB applies",
                    "method": "vector_search",
                    "dependencies": []
                },
                {
                    "question": "What are the specific requirements?",
                    "hypothesis": "Multiple documents required",
                    "method": "llm_inference",
                    "dependencies": ["step_1"]
                }
            ]
        })
        return llm
    
    @pytest.fixture
    def mock_validator(self):
        """Mock validation client."""
        validator = AsyncMock()
        validator.validate_reasoning_step = AsyncMock(return_value={
            "passed": True,
            "reason": "Valid reasoning",
            "confidence": 0.85
        })
        return validator
    
    @pytest.fixture
    def reasoning_engine(self, mock_llm, mock_validator):
        """Create reasoning engine instance."""
        return MultiHopReasoningEngine(mock_llm, mock_validator)
    
    @pytest.mark.asyncio
    async def test_query_decomposition(self, reasoning_engine):
        """Test decomposition of complex query into reasoning steps."""
        query = "What are the requirements for a construction permit in Bavaria?"
        
        chain = await reasoning_engine.decompose_query(query)
        
        assert isinstance(chain, ReasoningChain)
        assert chain.query == query
        assert len(chain.steps) == 2
        assert chain.steps[0].step_number == 1
        assert chain.steps[1].dependencies == ["step_1"]
    
    @pytest.mark.asyncio
    async def test_step_execution_success(self, reasoning_engine):
        """Test successful execution of a reasoning step."""
        chain = ReasoningChain(chain_id="test", query="test query")
        step = ReasoningStep(
            step_id="step_1",
            step_number=1,
            question="Test question",
            hypothesis="Test hypothesis",
            method="llm_inference"
        )
        chain.steps.append(step)
        
        result = await reasoning_engine.execute_step(step, chain)
        
        assert result.status == ReasoningStepStatus.VALIDATED
        assert result.validation_passed is True
        assert result.confidence == 0.85
        assert result.result is not None
    
    @pytest.mark.asyncio
    async def test_step_dependency_not_satisfied(self, reasoning_engine):
        """Test step skipped when dependency not satisfied."""
        chain = ReasoningChain(chain_id="test", query="test query")
        
        # Create dependent step without satisfying dependency
        step = ReasoningStep(
            step_id="step_2",
            step_number=2,
            question="Dependent question",
            hypothesis="Dependent hypothesis",
            method="llm_inference",
            dependencies=["step_1"]
        )
        chain.steps.append(step)
        
        result = await reasoning_engine.execute_step(step, chain)
        
        assert result.status == ReasoningStepStatus.SKIPPED
        assert "Dependency step_1 not satisfied" in result.validation_reason
    
    @pytest.mark.asyncio
    async def test_full_chain_execution(self, reasoning_engine):
        """Test execution of complete reasoning chain."""
        query = "Complex multi-step query"
        
        chain = await reasoning_engine.decompose_query(query)
        chain = await reasoning_engine.execute_chain(chain)
        
        assert chain.completed_at is not None
        assert chain.final_answer is not None
        assert 0 <= chain.overall_confidence <= 1.0
        assert chain.total_cost_cu >= 0
    
    @pytest.mark.asyncio
    async def test_confidence_calculation(self, reasoning_engine):
        """Test overall confidence calculation from step confidences."""
        chain = ReasoningChain(chain_id="test", query="test")
        
        # Add validated steps with different confidences
        chain.steps.append(ReasoningStep(
            step_id="s1", step_number=1, question="q1", hypothesis="h1",
            method="test", status=ReasoningStepStatus.VALIDATED,
            validation_passed=True, confidence=0.9
        ))
        chain.steps.append(ReasoningStep(
            step_id="s2", step_number=2, question="q2", hypothesis="h2",
            method="test", status=ReasoningStepStatus.VALIDATED,
            validation_passed=True, confidence=0.7
        ))
        
        confidence = reasoning_engine._calculate_overall_confidence(chain)
        
        # Later steps weighted more, so should be between 0.7 and 0.9
        assert 0.7 <= confidence <= 0.9


# ============================================================================
# PROACTIVE CLARIFICATION TESTS
# ============================================================================

class TestProactiveClarification:
    """Test suite for proactive clarification engine."""
    
    @pytest.fixture
    def mock_llm(self):
        """Mock LLM client for clarification."""
        llm = AsyncMock()
        llm.generate = AsyncMock(return_value={
            "ambiguities": [
                {
                    "question": "Did you mean 'X' or 'Y'?",
                    "options": ["X", "Y"],
                    "cost_impact": "Choosing X saves 50% cost",
                    "time_saved": 10.0,
                    "cost_saved": 5.0
                }
            ]
        })
        return llm
    
    @pytest.fixture
    def clarification_engine(self, mock_llm):
        """Create clarification engine instance."""
        return ProactiveClarificationEngine(mock_llm)
    
    @pytest.mark.asyncio
    async def test_detect_ambiguities(self, clarification_engine):
        """Test detection of ambiguous terms in query."""
        query = "Show me Python code"  # Ambiguous: Python language or Python snake?
        plan = {"estimated_cost_cu": 15.0}
        
        clarifications = await clarification_engine.analyze_query_for_clarifications(query, plan)
        
        assert len(clarifications) > 0
        assert any(c.question_type == ClarificationType.AMBIGUITY for c in clarifications)
    
    @pytest.mark.asyncio
    async def test_scope_clarification_for_expensive_query(self, clarification_engine):
        """Test scope clarification for expensive queries."""
        query = "Analyze all construction permits"
        plan = {
            "estimated_cost_cu": 25.0,  # > 10.0 threshold
            "estimated_time_s": 60.0
        }
        
        clarification_engine.llm.generate = AsyncMock(return_value={
            "should_ask": True,
            "question": "Do you want all permits or just recent ones?",
            "options": ["All permits", "Last 30 days", "Last year"],
            "cost_impact": "Limiting to recent reduces cost by 80%",
            "time_saved": 40.0,
            "cost_saved": 20.0
        })
        
        clarifications = await clarification_engine.analyze_query_for_clarifications(query, plan)
        
        scope_questions = [c for c in clarifications if c.question_type == ClarificationType.SCOPE]
        assert len(scope_questions) > 0
        assert scope_questions[0].estimated_cost_saved > 0
    
    @pytest.mark.asyncio
    async def test_preference_clarification(self, clarification_engine):
        """Test user preference clarification when multiple plans available."""
        query = "Research query"
        plan = {
            "estimated_cost_cu": 20.0,
            "alternative_plans": [
                {"name": "Speed", "estimated_time_s": 5, "estimated_cost_cu": 8, "predicted_quality": 0.75},
                {"name": "Balanced", "estimated_time_s": 15, "estimated_cost_cu": 20, "predicted_quality": 0.90},
                {"name": "Quality", "estimated_time_s": 30, "estimated_cost_cu": 35, "predicted_quality": 0.95}
            ]
        }
        
        clarifications = await clarification_engine.analyze_query_for_clarifications(query, plan)
        
        pref_questions = [c for c in clarifications if c.question_type == ClarificationType.PREFERENCE]
        assert len(pref_questions) > 0
        assert len(pref_questions[0].options) == 3


# ============================================================================
# WEB SEARCH TESTS
# ============================================================================

class TestWebSearch:
    """Test suite for web search integration."""
    
    @pytest.fixture
    def mock_search_api(self):
        """Mock search API client."""
        api = AsyncMock()
        api.search = AsyncMock(return_value=[
            {
                "url": "https://example.com/article1",
                "title": "Recent Article",
                "snippet": "This is recent information...",
                "published_date": datetime.now() - timedelta(days=5),
                "relevance": 0.85
            },
            {
                "url": "https://wikipedia.org/article2",
                "title": "Background Info",
                "snippet": "Historical context...",
                "relevance": 0.70
            }
        ])
        return api
    
    @pytest.fixture
    def mock_fetcher(self):
        """Mock content fetcher."""
        fetcher = AsyncMock()
        fetcher.fetch_url = AsyncMock(return_value="<html>Full content here</html>")
        return fetcher
    
    @pytest.fixture
    def web_engine(self, mock_search_api, mock_fetcher):
        """Create web search engine instance."""
        return WebSearchEngine(mock_search_api, mock_fetcher)
    
    @pytest.mark.asyncio
    async def test_web_search_needed_for_temporal_query(self, web_engine):
        """Test web search triggered for temporal queries."""
        query = "Latest COVID-19 statistics 2025"
        kb_results = [
            {"content": "Old data", "timestamp": datetime(2023, 1, 1), "relevance": 0.7}
        ]
        
        needed = await web_engine.determine_if_web_search_needed(query, kb_results)
        
        assert needed is True
    
    @pytest.mark.asyncio
    async def test_web_search_not_needed_for_complete_kb(self, web_engine):
        """Test web search not triggered when KB is complete."""
        query = "Basic legal definition"
        kb_results = [
            {"content": f"Result {i}", "timestamp": datetime.now(), "relevance": 0.8 + i*0.01}
            for i in range(10)
        ]
        
        needed = await web_engine.determine_if_web_search_needed(query, kb_results)
        
        assert needed is False
    
    @pytest.mark.asyncio
    async def test_search_web(self, web_engine):
        """Test web search execution."""
        query = "Recent news"
        
        results = await web_engine.search_web(query, max_results=5)
        
        assert len(results) == 2  # Mock returns 2
        assert all(isinstance(r, WebSearchResult) for r in results)
        assert results[0].source_authority > 0
    
    @pytest.mark.asyncio
    async def test_source_authority_calculation(self, web_engine):
        """Test authority scoring for different sources."""
        gov_score = await web_engine._calculate_source_authority("https://www.gov.de/article")
        edu_score = await web_engine._calculate_source_authority("https://university.edu/research")
        wiki_score = await web_engine._calculate_source_authority("https://wikipedia.org/wiki/topic")
        unknown_score = await web_engine._calculate_source_authority("https://random-blog.com/post")
        
        assert gov_score == 1.0  # Government sites most authoritative
        assert edu_score == 0.9
        assert wiki_score == 0.8
        assert unknown_score == 0.5  # Default
    
    @pytest.mark.asyncio
    async def test_integrate_web_with_kb_results(self, web_engine):
        """Test integration of web and KB results."""
        query = "Test query"
        kb_results = [
            {"content": "KB result", "relevance": 0.8, "authority": 0.7}
        ]
        web_results = [
            WebSearchResult(
                url="https://example.com/new",
                title="New article",
                snippet="Recent info",
                published_date=datetime.now(),
                relevance_score=0.85,
                source_authority=0.9,
                content="Full content"
            )
        ]
        
        merged = await web_engine.integrate_web_results_with_kb(query, kb_results, web_results)
        
        assert len(merged) == 2  # 1 KB + 1 web
        assert any(r["source_type"] == "knowledge_base" for r in merged)
        assert any(r["source_type"] == "web" for r in merged)
        # Web result should rank higher due to recency and authority
        assert merged[0]["source_type"] == "web"


# ============================================================================
# CONVERSATIONAL MEMORY TESTS
# ============================================================================

class TestConversationalMemory:
    """Test suite for conversational memory manager."""
    
    @pytest.fixture
    def mock_storage(self):
        """Mock storage backend."""
        storage = AsyncMock()
        storage.get_session = AsyncMock(return_value=None)
        storage.save_session = AsyncMock()
        storage.get_user_sessions = AsyncMock(return_value=[])
        return storage
    
    @pytest.fixture
    def mock_llm(self):
        """Mock LLM for context extraction."""
        llm = AsyncMock()
        llm.generate = AsyncMock(return_value={
            "topics": ["construction", "permits"],
            "entities": ["Bavaria", "BauGB"],
            "preferences": {"speed": "balanced"}
        })
        return llm
    
    @pytest.fixture
    def memory_manager(self, mock_storage, mock_llm):
        """Create memory manager instance."""
        return ConversationalMemoryManager(mock_storage, mock_llm)
    
    @pytest.mark.asyncio
    async def test_create_new_session(self, memory_manager):
        """Test creation of new conversation session."""
        user_id = "user123"
        
        session = await memory_manager.get_or_create_session(user_id)
        
        assert isinstance(session, ConversationSession)
        assert session.user_id == user_id
        assert len(session.turns) == 0
        assert session.total_cost_cu == 0.0
    
    @pytest.mark.asyncio
    async def test_resume_existing_session(self, memory_manager):
        """Test resuming an existing session."""
        existing_session = ConversationSession(
            session_id="session_123",
            user_id="user123",
            started_at=datetime.now() - timedelta(hours=1),
            last_activity=datetime.now() - timedelta(hours=1)
        )
        memory_manager.storage.get_session = AsyncMock(return_value=existing_session)
        
        session = await memory_manager.get_or_create_session("user123", "session_123")
        
        assert session.session_id == "session_123"
        assert session.last_activity > existing_session.last_activity  # Updated
    
    @pytest.mark.asyncio
    async def test_add_conversation_turn(self, memory_manager):
        """Test adding a turn to the conversation."""
        session = await memory_manager.get_or_create_session("user123")
        
        turn = ConversationTurn(
            turn_id="turn_1",
            timestamp=datetime.now(),
            user_message="What are the requirements?",
            system_response="The requirements are...",
            query_complexity="research",
            cost_cu=5.5,
            execution_time_s=12.3,
            satisfaction_score=4.5
        )
        
        session = await memory_manager.add_turn(session, turn)
        
        assert len(session.turns) == 1
        assert session.total_cost_cu == 5.5
        assert session.total_time_s == 12.3
        assert session.avg_satisfaction == 4.5
        assert len(session.topics) > 0  # Context extracted
    
    @pytest.mark.asyncio
    async def test_context_extraction(self, memory_manager):
        """Test extraction of topics, entities, and preferences."""
        session = ConversationSession(
            session_id="test",
            user_id="user123",
            started_at=datetime.now(),
            last_activity=datetime.now()
        )
        
        turn = ConversationTurn(
            turn_id="turn_1",
            timestamp=datetime.now(),
            user_message="I need information about construction permits in Bavaria",
            system_response="Here's information about construction permits...",
            query_complexity="simple",
            cost_cu=2.0,
            execution_time_s=5.0
        )
        
        await memory_manager._update_session_context(session, turn)
        
        assert "construction" in session.topics
        assert "permits" in session.topics
        assert "Bavaria" in session.entities
        assert "speed" in session.user_preferences
    
    @pytest.mark.asyncio
    async def test_get_relevant_context(self, memory_manager):
        """Test retrieval of relevant context for current query."""
        session = ConversationSession(
            session_id="test",
            user_id="user123",
            started_at=datetime.now(),
            last_activity=datetime.now(),
            topics=["construction", "permits"],
            turns=[
                ConversationTurn(
                    turn_id="turn_1",
                    timestamp=datetime.now(),
                    user_message="Previous question",
                    system_response="Previous answer",
                    query_complexity="simple",
                    cost_cu=2.0,
                    execution_time_s=5.0
                )
            ]
        )
        
        context = await memory_manager.get_relevant_context(session, "Current question", max_turns=3)
        
        assert "construction" in context
        assert "permits" in context
        assert "Previous question" in context
        assert "Current question" in context
    
    @pytest.mark.asyncio
    async def test_aggregate_user_preferences(self, memory_manager):
        """Test aggregation of preferences across sessions."""
        sessions = [
            ConversationSession(
                session_id="s1", user_id="user123",
                started_at=datetime.now(), last_activity=datetime.now(),
                user_preferences={"speed": "fast", "detail": "high"}
            ),
            ConversationSession(
                session_id="s2", user_id="user123",
                started_at=datetime.now(), last_activity=datetime.now(),
                user_preferences={"speed": "balanced", "detail": "high"}
            )
        ]
        memory_manager.storage.get_user_sessions = AsyncMock(return_value=sessions)
        
        prefs = await memory_manager.get_user_preferences("user123")
        
        assert "speed" in prefs
        assert "detail" in prefs
        assert prefs["detail"] == "high"  # Consistent across sessions


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestPhase1Integration:
    """Test suite for integrated Phase 1 features."""
    
    @pytest.fixture
    def mock_components(self):
        """Create mock components for integration."""
        reasoning = Mock(spec=MultiHopReasoningEngine)
        reasoning.decompose_query = AsyncMock()
        reasoning.execute_chain = AsyncMock(return_value=Mock(
            final_answer="Complex answer",
            overall_confidence=0.88,
            total_cost_cu=12.5
        ))
        
        clarification = Mock(spec=ProactiveClarificationEngine)
        clarification.analyze_query_for_clarifications = AsyncMock(return_value=[])
        
        web_search = Mock(spec=WebSearchEngine)
        web_search.determine_if_web_search_needed = AsyncMock(return_value=False)
        
        memory = Mock(spec=ConversationalMemoryManager)
        memory.get_or_create_session = AsyncMock(return_value=ConversationSession(
            session_id="test", user_id="user123",
            started_at=datetime.now(), last_activity=datetime.now()
        ))
        memory.get_relevant_context = AsyncMock(return_value="Previous context")
        memory.add_turn = AsyncMock()
        
        return reasoning, clarification, web_search, memory
    
    @pytest.fixture
    def coordinator(self, mock_components):
        """Create feature coordinator."""
        reasoning, clarification, web_search, memory = mock_components
        return Phase1FeatureCoordinator(reasoning, clarification, web_search, memory)
    
    @pytest.mark.asyncio
    async def test_simple_query_flow(self, coordinator):
        """Test complete flow for simple query."""
        result = await coordinator.process_query_with_phase1_features(
            user_id="user123",
            query="What is BGB?"
        )
        
        assert result["status"] == "success"
        assert "answer" in result
        assert "session_id" in result
        assert isinstance(result["cost_cu"], (int, float))
    
    @pytest.mark.asyncio
    async def test_query_needs_clarification(self, coordinator):
        """Test flow when clarification is needed."""
        coordinator.clarification.analyze_query_for_clarifications = AsyncMock(return_value=[
            ClarificationQuestion(
                question_id="q1",
                question_type=ClarificationType.AMBIGUITY,
                question="Did you mean X or Y?",
                options=["X", "Y"],
                cost_impact="Choosing X saves 50%",
                priority="high",
                estimated_time_saved=10.0,
                estimated_cost_saved=5.0
            )
        ])
        
        result = await coordinator.process_query_with_phase1_features(
            user_id="user123",
            query="Ambiguous query"
        )
        
        assert result["status"] == "needs_clarification"
        assert len(result["clarifications"]) > 0
        assert "session_id" in result
    
    @pytest.mark.asyncio
    async def test_complex_query_with_reasoning(self, coordinator):
        """Test complex query triggering multi-hop reasoning."""
        # Mock complex execution plan
        coordinator._generate_execution_plan = AsyncMock(return_value={
            "complexity": "research",
            "estimated_cost_cu": 20.0
        })
        
        result = await coordinator.process_query_with_phase1_features(
            user_id="user123",
            query="Complex research question"
        )
        
        assert result["status"] == "success"
        assert result["reasoning_chain_used"] is True
        coordinator.reasoning.decompose_query.assert_called_once()
        coordinator.reasoning.execute_chain.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_context_from_previous_session(self, coordinator):
        """Test using context from previous conversation."""
        # Create session with history
        session = ConversationSession(
            session_id="existing_session",
            user_id="user123",
            started_at=datetime.now() - timedelta(hours=1),
            last_activity=datetime.now() - timedelta(minutes=5),
            turns=[
                ConversationTurn(
                    turn_id="turn_1",
                    timestamp=datetime.now() - timedelta(minutes=5),
                    user_message="Previous question about permits",
                    system_response="Answer about permits",
                    query_complexity="simple",
                    cost_cu=3.0,
                    execution_time_s=8.0
                )
            ]
        )
        coordinator.memory.get_or_create_session = AsyncMock(return_value=session)
        
        result = await coordinator.process_query_with_phase1_features(
            user_id="user123",
            query="Follow-up question",
            session_id="existing_session"
        )
        
        assert result["status"] == "success"
        assert result["context_used"] is True  # Previous turn exists


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

class TestPhase1Performance:
    """Performance tests for Phase 1 features."""
    
    @pytest.mark.asyncio
    async def test_reasoning_chain_performance(self):
        """Test reasoning chain completes within acceptable time."""
        # Mock fast LLM and validator
        llm = AsyncMock()
        llm.generate = AsyncMock(return_value={"steps": []})
        validator = AsyncMock()
        validator.validate_reasoning_step = AsyncMock(return_value={
            "passed": True, "reason": "valid", "confidence": 0.85
        })
        
        engine = MultiHopReasoningEngine(llm, validator)
        
        start = datetime.now()
        chain = await engine.decompose_query("Test query")
        elapsed = (datetime.now() - start).total_seconds()
        
        assert elapsed < 1.0  # Should complete in under 1 second
    
    @pytest.mark.asyncio
    async def test_memory_retrieval_performance(self):
        """Test context retrieval is fast even with large history."""
        storage = AsyncMock()
        storage.get_session = AsyncMock(return_value=None)
        storage.save_session = AsyncMock()
        llm = AsyncMock()
        llm.generate = AsyncMock(return_value={"topics": [], "entities": [], "preferences": {}})
        
        manager = ConversationalMemoryManager(storage, llm)
        session = await manager.get_or_create_session("user123")
        
        # Add many turns
        for i in range(100):
            turn = ConversationTurn(
                turn_id=f"turn_{i}",
                timestamp=datetime.now(),
                user_message=f"Question {i}",
                system_response=f"Answer {i}",
                query_complexity="simple",
                cost_cu=2.0,
                execution_time_s=5.0
            )
            session.turns.append(turn)
        
        start = datetime.now()
        context = await manager.get_relevant_context(session, "New question", max_turns=3)
        elapsed = (datetime.now() - start).total_seconds()
        
        assert elapsed < 0.5  # Should complete in under 500ms
        assert len(context) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
