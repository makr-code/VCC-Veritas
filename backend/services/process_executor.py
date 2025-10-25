"""
Process Executor Service

Executes a ProcessTree by coordinating step execution with optimal parallelism.
Uses DependencyResolver for execution order and ThreadPoolExecutor for parallel steps.

The executor:
1. Gets execution plan from DependencyResolver
2. Executes steps in parallel groups
3. Tracks step status (pending → running → completed/failed)
4. Aggregates results into final response

Author: Veritas AI
Date: 2025-10-14
Version: 1.0
"""

import logging
import sys
import os
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import time

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.models.process_step import ProcessStep, StepStatus, StepResult, StepType
from backend.models.process_tree import ProcessTree
from backend.agents.framework.dependency_resolver import DependencyResolver

# Import streaming progress models
try:
    from backend.models.streaming_progress import (
        ProgressCallback, ProgressEvent, EventType, ProgressStatus,
        create_plan_started_event, create_step_started_event,
        create_step_progress_event, create_step_completed_event,
        create_step_failed_event, create_plan_completed_event
    )
    STREAMING_AVAILABLE = True
except ImportError:
    STREAMING_AVAILABLE = False
    logging.warning("⚠️ Streaming progress not available")

# Import AgentExecutor for real agent execution
try:
    from backend.services.agent_executor import AgentExecutor
    AGENT_EXECUTOR_AVAILABLE = True
except ImportError:
    AGENT_EXECUTOR_AVAILABLE = False
    logging.warning("⚠️ AgentExecutor not available - using mock mode")

# Import RAG Service for real document retrieval
try:
    from backend.services.rag_service import RAGService
    from backend.models.document_source import DocumentSource, SourceCitation, CitationConfidence
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    logging.warning("⚠️ RAG Service not available - using mock data")

# Import RerankerService for semantic re-ranking
try:
    from backend.services.reranker_service import RerankerService, ScoringMode
    RERANKER_AVAILABLE = True
except ImportError:
    RERANKER_AVAILABLE = False
    logging.warning("⚠️ RerankerService not available - reranking disabled")

# Import HypothesisService for query analysis (Phase 5)
try:
    from backend.services.hypothesis_service import HypothesisService
    from backend.models.hypothesis import Hypothesis, ConfidenceLevel
    HYPOTHESIS_AVAILABLE = True
except ImportError:
    HYPOTHESIS_AVAILABLE = False
    logging.warning("⚠️ HypothesisService not available - skipping query analysis")

logger = logging.getLogger(__name__)


