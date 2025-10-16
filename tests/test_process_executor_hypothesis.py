"""
Test ProcessExecutor Integration with HypothesisService (Phase 5)

Tests hypothesis generation integration into the process execution pipeline.

Version: 1.0.0
Phase: 5 (v5.0 Hypothesis Generation)
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from services.process_executor import ProcessExecutor
from models.process_tree import ProcessTree
from models.process_step import ProcessStep, StepType
from models.hypothesis import Hypothesis, QuestionType, ConfidenceLevel
from models.nlp_models import (
    NLPAnalysisResult, Intent, IntentType, Entity, EntityType,
    QueryParameters, QuestionType as NLPQuestionType
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def simple_nlp_analysis():
    """Create a simple NLP analysis result for testing."""
    return NLPAnalysisResult(
        query="Bauantrag für Einfamilienhaus in Stuttgart",
        intent=Intent(
            intent_type=IntentType.PROCEDURE_QUERY,
            confidence=0.95,
            keywords=["Bauantrag", "Einfamilienhaus", "Stuttgart"]
        ),
        entities=[
            Entity(
                text="Stuttgart",
                entity_type=EntityType.LOCATION,
                start_pos=37,
                end_pos=46,
                confidence=0.98
            )
        ],
        parameters=QueryParameters(
            location="Stuttgart",
            document_type="Bauantrag"
        ),
        question_type=NLPQuestionType.HOW,
        language="de",
        tokens=["Bauantrag", "für", "Einfamilienhaus", "in", "Stuttgart"]
    )


@pytest.fixture
def simple_process_tree(simple_nlp_analysis):
    """Create a simple ProcessTree for testing."""
    tree = ProcessTree(
        query="Bauantrag für Einfamilienhaus in Stuttgart",
        nlp_analysis=simple_nlp_analysis,
        metadata={"source": "test"}
    )
    
    # Add simple step
    step = ProcessStep(
        id="step_1",
        name="Search Building Permits",
        description="Search for building permit documents in Stuttgart",
        step_type=StepType.SEARCH,
        parameters={"query": "building permit Stuttgart"},
        dependencies=[]
    )
    tree.add_step(step)
    tree.execution_order = [["step_1"]]
    
    return tree


@pytest.fixture
def mock_hypothesis():
    """Create a mock hypothesis."""
    return Hypothesis(
        query="Bauantrag für Einfamilienhaus in Stuttgart",
        question_type=QuestionType.PROCEDURAL,
        primary_intent="Learn building permit process",
        confidence=ConfidenceLevel.HIGH,
        required_information=["Process steps", "Documents", "Timeline"],
        information_gaps=[],
        assumptions=["Residential building"],
        suggested_steps=["Search procedures", "List documents"],
        expected_response_type="list"
    )


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

def test_executor_with_hypothesis_enabled(simple_process_tree, mock_hypothesis):
    """Test ProcessExecutor with hypothesis generation enabled."""
    
    with patch('services.process_executor.HypothesisService') as mock_service_class:
        # Setup mock
        mock_service = Mock()
        mock_service.generate_hypothesis.return_value = mock_hypothesis
        mock_service_class.return_value = mock_service
        
        # Create executor with hypothesis enabled
        executor = ProcessExecutor(max_workers=2, use_agents=False, enable_hypothesis=True)
        
        # Execute process
        result = executor.execute_process(simple_process_tree)
        
        # Assertions
        assert result['success'] is True
        assert 'hypothesis' in result
        assert 'hypothesis_metadata' in result
        
        # Check hypothesis content
        hypothesis_data = result['hypothesis']
        assert hypothesis_data['query'] == simple_process_tree.query
        assert hypothesis_data['question_type'] == 'procedural'
        assert hypothesis_data['confidence'] == 'high'
        
        # Check hypothesis metadata
        meta = result['hypothesis_metadata']
        assert meta['question_type'] == 'procedural'
        assert meta['confidence'] == 'high'
        assert meta['requires_clarification'] is False
        assert meta['has_critical_gaps'] is False
        assert meta['information_gaps_count'] == 0
        
        # Verify hypothesis service was called
        mock_service.generate_hypothesis.assert_called_once()


def test_executor_with_hypothesis_disabled(simple_process_tree):
    """Test ProcessExecutor with hypothesis generation disabled."""
    
    # Create executor with hypothesis disabled
    executor = ProcessExecutor(max_workers=2, use_agents=False, enable_hypothesis=False)
    
    # Execute process
    result = executor.execute_process(simple_process_tree)
    
    # Assertions
    assert result['success'] is True
    assert 'hypothesis' not in result
    assert 'hypothesis_metadata' not in result


def test_executor_hypothesis_with_rag_context(simple_process_tree, mock_hypothesis):
    """Test hypothesis generation with RAG context."""
    
    with patch('services.process_executor.HypothesisService') as mock_service_class, \
         patch('services.process_executor.RAGService') as mock_rag_class:
        
        # Setup mocks
        mock_service = Mock()
        mock_service.generate_hypothesis.return_value = mock_hypothesis
        mock_service_class.return_value = mock_service
        
        mock_rag = Mock()
        mock_rag.search.return_value = {
            "results": [
                {"content": "Building permits in Stuttgart require 3 documents"},
                {"content": "Processing time: 6-8 weeks"}
            ]
        }
        mock_rag_class.return_value = mock_rag
        
        # Create executor with both services
        executor = ProcessExecutor(max_workers=2, use_agents=False, enable_hypothesis=True)
        executor.rag_service = mock_rag
        
        # Execute process
        result = executor.execute_process(simple_process_tree)
        
        # Assertions
        assert result['success'] is True
        assert 'hypothesis' in result
        
        # Verify RAG was called for context
        mock_rag.search.assert_called_once_with(simple_process_tree.query, top_k=3)
        
        # Verify hypothesis service received RAG context
        call_args = mock_service.generate_hypothesis.call_args
        assert call_args.kwargs['rag_context'] is not None
        assert len(call_args.kwargs['rag_context']) == 2


def test_executor_hypothesis_with_low_confidence(simple_process_tree):
    """Test hypothesis with low confidence and gaps."""
    
    # Create low confidence hypothesis with gaps
    low_conf_hypothesis = Hypothesis(
        query="Wie viel kostet ein Bauantrag?",
        question_type=QuestionType.CALCULATION,
        primary_intent="Determine cost",
        confidence=ConfidenceLevel.LOW,
        required_information=["Location", "Building type"],
        information_gaps=[
            Mock(gap_type="location", severity=Mock(value="critical"))
        ],
        assumptions=["General case"],
        suggested_steps=["Request clarification"],
        expected_response_type="text"
    )
    
    with patch('services.process_executor.HypothesisService') as mock_service_class:
        # Setup mock
        mock_service = Mock()
        mock_service.generate_hypothesis.return_value = low_conf_hypothesis
        mock_service_class.return_value = mock_service
        
        # Create executor
        executor = ProcessExecutor(max_workers=2, use_agents=False, enable_hypothesis=True)
        
        # Execute process
        result = executor.execute_process(simple_process_tree)
        
        # Assertions
        assert result['success'] is True
        assert 'hypothesis' in result
        
        # Check metadata for low confidence
        meta = result['hypothesis_metadata']
        assert meta['confidence'] == 'low'
        assert meta['requires_clarification'] is True
        assert meta['information_gaps_count'] >= 1


def test_executor_hypothesis_error_handling(simple_process_tree):
    """Test graceful handling of hypothesis generation errors."""
    
    with patch('services.process_executor.HypothesisService') as mock_service_class:
        # Setup mock to raise error
        mock_service = Mock()
        mock_service.generate_hypothesis.side_effect = Exception("LLM unavailable")
        mock_service_class.return_value = mock_service
        
        # Create executor
        executor = ProcessExecutor(max_workers=2, use_agents=False, enable_hypothesis=True)
        
        # Execute process (should not crash)
        result = executor.execute_process(simple_process_tree)
        
        # Assertions - execution continues without hypothesis
        assert result['success'] is True
        assert 'hypothesis' not in result  # No hypothesis due to error


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
