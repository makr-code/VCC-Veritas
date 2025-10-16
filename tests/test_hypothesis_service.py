"""
Test Suite for HypothesisService

Tests hypothesis generation, confidence scoring, error handling,
and integration with DirectOllamaLLM.

Version: 1.0.0
Phase: 5 (v5.0 Hypothesis Generation)
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from services.hypothesis_service import HypothesisService
from models.hypothesis import (
    Hypothesis,
    QuestionType,
    ConfidenceLevel,
    InformationGap,
    GapSeverity
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_ollama_client():
    """Mock DirectOllamaLLM client."""
    mock = MagicMock()
    return mock


@pytest.fixture
def hypothesis_service(mock_ollama_client):
    """Create HypothesisService with mocked Ollama client."""
    with patch('services.hypothesis_service.DirectOllamaLLM', return_value=mock_ollama_client):
        service = HypothesisService(model_name="llama3.1:8b")
        service.ollama_client = mock_ollama_client
        return service


@pytest.fixture
def sample_llm_response_high_confidence():
    """Sample LLM response with high confidence."""
    return """{
  "question_type": "procedural",
  "primary_intent": "Learn building permit application process",
  "confidence": "high",
  "required_information": ["Process steps", "Required documents", "Timeline"],
  "information_gaps": [],
  "assumptions": ["User refers to residential building permit"],
  "suggested_steps": [
    "Search for building permit procedures",
    "Identify required documents",
    "Explain submission process"
  ],
  "expected_response_type": "list"
}"""


@pytest.fixture
def sample_llm_response_low_confidence():
    """Sample LLM response with low confidence and gaps."""
    return """{
  "question_type": "calculation",
  "primary_intent": "Determine building permit cost",
  "confidence": "low",
  "required_information": ["Location", "Building type", "Cost structure"],
  "information_gaps": [
    {
      "gap_type": "location",
      "severity": "critical",
      "suggested_query": "In welcher Stadt soll gebaut werden?",
      "examples": ["Stuttgart", "München", "Berlin"]
    },
    {
      "gap_type": "building_type",
      "severity": "important",
      "suggested_query": "Um welche Art von Gebäude handelt es sich?",
      "examples": ["Einfamilienhaus", "Anbau", "Gartenhaus"]
    }
  ],
  "assumptions": ["User wants current 2025 fees"],
  "suggested_steps": [
    "Request location clarification",
    "Search for general cost structure",
    "Provide range or request more details"
  ],
  "expected_response_type": "text"
}"""


@pytest.fixture
def sample_llm_response_malformed():
    """Sample malformed LLM response (missing fields)."""
    return """{
  "question_type": "fact_retrieval",
  "primary_intent": "Answer query"
}"""


# ============================================================================
# TEST GROUP 1: HYPOTHESIS GENERATION (5 tests)
# ============================================================================

def test_generate_hypothesis_high_confidence(hypothesis_service, mock_ollama_client, sample_llm_response_high_confidence):
    """Test hypothesis generation with high confidence query."""
    # Setup mock
    mock_result = Mock()
    mock_result.content = sample_llm_response_high_confidence
    mock_ollama_client.invoke.return_value = mock_result
    
    # Generate hypothesis
    query = "Bauantrag für Einfamilienhaus in Stuttgart"
    hypothesis = hypothesis_service.generate_hypothesis(query)
    
    # Assertions
    assert hypothesis.query == query
    assert hypothesis.question_type == QuestionType.PROCEDURAL
    assert hypothesis.confidence == ConfidenceLevel.HIGH
    assert len(hypothesis.information_gaps) == 0
    assert not hypothesis.requires_clarification()
    assert hypothesis.is_high_confidence()
    assert len(hypothesis.suggested_steps) == 3
    
    # Verify LLM was called
    mock_ollama_client.invoke.assert_called_once()


def test_generate_hypothesis_with_gaps(hypothesis_service, mock_ollama_client, sample_llm_response_low_confidence):
    """Test hypothesis generation with information gaps."""
    # Setup mock
    mock_result = Mock()
    mock_result.content = sample_llm_response_low_confidence
    mock_ollama_client.invoke.return_value = mock_result
    
    # Generate hypothesis
    query = "Wie viel kostet ein Bauantrag?"
    hypothesis = hypothesis_service.generate_hypothesis(query)
    
    # Assertions
    assert hypothesis.query == query
    assert hypothesis.question_type == QuestionType.CALCULATION
    assert hypothesis.confidence == ConfidenceLevel.LOW
    assert len(hypothesis.information_gaps) == 2
    assert hypothesis.requires_clarification()
    assert hypothesis.has_critical_gaps()
    assert not hypothesis.is_high_confidence()
    
    # Check gaps
    critical_gaps = [g for g in hypothesis.information_gaps if g.severity == GapSeverity.CRITICAL]
    assert len(critical_gaps) == 1
    assert critical_gaps[0].gap_type == "location"
    
    # Check clarification questions
    questions = hypothesis.get_clarification_questions()
    assert len(questions) == 2
    assert "Stadt" in questions[0]


def test_generate_hypothesis_with_rag_context(hypothesis_service, mock_ollama_client, sample_llm_response_high_confidence):
    """Test hypothesis generation with RAG context."""
    # Setup mock
    mock_result = Mock()
    mock_result.content = sample_llm_response_high_confidence
    mock_ollama_client.invoke.return_value = mock_result
    
    # Generate hypothesis with context
    query = "Bauantrag Stuttgart"
    rag_context = [
        "Building permits in Stuttgart require 3 documents",
        "Processing time: 6-8 weeks",
        "Cost: €500-800 depending on project size"
    ]
    hypothesis = hypothesis_service.generate_hypothesis(query, rag_context=rag_context)
    
    # Assertions
    assert hypothesis.query == query
    assert hypothesis.confidence == ConfidenceLevel.HIGH
    
    # Verify LLM was called with context
    mock_ollama_client.invoke.assert_called_once()
    call_args = mock_ollama_client.invoke.call_args
    prompt = call_args.kwargs['prompt']
    assert "6-8 weeks" in prompt  # Context should be in prompt
    assert "€500-800" in prompt


def test_generate_hypothesis_comparison_query(hypothesis_service, mock_ollama_client):
    """Test hypothesis generation for comparison queries."""
    # Setup mock with comparison response
    mock_result = Mock()
    mock_result.content = """{
  "question_type": "comparison",
  "primary_intent": "Compare building materials",
  "confidence": "high",
  "required_information": ["Material properties", "Cost comparison", "Regulations"],
  "information_gaps": [],
  "assumptions": ["User is planning to build"],
  "suggested_steps": [
    "Search for material comparison",
    "Identify regulations",
    "Compare pros and cons"
  ],
  "expected_response_type": "comparison"
}"""
    mock_ollama_client.invoke.return_value = mock_result
    
    # Generate hypothesis
    query = "Holz oder Stein für Gartenhaus?"
    hypothesis = hypothesis_service.generate_hypothesis(query)
    
    # Assertions
    assert hypothesis.question_type == QuestionType.COMPARISON
    assert hypothesis.confidence == ConfidenceLevel.HIGH
    assert hypothesis.expected_response_type == "comparison"


def test_generate_hypothesis_timeline_query(hypothesis_service, mock_ollama_client):
    """Test hypothesis generation for timeline queries."""
    # Setup mock with timeline response
    mock_result = Mock()
    mock_result.content = """{
  "question_type": "timeline",
  "primary_intent": "Determine processing duration",
  "confidence": "medium",
  "required_information": ["Location", "Project type", "Processing times"],
  "information_gaps": [
    {
      "gap_type": "location",
      "severity": "important",
      "suggested_query": "In welcher Stadt?",
      "examples": ["Stuttgart", "München"]
    }
  ],
  "assumptions": ["User refers to building permit"],
  "suggested_steps": [
    "Clarify location",
    "Search for processing times",
    "Provide timeline range"
  ],
  "expected_response_type": "text"
}"""
    mock_ollama_client.invoke.return_value = mock_result
    
    # Generate hypothesis
    query = "Wie lange dauert die Baugenehmigung?"
    hypothesis = hypothesis_service.generate_hypothesis(query)
    
    # Assertions
    assert hypothesis.question_type == QuestionType.TIMELINE
    assert hypothesis.confidence == ConfidenceLevel.MEDIUM
    assert len(hypothesis.information_gaps) == 1


# ============================================================================
# TEST GROUP 2: CONFIDENCE SCORING (3 tests)
# ============================================================================

def test_confidence_high_no_gaps(hypothesis_service, mock_ollama_client):
    """Test that high confidence queries have no critical gaps."""
    # Setup mock
    mock_result = Mock()
    mock_result.content = """{
  "question_type": "procedural",
  "primary_intent": "Learn process",
  "confidence": "high",
  "required_information": ["Steps"],
  "information_gaps": [],
  "assumptions": ["Clear query"],
  "suggested_steps": ["Search", "Explain"],
  "expected_response_type": "list"
}"""
    mock_ollama_client.invoke.return_value = mock_result
    
    # Generate
    hypothesis = hypothesis_service.generate_hypothesis("Clear specific query")
    
    # Assertions
    assert hypothesis.is_high_confidence()
    assert not hypothesis.has_critical_gaps()
    assert not hypothesis.requires_clarification()


def test_confidence_medium_some_gaps(hypothesis_service, mock_ollama_client):
    """Test that medium confidence queries may have gaps."""
    # Setup mock
    mock_result = Mock()
    mock_result.content = """{
  "question_type": "calculation",
  "primary_intent": "Calculate cost",
  "confidence": "medium",
  "required_information": ["Cost data"],
  "information_gaps": [
    {
      "gap_type": "location",
      "severity": "important",
      "suggested_query": "Where?",
      "examples": ["City A", "City B"]
    }
  ],
  "assumptions": ["General case"],
  "suggested_steps": ["Search", "Provide range"],
  "expected_response_type": "text"
}"""
    mock_ollama_client.invoke.return_value = mock_result
    
    # Generate
    hypothesis = hypothesis_service.generate_hypothesis("Somewhat ambiguous query")
    
    # Assertions
    assert hypothesis.confidence == ConfidenceLevel.MEDIUM
    assert not hypothesis.is_high_confidence()
    assert len(hypothesis.information_gaps) == 1
    assert not hypothesis.has_critical_gaps()  # Only important gap


def test_confidence_low_critical_gaps(hypothesis_service, mock_ollama_client):
    """Test that low confidence queries have critical gaps."""
    # Setup mock
    mock_result = Mock()
    mock_result.content = """{
  "question_type": "fact_retrieval",
  "primary_intent": "Unclear intent",
  "confidence": "low",
  "required_information": ["Context", "Specifics"],
  "information_gaps": [
    {
      "gap_type": "context",
      "severity": "critical",
      "suggested_query": "What do you mean?",
      "examples": ["Option A", "Option B"]
    }
  ],
  "assumptions": ["Guessing intent"],
  "suggested_steps": ["Request clarification"],
  "expected_response_type": "text"
}"""
    mock_ollama_client.invoke.return_value = mock_result
    
    # Generate
    hypothesis = hypothesis_service.generate_hypothesis("Vague query")
    
    # Assertions
    assert hypothesis.confidence == ConfidenceLevel.LOW
    assert not hypothesis.is_high_confidence()
    assert hypothesis.has_critical_gaps()
    assert hypothesis.requires_clarification()


# ============================================================================
# TEST GROUP 3: ERROR HANDLING (2 tests)
# ============================================================================

def test_fallback_on_llm_error(hypothesis_service, mock_ollama_client):
    """Test fallback hypothesis when LLM fails."""
    # Setup mock to raise exception
    mock_ollama_client.invoke.side_effect = Exception("Connection error")
    
    # Generate hypothesis (should not raise)
    query = "Test query"
    hypothesis = hypothesis_service.generate_hypothesis(query)
    
    # Assertions
    assert hypothesis.query == query
    assert hypothesis.confidence == ConfidenceLevel.UNKNOWN
    assert hypothesis.question_type == QuestionType.FACT_RETRIEVAL
    assert len(hypothesis.information_gaps) == 1
    assert hypothesis.information_gaps[0].gap_type == "llm_failure"
    assert hypothesis.metadata.get("fallback") is True


def test_fallback_on_malformed_json(hypothesis_service, mock_ollama_client, sample_llm_response_malformed):
    """Test fallback when LLM returns malformed JSON."""
    # Setup mock with incomplete response
    mock_result = Mock()
    mock_result.content = sample_llm_response_malformed
    mock_ollama_client.invoke.return_value = mock_result
    
    # Generate hypothesis (should fallback due to missing fields)
    query = "Test query"
    hypothesis = hypothesis_service.generate_hypothesis(query)
    
    # Assertions
    assert hypothesis.query == query
    assert hypothesis.confidence == ConfidenceLevel.UNKNOWN


# ============================================================================
# TEST GROUP 4: STATISTICS (2 tests)
# ============================================================================

def test_statistics_tracking(hypothesis_service, mock_ollama_client, sample_llm_response_high_confidence):
    """Test that statistics are tracked correctly."""
    # Setup mock
    mock_result = Mock()
    mock_result.content = sample_llm_response_high_confidence
    mock_ollama_client.invoke.return_value = mock_result
    
    # Reset stats
    hypothesis_service.reset_statistics()
    
    # Generate multiple hypotheses
    for i in range(3):
        hypothesis_service.generate_hypothesis(f"Query {i}")
    
    # Get stats
    stats = hypothesis_service.get_statistics()
    
    # Assertions
    assert stats["total_hypotheses"] == 3
    assert stats["high_confidence"] == 3
    assert stats["high_confidence_pct"] == 100.0
    assert stats["fallback_count"] == 0
    assert stats["avg_generation_time_ms"] > 0


def test_statistics_reset(hypothesis_service):
    """Test statistics reset functionality."""
    # Get initial stats
    stats_before = hypothesis_service.get_statistics()
    
    # Reset
    hypothesis_service.reset_statistics()
    
    # Get stats after reset
    stats_after = hypothesis_service.get_statistics()
    
    # Assertions
    assert stats_after["total_hypotheses"] == 0
    assert stats_after["high_confidence"] == 0
    assert stats_after["avg_generation_time_ms"] == 0.0


# ============================================================================
# TEST GROUP 5: INTEGRATION (2 tests)
# ============================================================================

def test_json_parsing_with_markdown(hypothesis_service, mock_ollama_client):
    """Test JSON parsing with markdown code blocks."""
    # Setup mock with markdown response
    mock_result = Mock()
    mock_result.content = """Here's the analysis:

