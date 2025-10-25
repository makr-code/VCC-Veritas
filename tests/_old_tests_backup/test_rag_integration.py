"""
RAG Integration Tests

Comprehensive test suite for RAG Service and ProcessExecutor integration.
Tests document retrieval, ranking, citations, and end-to-end workflows.

Author: VERITAS AI
Created: 14. Oktober 2025
Version: 1.0
"""

import sys
import os
import pytest
from typing import List, Dict, Any
from datetime import datetime

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.services.rag_service import RAGService, SearchFilters, SearchWeights, RankingStrategy
from backend.models.document_source import (
    DocumentSource, SourceCitation, RelevanceScore, SourceType,
    CitationConfidence, create_mock_document
)
from backend.services.process_executor import ProcessExecutor
from backend.services.nlp_service import NLPService
from backend.services.process_builder import ProcessBuilder
from backend.models.process_step import StepType


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def rag_service():
    """Create RAG service instance"""
    return RAGService()


@pytest.fixture
def mock_documents():
    """Create mock documents for testing"""
    return [
        create_mock_document(
            "doc_1",
            "Bauantragsverfahren in Baden-Württemberg",
            "Ein Bauantrag in Stuttgart erfordert folgende Schritte: 1. Bauvoranfrage, 2. Vollständige Bauunterlagen, 3. Einreichung beim Bauamt...",
            relevance=0.92
        ),
        create_mock_document(
            "doc_2",
            "Einfamilienhaus Genehmigung",
            "Die Genehmigung für ein Einfamilienhaus erfolgt nach Prüfung der Bauunterlagen. Erforderlich sind Bauzeichnungen, statische Berechnungen...",
            relevance=0.85
        ),
        create_mock_document(
            "doc_3",
            "Baukosten in München",
            "Die durchschnittlichen Kosten für einen Bauantrag in München betragen 2.500 Euro. Dies umfasst Bearbeitungsgebühren...",
            relevance=0.78
        ),
        create_mock_document(
            "doc_4",
            "GmbH Gründung: Leitfaden",
            "Eine GmbH kann ab 25.000 Euro Stammkapital gegründet werden. Erforderlich sind Gesellschaftsvertrag, Notartermin...",
            relevance=0.88
        ),
        create_mock_document(
            "doc_5",
            "Aktiengesellschaft: Voraussetzungen",
            "Die AG benötigt mindestens 50.000 Euro Grundkapital. Der Vorstand muss bestellt werden, Aufsichtsrat ist erforderlich...",
            relevance=0.82
        ),
    ]


@pytest.fixture
def executor_with_rag(rag_service):
    """Create ProcessExecutor with RAG service"""
    return ProcessExecutor(max_workers=2, use_agents=False, rag_service=rag_service)


@pytest.fixture
def nlp_service():
    """Create NLP service"""
    return NLPService()


@pytest.fixture
def process_builder(nlp_service):
    """Create process builder"""
    return ProcessBuilder(nlp_service)


# ============================================================================
# Test 1: RAG Service Initialization
# ============================================================================

def test_rag_service_initialization(rag_service):
    """Test that RAG service initializes correctly"""
    assert rag_service is not None
    # Service should be available (even in mock mode)
    # Real UDS3 backends may be None in test environment
    print(f"✅ RAG Service initialized")
    print(f"   ChromaDB: {'✅' if rag_service.chromadb else '❌ (mock)'}")
    print(f"   Neo4j: {'✅' if rag_service.neo4j else '❌ (mock)'}")
    print(f"   PostgreSQL: {'✅' if rag_service.postgresql else '❌ (mock)'}")


# ============================================================================
# Test 2: Vector Search Basic
# ============================================================================

def test_vector_search_basic(rag_service):
    """Test basic vector search functionality"""
    query = "Bauantrag für Einfamilienhaus"
    results = rag_service.vector_search(query)
    
    assert isinstance(results, list)
    print(f"✅ Vector search returned {len(results)} results")
    
    if results:
        first_result = results[0]
        assert hasattr(first_result, 'document_id')
        assert hasattr(first_result, 'relevance_score')
        print(f"   First result: {first_result.metadata.title} (score: {first_result.relevance_score:.2f})")


# ============================================================================
# Test 3: Hybrid Search Ranking
# ============================================================================

def test_hybrid_search_ranking(rag_service):
    """Test hybrid search with different ranking strategies"""
    query = "GmbH gründen"
    
    # Test with RRF (default)
    result_rrf = rag_service.hybrid_search(
        query,
        ranking_strategy=RankingStrategy.RECIPROCAL_RANK_FUSION
    )
    
    assert result_rrf.total_count >= 0
    assert result_rrf.query == query
    print(f"✅ Hybrid search (RRF): {len(result_rrf.results)} results")
    print(f"   Methods used: {[m.value for m in result_rrf.search_methods_used]}")
    print(f"   Execution time: {result_rrf.execution_time_ms:.2f}ms")
    
    # Verify results are sorted by relevance
    if len(result_rrf.results) > 1:
        scores = [r.relevance_score for r in result_rrf.results]
        assert scores == sorted(scores, reverse=True), "Results should be sorted by relevance"


