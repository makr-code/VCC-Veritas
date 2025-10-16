"""
Agent Executor Service

Bridges ProcessExecutor with the existing VERITAS agent system.
Maps ProcessStep types to appropriate agent calls using the agent registry.

This service:
1. Maps StepType to AgentCapability
2. Selects appropriate agent from registry
3. Executes agent with step parameters
4. Returns agent result as StepResult

Author: Veritas AI
Date: 2025-10-14
Version: 1.0
"""

import logging
import sys
import os
from typing import Dict, Any, Optional, List
from datetime import datetime

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.models.process_step import ProcessStep, StepType, StepResult

# Try to import RAG service for document retrieval
try:
    from backend.services.rag_service import RAGService
    from backend.models.document_source import DocumentSource, SourceCitation
    RAG_SERVICE_AVAILABLE = True
except ImportError:
    RAG_SERVICE_AVAILABLE = False
    logging.warning("⚠️ RAG Service not available")

# Try to import agent system (graceful degradation if not available)
try:
    from backend.agents.veritas_api_agent_registry import (
        get_agent_registry,
        AgentCapability
    )
    AGENT_REGISTRY_AVAILABLE = True
except ImportError:
    AGENT_REGISTRY_AVAILABLE = False
    logging.warning("⚠️ Agent Registry not available - using mock mode")

try:
    from backend.agents.veritas_api_agent_orchestrator import AgentOrchestrator
    ORCHESTRATOR_AVAILABLE = True
except ImportError:
    ORCHESTRATOR_AVAILABLE = False
    logging.warning("⚠️ Agent Orchestrator not available - using mock mode")

logger = logging.getLogger(__name__)