```json
{
  "question_type": "procedural",
  "primary_intent": "Test",
  "confidence": "high",
  "required_information": ["Test"],
  "information_gaps": [],
  "assumptions": ["Test"],
  "suggested_steps": ["Test"],
  "expected_response_type": "text"
}
```

Hope this helps!"""
    mock_ollama_client.invoke.return_value = mock_result
    
    # Generate hypothesis
    hypothesis = hypothesis_service.generate_hypothesis("Test query")
    
    # Assertions
    assert hypothesis.question_type == QuestionType.PROCEDURAL
    assert hypothesis.confidence == ConfidenceLevel.HIGH


def test_case_insensitive_enum_parsing(hypothesis_service, mock_ollama_client):
    """Test that enum parsing handles different cases."""
    # Setup mock with uppercase confidence
    mock_result = Mock()
    mock_result.content = """{
  "question_type": "PROCEDURAL",
  "primary_intent": "Test",
  "confidence": "HIGH",
  "required_information": ["Test"],
  "information_gaps": [
    {
      "gap_type": "test",
      "severity": "CRITICAL",
      "suggested_query": "Test?",
      "examples": ["A", "B"]
    }
  ],
  "assumptions": ["Test"],
  "suggested_steps": ["Test"],
  "expected_response_type": "text"
}"""
    mock_ollama_client.invoke.return_value = mock_result
    
    # Generate hypothesis (should handle uppercase)
    hypothesis = hypothesis_service.generate_hypothesis("Test query")
    
    # Assertions
    assert hypothesis.question_type == QuestionType.PROCEDURAL
    assert hypothesis.confidence == ConfidenceLevel.HIGH
    assert hypothesis.information_gaps[0].severity == GapSeverity.CRITICAL


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