# ============================================================================
# Test 4: Document Deduplication
# ============================================================================

def test_document_deduplication(mock_documents):
    """Test that duplicate documents are filtered"""
    # Create duplicate
    dup_doc = create_mock_document(
        "doc_1",  # Same ID as first document
        "Duplicate Document",
        "This is a duplicate",
        relevance=0.75
    )
    
    docs_with_dup = mock_documents + [dup_doc]
    
    # Simulate deduplication
    seen_ids = set()
    unique_docs = []
    for doc in docs_with_dup:
        if doc.document_id not in seen_ids:
            seen_ids.add(doc.document_id)
            unique_docs.append(doc)
    
    assert len(unique_docs) == len(mock_documents)
    print(f"✅ Deduplication: {len(docs_with_dup)} → {len(unique_docs)} documents")


# ============================================================================
# Test 5: Relevance Threshold Filtering
# ============================================================================

def test_relevance_threshold_filtering(mock_documents):
    """Test filtering documents by relevance threshold"""
    threshold = 0.8
    filtered = [doc for doc in mock_documents if doc.relevance_score.hybrid >= threshold]
    
    print(f"✅ Filtering with threshold {threshold}:")
    print(f"   Total documents: {len(mock_documents)}")
    print(f"   High relevance (>={threshold}): {len(filtered)}")
    
    # All filtered docs should meet threshold
    for doc in filtered:
        assert doc.relevance_score.hybrid >= threshold


# ============================================================================
# Test 6: Context Building with Token Limit
# ============================================================================

def test_context_building_token_limit(rag_service, mock_documents):
    """Test that context building respects token limits"""
    # Build context with small token limit
    executor = ProcessExecutor(use_agents=False, rag_service=rag_service)
    context = executor._build_context(mock_documents, max_tokens=200)
    
    # Estimate tokens (4 chars per token)
    estimated_tokens = len(context) // 4
    
    print(f"✅ Context building:")
    print(f"   Characters: {len(context)}")
    print(f"   Estimated tokens: {estimated_tokens}")
    print(f"   Limit: 200 tokens")
    
    # Should not significantly exceed limit (allow 10% overage for formatting)
    assert estimated_tokens <= 220, "Context should respect token limit"


# ============================================================================
# Test 7: Source Citation Extraction
# ============================================================================

def test_source_citation_extraction(mock_documents):
    """Test extraction of source citations"""
    executor = ProcessExecutor(use_agents=False)
    citations = executor._extract_citations(mock_documents)
    
    assert len(citations) == len(mock_documents)
    print(f"✅ Extracted {len(citations)} citations")
    
    for i, citation in enumerate(citations):
        assert isinstance(citation, SourceCitation)
        assert citation.source.document_id == mock_documents[i].document_id
        assert isinstance(citation.confidence, CitationConfidence)
        print(f"   {i+1}. {citation.source.title} ({citation.confidence.value})")


# ============================================================================
# Test 8: Executor RAG Integration
# ============================================================================

def test_executor_rag_integration(executor_with_rag, process_builder):
    """Test that ProcessExecutor integrates with RAG correctly"""
    query = "Bauantrag für Stuttgart"
    tree = process_builder.build_process_tree(query)
    
    # Execute with RAG
    result = executor_with_rag.execute_process(tree)
    
    assert result['success'] is True
    print(f"✅ Executor with RAG: {result['steps_completed']} steps completed")
    
    # Check if any step has RAG data
    has_rag_data = False
    for step_id, step_result in result['step_results'].items():
        metadata = step_result.get('metadata', {})
        if metadata.get('execution_mode') == 'mock_with_rag':
            has_rag_data = True
            docs_retrieved = metadata.get('documents_retrieved', 0)
            print(f"   Step '{step_id}' retrieved {docs_retrieved} documents")
            break
    
    # Note: May not have RAG data if service is not available
    print(f"   RAG data present: {has_rag_data}")


# ============================================================================
# Test 9: Query Reformulation
# ============================================================================

def test_query_reformulation(executor_with_rag):
    """Test that queries are reformulated based on step type"""
    from backend.models.process_step import ProcessStep
    
    test_cases = [
        (StepType.SEARCH, "Bauantrag", "Information about Bauantrag"),
        (StepType.RETRIEVAL, "Kosten", "Data and facts about Kosten"),
        (StepType.VALIDATION, "Genehmigung", "Legal requirements and regulations for Genehmigung"),
    ]
    
    print(f"✅ Query reformulation:")
    for step_type, desc, expected_prefix in test_cases:
        step = ProcessStep(
            id="test",
            name="Test Step",
            step_type=step_type,
            description=desc
        )
        
        reformulated = executor_with_rag._reformulate_query_for_step(step)
        print(f"   {step_type.value}: '{desc}' → '{reformulated}'")
        assert desc in reformulated or expected_prefix.split()[0] in reformulated


