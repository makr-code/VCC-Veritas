"""
Phase 1 Feature Implementations for Gemini Deep Search & Copilot Agents Parity

This module implements the 4 high-priority features from Phase 1 (Months 1-2):
1. Multi-hop reasoning chains with intermediate validation
2. Proactive clarification questions before execution
3. Web search integration for recent information
4. Conversational memory across sessions

Author: VERITAS Development Team
Created: 2025-12-03
Version: 1.0.0
"""

from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
from abc import ABC, abstractmethod


# ============================================================================
# 1. MULTI-HOP REASONING CHAINS
# ============================================================================

class ReasoningStepStatus(Enum):
    """Status of a reasoning step in the chain."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    VALIDATED = "validated"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class ReasoningStep:
    """Single step in a multi-hop reasoning chain."""
    step_id: str
    step_number: int
    question: str  # What are we trying to answer in this step?
    hypothesis: str  # Our hypothesis for this step
    method: str  # How we'll test this (e.g., "vector_search", "llm_inference")
    dependencies: List[str] = field(default_factory=list)  # IDs of prerequisite steps
    
    # Execution results
    status: ReasoningStepStatus = ReasoningStepStatus.PENDING
    result: Optional[str] = None
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    validation_passed: bool = False
    validation_reason: str = ""
    
    # Metadata
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cost_cu: float = 0.0


@dataclass
class ReasoningChain:
    """Complete multi-hop reasoning chain for a complex query."""
    chain_id: str
    query: str
    steps: List[ReasoningStep] = field(default_factory=list)
    
    # Chain metadata
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    total_cost_cu: float = 0.0
    
    # Chain results
    final_answer: Optional[str] = None
    overall_confidence: float = 0.0
    failed_steps: List[str] = field(default_factory=list)


class MultiHopReasoningEngine:
    """
    Implements chain-of-thought reasoning with intermediate validation.
    
    This mirrors Gemini Deep Search's ability to break down complex queries
    into a series of validated reasoning steps, where each step builds upon
    previous validated conclusions.
    """
    
    def __init__(self, llm_client, validator):
        self.llm = llm_client
        self.validator = validator
    
    async def decompose_query(self, query: str) -> ReasoningChain:
        """
        Decompose complex query into multi-hop reasoning steps.
        
        Args:
            query: User's complex question
            
        Returns:
            ReasoningChain with steps to answer the query
        """
        chain = ReasoningChain(
            chain_id=f"chain_{datetime.now().timestamp()}",
            query=query
        )
        
        # Use LLM to decompose query into reasoning steps
        decomposition_prompt = f"""
        Analyze this complex query and break it down into a chain of reasoning steps.
        Each step should answer a sub-question that leads to the final answer.
        
        Query: {query}
        
        For each step, provide:
        1. The sub-question to answer
        2. A hypothesis for what the answer might be
        3. The method to validate (search, calculation, inference)
        4. Dependencies on previous steps (if any)
        
        Format as JSON array of steps.
        """
        
        steps_data = await self.llm.generate(decomposition_prompt, format="json")
        
        # Create ReasoningStep objects
        for idx, step_data in enumerate(steps_data.get("steps", [])):
            step = ReasoningStep(
                step_id=f"step_{idx+1}",
                step_number=idx + 1,
                question=step_data["question"],
                hypothesis=step_data["hypothesis"],
                method=step_data["method"],
                dependencies=step_data.get("dependencies", [])
            )
            chain.steps.append(step)
        
        return chain
    
    async def execute_step(self, step: ReasoningStep, chain: ReasoningChain) -> ReasoningStep:
        """
        Execute a single reasoning step and validate the result.
        
        Args:
            step: The step to execute
            chain: Parent chain for context
            
        Returns:
            Updated step with results
        """
        step.status = ReasoningStepStatus.IN_PROGRESS
        step.started_at = datetime.now()
        
        # Check dependencies are satisfied
        for dep_id in step.dependencies:
            dep_step = next((s for s in chain.steps if s.step_id == dep_id), None)
            if not dep_step or not dep_step.validation_passed:
                step.status = ReasoningStepStatus.SKIPPED
                step.validation_reason = f"Dependency {dep_id} not satisfied"
                return step
        
        # Execute based on method
        if step.method == "vector_search":
            step.result, step.evidence = await self._execute_vector_search(step, chain)
        elif step.method == "llm_inference":
            step.result, step.evidence = await self._execute_llm_inference(step, chain)
        elif step.method == "graph_traversal":
            step.result, step.evidence = await self._execute_graph_traversal(step, chain)
        else:
            step.status = ReasoningStepStatus.FAILED
            step.validation_reason = f"Unknown method: {step.method}"
            return step
        
        # Validate the step result
        validation = await self.validator.validate_reasoning_step(step, chain)
        step.validation_passed = validation["passed"]
        step.validation_reason = validation["reason"]
        step.confidence = validation["confidence"]
        
        step.status = ReasoningStepStatus.VALIDATED if step.validation_passed else ReasoningStepStatus.FAILED
        step.completed_at = datetime.now()
        
        return step
    
    async def _execute_vector_search(self, step: ReasoningStep, chain: ReasoningChain) -> Tuple[str, List[Dict]]:
        """Execute vector search for this step."""
        # Implementation would integrate with existing UDS3/ThemisDB
        result = f"Answer to: {step.question}"
        evidence = [{"source": "vector_db", "content": "Supporting evidence"}]
        return result, evidence
    
    async def _execute_llm_inference(self, step: ReasoningStep, chain: ReasoningChain) -> Tuple[str, List[Dict]]:
        """Execute LLM inference for this step."""
        # Build context from previous validated steps
        context = self._build_context_from_chain(chain, step)
        
        prompt = f"""
        Question: {step.question}
        Hypothesis: {step.hypothesis}
        
        Context from previous steps:
        {context}
        
        Provide a well-reasoned answer with supporting evidence.
        """
        
        result = await self.llm.generate(prompt)
        evidence = [{"source": "llm", "content": result}]
        return result, evidence
    
    async def _execute_graph_traversal(self, step: ReasoningStep, chain: ReasoningChain) -> Tuple[str, List[Dict]]:
        """Execute graph traversal for this step."""
        # Integration with Neo4j graph database
        result = f"Graph-based answer to: {step.question}"
        evidence = [{"source": "graph_db", "content": "Graph relationships"}]
        return result, evidence
    
    def _build_context_from_chain(self, chain: ReasoningChain, current_step: ReasoningStep) -> str:
        """Build context string from previously validated steps."""
        context_parts = []
        for step in chain.steps:
            if step.step_number < current_step.step_number and step.validation_passed:
                context_parts.append(f"Step {step.step_number}: {step.question}\nAnswer: {step.result}")
        return "\n\n".join(context_parts)
    
    async def execute_chain(self, chain: ReasoningChain) -> ReasoningChain:
        """
        Execute entire reasoning chain with validation.
        
        Args:
            chain: The chain to execute
            
        Returns:
            Completed chain with all steps executed
        """
        for step in chain.steps:
            step = await self.execute_step(step, chain)
            chain.total_cost_cu += step.cost_cu
            
            if step.status == ReasoningStepStatus.FAILED:
                chain.failed_steps.append(step.step_id)
        
        # Synthesize final answer from all validated steps
        chain.final_answer = await self._synthesize_final_answer(chain)
        chain.overall_confidence = self._calculate_overall_confidence(chain)
        chain.completed_at = datetime.now()
        
        return chain
    
    async def _synthesize_final_answer(self, chain: ReasoningChain) -> str:
        """Synthesize final answer from validated reasoning steps."""
        validated_steps = [s for s in chain.steps if s.validation_passed]
        
        synthesis_prompt = f"""
        Original query: {chain.query}
        
        Validated reasoning steps:
        {self._format_steps_for_synthesis(validated_steps)}
        
        Synthesize a comprehensive final answer that addresses the original query
        by integrating insights from all validated steps.
        """
        
        final_answer = await self.llm.generate(synthesis_prompt)
        return final_answer
    
    def _format_steps_for_synthesis(self, steps: List[ReasoningStep]) -> str:
        """Format steps for synthesis prompt."""
        formatted = []
        for step in steps:
            formatted.append(f"""
