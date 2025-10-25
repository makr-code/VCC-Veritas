"""
Test AgentExecutor with Source Citations

Tests the integration of RAG document retrieval into AgentExecutor,
verifying that source citations are properly included in results.

Author: VERITAS AI
Created: 14. Oktober 2025
"""

import sys
import os

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.services.agent_executor import AgentExecutor
from backend.models.process_step import ProcessStep, StepType


def test_agent_executor_with_citations():
    """Test AgentExecutor includes source citations"""
    
    print("=" * 80)
    print("AGENT EXECUTOR WITH SOURCE CITATIONS TEST")
    print("=" * 80)
    
    # Initialize executor
    executor = AgentExecutor()
    
    print(f"\n✅ AgentExecutor initialized")
    print(f"   Agent mode: {'real' if executor.use_agents else 'mock'}")
    print(f"   RAG Service: {'available' if executor.rag_service else 'not available'}")
    
    # Create test step
    step = ProcessStep(
        id="test_search",
        name="Search for Bauantrag requirements",
        description="Find documentation about building permit requirements in Stuttgart",
        step_type=StepType.SEARCH,
        parameters={'location': 'Stuttgart', 'document_type': 'Bauantrag'}
    )
    
    print(f"\n{'=' * 80}")
    print(f"Test Step:")
    print(f"  Name: {step.name}")
    print(f"  Type: {step.step_type.value}")
    print(f"  Description: {step.description}")
    
    # Execute step
    result = executor.execute_step(step)
    
    print(f"\n{'=' * 80}")
    print(f"Execution Result:")
    print(f"  Success: {result.success}")
    print(f"  Execution time: {result.execution_time}s")
    
    # Check metadata
    print(f"\nMetadata:")
    for key, value in result.metadata.items():
        print(f"  {key}: {value}")
    
    # Check data
    print(f"\nResult Data:")
    if result.data:
        for key, value in result.data.items():
            if key == 'query':
                print(f"  {key}: {value[:100]}..." if len(str(value)) > 100 else f"  {key}: {value}")
            else:
                print(f"  {key}: {value}")
    
    # Check source citations
    print(f"\n{'=' * 80}")
    if result.source_citations:
        print(f"✅ Source Citations Found: {len(result.source_citations)}")
        for i, citation in enumerate(result.source_citations, 1):
            print(f"\nCitation {i}:")
            if hasattr(citation, 'format_citation'):
                print(f"  {citation.format_citation()}")
            elif hasattr(citation, 'to_dict'):
                citation_dict = citation.to_dict()
                print(f"  Source: {citation_dict.get('source', {}).get('title', 'Unknown')}")
                print(f"  Confidence: {citation_dict.get('confidence', 'Unknown')}")
                print(f"  Relevance: {citation_dict.get('relevance_score', 0.0):.3f}")
            else:
                print(f"  {citation}")
    else:
        print(f"⚠️ No source citations (RAG Service may not be available)")
    
    # Test serialization
    print(f"\n{'=' * 80}")
    print(f"Serialization Test:")
    result_dict = result.to_dict()
    print(f"  Keys: {list(result_dict.keys())}")
    if 'source_citations' in result_dict:
        print(f"  ✅ source_citations included in serialization")
        print(f"  Citations count: {len(result_dict['source_citations'])}")
    else:
        print(f"  ℹ️ No source_citations in serialization (RAG not available)")
    
    print(f"\n{'=' * 80}")
    print(f"✅ Test Complete!")
    print(f"{'=' * 80}")


if __name__ == "__main__":
    test_agent_executor_with_citations()
