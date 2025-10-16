"""
Test Query Expansion Functionality (Phase 5 - Task 2.2)

Tests the expand_query() method for query reformulation and synonym generation.

Version: 1.0.0
Phase: 5 (v5.0 Enhanced RAG)
"""

import pytest
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from services.rag_service import RAGService


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def rag_service():
    """Create RAG service for testing"""
    return RAGService()


# ============================================================================
# TESTS
# ============================================================================

def test_expand_query_basic(rag_service):
    """Test basic query expansion"""
    query = "Bauantrag Stuttgart"
    expansions = rag_service.expand_query(query, max_expansions=3)
    
    # Should include original query
    assert query in expansions, "Should include original query"
    
    # Should generate expansions
    assert len(expansions) > 1, "Should generate expansions"
    assert len(expansions) <= 4, "Should respect max_expansions + original"
    
    # All expansions should be strings
    for exp in expansions:
        assert isinstance(exp, str)


def test_expand_query_bauantrag_synonyms(rag_service):
    """Test Bauantrag synonyms"""
    query = "Bauantrag in München"
    expansions = rag_service.expand_query(query, max_expansions=3)
    
    # Check for expected synonyms
    expected_terms = ['baugenehmigung', 'bauantragsverfahren', 'baugesuch']
    
    found_synonyms = []
    for exp in expansions:
        exp_lower = exp.lower()
        for term in expected_terms:
            if term in exp_lower:
                found_synonyms.append(term)
    
    assert len(found_synonyms) > 0, "Should generate at least one synonym"


def test_expand_query_gewerbeanmeldung(rag_service):
    """Test Gewerbeanmeldung synonyms"""
    query = "Gewerbeanmeldung München"
    expansions = rag_service.expand_query(query, max_expansions=2)
    
    # Check for business-related synonyms
    expected_terms = ['gewerbeschein', 'gewerbeerlaubnis', 'gewerbemeldung']
    
    found_synonyms = []
    for exp in expansions:
        exp_lower = exp.lower()
        for term in expected_terms:
            if term in exp_lower:
                found_synonyms.append(term)
    
    assert len(found_synonyms) > 0, "Should generate business synonyms"


def test_expand_query_personalausweis(rag_service):
    """Test Personalausweis synonyms"""
    query = "Personalausweis beantragen"
    expansions = rag_service.expand_query(query, max_expansions=2)
    
    # Should generate document-related synonyms
    assert len(expansions) >= 2, "Should generate at least 1 expansion + original"
    
    # Check for document synonyms
    combined = " ".join(expansions).lower()
    assert any(term in combined for term in ['ausweis', 'identitätskarte', 'id-karte'])


def test_expand_query_max_expansions(rag_service):
    """Test max_expansions parameter"""
    query = "Bauantrag für Einfamilienhaus"
    
    # Test different limits
    expansions_1 = rag_service.expand_query(query, max_expansions=1)
    expansions_3 = rag_service.expand_query(query, max_expansions=3)
    expansions_5 = rag_service.expand_query(query, max_expansions=5)
    
    # Should respect limits (including original)
    assert len(expansions_1) <= 2, "Should limit to 1 expansion + original"
    assert len(expansions_3) <= 4, "Should limit to 3 expansions + original"
    assert len(expansions_5) <= 6, "Should limit to 5 expansions + original"


def test_expand_query_include_original_false(rag_service):
    """Test exclude original query"""
    query = "Bauantrag Stuttgart"
    expansions = rag_service.expand_query(query, include_original=False)
    
    # Should NOT include original
    assert query not in expansions, "Should not include original query"
    
    # Should still generate expansions
    assert len(expansions) > 0, "Should generate expansions"


def test_expand_query_no_matches(rag_service):
    """Test query with no matching terms"""
    query = "Unknown query xyz123"
    expansions = rag_service.expand_query(query, max_expansions=3)
    
    # Should only return original query
    assert len(expansions) == 1, "Should only return original for unknown terms"
    assert expansions[0] == query


def test_expand_query_multiple_terms(rag_service):
    """Test query with multiple expandable terms"""
    query = "Bauantrag kosten"
    expansions = rag_service.expand_query(query, max_expansions=5)
    
    # Should expand both terms
    combined = " ".join(expansions).lower()
    
    # Check for building synonyms
    has_building = any(term in combined for term in ['baugenehmigung', 'bauantragsverfahren'])
    
    # Check for cost synonyms
    has_cost = any(term in combined for term in ['gebühren', 'preise', 'ausgaben'])
    
    # At least one category should have synonyms
    assert has_building or has_cost, "Should expand at least one term category"


def test_expand_query_case_preservation(rag_service):
    """Test that case is preserved in expansions"""
    query = "BAUANTRAG Stuttgart"
    expansions = rag_service.expand_query(query, max_expansions=2)
    
    # Expansions should exist
    assert len(expansions) > 1
    
    # Check that Stuttgart is preserved in all expansions
    for exp in expansions:
        if exp != query:  # Skip original
            assert "Stuttgart" in exp, "Should preserve case of unmodified terms"


def test_expand_query_no_duplicates(rag_service):
    """Test that no duplicate expansions are generated"""
    query = "Bauantrag für Einfamilienhaus"
    expansions = rag_service.expand_query(query, max_expansions=10)
    
    # Check for duplicates
    unique_expansions = set(expansions)
    assert len(unique_expansions) == len(expansions), "Should not generate duplicates"


def test_expand_query_umlauts(rag_service):
    """Test expansion with German umlauts"""
    query = "Führerschein verlängern"
    expansions = rag_service.expand_query(query, max_expansions=2)
    
    # Should handle umlauts correctly
    assert len(expansions) >= 2
    
    # Check for driver's license synonyms
    combined = " ".join(expansions).lower()
    assert any(term in combined for term in ['fahrerlaubnis', 'fahrberechtigung'])


def test_expand_query_authorities(rag_service):
    """Test expansion of authority names"""
    query = "Kontakt Bauamt Stuttgart"
    expansions = rag_service.expand_query(query, max_expansions=3)
    
    # Should expand authority names
    combined = " ".join(expansions).lower()
    assert any(term in combined for term in ['bauaufsicht', 'baubehörde', 'bauordnungsamt'])


def test_expand_query_procedures(rag_service):
    """Test expansion of procedure terms"""
    query = "Anmeldung beim Einwohnermeldeamt"
    expansions = rag_service.expand_query(query, max_expansions=3)
    
    # Should expand procedure terms
    combined = " ".join(expansions).lower()
    assert any(term in combined for term in ['registrierung', 'meldung', 'eintragung']), \
        f"Should find procedure synonyms in: {expansions}"


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("="*80)
    print("QUERY EXPANSION TEST SUITE")
    print("="*80)
    
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