Step {step.step_number}: {step.question}
Result: {step.result}
Confidence: {step.confidence:.2f}
Evidence: {len(step.evidence)} sources
            """.strip())
        return "\n\n".join(formatted)
    
    def _calculate_overall_confidence(self, chain: ReasoningChain) -> float:
        """Calculate overall confidence from individual step confidences."""
        validated_steps = [s for s in chain.steps if s.validation_passed]
        if not validated_steps:
            return 0.0
        
        # Weight later steps more heavily (they build on earlier ones)
        total_weight = 0.0
        weighted_sum = 0.0
        
        for step in validated_steps:
            weight = step.step_number / len(chain.steps)
            weighted_sum += step.confidence * weight
            total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0


# ============================================================================
# 2. PROACTIVE CLARIFICATION
# ============================================================================

class ClarificationType(Enum):
    """Types of clarification questions."""
    AMBIGUITY = "ambiguity"  # Query has ambiguous terms
    SCOPE = "scope"  # Unclear scope or boundaries
    PREFERENCE = "preference"  # User preference needed (speed vs quality)
    CONSTRAINT = "constraint"  # Missing constraints (time, cost)
    CONTEXT = "context"  # Missing contextual information


@dataclass
class ClarificationQuestion:
    """A clarification question to ask the user before expensive operations."""
    question_id: str
    question_type: ClarificationType
    question: str
    options: List[str]  # Possible answers
    cost_impact: str  # How this affects cost/time
    priority: str  # "critical", "high", "medium", "low"
    estimated_time_saved: float  # Seconds saved by clarifying
    estimated_cost_saved: float  # CU saved by clarifying


class ProactiveClarificationEngine:
    """
    Asks clarifying questions BEFORE executing expensive operations.
    
    This mirrors Copilot Agents' ability to proactively ask for clarification
    to avoid wasting resources on misunderstood queries.
    """
    
    def __init__(self, llm_client):
        self.llm = llm_client
    
    async def analyze_query_for_clarifications(self, query: str, execution_plan: Dict) -> List[ClarificationQuestion]:
        """
        Analyze query and execution plan to identify needed clarifications.
        
        Args:
            query: User's query
            execution_plan: Proposed execution plan with costs
            
        Returns:
            List of clarification questions to ask before execution
        """
        clarifications = []
        
        # Check for ambiguous terms
        ambiguities = await self._detect_ambiguities(query)
        for amb in ambiguities:
            clarifications.append(ClarificationQuestion(
                question_id=f"clarify_amb_{len(clarifications)}",
                question_type=ClarificationType.AMBIGUITY,
                question=amb["question"],
                options=amb["options"],
                cost_impact=amb["cost_impact"],
                priority="high",
                estimated_time_saved=amb["time_saved"],
                estimated_cost_saved=amb["cost_saved"]
            ))
        
        # Check for scope clarity
        if execution_plan.get("estimated_cost_cu", 0) > 10.0:  # Expensive query
            scope_question = await self._generate_scope_question(query, execution_plan)
            if scope_question:
                clarifications.append(scope_question)
        
        # Check for user preferences
        if len(execution_plan.get("alternative_plans", [])) > 1:
            pref_question = self._generate_preference_question(execution_plan)
            clarifications.append(pref_question)
        
        return clarifications
    
    async def _detect_ambiguities(self, query: str) -> List[Dict]:
        """Detect ambiguous terms in query that need clarification."""
        detection_prompt = f"""
        Analyze this query for ambiguous terms that could lead to expensive
        irrelevant searches if misinterpreted.
        
        Query: {query}
        
        For each ambiguity found, provide:
        1. The ambiguous term
        2. A clarifying question
        3. Possible interpretations
        4. How much cost/time clarification would save
        
        Format as JSON array.
        """
        
        result = await self.llm.generate(detection_prompt, format="json")
        return result.get("ambiguities", [])
    
    async def _generate_scope_question(self, query: str, plan: Dict) -> Optional[ClarificationQuestion]:
        """Generate question about query scope to prevent over-searching."""
        scope_prompt = f"""
        This query will trigger an expensive search across multiple sources.
        
        Query: {query}
        Estimated cost: {plan.get('estimated_cost_cu', 0)} CU
        Estimated time: {plan.get('estimated_time_s', 0)} seconds
        
        Should we ask the user to clarify the scope to reduce unnecessary work?
        If yes, suggest a clarifying question with options.
        
        Format as JSON.
        """
        
        result = await self.llm.generate(scope_prompt, format="json")
        
        if result.get("should_ask", False):
            return ClarificationQuestion(
                question_id="scope_clarification",
                question_type=ClarificationType.SCOPE,
                question=result["question"],
                options=result["options"],
                cost_impact=result["cost_impact"],
                priority="high",
                estimated_time_saved=result.get("time_saved", 0),
                estimated_cost_saved=result.get("cost_saved", 0)
            )
        
        return None
    
    def _generate_preference_question(self, plan: Dict) -> ClarificationQuestion:
        """Generate question about user preferences (speed vs quality vs cost)."""
        plans = plan.get("alternative_plans", [])
        
        options = []
        for p in plans:
            options.append(
                f"{p['name']}: {p['estimated_time_s']}s, {p['estimated_cost_cu']} CU, "
                f"{p['predicted_quality']*100:.0f}% quality"
            )
        
        return ClarificationQuestion(
            question_id="preference_speed_cost_quality",
            question_type=ClarificationType.PREFERENCE,
            question="We have multiple execution strategies. Which do you prefer?",
            options=options,
            cost_impact="Choosing 'speed' saves time but may reduce quality. 'quality' takes longer.",
            priority="medium",
            estimated_time_saved=max(p['estimated_time_s'] for p in plans) - min(p['estimated_time_s'] for p in plans),
            estimated_cost_saved=max(p['estimated_cost_cu'] for p in plans) - min(p['estimated_cost_cu'] for p in plans)
        )


# ============================================================================
# 3. WEB SEARCH INTEGRATION
# ============================================================================

@dataclass
class WebSearchResult:
    """Result from web search."""
    url: str
    title: str
    snippet: str
    published_date: Optional[datetime]
    relevance_score: float
    source_authority: float  # Authority score of the source
    content: Optional[str] = None  # Full content if fetched


class WebSearchEngine:
    """
    Integrates web search for recent information not in knowledge base.
    
    This mirrors Gemini Deep Search's ability to fetch current information
    from the web when the knowledge base is outdated or incomplete.
    """
    
    def __init__(self, search_api_client, content_fetcher):
        self.search_api = search_api_client
        self.fetcher = content_fetcher
    
    async def determine_if_web_search_needed(self, query: str, kb_results: List[Dict]) -> bool:
        """
        Determine if web search is needed based on query and KB results.
        
        Args:
            query: User's query
            kb_results: Results from knowledge base search
            
        Returns:
            True if web search would add value
        """
        # Check for temporal indicators
        temporal_keywords = ["recent", "latest", "current", "today", "2024", "2025", "now"]
        has_temporal = any(kw in query.lower() for kw in temporal_keywords)
        
        # Check KB result freshness
        kb_has_recent = False
        if kb_results:
            newest_kb = max((r.get("timestamp", datetime.min) for r in kb_results if "timestamp" in r), default=datetime.min)
            kb_has_recent = (datetime.now() - newest_kb).days < 30
        
        # Check KB completeness
        kb_is_complete = len(kb_results) >= 10 and any(r.get("relevance", 0) > 0.8 for r in kb_results)
        
        # Decision logic
        if has_temporal and not kb_has_recent:
            return True  # Query needs recent info, KB is outdated
        
        if not kb_is_complete:
            return True  # KB results insufficient
        
        return False
    
    async def search_web(self, query: str, max_results: int = 10) -> List[WebSearchResult]:
        """
        Search the web for relevant information.
        
        Args:
            query: Search query
            max_results: Maximum results to return
            
        Returns:
            List of web search results
        """
        # Use search API (Google, Bing, DuckDuckGo, etc.)
        raw_results = await self.search_api.search(query, limit=max_results)
        
        results = []
        for item in raw_results:
            result = WebSearchResult(
                url=item["url"],
                title=item["title"],
                snippet=item["snippet"],
                published_date=item.get("published_date"),
                relevance_score=item.get("relevance", 0.5),
                source_authority=await self._calculate_source_authority(item["url"])
            )
            results.append(result)
        
        return results
    
    async def fetch_and_extract_content(self, result: WebSearchResult) -> WebSearchResult:
        """
        Fetch full content from URL and extract relevant text.
        
        Args:
            result: Web search result with URL
            
        Returns:
            Updated result with full content
        """
        content = await self.fetcher.fetch_url(result.url)
        result.content = self._extract_main_content(content)
        return result
    
    async def _calculate_source_authority(self, url: str) -> float:
        """Calculate authority score for a source."""
        # Check against whitelist of authoritative domains
        authoritative_domains = {
            ".gov": 1.0,
            ".edu": 0.9,
            ".org": 0.7,
            "wikipedia.org": 0.8,
            "arxiv.org": 0.95,
            # Add more
        }
        
        for domain, score in authoritative_domains.items():
            if domain in url:
                return score
        
        return 0.5  # Default score for unknown sources
    
    def _extract_main_content(self, html: str) -> str:
        """Extract main text content from HTML."""
        # Use libraries like BeautifulSoup, readability, or trafilatura
        # Simplified implementation
        return html[:5000]  # Placeholder
    
    async def integrate_web_results_with_kb(
        self,
        query: str,
        kb_results: List[Dict],
        web_results: List[WebSearchResult]
    ) -> List[Dict]:
        """
        Intelligently merge web search results with knowledge base results.
        
        Args:
            query: Original query
            kb_results: Results from knowledge base
            web_results: Results from web search
            
        Returns:
            Merged and ranked results
        """
        merged = []
        
        # Add KB results with source indicator
        for kb_res in kb_results:
            merged.append({
                **kb_res,
                "source_type": "knowledge_base",
                "is_recent": False
            })
        
        # Add web results with source indicator
        for web_res in web_results:
            merged.append({
                "content": web_res.content or web_res.snippet,
                "title": web_res.title,
                "url": web_res.url,
                "relevance": web_res.relevance_score,
                "authority": web_res.source_authority,
                "source_type": "web",
                "is_recent": True,
                "published_date": web_res.published_date
            })
        
        # Re-rank merged results
        merged = await self._rerank_merged_results(query, merged)
        
        return merged
    
    async def _rerank_merged_results(self, query: str, results: List[Dict]) -> List[Dict]:
        """Rerank merged results considering recency, authority, and relevance."""
        def score_result(r: Dict) -> float:
            relevance = r.get("relevance", 0.5)
            authority = r.get("authority", 0.5)
            recency_bonus = 0.1 if r.get("is_recent", False) else 0.0
            
            return relevance * 0.5 + authority * 0.4 + recency_bonus
        
        results.sort(key=score_result, reverse=True)
        return results


# ============================================================================
# 4. CONVERSATIONAL MEMORY
# ============================================================================

@dataclass
class ConversationTurn:
    """Single turn in a conversation."""
    turn_id: str
    timestamp: datetime
    user_message: str
    system_response: str
    query_complexity: str  # "simple", "research", "scientific"
    cost_cu: float
    execution_time_s: float
    satisfaction_score: Optional[float] = None  # User feedback


@dataclass
class ConversationSession:
    """Complete conversation session with context."""
    session_id: str
    user_id: str
    started_at: datetime
    last_activity: datetime
    turns: List[ConversationTurn] = field(default_factory=list)
    
    # Extracted context
    topics: List[str] = field(default_factory=list)
    entities: List[str] = field(default_factory=list)
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    
    # Session metadata
    total_cost_cu: float = 0.0
    total_time_s: float = 0.0
    avg_satisfaction: float = 0.0


class ConversationalMemoryManager:
    """
    Maintains context across multiple query sessions.
    
    This mirrors Copilot Agents' ability to remember previous conversations
    and use that context to provide better, more personalized responses.
    """
    
    def __init__(self, storage_backend, llm_client):
        self.storage = storage_backend
        self.llm = llm_client
    
    async def get_or_create_session(self, user_id: str, session_id: Optional[str] = None) -> ConversationSession:
        """
        Get existing session or create new one.
        
        Args:
            user_id: User identifier
            session_id: Optional session ID to resume
            
        Returns:
            ConversationSession object
        """
        if session_id:
            session = await self.storage.get_session(session_id)
            if session:
                session.last_activity = datetime.now()
                return session
        
        # Create new session
        session = ConversationSession(
            session_id=f"session_{user_id}_{datetime.now().timestamp()}",
            user_id=user_id,
            started_at=datetime.now(),
            last_activity=datetime.now()
        )
        
        await self.storage.save_session(session)
        return session
    
    async def add_turn(self, session: ConversationSession, turn: ConversationTurn) -> ConversationSession:
        """
        Add a conversation turn and update session context.
        
        Args:
            session: Current session
            turn: New conversation turn
            
        Returns:
            Updated session
        """
        session.turns.append(turn)
        session.total_cost_cu += turn.cost_cu
        session.total_time_s += turn.execution_time_s
        session.last_activity = datetime.now()
        
        # Update satisfaction average
        if turn.satisfaction_score is not None:
            scored_turns = [t for t in session.turns if t.satisfaction_score is not None]
            session.avg_satisfaction = sum(t.satisfaction_score for t in scored_turns) / len(scored_turns)
        
        # Extract and update context
        await self._update_session_context(session, turn)
        
        # Save to storage
        await self.storage.save_session(session)
        
        return session
    
    async def _update_session_context(self, session: ConversationSession, turn: ConversationTurn):
        """Extract topics, entities, and preferences from the turn."""
        extraction_prompt = f"""
        Analyze this conversation turn and extract:
        1. Topics discussed
        2. Named entities mentioned
        3. Any user preferences revealed
        
        User message: {turn.user_message}
        System response: {turn.system_response}
        
        Previous session topics: {session.topics}
        Previous entities: {session.entities}
        
        Format as JSON with topics, entities, and preferences.
        """
        
        extracted = await self.llm.generate(extraction_prompt, format="json")
        
        # Update topics (avoid duplicates)
        new_topics = [t for t in extracted.get("topics", []) if t not in session.topics]
        session.topics.extend(new_topics)
        
        # Update entities
        new_entities = [e for e in extracted.get("entities", []) if e not in session.entities]
        session.entities.extend(new_entities)
        
        # Update preferences
        session.user_preferences.update(extracted.get("preferences", {}))
    
    async def get_relevant_context(self, session: ConversationSession, current_query: str, max_turns: int = 3) -> str:
        """
        Get relevant context from conversation history for current query.
        
        Args:
            session: Current session
            current_query: The user's current query
            max_turns: Maximum previous turns to include
            
        Returns:
            Formatted context string
        """
        if not session.turns:
            return ""
        
        # Get most recent turns
        recent_turns = session.turns[-max_turns:]
        
        # Build context string
        context_parts = []
        
        # Add session overview
        context_parts.append(f"Session started: {session.started_at}")
        context_parts.append(f"Main topics: {', '.join(session.topics[:5])}")
        
        if session.user_preferences:
            context_parts.append(f"User preferences: {session.user_preferences}")
        
        # Add recent conversation
        context_parts.append("\n--- Recent Conversation ---")
        for turn in recent_turns:
            context_parts.append(f"\nUser: {turn.user_message}")
            context_parts.append(f"Assistant: {turn.system_response[:200]}...")  # Truncate long responses
        
        context_parts.append(f"\n--- Current Query ---\n{current_query}")
        
        return "\n".join(context_parts)
    
    async def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """
        Get aggregated user preferences across all sessions.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary of user preferences
        """
        sessions = await self.storage.get_user_sessions(user_id)
        
        # Aggregate preferences
        aggregated = {}
        for session in sessions:
            for key, value in session.user_preferences.items():
                if key not in aggregated:
                    aggregated[key] = []
                aggregated[key].append(value)
        
        # Take most common/recent preference for each key
        final_prefs = {}
        for key, values in aggregated.items():
            if isinstance(values[0], (int, float)):
                final_prefs[key] = sum(values) / len(values)  # Average
            else:
                final_prefs[key] = max(set(values), key=values.count)  # Most common
        
        return final_prefs


# ============================================================================
# INTEGRATION COORDINATOR
# ============================================================================

class Phase1FeatureCoordinator:
    """
    Coordinates all Phase 1 features for seamless integration.
    
    This class orchestrates:
    1. Multi-hop reasoning for complex queries
    2. Proactive clarification before expensive ops
    3. Web search when KB is insufficient
    4. Conversational memory for context
    """
    
    def __init__(
        self,
        reasoning_engine: MultiHopReasoningEngine,
        clarification_engine: ProactiveClarificationEngine,
        web_search_engine: WebSearchEngine,
        memory_manager: ConversationalMemoryManager
    ):
        self.reasoning = reasoning_engine
        self.clarification = clarification_engine
        self.web_search = web_search_engine
        self.memory = memory_manager
    
    async def process_query_with_phase1_features(
        self,
        user_id: str,
        query: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a query using all Phase 1 features.
        
        Args:
            user_id: User identifier
            query: User's query
            session_id: Optional session to continue
            
        Returns:
            Complete response with all Phase 1 enhancements
        """
        # 1. Get/create conversation session
        session = await self.memory.get_or_create_session(user_id, session_id)
        
        # 2. Enhance query with conversational context
        context = await self.memory.get_relevant_context(session, query)
        enhanced_query = f"{context}\n\nCurrent query: {query}"
        
        # 3. Generate initial execution plan
        execution_plan = await self._generate_execution_plan(enhanced_query)
        
        # 4. Proactive clarification (if needed)
        clarifications = await self.clarification.analyze_query_for_clarifications(
            query, execution_plan
        )
        
        if clarifications:
            return {
                "status": "needs_clarification",
                "clarifications": [
                    {
                        "question": c.question,
                        "options": c.options,
                        "cost_impact": c.cost_impact,
                        "priority": c.priority
                    }
                    for c in clarifications
                ],
                "session_id": session.session_id
            }
        
        # 5. Determine if query needs multi-hop reasoning
        needs_reasoning = execution_plan.get("complexity") in ["research", "scientific"]
        
        if needs_reasoning:
            # Execute with multi-hop reasoning
            chain = await self.reasoning.decompose_query(enhanced_query)
            chain = await self.reasoning.execute_chain(chain)
            
            final_answer = chain.final_answer
            confidence = chain.overall_confidence
            cost_cu = chain.total_cost_cu
        else:
            # Simple query - direct execution
            final_answer, confidence, cost_cu = await self._execute_simple_query(enhanced_query)
        
        # 6. Check if web search needed
        kb_results = []  # Would come from execution above
        if await self.web_search.determine_if_web_search_needed(query, kb_results):
            web_results = await self.web_search.search_web(query, max_results=5)
            # Fetch full content for top results
            for result in web_results[:3]:
                await self.web_search.fetch_and_extract_content(result)
            
            # Integrate web results
            kb_results = await self.web_search.integrate_web_results_with_kb(
                query, kb_results, web_results
            )
        
        # 7. Save conversation turn
        turn = ConversationTurn(
            turn_id=f"turn_{len(session.turns) + 1}",
            timestamp=datetime.now(),
            user_message=query,
            system_response=final_answer,
            query_complexity=execution_plan.get("complexity", "simple"),
            cost_cu=cost_cu,
            execution_time_s=0.0  # Would be measured
        )
        
        session = await self.memory.add_turn(session, turn)
        
        return {
            "status": "success",
            "answer": final_answer,
            "confidence": confidence,
            "cost_cu": cost_cu,
            "session_id": session.session_id,
            "context_used": len(session.turns) > 1,
            "web_search_used": bool(web_results) if 'web_results' in locals() else False,
            "reasoning_chain_used": needs_reasoning
        }
    
    async def _generate_execution_plan(self, query: str) -> Dict:
        """Generate execution plan for query."""
        # Placeholder - would integrate with existing plan generator
        return {
            "complexity": "simple",
            "estimated_cost_cu": 5.0,
            "estimated_time_s": 10.0,
            "alternative_plans": []
        }
    
    async def _execute_simple_query(self, query: str) -> Tuple[str, float, float]:
        """Execute a simple query without multi-hop reasoning."""
        # Placeholder - would integrate with existing query execution
        return "Simple answer", 0.85, 3.0
