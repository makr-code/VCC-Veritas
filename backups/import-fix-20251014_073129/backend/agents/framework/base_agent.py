"""
VERITAS Agent Framework - BaseAgent Implementation
==================================================

Abstract base class for all VERITAS agents with schema-based execution.

Based on: codespaces-blank mockup agent system
Integration: Multi-agent research plan execution with database persistence

Key Features:
- Schema-based plan execution
- Step-by-step result tracking
- Database persistence via SQLite
- Quality metrics and error handling
- VERITAS-specific tool integration (UDS3, Phase5 Hybrid Search)

Author: VERITAS Development Team
Created: 2025
"""

import json
import sqlite3
import logging
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from uuid import uuid4

# Handle relative imports for package vs standalone execution
try:
    from .schema_validation import validate_research_plan, validate_step
    from .state_machine import StateMachine, PlanState, StateTransition, StateTransitionError
    from .dependency_resolver import DependencyResolver, DependencyError
    from .retry_handler import RetryHandler, RetryConfig, RetryStrategy
    from .quality_gate import QualityGate, QualityPolicy, GateDecision
    from .agent_monitoring import AgentMonitor
except ImportError:
    from schema_validation import validate_research_plan, validate_step
    from state_machine import StateMachine, PlanState, StateTransition, StateTransitionError
    from dependency_resolver import DependencyResolver, DependencyError
    from retry_handler import RetryHandler, RetryConfig, RetryStrategy
    from quality_gate import QualityGate, QualityPolicy, GateDecision
    from agent_monitoring import AgentMonitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Abstract base agent for VERITAS research plan execution.
    
    All VERITAS agents should inherit from this class and implement:
    - execute_step(): Domain-specific step execution logic
    - get_agent_type(): Return agent type identifier
    - get_capabilities(): Return list of agent capabilities
    
    Attributes:
        agent_id: Unique agent identifier
        db_path: Path to SQLite database
        config: Agent configuration dictionary
    
    Example:
        >>> class EnvironmentalAgent(BaseAgent):
        ...     def execute_step(self, step, context):
        ...         # Domain-specific logic
        ...         return {"status": "success", "data": {...}}
        ...     
        ...     def get_agent_type(self):
        ...         return "environmental"
        ...     
        ...     def get_capabilities(self):
        ...         return ["regulation_search", "compliance_check"]
    """
    
    def __init__(
        self,
        agent_id: Optional[str] = None,
        db_path: Optional[Path] = None,
        config: Optional[Dict[str, Any]] = None,
        quality_policy: Optional[QualityPolicy] = None,
        enable_monitoring: bool = True
    ):
        """
        Initialize base agent.
        
        Args:
            agent_id: Unique agent identifier (auto-generated if None)
            db_path: Path to SQLite database (default: data/agent_framework.db)
            config: Agent configuration dictionary
            quality_policy: Quality gate policy (optional)
            enable_monitoring: Enable monitoring (default: True)
        """
        self.agent_id = agent_id or str(uuid4())
        self.db_path = db_path or Path(__file__).parent.parent.parent.parent / "data" / "agent_framework.db"
        self.config = config or {}
        self._connection = None
        self._state_machines: Dict[str, StateMachine] = {}  # plan_id -> StateMachine
        
        # Initialize quality gate if policy provided
        self.quality_gate = None
        if quality_policy:
            self.quality_gate = QualityGate(quality_policy)
            logger.info(f"Quality gate enabled with policy: min={quality_policy.min_quality}")
        
        # Initialize monitoring
        self.monitor = None
        if enable_monitoring:
            self.monitor = AgentMonitor(
                agent_id=self.agent_id,
                agent_type=self.get_agent_type()
            )
            logger.info(f"Monitoring enabled for agent {self.agent_id}")
        
        logger.info(f"Initialized {self.get_agent_type()} agent: {self.agent_id}")
    
    @abstractmethod
    def execute_step(
        self,
        step: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a single research plan step (domain-specific logic).
        
        This method MUST be implemented by each agent subclass with
        domain-specific execution logic.
        
        Args:
            step: Step definition from research plan
                {
                    "step_id": str,
                    "step_number": int,
                    "agent_type": str,
                    "action": str,
                    "parameters": Dict[str, Any],
                    "tools": List[str],
                    "expected_output": str,
                    "dependencies": List[str]
                }
            context: Execution context including previous results
                {
                    "plan_id": str,
                    "previous_results": Dict[str, Any],
                    "uds3_databases": List[str],
                    "phase5_enabled": bool,
                    "security_level": str
                }
        
        Returns:
            Result dictionary:
                {
                    "status": "success" | "failed",
                    "data": Any,  # Domain-specific result data
                    "quality_score": float,  # 0.0-1.0
                    "sources": List[str],
                    "metadata": Dict[str, Any],
                    "error": Optional[str]
                }
        
        Raises:
            NotImplementedError: If not implemented by subclass
        
        Example:
            >>> def execute_step(self, step, context):
            ...     action = step["action"]
            ...     params = step["parameters"]
            ...     
            ...     if action == "search_regulations":
            ...         results = self._search_regulations(params)
            ...         return {
            ...             "status": "success",
            ...             "data": results,
            ...             "quality_score": 0.95,
            ...             "sources": ["UDS3-environmental"],
            ...             "metadata": {"count": len(results)}
            ...         }
            ...     else:
            ...         return {
            ...             "status": "failed",
            ...             "error": f"Unknown action: {action}"
            ...         }
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement execute_step()"
        )
    
    @abstractmethod
    def get_agent_type(self) -> str:
        """
        Return agent type identifier.
        
        Returns:
            Agent type string (e.g., "environmental", "financial", "orchestrator")
        
        Example:
            >>> def get_agent_type(self):
            ...     return "environmental"
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement get_agent_type()"
        )
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """
        Return list of agent capabilities.
        
        Returns:
            List of capability strings
        
        Example:
            >>> def get_capabilities(self):
            ...     return [
            ...         "regulation_search",
            ...         "compliance_check",
            ...         "environmental_impact_analysis"
            ...     ]
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement get_capabilities()"
        )
    
    def execute(
        self,
        plan: Dict[str, Any],
        start_step: Optional[int] = None,
        end_step: Optional[int] = None,
        parallel: bool = True,
        max_workers: int = 4
    ) -> Dict[str, Any]:
        """
        Execute research plan (or step range) with database persistence.
        
        This is the main execution method that:
        1. Validates the research plan
        2. Creates plan record in database
        3. Executes steps (parallel if dependencies allow and parallel=True)
        4. Stores results in database
        5. Returns execution summary
        
        Args:
            plan: Research plan document (validated against JSON schema)
            start_step: Optional starting step number (1-indexed)
            end_step: Optional ending step number (1-indexed)
            parallel: Enable parallel execution (default: True)
            max_workers: Maximum parallel workers (default: 4)
        
        Returns:
            Execution result:
                {
                    "plan_id": str,
                    "status": "completed" | "failed" | "partial",
                    "steps_executed": int,
                    "steps_succeeded": int,
                    "steps_failed": int,
                    "total_quality_score": float,
                    "results": Dict[str, Any],  # Step ID -> result
                    "execution_time_ms": int,
                    "execution_mode": "parallel" | "sequential",
                    "max_parallelism": int,
                    "errors": List[str]
                }
        
        Example:
            >>> plan = {
            ...     "plan_id": "env_001",
            ...     "research_question": "What are the regulations?",
            ...     "schema_name": "environmental",
            ...     "steps": [...]
            ... }
            >>> result = agent.execute(plan)
            >>> print(f"Executed {result['steps_executed']} steps")
        """
        start_time = datetime.utcnow()
        
        # Validate plan
        is_valid, errors = validate_research_plan(plan)
        if not is_valid:
            logger.error(f"Invalid research plan: {errors}")
            return {
                "plan_id": plan.get("plan_id", "unknown"),
                "status": "failed",
                "steps_executed": 0,
                "steps_succeeded": 0,
                "steps_failed": 0,
                "total_quality_score": 0.0,
                "results": {},
                "execution_time_ms": 0,
                "errors": errors
            }
        
        plan_id = plan["plan_id"]
        steps = plan["steps"]
        
        # Initialize state machine for this plan
        state_machine = StateMachine(
            plan_id,
            on_state_change=lambda t: self._on_state_change(t)
        )
        self._state_machines[plan_id] = state_machine
        
        # Determine step range
        start_idx = (start_step - 1) if start_step else 0
        end_idx = end_step if end_step else len(steps)
        steps_to_execute = steps[start_idx:end_idx]
        
        logger.info(
            f"Executing plan {plan_id}: {len(steps_to_execute)} steps "
            f"(range: {start_idx + 1}-{end_idx})"
        )
        
        # Create plan record
        self._create_plan_record(plan)
        
        # Transition to RUNNING state
        try:
            state_machine.transition_to(
                PlanState.RUNNING,
                "Execution started",
                metadata={"plan_id": plan_id}
            )
        except StateTransitionError as e:
            logger.error(f"Cannot start execution: {e}")
            return {
                "plan_id": plan_id,
                "status": "failed",
                "steps_executed": 0,
                "steps_succeeded": 0,
                "steps_failed": 0,
                "total_quality_score": 0.0,
                "results": {},
                "execution_time_ms": 0,
                "errors": [str(e)]
            }
        
        # Initialize execution context
        context = {
            "plan_id": plan_id,
            "previous_results": {},
            "uds3_databases": plan.get("veritas_extensions", {}).get("uds3_databases", []),
            "phase5_enabled": plan.get("veritas_extensions", {}).get("phase5_hybrid_search", False),
            "security_level": plan.get("veritas_extensions", {}).get("security_level", "public")
        }
        
        # Execute steps (parallel or sequential)
        if parallel and len(steps_to_execute) > 1:
            execution_result = self._execute_parallel(
                plan_id,
                steps_to_execute,
                context,
                max_workers
            )
            execution_mode = "parallel"
        else:
            execution_result = self._execute_sequential(
                plan_id,
                steps_to_execute,
                context
            )
            execution_mode = "sequential"
        
        results = execution_result["results"]
        succeeded = execution_result["succeeded"]
        failed = execution_result["failed"]
        total_quality = execution_result["total_quality"]
        errors_list = execution_result["errors"]
        max_parallelism = execution_result.get("max_parallelism", 1)
        
        # Calculate final status
        total_executed = succeeded + failed
        avg_quality = (total_quality / succeeded) if succeeded > 0 else 0.0
        
        if failed == 0:
            status = "completed"
            target_state = PlanState.COMPLETED
        elif succeeded == 0:
            status = "failed"
            target_state = PlanState.FAILED
        else:
            status = "partial"
            target_state = PlanState.COMPLETED  # Partial completion still counts as completed
        
        execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        # Transition to final state
        try:
            state_machine.transition_to(
                target_state,
                f"Execution finished: {succeeded}/{total_executed} steps succeeded",
                metadata={
                    "plan_id": plan_id,
                    "steps_succeeded": succeeded,
                    "steps_failed": failed,
                    "quality_score": avg_quality,
                    "execution_time_ms": execution_time
                }
            )
        except StateTransitionError as e:
            logger.warning(f"State transition warning: {e}")
        
        # Update plan status
        self._update_plan_status(plan_id, status, avg_quality, execution_time)
        
        logger.info(
            f"Plan {plan_id} {status}: {succeeded}/{total_executed} steps succeeded "
            f"(quality: {avg_quality:.2f}, time: {execution_time}ms)"
        )
        
        return {
            "plan_id": plan_id,
            "status": status,
            "steps_executed": total_executed,
            "steps_succeeded": succeeded,
            "steps_failed": failed,
            "total_quality_score": avg_quality,
            "results": results,
            "execution_time_ms": execution_time,
            "execution_mode": execution_mode,
            "max_parallelism": max_parallelism,
            "errors": errors_list
        }
    
    def _execute_sequential(
        self,
        plan_id: str,
        steps: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute steps sequentially (original behavior).
        
        Args:
            plan_id: Plan identifier
            steps: Steps to execute
            context: Execution context
        
        Returns:
            Execution results dictionary
        """
        results = {}
        succeeded = 0
        failed = 0
        total_quality = 0.0
        errors_list = []
        
        for step in steps:
            step_id = step["step_id"]
            step_number = step.get("step_index", 0) + 1
            logger.info(f"Executing step {step_number}: {step_id} (sequential)")
            
            try:
                # Validate step
                is_valid_step, step_errors = validate_step(step)
                if not is_valid_step:
                    raise ValueError(f"Invalid step: {step_errors}")
                
                # Get retry configuration from step or use defaults
                step_params = step.get("parameters", {})
                max_retries = step_params.get("max_retries", 3)
                
                # Create retry handler with step-specific config
                retry_config = RetryConfig(
                    max_retries=max_retries,
                    base_delay=1.0,
                    backoff_factor=2.0,
                    strategy=RetryStrategy.EXPONENTIAL,
                    jitter=True
                )
                retry_handler = RetryHandler(config=retry_config)
                
                # Execute with retry logic
                result = retry_handler.execute_with_retry(
                    func=self._execute_step_internal,
                    step_id=step_id,
                    max_retries=max_retries,
                    context=context,
                    step=step
                )
                
                # Store result
                self._store_step_result(plan_id, step, result)
                results[step_id] = result
                
                # Update context
                context["previous_results"][step_id] = result
                
                # Update metrics
                if result.get("status") == "success":
                    succeeded += 1
                    total_quality += result.get("quality_score", 0.0)
                else:
                    failed += 1
                    errors_list.append(
                        f"Step {step_number} ({step_id}): {result.get('error', 'Unknown error')}"
                    )
            
            except Exception as e:
                logger.error(f"Error executing step {step_id}: {e}", exc_info=True)
                failed += 1
                errors_list.append(f"Step {step_number} ({step_id}): {str(e)}")
                
                # Create failed result
                failed_result = {
                    "status": "failed",
                    "error": str(e),
                    "quality_score": 0.0,
                    "retry_count": step_params.get("max_retries", 3)  # Max retries exhausted
                }
                
                # Store failed result in DB
                self._store_step_result(plan_id, step, failed_result)
                results[step_id] = failed_result
        
        return {
            "results": results,
            "succeeded": succeeded,
            "failed": failed,
            "total_quality": total_quality,
            "errors": errors_list,
            "max_parallelism": 1
        }
    
    def _execute_parallel(
        self,
        plan_id: str,
        steps: List[Dict[str, Any]],
        context: Dict[str, Any],
        max_workers: int = 4
    ) -> Dict[str, Any]:
        """
        Execute steps in parallel based on dependencies.
        
        Uses DependencyResolver to determine execution groups and
        ThreadPoolExecutor for parallel execution.
        
        Args:
            plan_id: Plan identifier
            steps: Steps to execute
            context: Execution context
            max_workers: Maximum parallel workers
        
        Returns:
            Execution results dictionary
        """
        try:
            # Build dependency graph
            resolver = DependencyResolver(steps)
            execution_plan = resolver.get_execution_plan()
            max_parallelism = max(len(group) for group in execution_plan) if execution_plan else 1
            
            logger.info(
                f"Parallel execution: {len(execution_plan)} groups, "
                f"max parallelism: {max_parallelism}"
            )
        
        except DependencyError as e:
            logger.error(f"Dependency resolution failed: {e}")
            # Fall back to sequential execution
            return self._execute_sequential(plan_id, steps, context)
        
        results = {}
        succeeded = 0
        failed = 0
        total_quality = 0.0
        errors_list = []
        
        # Create step lookup map
        step_map = {step["step_id"]: step for step in steps}
        
        # Execute each group in sequence, but steps within group in parallel
        for group_index, step_ids in enumerate(execution_plan, 1):
            logger.info(
                f"Executing group {group_index}/{len(execution_plan)}: "
                f"{len(step_ids)} steps in parallel"
            )
            
            # Execute steps in this group in parallel
            with ThreadPoolExecutor(max_workers=min(max_workers, len(step_ids))) as executor:
                # Submit all steps in this group
                future_to_step = {}
                for step_id in step_ids:
                    step = step_map[step_id]
                    future = executor.submit(
                        self._execute_single_step,
                        plan_id,
                        step,
                        context
                    )
                    future_to_step[future] = step
                
                # Collect results as they complete
                for future in as_completed(future_to_step):
                    step = future_to_step[future]
                    step_id = step["step_id"]
                    
                    try:
                        result = future.result()
                        results[step_id] = result
                        
                        # Update context (thread-safe since we wait for group completion)
                        context["previous_results"][step_id] = result
                        
                        # Update metrics
                        if result.get("status") == "success":
                            succeeded += 1
                            total_quality += result.get("quality_score", 0.0)
                        else:
                            failed += 1
                            step_number = step.get("step_index", 0) + 1
                            errors_list.append(
                                f"Step {step_number} ({step_id}): {result.get('error', 'Unknown error')}"
                            )
                    
                    except Exception as e:
                        logger.error(f"Error in parallel execution of {step_id}: {e}", exc_info=True)
                        failed += 1
                        step_number = step.get("step_index", 0) + 1
                        errors_list.append(f"Step {step_number} ({step_id}): {str(e)}")
                        results[step_id] = {
                            "status": "failed",
                            "error": str(e),
                            "quality_score": 0.0
                        }
        
        return {
            "results": results,
            "succeeded": succeeded,
            "failed": failed,
            "total_quality": total_quality,
            "errors": errors_list,
            "max_parallelism": max_parallelism
        }
    
    def _execute_single_step(
        self,
        plan_id: str,
        step: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a single step with retry logic (used by parallel executor).
        
        Args:
            plan_id: Plan identifier
            step: Step to execute
            context: Execution context
        
        Returns:
            Step execution result
        """
        step_id = step["step_id"]
        step_number = step.get("step_index", 0) + 1
        
        logger.info(f"Executing step {step_number}: {step_id} (parallel)")
        
        # Start timing for monitoring
        start_time = datetime.utcnow()
        
        # Validate step
        is_valid_step, step_errors = validate_step(step)
        if not is_valid_step:
            raise ValueError(f"Invalid step: {step_errors}")
        
        # Get retry configuration from step or use defaults
        step_params = step.get("parameters", {})
        max_retries = step_params.get("max_retries", 3)
        
        # Create retry handler with step-specific config
        retry_config = RetryConfig(
            max_retries=max_retries,
            base_delay=1.0,
            backoff_factor=2.0,
            strategy=RetryStrategy.EXPONENTIAL,
            jitter=True
        )
        retry_handler = RetryHandler(config=retry_config)
        
        # Execute with retry logic
        result = retry_handler.execute_with_retry(
            func=self._execute_step_internal,
            step_id=step_id,
            max_retries=max_retries,
            context=context,
            step=step
        )
        
        # Calculate execution time
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Record metrics if monitoring enabled
        if self.monitor:
            self.monitor.record_step_execution(
                step_id=step_id,
                duration=execution_time,
                status=result.get("status", "failed"),
                quality_score=result.get("quality_score", 0.0),
                retry_count=retry_handler.current_attempt - 1 if hasattr(retry_handler, 'current_attempt') else 0
            )
        
        # Store result (thread-safe since we create new connection)
        self._store_step_result(plan_id, step, result)
        
        return result
    
    def _execute_step_internal(
        self,
        context: Dict[str, Any],
        step: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Internal step execution (called by retry handler).
        
        Args:
            context: Execution context
            step: Step to execute
        
        Returns:
            Step execution result
        """
        return self.execute_step(step, context)
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get or create database connection."""
        if self._connection is None:
            self._connection = sqlite3.connect(str(self.db_path))
            self._connection.row_factory = sqlite3.Row
        return self._connection
    
    def _create_plan_record(self, plan: Dict[str, Any]) -> None:
        """Create research plan record in database."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        veritas_ext = plan.get("veritas_extensions", {})
        
        cursor.execute("""
            INSERT INTO research_plans (
                plan_id, research_question, schema_name, status,
                plan_document, total_steps, uds3_databases,
                phase5_hybrid_search, security_level, source_domains,
                query_complexity, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            plan["plan_id"],
            plan["research_question"],
            plan["schema_name"],
            "pending",
            json.dumps(plan),
            len(plan.get("steps", [])),
            json.dumps(veritas_ext.get("uds3_databases", [])),
            1 if veritas_ext.get("phase5_hybrid_search", False) else 0,
            veritas_ext.get("security_level", "internal"),
            json.dumps(veritas_ext.get("source_domains", [])),
            plan.get("query_complexity", "standard"),
            datetime.utcnow().isoformat()
        ))
        
        conn.commit()
        logger.debug(f"Created plan record: {plan['plan_id']}")
    
    def _store_step_result(
        self,
        plan_id: str,
        step: Dict[str, Any],
        result: Dict[str, Any]
    ) -> None:
        """Store step execution result in database (thread-safe)."""
        # Create new connection for thread safety
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        step_index = step.get("step_index", 0)
        
        # Map result status to database status
        result_status = result.get("status", "unknown")
        db_status = "completed" if result_status == "success" else "failed" if result_status == "failed" else "pending"
        
        # Get retry information from result
        retry_count = result.get("retry_count", 0)
        
        try:
            # Insert step record (if not exists)
            cursor.execute("""
                INSERT OR REPLACE INTO research_plan_steps (
                    plan_id, step_id, step_index, step_name, step_type,
                    agent_name, agent_type, depends_on, status,
                    step_config, result, execution_time_ms, retry_count, completed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                plan_id,
                step["step_id"],
                step_index,
                step.get("step_name", ""),
                step.get("step_type", "unknown"),
                step.get("agent_name", ""),
                step.get("agent_type", "unknown"),
                json.dumps(step.get("depends_on", [])),
                db_status,
                json.dumps(step),
                json.dumps(result),
                result.get("execution_time_ms", 0),
                retry_count,
                datetime.utcnow().isoformat()
            ))
            
            conn.commit()
            logger.debug(
                f"Stored result for step: {step['step_id']} "
                f"(status: {db_status}, retries: {retry_count})"
            )
        finally:
            conn.close()
    
    def _update_plan_status(
        self,
        plan_id: str,
        status: str,
        quality_score: float,
        execution_time_ms: int
    ) -> None:
        """Update plan execution status in database."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE research_plans
            SET status = ?,
                execution_time_ms = ?,
                updated_at = ?,
                progress_percentage = 100.0
            WHERE plan_id = ?
        """, (
            status if status != "partial" else "completed",  # Map partial to completed
            execution_time_ms,
            datetime.utcnow().isoformat(),
            plan_id
        ))
        
        conn.commit()
        logger.debug(f"Updated plan status: {plan_id} -> {status}")
    
    def _on_state_change(self, transition: StateTransition) -> None:
        """
        Callback for state machine transitions.
        
        Updates database with state change information.
        
        Args:
            transition: State transition details
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Extract plan_id from metadata or use a placeholder
        plan_id = transition.metadata.get("plan_id") if transition.metadata else None
        
        # Log state transition in agent_execution_log
        cursor.execute("""
            INSERT INTO agent_execution_log (
                plan_id, log_level, message, agent_name, timestamp
            ) VALUES (?, ?, ?, ?, ?)
        """, (
            plan_id,
            "INFO",
            f"State transition: {transition.from_state.value} → {transition.to_state.value} ({transition.reason})",
            self.get_agent_type(),
            transition.timestamp
        ))
        
        conn.commit()
        logger.debug(f"Logged state transition: {transition.from_state.value} → {transition.to_state.value}")
    
    def get_state_machine(self, plan_id: str) -> Optional[StateMachine]:
        """
        Get state machine for a specific plan.
        
        Args:
            plan_id: Plan identifier
        
        Returns:
            StateMachine instance or None if not found
        
        Example:
            >>> sm = agent.get_state_machine("plan_001")
            >>> if sm:
            ...     print(f"Current state: {sm.current_state.value}")
        """
        return self._state_machines.get(plan_id)
    
    def get_plan_results(self, plan_id: str) -> Dict[str, Any]:
        """
        Retrieve plan execution results from database.
        
        Args:
            plan_id: Plan identifier
        
        Returns:
            Dictionary with plan details and step results
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Get plan
        cursor.execute("""
            SELECT * FROM research_plans WHERE plan_id = ?
        """, (plan_id,))
        plan_row = cursor.fetchone()
        
        if not plan_row:
            return {"error": f"Plan not found: {plan_id}"}
        
        # Get step results
        cursor.execute("""
            SELECT * FROM research_plan_steps
            WHERE plan_id = ?
            ORDER BY step_index
        """, (plan_id,))
        step_rows = cursor.fetchall()
        
        # Get state machine info if available
        state_machine = self.get_state_machine(plan_id)
        state_info = state_machine.to_dict() if state_machine else None
        
        result = {
            "plan_id": plan_row["plan_id"],
            "research_question": plan_row["research_question"],
            "status": plan_row["status"],
            "execution_time_ms": plan_row["execution_time_ms"],
            "created_at": plan_row["created_at"],
            "updated_at": plan_row["updated_at"],
            "steps": [
                {
                    "step_id": row["step_id"],
                    "step_number": row["step_index"] + 1,
                    "step_name": row["step_name"],
                    "step_type": row["step_type"],
                    "agent_name": row["agent_name"],
                    "agent_type": row["agent_type"],
                    "status": row["status"],
                    "result_data": json.loads(row["result"]) if row["result"] else None,
                    "error": row["error_message"]
                }
                for row in step_rows
            ]
        }
        
        # Add state machine info if available
        if state_info:
            result["state_machine"] = state_info
        
        return result
    
    def close(self) -> None:
        """Close database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.debug(f"Closed database connection for agent: {self.agent_id}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def __del__(self):
        """Destructor to ensure connection is closed."""
        self.close()


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    from schema_validation import create_minimal_plan
    
    print("=" * 80)
    print("VERITAS AGENT FRAMEWORK - BASE AGENT TEST")
    print("=" * 80)
    
    # Create sample agent implementation
    class SampleAgent(BaseAgent):
        """Sample agent for testing."""
        
        def execute_step(self, step, context):
            """Execute sample step."""
            step_type = step.get("step_type", "unknown")
            agent_name = step.get("agent_name", "unknown")
            
            logger.info(f"Executing step: {step_type} via {agent_name}")
            
            # Simulate processing
            return {
                "status": "success",
                "data": {
                    "step_type": step_type,
                    "agent_name": agent_name,
                    "processed": True,
                    "context_keys": list(context.keys())
                },
                "quality_score": 0.9,
                "sources": ["sample_source"],
                "metadata": {"timestamp": datetime.utcnow().isoformat()}
            }
        
        def get_agent_type(self):
            return "DataRetrievalAgent"
        
        def get_capabilities(self):
            return ["data_retrieval", "test_processing"]
    
    # Create test plan with VALID schema values
    test_id = str(uuid4())[:8]  # Unique ID for each test run
    plan = create_minimal_plan(
        plan_id=f"test_base_agent_{test_id}",
        research_question="Test base agent functionality",
        schema_name="standard"  # Must be one of the allowed schema names
    )
    
    # Add steps with ALL required fields from schema - use valid agent names
    plan["steps"] = [
        {
            "step_id": "step_001",
            "step_index": 0,
            "step_name": "Retrieve Environmental Data",
            "step_type": "data_retrieval",
            "agent_name": "environmental",  # Must be registered agent name
            "agent_type": "DataRetrievalAgent",
            "depends_on": [],
            "status": "pending",
            "retry_count": 0,
            "max_retries": 3,
            "timeout_seconds": 60
        },
        {
            "step_id": "step_002",
            "step_index": 1,
            "step_name": "Analyze Retrieved Data",
            "step_type": "data_analysis",
            "agent_name": "registry",  # Must be registered agent name
            "agent_type": "DataAnalysisAgent",
            "depends_on": ["step_001"],
            "status": "pending",
            "retry_count": 0,
            "max_retries": 3,
            "timeout_seconds": 60
        }
    ]
    
    print("\n📋 Test Plan Created:")
    print(f"  Plan ID: {plan['plan_id']}")
    print(f"  Question: {plan['research_question']}")
    print(f"  Steps: {len(plan['steps'])}")
    
    # Execute plan (sequential)
    print("\n🚀 Test 1: Sequential Execution")
    with SampleAgent() as agent:
        result = agent.execute(plan, parallel=False)
        
        print(f"\n✅ Execution {result['status'].upper()}")
        print(f"  Execution mode: {result['execution_mode']}")
        print(f"  Steps executed: {result['steps_executed']}")
        print(f"  Steps succeeded: {result['steps_succeeded']}")
        print(f"  Steps failed: {result['steps_failed']}")
        print(f"  Quality score: {result['total_quality_score']:.2f}")
        print(f"  Execution time: {result['execution_time_ms']}ms")
        
        if result['errors']:
            print(f"  Errors: {result['errors']}")
    
    # Create parallel test plan with dependencies
    print("\n🚀 Test 2: Parallel Execution with Dependencies")
    test_id_2 = str(uuid4())[:8]
    plan2 = create_minimal_plan(
        plan_id=f"test_parallel_{test_id_2}",
        research_question="Test parallel execution",
        schema_name="standard"
    )
    
    # Add 4 steps: A, B and C depend on A, D depends on B and C
    plan2["steps"] = [
        {
            "step_id": "step_A",
            "step_index": 0,
            "step_name": "Initial Data Retrieval",
            "step_type": "data_retrieval",
            "agent_name": "environmental",
            "agent_type": "DataRetrievalAgent",
            "depends_on": [],
            "status": "pending",
            "retry_count": 0,
            "max_retries": 3,
            "timeout_seconds": 60
        },
        {
            "step_id": "step_B",
            "step_index": 1,
            "step_name": "Analyze Branch 1",
            "step_type": "data_analysis",
            "agent_name": "registry",
            "agent_type": "DataAnalysisAgent",
            "depends_on": ["step_A"],
            "status": "pending",
            "retry_count": 0,
            "max_retries": 3,
            "timeout_seconds": 60
        },
        {
            "step_id": "step_C",
            "step_index": 2,
            "step_name": "Analyze Branch 2",
            "step_type": "data_analysis",
            "agent_name": "pipeline_manager",
            "agent_type": "DataAnalysisAgent",
            "depends_on": ["step_A"],
            "status": "pending",
            "retry_count": 0,
            "max_retries": 3,
            "timeout_seconds": 60
        },
        {
            "step_id": "step_D",
            "step_index": 3,
            "step_name": "Synthesize Results",
            "step_type": "synthesis",
            "agent_name": "orchestrator",
            "agent_type": "SynthesisAgent",
            "depends_on": ["step_B", "step_C"],
            "status": "pending",
            "retry_count": 0,
            "max_retries": 3,
            "timeout_seconds": 60
        }
    ]
    
    with SampleAgent() as agent:
        result = agent.execute(plan2, parallel=True, max_workers=3)
        
        print(f"\n✅ Execution {result['status'].upper()}")
        print(f"  Execution mode: {result['execution_mode']}")
        print(f"  Max parallelism: {result['max_parallelism']}")
        print(f"  Steps executed: {result['steps_executed']}")
        print(f"  Steps succeeded: {result['steps_succeeded']}")
        print(f"  Steps failed: {result['steps_failed']}")
        print(f"  Quality score: {result['total_quality_score']:.2f}")
        print(f"  Execution time: {result['execution_time_ms']}ms")
        print(f"  Expected: 3 groups - [A], [B,C], [D] with max parallelism 2")
        
        # Check state machine
        print("\n🔄 State Machine:")
        sm = agent.get_state_machine(plan2["plan_id"])
        if sm:
            print(f"  Current state: {sm.current_state.value}")
            print(f"  Is terminal: {sm.is_terminal()}")
            print(f"  Transitions: {len(sm.transition_history)}")
            for i, t in enumerate(sm.transition_history, 1):
                print(f"    {i}. {t.from_state.value} → {t.to_state.value} ({t.reason})")
        
        # Retrieve results from database
        print("\n📊 Retrieving results from database...")
        db_results = agent.get_plan_results(plan["plan_id"])
        
        if "error" in db_results:
            print(f"  {db_results['error']}")
        else:
            print(f"  Plan status: {db_results['status']}")
            print(f"  Quality score: {db_results.get('quality_score', 0.0):.2f}")
            print(f"  Steps in DB: {len(db_results['steps'])}")
            
            # Show state machine info from DB results
            if "state_machine" in db_results:
                sm_info = db_results["state_machine"]
                print(f"  State machine transitions: {sm_info['transition_count']}")
            
            for step in db_results["steps"]:
                step_number = step.get("step_number", 0)
                print(f"\n  Step {step_number}: {step['step_id']}")
                print(f"    Name: {step.get('step_name', 'N/A')}")
                print(f"    Type: {step.get('step_type', 'N/A')}")
                print(f"    Status: {step.get('status', 'unknown')}")
                if step.get("result_data"):
                    print(f"    Data keys: {list(step['result_data'].keys())}")
    
    print("\n✨ BaseAgent test complete!")
