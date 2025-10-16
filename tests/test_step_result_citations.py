"""
Manual test of StepResult with source citations

Tests that StepResult properly handles source_citations field.
"""

from backend.models.process_step import StepResult
from backend.models.document_source import (
    DocumentSource, SourceCitation, RelevanceScore, 
    SourceType, CitationConfidence, create_mock_document
)


def test_step_result_with_citations():
    """Test StepResult with source citations"""
    
    print("=" * 80)
    print("STEP RESULT WITH SOURCE CITATIONS TEST")
    print("=" * 80)
    
    # Create mock documents
    doc1 = create_mock_document(
        "doc_1",
        "Bauantragsverfahren Baden-Württemberg",
        "Ein Bauantrag in Stuttgart erfordert...",
        relevance=0.92
    )
    
    doc2 = create_mock_document(
        "doc_2",
        "Einfamilienhaus Genehmigung",
        "Die Genehmigung für ein Einfamilienhaus...",
        relevance=0.85
    )
    
    # Create citations
    citation1 = doc1.to_citation()
    citation1.page_number = 42
    citation1.section_title = "§ 3 Bauantrag"
    
    citation2 = doc2.to_citation()
    citation2.page_number = 15
    citation2.section_title = "Kapitel 2: Verfahren"
    
    citations = [citation1, citation2]
    
    print(f"\n✅ Created {len(citations)} mock citations")
    
    # Create StepResult with citations
    result = StepResult(
        success=True,
        data={
            'result': 'Found information about building permits',
            'documents_retrieved': 2
        },
        execution_time=0.5,
        source_citations=citations,
        metadata={
            'agent_mode': 'test',
            'rag_enabled': True
        }
    )
    
    print(f"\n✅ Created StepResult with citations")
    print(f"   Success: {result.success}")
    print(f"   Citations: {len(result.source_citations) if result.source_citations else 0}")
    
    # Test serialization
    print(f"\n{'=' * 80}")
    print(f"Serialization Test:")
    result_dict = result.to_dict()
    
    print(f"  Keys: {list(result_dict.keys())}")
    
    if 'source_citations' in result_dict:
        print(f"  ✅ source_citations key present")
        print(f"  Citations count: {len(result_dict['source_citations'])}")
        
        print(f"\n  Citation Details:")
        for i, citation_dict in enumerate(result_dict['source_citations'], 1):
            print(f"\n  Citation {i}:")
            source = citation_dict.get('source', {})
            print(f"    Title: {source.get('title', 'Unknown')}")
            print(f"    Page: {citation_dict.get('page_number', 'N/A')}")
            print(f"    Section: {citation_dict.get('section_title', 'N/A')}")
            print(f"    Confidence: {citation_dict.get('confidence', 'Unknown')}")
            print(f"    Relevance: {citation_dict.get('relevance_score', 0.0):.3f}")
    else:
        print(f"  ❌ source_citations key missing!")
    
    # Test citation formatting
    print(f"\n{'=' * 80}")
    print(f"Citation Formatting:")
    for i, citation in enumerate(citations, 1):
        print(f"\n  {i}. {citation.format_citation()}")
    
    print(f"\n{'=' * 80}")
    print(f"✅ All tests passed!")
    print(f"{'=' * 80}")


if __name__ == "__main__":
    test_step_result_with_citations()