class ProcessExecutor:
    """
    Executes a ProcessTree with optimal parallelism.
    
    The executor uses DependencyResolver to determine execution order and
    ThreadPoolExecutor to run independent steps in parallel.
    
    Features:
    - Parallel execution of independent steps
    - Error handling with optional retry
    - Step status tracking
    - Result aggregation
    - Execution time tracking
    
    Example:
        >>> executor = ProcessExecutor(max_workers=4)
        >>> result = executor.execute_process(tree)
        >>> # Returns: ProcessResult with aggregated data
    """
    
    def __init__(self, max_workers: int = 4, retry_failed: bool = False, use_agents: bool = True, 
                 rag_service: Optional['RAGService'] = None,
                 enable_hypothesis: bool = True,
                 enable_reranking: bool = True):
        """
        Initialize ProcessExecutor.
        
        Args:
            max_workers: Maximum number of parallel workers
            retry_failed: Whether to retry failed steps
            use_agents: Whether to use real agents (True) or mock mode (False)
            rag_service: Optional RAG service for document retrieval
            enable_hypothesis: Whether to enable hypothesis generation (Phase 5 feature)
            enable_reranking: Whether to enable semantic re-ranking (default: True)
        """
        self.max_workers = max_workers
        self.retry_failed = retry_failed
        self.use_agents = use_agents and AGENT_EXECUTOR_AVAILABLE
        self.streaming_available = STREAMING_AVAILABLE
        self.enable_hypothesis = enable_hypothesis and HYPOTHESIS_AVAILABLE
        self.enable_reranking = enable_reranking and RERANKER_AVAILABLE
        
        # Initialize RAG Service
        self.rag_service = rag_service
        if rag_service:
            logger.info("✅ RAG Service enabled for document retrieval")
        elif RAG_AVAILABLE:
            # Auto-initialize RAG service if not provided
            try:
                self.rag_service = RAGService()
                logger.info("✅ RAG Service auto-initialized")
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize RAG Service: {e}")
                self.rag_service = None
        
        # Initialize RerankerService if enabled
        self.reranker_service = None
        if self.enable_reranking:
            try:
                self.reranker_service = RerankerService(
                    model_name="llama3.1:8b",
                    scoring_mode=ScoringMode.COMBINED,
                    temperature=0.1
                )
                logger.info("✅ RerankerService enabled for semantic re-ranking")
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize RerankerService: {e}")
                self.enable_reranking = False
        
        # Initialize AgentExecutor if available
        if self.use_agents:
            try:
                self.agent_executor = AgentExecutor()
                logger.info(f"✅ ProcessExecutor with real agents (workers={max_workers})")
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize AgentExecutor: {e}")
                self.use_agents = False
                logger.info(f"📋 ProcessExecutor fallback to mock mode (workers={max_workers})")
        else:
            logger.info(f"📋 ProcessExecutor in mock mode (workers={max_workers})")
        
        # Initialize HypothesisService if enabled (Phase 5)
        self.hypothesis_service = None
        if self.enable_hypothesis:
            try:
                self.hypothesis_service = HypothesisService(model_name="llama3.1:8b")
                logger.info("✅ HypothesisService enabled for query analysis (Phase 5)")
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize HypothesisService: {e}")
                self.enable_hypothesis = False

    
    def execute_process(self, tree: ProcessTree, 
                       progress_callback: Optional['ProgressCallback'] = None) -> Dict[str, Any]:
        """
        Execute a complete ProcessTree.
        
        Args:
            tree: ProcessTree to execute
            progress_callback: Optional callback for progress updates
            
        Returns:
            ProcessResult dictionary with:
                - success: bool
                - data: Dict with aggregated results
                - execution_time: float (seconds)
                - steps_completed: int
                - steps_failed: int
                - step_results: Dict[step_id, StepResult]
                - hypothesis: Optional[Hypothesis] (Phase 5)
        """
        logger.info(f"Starting process execution: {tree.query}")
        start_time = time.time()
        
        # Phase 5: Generate hypothesis before execution
        hypothesis = None
        if self.enable_hypothesis and self.hypothesis_service:
            try:
                logger.info("🔍 Generating query hypothesis (Phase 5)...")
                
                # Get RAG context if available
                rag_context = None
                if self.rag_service:
                    try:
                        # Quick RAG search for context (limit to 3 results)
                        search_results = self.rag_service.search(tree.query, top_k=3)
                        if search_results and "results" in search_results:
                            rag_context = [
                                result.get("content", "")[:200]  # First 200 chars
                                for result in search_results["results"]
                            ]
                    except Exception as e:
                        logger.warning(f"⚠️ RAG context retrieval failed: {e}")
                
                # Generate hypothesis
                hypothesis = self.hypothesis_service.generate_hypothesis(
                    query=tree.query,
                    rag_context=rag_context
                )
                
                logger.info(f"✅ Hypothesis: type={hypothesis.question_type.value}, "
                           f"confidence={hypothesis.confidence.value}, "
                           f"gaps={len(hypothesis.information_gaps)}")
                
                # Check if clarification is needed
                if hypothesis.requires_clarification():
                    logger.warning(f"⚠️ Query requires clarification ({len(hypothesis.information_gaps)} gaps)")
                    questions = hypothesis.get_clarification_questions()
                    for i, q in enumerate(questions, 1):
                        logger.info(f"   {i}. {q}")
                
            except Exception as e:
                logger.error(f"❌ Hypothesis generation failed: {e}")
                hypothesis = None
        
        # Emit plan started event
        total_steps = len(tree.steps)
        if progress_callback and self.streaming_available:
            progress_callback.emit(create_plan_started_event(total_steps, tree.query))
        
        # Step 1: Convert ProcessTree to DependencyResolver format
        resolver_steps = self._convert_to_resolver_format(tree)
        
        # Step 2: Create DependencyResolver and get execution plan
        resolver = DependencyResolver(resolver_steps)
        execution_plan = resolver.get_execution_plan()
        
        logger.info(f"Execution plan: {len(execution_plan)} levels")
        
        # Step 3: Execute each level sequentially, steps within level in parallel
        step_results = {}
        completed_steps = set()
        failed_steps = set()
        current_step_num = 0
        
        for level_num, level_steps in enumerate(execution_plan):
            logger.info(f"Executing level {level_num}: {len(level_steps)} steps")
            
            # Execute all steps in this level in parallel
            level_results = self._execute_parallel_group(
                tree, level_steps, current_step_num, total_steps, progress_callback
            )
            
            # Update current step number
            current_step_num += len(level_steps)
            
            # Update step results and tracking
            for step_id, result in level_results.items():
                step_results[step_id] = result
                
                # Update step in tree
                step = tree.get_step(step_id)
                if result.success:
                    step.mark_completed(result)
                    completed_steps.add(step_id)
                    logger.info(f"✅ Step completed: {step.name}")
                else:
                    step.mark_failed(result.error or "Unknown error")
                    failed_steps.add(step_id)
                    logger.error(f"❌ Step failed: {step.name} - {result.error}")
        
        # Step 4: Aggregate results
        execution_time = time.time() - start_time
        final_result = self._aggregate_results(tree, step_results, execution_time, hypothesis)
        
        # Emit plan completed event
        if progress_callback and self.streaming_available:
            progress_callback.emit(create_plan_completed_event(
                total_steps, len(completed_steps), len(failed_steps), execution_time
            ))
        
        logger.info(f"Process execution complete: {len(completed_steps)} completed, "
                   f"{len(failed_steps)} failed, {execution_time:.2f}s")
        
        return final_result
    
    def _convert_to_resolver_format(self, tree: ProcessTree) -> List[Dict[str, Any]]:
        """
        Convert ProcessTree to DependencyResolver format.
        
        Args:
            tree: ProcessTree
            
        Returns:
            List of step definitions for DependencyResolver
        """
        steps = []
        for step_id, step in tree.steps.items():
            steps.append({
                "step_id": step.id,
                "depends_on": step.dependencies,
                "name": step.name,
                "step_type": step.step_type.value,
                "parameters": step.parameters
            })
        return steps
    
    def _execute_parallel_group(self, tree: ProcessTree, 
                               step_ids: List[str],
                               base_step_num: int = 0,
                               total_steps: int = 0,
                               progress_callback: Optional['ProgressCallback'] = None) -> Dict[str, StepResult]:
        """
        Execute a group of steps in parallel.
        
        Args:
            tree: ProcessTree
            step_ids: List of step IDs to execute
            base_step_num: Starting step number for this group
            total_steps: Total number of steps in entire plan
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dictionary of step_id -> StepResult
        """
        results = {}
        
        # Emit step started events for all steps in this group
        if progress_callback and self.streaming_available:
            for i, step_id in enumerate(step_ids):
                step = tree.get_step(step_id)
                current_step = base_step_num + i + 1
                progress_callback.emit(create_step_started_event(
                    step_id, step.name, current_step, total_steps,
                    metadata={'step_type': step.step_type.value}
                ))
        
        # Use ThreadPoolExecutor for parallel execution
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all steps
            future_to_step = {
                executor.submit(
                    self._execute_step, 
                    tree.get_step(step_id),
                    base_step_num + i + 1,
                    total_steps,
                    progress_callback
                ): step_id
                for i, step_id in enumerate(step_ids)
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_step):
                step_id = future_to_step[future]
                try:
                    result = future.result()
                    results[step_id] = result
                except Exception as e:
                    logger.error(f"Exception in step {step_id}: {e}")
                    results[step_id] = StepResult(
                        success=False,
                        error=f"Exception: {str(e)}"
                    )
        
        return results
    
    def _execute_step(self, step: ProcessStep, 
                     current_step: int = 0,
                     total_steps: int = 0,
                     progress_callback: Optional['ProgressCallback'] = None) -> StepResult:
        """
        Execute a single step.
        
        Uses AgentExecutor if available, otherwise falls back to mock mode.
        
        Args:
            step: ProcessStep to execute
            current_step: Current step number (for progress)
            total_steps: Total number of steps (for progress)
            progress_callback: Optional callback for progress updates
            
        Returns:
            StepResult
        """
        logger.info(f"Executing step: {step.name} ({step.step_type.value})")
        step_start_time = time.time()
        
        # Mark step as running
        step.mark_running()
        
        try:
            # Use AgentExecutor if available
            if self.use_agents and hasattr(self, 'agent_executor'):
                # Emit progress update (agents starting)
                if progress_callback and self.streaming_available:
                    progress_callback.emit(create_step_progress_event(
                        step.id, step.name, current_step, total_steps, 25.0,
                        message=f"Using agents for {step.name}..."
                    ))
                
                result = self.agent_executor.execute_step(step)
                
                # Emit progress update (agents completed)
                if progress_callback and self.streaming_available:
                    progress_callback.emit(create_step_progress_event(
                        step.id, step.name, current_step, total_steps, 90.0,
                        message=f"Agent execution completed"
                    ))
                
                logger.debug(f"Agent execution: {step.name} - Success: {result.success}")
                
                # Emit step completed event
                execution_time = time.time() - step_start_time
                if progress_callback and self.streaming_available:
                    if result.success:
                        progress_callback.emit(create_step_completed_event(
                            step.id, step.name, current_step, total_steps, 
                            execution_time, result.data
                        ))
                    else:
                        progress_callback.emit(create_step_failed_event(
                            step.id, step.name, current_step, total_steps,
                            result.error or "Unknown error"
                        ))
                
                return result
            
            # Fallback: Mock execution
            else:
                # Emit progress update (mock starting)
                if progress_callback and self.streaming_available:
                    progress_callback.emit(create_step_progress_event(
                        step.id, step.name, current_step, total_steps, 10.0,
                        message=f"Mock execution for {step.name}..."
                    ))
                
                # PHASE 4: Retrieve relevant documents via RAG
                documents = []
                if self.rag_service:
                    documents = self._retrieve_documents(step, max_results=5, min_relevance=0.3)
                    if documents:
                        logger.info(f"✅ Retrieved {len(documents)} documents for '{step.name}'")
                
                # Emit progress update (30% - after document retrieval)
                if progress_callback and self.streaming_available:
                    progress_callback.emit(create_step_progress_event(
                        step.id, step.name, current_step, total_steps, 30.0,
                        message=f"Retrieved {len(documents)} documents..."
                    ))
                
                # MOCK: Simulate execution time
                execution_time = self._simulate_step_execution(step)
                
                # Emit progress update (50%)
                if progress_callback and self.streaming_available:
                    progress_callback.emit(create_step_progress_event(
                        step.id, step.name, current_step, total_steps, 50.0,
                        message=f"Processing {step.name}..."
                    ))
                
                # MOCK: Generate fake result based on step type
                # If we have real documents, include their content
                if documents:
                    data = self._generate_data_with_documents(step, documents)
                else:
                    data = self._generate_mock_data(step)
                
                # Emit progress update (90%)
                if progress_callback and self.streaming_available:
                    progress_callback.emit(create_step_progress_event(
                        step.id, step.name, current_step, total_steps, 90.0,
                        message=f"Finalizing {step.name}..."
                    ))
                
                # PHASE 4: Extract source citations
                citations = []
                if documents and RAG_AVAILABLE:
                    citations = self._extract_citations(documents)
                
                # Create successful result with sources
                result = StepResult(
                    success=True,
                    data=data,
                    execution_time=execution_time,
                    metadata={
                        'step_id': step.id,
                        'step_type': step.step_type.value,
                        'execution_mode': 'mock_with_rag' if documents else 'mock',
                        'timestamp': datetime.now().isoformat(),
                        'documents_retrieved': len(documents),
                        'citations': [c.to_dict() for c in citations] if citations else []
                    }
                )

            
            logger.debug(f"Step completed: {step.name} in {result.execution_time:.2f}s")
            
            # Emit step completed event (for mock mode)
            if progress_callback and self.streaming_available and not self.use_agents:
                progress_callback.emit(create_step_completed_event(
                    step.id, step.name, current_step, total_steps, 
                    result.execution_time, result.data
                ))
            
            return result
            
        except Exception as e:
            logger.error(f"Step execution failed: {step.name} - {e}")
            
            # Emit step failed event
            if progress_callback and self.streaming_available:
                progress_callback.emit(create_step_failed_event(
                    step.id, step.name, current_step, total_steps, str(e)
                ))
            
            return StepResult(
                success=False,
                error=str(e),
                metadata={'step_id': step.id}
            )
    
    def _simulate_step_execution(self, step: ProcessStep) -> float:
        """
        Simulate step execution with realistic delays.
        
        Args:
            step: ProcessStep
            
        Returns:
            Execution time in seconds
        """
        # Simulate different execution times for different step types
        time_ranges = {
            StepType.SEARCH: (0.1, 0.3),
            StepType.RETRIEVAL: (0.05, 0.15),
            StepType.ANALYSIS: (0.2, 0.5),
            StepType.SYNTHESIS: (0.15, 0.3),
            StepType.VALIDATION: (0.05, 0.1),
            StepType.TRANSFORMATION: (0.05, 0.1),
            StepType.CALCULATION: (0.1, 0.2),
            StepType.COMPARISON: (0.2, 0.4),
            StepType.AGGREGATION: (0.15, 0.3),
            StepType.OTHER: (0.1, 0.2)
        }
        
        min_time, max_time = time_ranges.get(step.step_type, (0.1, 0.2))
        
        # Use average time for simulation
        sleep_time = (min_time + max_time) / 2
        time.sleep(sleep_time)
        
        return sleep_time
    
    def _generate_data_with_documents(
        self,
        step: ProcessStep,
        documents: List['DocumentSource']
    ) -> Dict[str, Any]:
        """
        Generate step data using real retrieved documents.
        
        Combines mock structure with real document content for more
        realistic results.
        
        Args:
            step: ProcessStep
            documents: Retrieved documents from RAG
            
        Returns:
            Data dictionary with real document content
        """
        # Build context from documents
        context = self._build_context(documents, max_tokens=1000)
        
        # Get base mock data
        mock_data = self._generate_mock_data(step)
        
        # Enhance with real document information
        enhanced_data = {
            **mock_data,
            'rag_enabled': True,
            'documents_retrieved': len(documents),
            'document_sources': [
                {
                    'id': doc.document_id,
                    'title': doc.title,
                    'relevance': doc.relevance_score.hybrid,
                    'excerpt': doc.get_excerpt(150)
                }
                for doc in documents
            ],
            'context_preview': context[:200] + "..." if len(context) > 200 else context
        }
        
        # Override mock content with real document excerpts for specific step types
        if step.step_type == StepType.RETRIEVAL:
            enhanced_data['content'] = context
        elif step.step_type == StepType.SEARCH:
            enhanced_data['documents'] = [doc.title for doc in documents]
            enhanced_data['relevance_scores'] = [doc.relevance_score.hybrid for doc in documents]
        
        return enhanced_data
    
    def _generate_mock_data(self, step: ProcessStep) -> Dict[str, Any]:
        """
        Generate mock data for a step based on its type and parameters.
        
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
                'documents': [
                    f"Document {i+1}" for i in range(5)
                ],
                'relevance_scores': [0.95, 0.87, 0.82, 0.76, 0.71]
            }
        
        elif step_type == StepType.RETRIEVAL:
            return {
                'documents_retrieved': 3,
                'content': f"Mock content for {step.name}",
                'metadata': params
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
                'summary': f"Analysis of {entity}"
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
                'recommendation': f"Choose {entities[0]} if condition X, else {entities[1]}"
            }
        
        elif step_type == StepType.SYNTHESIS:
            return {
                'checklist': [
                    "Item 1: Check requirements",
                    "Item 2: Prepare documents",
                    "Item 3: Submit application"
                ],
                'summary': f"Synthesized result for {step.name}",
                'sources': params
            }
        
        elif step_type == StepType.CALCULATION:
            return {
                'calculated_value': 450.00,
                'currency': 'EUR',
                'breakdown': {
                    'base_fee': 350.00,
                    'processing_fee': 100.00
                },
                'notes': 'Mock calculation result'
            }
        
        else:
            return {
                'step_type': step_type.value,
                'result': f"Mock result for {step.name}",
                'parameters': params
            }
    
    def _aggregate_results(self, tree: ProcessTree, 
                          step_results: Dict[str, StepResult],
                          execution_time: float,
                          hypothesis: Optional['Hypothesis'] = None) -> Dict[str, Any]:
        """
        Aggregate step results into final process result.
        
        Args:
            tree: ProcessTree
            step_results: Dictionary of step_id -> StepResult
            execution_time: Total execution time
            hypothesis: Optional hypothesis from Phase 5
            
        Returns:
            ProcessResult dictionary
        """
        # Count successes and failures
        completed = sum(1 for r in step_results.values() if r.success)
        failed = len(step_results) - completed
        
        # Collect all data from successful steps
        aggregated_data = {}
        for step_id, result in step_results.items():
            if result.success and result.data:
                step = tree.get_step(step_id)
                aggregated_data[step.name] = result.data
        
        # Get leaf steps (final results)
        leaf_steps = tree.get_leaf_steps()
        final_results = {}
        for step in leaf_steps:
            if step.id in step_results and step_results[step.id].success:
                final_results[step.name] = step_results[step.id].data
        
        # Build result dictionary
        result = {
            'success': failed == 0,
            'query': tree.query,
            'data': aggregated_data,
            'final_results': final_results,
            'execution_time': execution_time,
            'steps_total': len(step_results),
            'steps_completed': completed,
            'steps_failed': failed,
            'step_results': {
                step_id: result.to_dict() 
                for step_id, result in step_results.items()
            },
            'tree_metadata': tree.metadata,
            'timestamp': datetime.now().isoformat()
        }
        
        # Add hypothesis if available (Phase 5)
        if hypothesis:
            result['hypothesis'] = hypothesis.to_dict()
            result['hypothesis_metadata'] = {
                'question_type': hypothesis.question_type.value,
                'confidence': hypothesis.confidence.value,
                'requires_clarification': hypothesis.requires_clarification(),
                'has_critical_gaps': hypothesis.has_critical_gaps(),
                'information_gaps_count': len(hypothesis.information_gaps)
            }
        
        return result
    
    # ============================================================================
    # RAG Integration Methods (Phase 4)
    # ============================================================================
    
    def _retrieve_documents(
        self,
        step: ProcessStep,
        max_results: int = 5,
        min_relevance: float = 0.3
    ) -> List['DocumentSource']:
        """
        Retrieve relevant documents for a step using RAG Service.
        
        Args:
            step: ProcessStep to retrieve documents for
            max_results: Maximum number of documents to retrieve
            min_relevance: Minimum relevance score threshold
            
        Returns:
            List of DocumentSource objects
        """
        if not self.rag_service:
            logger.debug(f"RAG Service not available for step: {step.name}")
            return []
        
        try:
            # Reformulate query based on step type and description
            query = self._reformulate_query_for_step(step)
            logger.info(f"RAG query for step '{step.name}': {query}")
            
            # Perform hybrid search
            from backend.services.rag_service import SearchFilters
            filters = SearchFilters(
                max_results=max_results,
                min_relevance=min_relevance
            )
            
            search_result = self.rag_service.hybrid_search(
                query=query,
                filters=filters
            )
            
            # Apply semantic re-ranking if enabled
            if self.enable_reranking and self.reranker_service and search_result.results:
                try:
                    # Prepare documents for reranking
                    docs_for_rerank = []
                    for result in search_result.results:
                        docs_for_rerank.append({
                            'document_id': result.document_id,
                            'content': result.content,
                            'relevance_score': result.relevance_score,
                            'metadata': result.metadata
                        })
                    
                    # Perform reranking
                    reranking_results = self.reranker_service.rerank(
                        query=query,
                        documents=docs_for_rerank,
                        top_k=max_results,
                        batch_size=5
                    )
                    
                    # Create mapping of document_id to reranking result
                    rerank_map = {r.document_id: r for r in reranking_results}
                    
                    # Update relevance scores with reranked scores
                    for result in search_result.results:
                        if result.document_id in rerank_map:
                            rerank = rerank_map[result.document_id]
                            # Store original score in metadata
                            if not hasattr(result.metadata, 'custom_fields'):
                                result.metadata.custom_fields = {}
                            result.metadata.custom_fields['original_score'] = result.relevance_score
                            result.metadata.custom_fields['score_delta'] = rerank.score_delta
                            result.metadata.custom_fields['rerank_confidence'] = rerank.confidence
                            # Update with reranked score
                            result.relevance_score = rerank.reranked_score
                    
                    # Re-sort by updated scores
                    search_result.results.sort(key=lambda x: x.relevance_score, reverse=True)
                    
                    logger.info(f"Re-ranking applied: {len(reranking_results)} documents re-scored")
                    
                except Exception as e:
                    logger.warning(f"Re-ranking failed, using original scores: {e}")
            
            # Convert search results to DocumentSource objects
            documents = []
            for result in search_result.results:
                # Create DocumentSource from search result
                doc = DocumentSource(
                    document_id=result.document_id,
                    title=result.metadata.title,
                    content=result.content,
                    source_type=result.metadata.source_type,
                    relevance_score=result.relevance_score,
                    file_path=result.metadata.file_path,
                    page_count=result.metadata.page_count,
                    tags=result.metadata.tags
                )
                documents.append(doc)
            
            logger.info(f"Retrieved {len(documents)} documents for step: {step.name}")
            return documents
            
        except Exception as e:
            logger.error(f"Failed to retrieve documents for step {step.name}: {e}")
            return []
    
    def _reformulate_query_for_step(self, step: ProcessStep) -> str:
        """
        Reformulate query based on step type and description.
        
        Different step types need different query formulations:
        - RESEARCH: Broad search for general information
        - DATA_RETRIEVAL: Specific data points
        - ANALYSIS: Analytical documents
        - VALIDATION: Legal/regulatory texts
        
        Args:
            step: ProcessStep
            
        Returns:
            Reformulated query string
        """
        step_type = step.step_type
        description = step.description
        name = step.name
        
        # Step type specific query prefixes
        if step_type == StepType.SEARCH:
            return f"Information about {description}"
        elif step_type == StepType.RETRIEVAL:
            return f"Data and facts about {description}"
        elif step_type == StepType.ANALYSIS:
            return f"Analysis and evaluation of {description}"
        elif step_type == StepType.VALIDATION:
            return f"Legal requirements and regulations for {description}"
        elif step_type == StepType.SYNTHESIS:
            return f"Documentation and guides for {description}"
        else:
            # Default: Use step name + description
            return f"{name}: {description}"
    
    def _build_context(
        self,
        documents: List['DocumentSource'],
        max_tokens: int = 2000
    ) -> str:
        """
        Build context string from documents for LLM input.
        
        Formats documents into a context string suitable for LLM consumption,
        respecting token limits.
        
        Args:
            documents: List of DocumentSource objects
            max_tokens: Maximum tokens for context (approximate)
            
        Returns:
            Formatted context string
        """
        if not documents:
            return ""
        
        context_parts = []
        current_tokens = 0
        chars_per_token = 4  # Rough estimate
        max_chars = max_tokens * chars_per_token
        
        for i, doc in enumerate(documents, 1):
            # Format: [Source N] Title\nContent excerpt
            source_header = f"[Source {i}] {doc.title}\n"
            excerpt = doc.get_excerpt(500)  # Limit each excerpt
            
            part = source_header + excerpt
            part_tokens = len(part) // chars_per_token
            
            if current_tokens + part_tokens > max_tokens:
                logger.debug(f"Context token limit reached ({max_tokens}), using {i-1} documents")
                break
            
            context_parts.append(part)
            current_tokens += part_tokens
        
        context = "\n\n".join(context_parts)
        logger.debug(f"Built context: {len(context)} chars, ~{current_tokens} tokens from {len(context_parts)} documents")
        return context
    
    def _extract_citations(
        self,
        documents: List['DocumentSource']
    ) -> List['SourceCitation']:
        """
        Extract source citations from documents.
        
        Creates SourceCitation objects for each document with
        confidence levels and page numbers (if available).
        
        Args:
            documents: List of DocumentSource objects
            
        Returns:
            List of SourceCitation objects
        """
        citations = []
        
        for doc in documents:
            # Get confidence level from relevance score
            confidence = doc.get_confidence()
            
            # Extract page number from metadata if available
            page_number = None
            if doc.custom_metadata and 'page_number' in doc.custom_metadata:
                page_number = doc.custom_metadata['page_number']
            
            # Create citation with excerpt
            citation = SourceCitation(
                source=doc,
                confidence=confidence,
                page_number=page_number,
                excerpt=doc.get_excerpt(200)
            )
            
            citations.append(citation)
        
        logger.debug(f"Extracted {len(citations)} citations")
        return citations


# Example usage
if __name__ == "__main__":
    from backend.services.nlp_service import NLPService
    from backend.services.process_builder import ProcessBuilder
    
    print("=" * 70)
    print("ProcessExecutor Test Examples")
    print("=" * 70)
    
    # Initialize services
    nlp = NLPService()
    builder = ProcessBuilder(nlp)
    executor = ProcessExecutor(max_workers=4)
    
    # Test queries
    test_queries = [
        "Bauantrag für Stuttgart",
        "Unterschied zwischen GmbH und AG",
        "Wie viel kostet ein Bauantrag?"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'=' * 70}")
        print(f"Test {i}: {query}")
        print('=' * 70)
        
        # Build process tree
        tree = builder.build_process_tree(query)
        print(f"\n📋 Process Tree:")
        print(f"   Steps: {tree.total_steps}")
        print(f"   Levels: {len(tree.execution_order)}")
        print(f"   Estimated time: {tree.estimated_time:.1f}s")
        
        # Execute process
        print(f"\n🚀 Executing process...")
        result = executor.execute_process(tree)
        
        # Display results
        print(f"\n✅ Execution complete!")
        print(f"   Success: {result['success']}")
        print(f"   Execution time: {result['execution_time']:.2f}s")
        print(f"   Steps completed: {result['steps_completed']}/{result['steps_total']}")
        print(f"   Steps failed: {result['steps_failed']}")
        
        print(f"\n📊 Final Results:")
        for step_name, data in result['final_results'].items():
            print(f"   - {step_name}:")
            if isinstance(data, dict):
                for key, value in list(data.items())[:3]:  # Show first 3 items
                    print(f"       {key}: {value}")
            else:
                print(f"       {data}")
        
        print(f"\n📝 All Step Data:")
        for step_name, data in result['data'].items():
            print(f"   - {step_name}: {list(data.keys()) if isinstance(data, dict) else type(data).__name__}")
    
    print("\n" + "=" * 70)
    print("✅ All ProcessExecutor tests completed!")
    print("=" * 70)