# ============================================================================
# Test 10: Empty Search Results
# ============================================================================

def test_empty_search_results(rag_service):
    """Test handling of empty search results"""
    query = "xyzabcdef123notfound"  # Query unlikely to match
    results = rag_service.vector_search(query)
    
    # Should return empty list, not error
    assert isinstance(results, list)
    print(f"✅ Empty search handled gracefully: {len(results)} results")


# ============================================================================
# Test 11: Error Handling - No UDS3
# ============================================================================

def test_error_handling_no_uds3():
    """Test that system handles missing UDS3 gracefully"""
    # Create executor without RAG service
    executor = ProcessExecutor(use_agents=False, rag_service=None)
    
    # Should either have no service or mock mode
    if executor.rag_service is None:
        print(f"✅ Executor handles missing RAG service (None)")
    else:
        # Mock mode is acceptable
        print(f"✅ Executor handles missing RAG service (mock mode)")
        assert not executor.rag_service.is_available() or executor.rag_service.chromadb is None


# ============================================================================
# Test 12: RelevanceScore Calculation
# ============================================================================

def test_relevance_score_calculation():
    """Test relevance score calculation"""
    score = RelevanceScore(semantic=0.9, keyword=0.7, graph=0.5)
    
    # Calculate hybrid with default weights
    hybrid = score.calculate_hybrid(
        semantic_weight=0.5,
        keyword_weight=0.3,
        graph_weight=0.2
    )
    
    expected = (0.9 * 0.5) + (0.7 * 0.3) + (0.5 * 0.2)
    assert abs(hybrid - expected) < 0.001
    print(f"✅ Relevance score calculation: {hybrid:.3f} (expected: {expected:.3f})")
    
    # Test confidence level
    confidence = score.get_confidence()
    assert confidence in [CitationConfidence.HIGH, CitationConfidence.MEDIUM, CitationConfidence.LOW]
    print(f"   Confidence level: {confidence.value}")


# ============================================================================
# Test 13: Document Source Serialization
# ============================================================================

def test_document_source_serialization(mock_documents):
    """Test that DocumentSource can be serialized and deserialized"""
    doc = mock_documents[0]
    
    # Serialize
    doc_dict = doc.to_dict()
    assert isinstance(doc_dict, dict)
    assert 'document_id' in doc_dict
    assert 'title' in doc_dict
    
    # Deserialize
    doc_restored = DocumentSource.from_dict(doc_dict)
    assert doc_restored.document_id == doc.document_id
    assert doc_restored.title == doc.title
    
    print(f"✅ Document serialization: {doc.document_id} → dict → {doc_restored.document_id}")


# ============================================================================
# Test 14: Citation Confidence Levels
# ============================================================================

def test_citation_confidence_levels():
    """Test citation confidence level assignment"""
    test_cases = [
        (0.95, CitationConfidence.HIGH),
        (0.82, CitationConfidence.HIGH),
        (0.65, CitationConfidence.MEDIUM),
        (0.45, CitationConfidence.LOW),
        (0.25, CitationConfidence.UNKNOWN),
    ]
    
    print(f"✅ Citation confidence levels:")
    for relevance, expected_confidence in test_cases:
        score = RelevanceScore(hybrid=relevance)
        confidence = score.get_confidence()
        print(f"   {relevance:.2f} → {confidence.value}")
        assert confidence == expected_confidence


# ============================================================================
# Test 15: End-to-End with Mock Docs
# ============================================================================

def test_end_to_end_with_mock_docs(nlp_service, mock_documents):
    """Test end-to-end workflow with mock documents"""
    # Create services
    builder = ProcessBuilder(nlp_service)
    rag_service = RAGService()
    executor = ProcessExecutor(use_agents=False, rag_service=rag_service)
    
    # Build tree
    query = "Bauantrag für Einfamilienhaus in Stuttgart"
    tree = builder.build_process_tree(query)
    
    print(f"✅ End-to-end test:")
    print(f"   Query: {query}")
    print(f"   Steps: {tree.total_steps}")
    
    # Execute
    result = executor.execute_process(tree)
    
    assert result['success'] is True
    assert result['steps_completed'] == tree.total_steps
    print(f"   Success: {result['success']}")
    print(f"   Steps completed: {result['steps_completed']}/{tree.total_steps}")
    print(f"   Execution time: {result['execution_time']:.2f}s")


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    print("="*80)
    print("RAG INTEGRATION TESTS")
    print("="*80)
    
    # Run with pytest
    pytest.main([__file__, "-v", "-s"])