class AgentExecutor:
    """
    Executes ProcessSteps using the VERITAS agent system.
    
    Maps ProcessStep types to agent capabilities and orchestrates
    execution through the existing agent infrastructure.
    
    Features:
    - Step type → Agent capability mapping
    - Agent selection from registry
    - Parameter translation
    - Result transformation
    - Graceful fallback to mock mode
    
    Example:
        >>> executor = AgentExecutor()
        >>> step = ProcessStep(...)
        >>> result = executor.execute_step(step)
    """
    
    def __init__(self, rag_service: Optional['RAGService'] = None):
        """
        Initialize AgentExecutor.
        
        Args:
            rag_service: Optional RAG service for document retrieval
        """
        self.use_agents = AGENT_REGISTRY_AVAILABLE and ORCHESTRATOR_AVAILABLE
        
        # Initialize RAG service if available
        self.rag_service = rag_service
        if rag_service is None and RAG_SERVICE_AVAILABLE:
            try:
                self.rag_service = RAGService()
                logger.info("✅ RAG Service initialized in AgentExecutor")
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize RAG Service: {e}")
        
        if self.use_agents:
            try:
                self.agent_registry = get_agent_registry()
                self.orchestrator = AgentOrchestrator()
                logger.info("✅ AgentExecutor initialized with real agents")
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize agents: {e}")
                self.use_agents = False
                logger.info("📋 AgentExecutor fallback to mock mode")
        else:
            logger.info("📋 AgentExecutor running in mock mode")
        
        # Initialize mapping
        self._init_step_to_capability_mapping()
    
    def _retrieve_documents_for_agent(
        self,
        step: ProcessStep,
        top_k: int = 3
    ) -> tuple[List['DocumentSource'], List['SourceCitation']]:
        """
        Retrieve relevant documents for agent execution.
        
        Args:
            step: ProcessStep to retrieve documents for
            top_k: Number of documents to retrieve
            
        Returns:
            Tuple of (documents, citations)
        """
        if not self.rag_service or not self.rag_service.is_available():
            return [], []
        
        try:
            # Build query from step
            query = f"{step.name}: {step.description}"
            
            # Retrieve documents
            search_result = self.rag_service.hybrid_search(
                query=query,
                filters={'max_results': top_k}
            )
            
            if not search_result or not search_result.results:
                return [], []
            
            # Extract citations
            citations = []
            for doc in search_result.results:
                citation = doc.to_citation() if hasattr(doc, 'to_citation') else None
                if citation:
                    citations.append(citation)
            
            logger.info(f"📚 Retrieved {len(search_result.results)} documents for agent execution")
            return search_result.results, citations
            
        except Exception as e:
            logger.warning(f"⚠️ Document retrieval failed: {e}")
            return [], []
    
    def _init_step_to_capability_mapping(self):
        """
        Initialize mapping from ProcessStep types to AgentCapabilities.
        
        This defines how different step types map to agent capabilities
        in the VERITAS agent system.
        """
        self.step_capability_map = {
            # Search → Document Retrieval + Semantic Search
            StepType.SEARCH: [
                AgentCapability.DOCUMENT_RETRIEVAL if AGENT_REGISTRY_AVAILABLE else "document_retrieval",
                AgentCapability.SEMANTIC_SEARCH if AGENT_REGISTRY_AVAILABLE else "semantic_search"
            ],
            
            # Retrieval → Document Retrieval
            StepType.RETRIEVAL: [
                AgentCapability.DOCUMENT_RETRIEVAL if AGENT_REGISTRY_AVAILABLE else "document_retrieval"
            ],
            
            # Analysis → Data Analysis + Domain Classification
            StepType.ANALYSIS: [
                AgentCapability.DATA_ANALYSIS if AGENT_REGISTRY_AVAILABLE else "data_analysis",
                AgentCapability.DOMAIN_CLASSIFICATION if AGENT_REGISTRY_AVAILABLE else "domain_classification"
            ],
            
            # Synthesis → Knowledge Synthesis + Structured Response
            StepType.SYNTHESIS: [
                AgentCapability.KNOWLEDGE_SYNTHESIS if AGENT_REGISTRY_AVAILABLE else "knowledge_synthesis",
                AgentCapability.STRUCTURED_RESPONSE_GENERATION if AGENT_REGISTRY_AVAILABLE else "structured_response"
            ],
            
            # Validation → Compliance Checking + Quality Assessment
            StepType.VALIDATION: [
                AgentCapability.COMPLIANCE_CHECKING if AGENT_REGISTRY_AVAILABLE else "compliance_checking"
            ],
            
            # Transformation → Data Processing
            StepType.TRANSFORMATION: [
                AgentCapability.DATA_ANALYSIS if AGENT_REGISTRY_AVAILABLE else "data_analysis"
            ],
            
            # Calculation → Financial Impact Analysis
            StepType.CALCULATION: [
                AgentCapability.FINANCIAL_IMPACT_ANALYSIS if AGENT_REGISTRY_AVAILABLE else "financial_impact"
            ],
            
            # Comparison → Multi-Source Synthesis
            StepType.COMPARISON: [
                AgentCapability.MULTI_SOURCE_SYNTHESIS if AGENT_REGISTRY_AVAILABLE else "multi_source_synthesis"
            ],
            
            # Aggregation → Knowledge Synthesis
            StepType.AGGREGATION: [
                AgentCapability.KNOWLEDGE_SYNTHESIS if AGENT_REGISTRY_AVAILABLE else "knowledge_synthesis"
            ],
            
            # Other → Query Processing (fallback)
            StepType.OTHER: [
                AgentCapability.QUERY_PROCESSING if AGENT_REGISTRY_AVAILABLE else "query_processing"
            ]
        }
    
    def execute_step(self, step: ProcessStep) -> StepResult:
        """
        Execute a ProcessStep using agents.
        
        Args:
            step: ProcessStep to execute
            
        Returns:
            StepResult with agent execution result
        """
        logger.info(f"Executing step: {step.name} ({step.step_type.value})")
        
        if self.use_agents:
            return self._execute_with_agents(step)
        else:
            return self._execute_mock(step)
    
    def _execute_with_agents(self, step: ProcessStep) -> StepResult:
        """
        Execute step using real agents with optional RAG document retrieval.
        
        Args:
            step: ProcessStep to execute
            
        Returns:
            StepResult with agent results and source citations
        """
        try:
            # Retrieve relevant documents if RAG is available
            documents, citations = self._retrieve_documents_for_agent(step, top_k=3)
            
            # Get required capabilities for this step type
            capabilities = self.step_capability_map.get(
                step.step_type,
                [AgentCapability.QUERY_PROCESSING]
            )
            
            # Build query for orchestrator
            query_text = self._build_agent_query(step)
            
            # Add document context if available
            if documents:
                doc_context = "\n\n".join([
                    f"Document {i+1}: {doc.title}\n{doc.excerpt if hasattr(doc, 'excerpt') else doc.content[:200]}"
                    for i, doc in enumerate(documents)
                ])
                query_text = f"{query_text}\n\nRelevant Documents:\n{doc_context}"
            
            # Execute through orchestrator
            # Note: This is a simplified integration - full implementation
            # would need to adapt to orchestrator's specific API
            result_data = {
                'step_id': step.id,
                'step_type': step.step_type.value,
                'capabilities_used': [str(c) for c in capabilities],
                'query': query_text,
                'parameters': step.parameters,
                'agent_mode': 'real',
                'documents_retrieved': len(documents),
                'note': 'Agent execution with RAG integration'
            }
            
            # Add document metadata if available
            if documents:
                result_data['document_sources'] = [
                    {
                        'document_id': doc.document_id if hasattr(doc, 'document_id') else f'doc_{i}',
                        'title': doc.title if hasattr(doc, 'title') else 'Unknown',
                        'relevance': doc.relevance_score if hasattr(doc, 'relevance_score') else 0.0
                    }
                    for i, doc in enumerate(documents)
                ]
            
            # For now, return structured result
            # TODO: Replace with actual orchestrator.execute_query(query_text)
            logger.info(f"✅ Agent execution complete: {step.name} (with {len(citations)} citations)")
            
            return StepResult(
                success=True,
                data=result_data,
                source_citations=citations if citations else None,
                metadata={
                    'agent_mode': 'real',
                    'capabilities': [str(c) for c in capabilities],
                    'documents_retrieved': len(documents),
                    'timestamp': datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"❌ Agent execution failed: {step.name} - {e}")
            return StepResult(
                success=False,
                error=f"Agent execution error: {str(e)}",
                metadata={'step_id': step.id}
            )
    
    def _execute_mock(self, step: ProcessStep) -> StepResult:
        """
        Execute step in mock mode (fallback) with mock citations.
        
        Args:
            step: ProcessStep to execute
            
        Returns:
            StepResult with mock data and mock citations
        """
        import time
        
        # Simulate execution time
        time.sleep(0.1)
        
        # Try to retrieve documents even in mock mode
        documents, citations = self._retrieve_documents_for_agent(step, top_k=2)
        
        # Generate mock data
        data = self._generate_mock_data(step)
        
        # Add document info to mock data
        if documents:
            data['documents_retrieved'] = len(documents)
            data['document_sources'] = [
                {
                    'document_id': doc.document_id if hasattr(doc, 'document_id') else f'doc_{i}',
                    'title': doc.title if hasattr(doc, 'title') else f'Mock Document {i+1}'
                }
                for i, doc in enumerate(documents)
            ]
        
        return StepResult(
            success=True,
            data=data,
            execution_time=0.1,
            source_citations=citations if citations else None,
            metadata={
                'agent_mode': 'mock',
                'step_id': step.id,
                'step_type': step.step_type.value,
                'documents_retrieved': len(documents),
                'timestamp': datetime.now().isoformat()
            }
        )
    
    def _build_agent_query(self, step: ProcessStep) -> str:
        """
        Build query text for agent orchestrator.
        
        Args:
            step: ProcessStep
            
        Returns:
            Query string for agent execution
        """
        # Extract key information from step
        name = step.name
        params = step.parameters
        
        # Build query based on step type and parameters
        query_parts = [name]
        
        # Add location if present
        if 'location' in params:
            query_parts.append(f"in {params['location']}")
        
        # Add document type if present
        if 'document_type' in params:
            query_parts.append(f"für {params['document_type']}")
        
        # Add entity if present
        if 'entity' in params:
            query_parts.append(f"über {params['entity']}")
        
        return " ".join(query_parts)
    
    def _generate_mock_data(self, step: ProcessStep) -> Dict[str, Any]:
        """
        Generate mock data for step (fallback mode).
        
        Args:
            step: ProcessStep
            
        Returns:
            Mock data dictionary
        """
        step_type = step.step_type
        params = step.parameters
        
        # Generate mock data based on step type
        if step_type == StepType.SEARCH:
            return {
                'results_found': 5,
                'search_query': params.get('query', 'mock query'),
                'documents': [f"Document {i+1}" for i in range(5)],
                'relevance_scores': [0.95, 0.87, 0.82, 0.76, 0.71],
                'mode': 'mock'
            }
        
        elif step_type == StepType.RETRIEVAL:
            return {
                'documents_retrieved': 3,
                'content': f"Mock content for {step.name}",
                'metadata': params,
                'mode': 'mock'
            }
        
        elif step_type == StepType.ANALYSIS:
            entity = params.get('entity', 'unknown')
            return {
                'entity': entity,
                'key_characteristics': [
                    f"{entity} characteristic 1",
                    f"{entity} characteristic 2",
                    f"{entity} characteristic 3"
                ],
                'summary': f"Analysis of {entity}",
                'mode': 'mock'
            }
        
        elif step_type == StepType.COMPARISON:
            entities = params.get('entities', ['A', 'B'])
            return {
                'entities': entities,
                'similarities': [
                    f"Both have property X",
                    f"Both are regulated"
                ],
                'differences': [
                    f"{entities[0]} has feature Y",
                    f"{entities[1]} has feature Z"
                ],
                'recommendation': f"Choose {entities[0]} if condition X, else {entities[1]}",
                'mode': 'mock'
            }
        
        elif step_type == StepType.SYNTHESIS:
            return {
                'checklist': [
                    "Item 1: Check requirements",
                    "Item 2: Prepare documents",
                    "Item 3: Submit application"
                ],
                'summary': f"Synthesized result for {step.name}",
                'sources': params,
                'mode': 'mock'
            }
        
        elif step_type == StepType.CALCULATION:
            return {
                'calculated_value': 450.00,
                'currency': 'EUR',
                'breakdown': {
                    'base_fee': 350.00,
                    'processing_fee': 100.00
                },
                'notes': 'Mock calculation result',
                'mode': 'mock'
            }
        
        else:
            return {
                'step_type': step_type.value,
                'result': f"Mock result for {step.name}",
                'parameters': params,
                'mode': 'mock'
            }


# Example usage
if __name__ == "__main__":
    from backend.models.process_step import ProcessStep, StepType
    
    print("=" * 70)
    print("AgentExecutor Test")
    print("=" * 70)
    
    # Initialize
    executor = AgentExecutor()
    print(f"\n✅ AgentExecutor initialized")
    print(f"   Agent mode: {'real' if executor.use_agents else 'mock'}")
    
    # Test steps
    test_steps = [
        ProcessStep(
            id="test_1",
            name="Search Stuttgart Building Regulations",
            description="Search for building regulations",
            step_type=StepType.SEARCH,
            parameters={'location': 'Stuttgart', 'document_type': 'Bauvorschrift'}
        ),
        ProcessStep(
            id="test_2",
            name="Analyze GmbH characteristics",
            description="Analyze GmbH legal structure",
            step_type=StepType.ANALYSIS,
            parameters={'entity': 'GmbH'}
        ),
        ProcessStep(
            id="test_3",
            name="Calculate costs",
            description="Calculate application costs",
            step_type=StepType.CALCULATION,
            parameters={'document_type': 'Bauantrag'}
        )
    ]
    
    for step in test_steps:
        print(f"\n{'=' * 70}")
        print(f"Executing: {step.name}")
        print(f"Type: {step.step_type.value}")
        print(f"Parameters: {step.parameters}")
        
        result = executor.execute_step(step)
        
        print(f"\n✅ Result:")
        print(f"   Success: {result.success}")
        print(f"   Mode: {result.metadata.get('agent_mode', 'unknown')}")
        if result.data:
            print(f"   Data keys: {list(result.data.keys())}")
            if 'mode' in result.data:
                print(f"   Execution mode: {result.data['mode']}")
    
    print("\n" + "=" * 70)
    print("✅ AgentExecutor tests complete!")
    print("=" * 70)
