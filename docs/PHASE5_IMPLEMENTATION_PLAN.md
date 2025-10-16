# Phase 5 Implementation Plan - v5.0 Hypothesis Generation + Enhanced RAG

**Created:** 14. Oktober 2025  
**Status:** 🎯 **READY TO START**  
**Target Completion:** 3-4 Tage (24-32 Stunden)

---

## 🎯 Overview

**Phase 5 kombiniert zwei wichtige Features:**

1. **v5.0 Hypothesis Generation** (~800 LOC, 2-3 Tage)
   - LLM-enhanced Query Understanding
   - Foundation für Structured Response System
   
2. **Enhanced RAG Features** (~200 LOC, 1-2 Tage)
   - Performance Optimierung (3-5x schneller)
   - Caching & Batch Operations

**Total:** ~1,000 LOC, 3-4 Tage

---

## 📦 Part 1: v5.0 Hypothesis Generation (800 LOC)

### Task 1.1: Hypothesis Service Core (~300 LOC, 6-8h)

**File:** `backend/services/hypothesis_service.py`

**Implementation:**
```python
"""
VERITAS v5.0 - Hypothesis Generation Service
===========================================

LLM-enhanced query analysis for structured response generation.

Features:
- Query → Hypothesis conversion via LLM
- Confidence scoring
- Question type classification
- Information gap detection

Usage:
    from backend.services.hypothesis_service import HypothesisService
    
    service = HypothesisService()
    hypothesis = service.generate_hypothesis(
        query="Bauantrag für Einfamilienhaus in Stuttgart",
        rag_context=rag_context  # Optional RAG results
    )
    
    print(f"Type: {hypothesis.question_type}")
    print(f"Confidence: {hypothesis.confidence}")
    print(f"Intent: {hypothesis.primary_intent}")
"""

import sys
import os
import json
import logging
from typing import Dict, Any, Optional, List
from dataclasses import asdict

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.models.hypothesis import (
    Hypothesis, QuestionType, ConfidenceLevel, InformationGap
)
from backend.services.veritas_ollama_client import VeritasOllamaClient

logger = logging.getLogger(__name__)


class HypothesisService:
    """
    Service for generating hypotheses from user queries using LLM.
    
    Analyzes queries to create structured hypotheses that guide
    the response generation process.
    """
    
    def __init__(
        self,
        ollama_client: Optional[VeritasOllamaClient] = None,
        model: str = "llama2",
        prompt_file: str = None
    ):
        """
        Initialize hypothesis service.
        
        Args:
            ollama_client: Ollama client instance (optional)
            model: LLM model name (default: llama2)
            prompt_file: Path to hypothesis prompt template
        """
        self.ollama_client = ollama_client or VeritasOllamaClient()
        self.model = model
        
        # Load prompt template
        if prompt_file is None:
            prompt_file = os.path.join(
                os.path.dirname(__file__), 
                "../prompts/hypothesis_prompt.txt"
            )
        
        self.prompt_template = self._load_prompt_template(prompt_file)
        
        logger.info(f"HypothesisService initialized with model: {model}")
    
    def _load_prompt_template(self, filepath: str) -> str:
        """Load hypothesis generation prompt template."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            logger.warning(f"Prompt file not found: {filepath}, using default")
            return self._get_default_prompt()
    
    def _get_default_prompt(self) -> str:
        """Get default hypothesis prompt if file not found."""
        return """You are a query analysis expert. Analyze the user query and generate a structured hypothesis.

Output a JSON object with:
{
    "question_type": "fact_retrieval|comparison|procedural|calculation|opinion",
    "primary_intent": "string describing main intent",
    "confidence": "high|medium|low",
    "required_information": ["list of required info"],
    "information_gaps": ["list of missing info"],
    "assumptions": ["list of assumptions"]
}

Query: {query}

Analysis:"""
    
    def generate_hypothesis(
        self,
        query: str,
        rag_context: Optional[Dict[str, Any]] = None
    ) -> Hypothesis:
        """
        Generate hypothesis from user query.
        
        Args:
            query: User query string
            rag_context: Optional RAG search results for context
        
        Returns:
            Hypothesis object
        """
        logger.info(f"Generating hypothesis for query: {query[:50]}...")
        
        # Build prompt
        prompt = self._build_prompt(query, rag_context)
        
        # Call LLM
        try:
            response = self._call_llm(prompt)
            hypothesis_data = self._parse_llm_response(response)
            
            # Create Hypothesis object
            hypothesis = Hypothesis(
                query=query,
                question_type=QuestionType(hypothesis_data.get('question_type', 'fact_retrieval')),
                primary_intent=hypothesis_data.get('primary_intent', ''),
                confidence=ConfidenceLevel(hypothesis_data.get('confidence', 'medium')),
                required_information=hypothesis_data.get('required_information', []),
                information_gaps=[
                    InformationGap(
                        gap_type=gap,
                        severity="important",
                        suggested_query=f"Provide {gap}"
                    )
                    for gap in hypothesis_data.get('information_gaps', [])
                ],
                assumptions=hypothesis_data.get('assumptions', [])
            )
            
            logger.info(f"Hypothesis generated: {hypothesis.question_type.value}, confidence: {hypothesis.confidence.value}")
            return hypothesis
            
        except Exception as e:
            logger.error(f"Hypothesis generation failed: {e}")
            return self._create_fallback_hypothesis(query)
    
    def _build_prompt(
        self, 
        query: str, 
        rag_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build LLM prompt from query and context."""
        prompt = self.prompt_template.replace("{query}", query)
        
        if rag_context:
            context_summary = self._summarize_rag_context(rag_context)
            prompt += f"\n\nAvailable Context:\n{context_summary}"
        
        return prompt
    
    def _summarize_rag_context(self, rag_context: Dict[str, Any]) -> str:
        """Summarize RAG context for prompt."""
        if not rag_context or 'results' not in rag_context:
            return "No context available"
        
        results = rag_context['results'][:3]  # Top 3 results
        summary = []
        
        for i, doc in enumerate(results, 1):
            title = doc.get('title', 'Unknown')
            excerpt = doc.get('excerpt', '')[:100]
            summary.append(f"{i}. {title}: {excerpt}...")
        
        return "\n".join(summary)
    
    def _call_llm(self, prompt: str) -> str:
        """Call LLM to generate hypothesis."""
        # Use Ollama client
        response = self.ollama_client.generate(
            model=self.model,
            prompt=prompt,
            max_tokens=500,
            temperature=0.3  # Lower temperature for structured output
        )
        
        return response.get('response', '')
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM JSON response."""
        # Try to extract JSON from response
        try:
            # Find JSON block
            start = response.find('{')
            end = response.rfind('}') + 1
            
            if start >= 0 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
            else:
                raise ValueError("No JSON found in response")
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}")
            raise ValueError(f"Invalid JSON response: {e}")
    
    def _create_fallback_hypothesis(self, query: str) -> Hypothesis:
        """Create fallback hypothesis if LLM fails."""
        logger.warning("Creating fallback hypothesis")
        
        return Hypothesis(
            query=query,
            question_type=QuestionType.FACT_RETRIEVAL,
            primary_intent="Answer user question",
            confidence=ConfidenceLevel.LOW,
            required_information=["User query details"],
            information_gaps=[],
            assumptions=["Fallback hypothesis due to LLM error"]
        )
```

**Tests:**
- `test_generate_hypothesis_success()` - Happy path
- `test_generate_hypothesis_with_context()` - With RAG context
- `test_generate_hypothesis_invalid_json()` - Error handling
- `test_confidence_scoring()` - Confidence levels
- `test_fallback_hypothesis()` - Fallback on error

---

### Task 1.2: Hypothesis Data Models (~150 LOC, 2-3h)

**File:** `backend/models/hypothesis.py`

**Implementation:**
```python
"""
VERITAS v5.0 - Hypothesis Data Models
=====================================

Data structures for hypothesis generation and analysis.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional


class QuestionType(Enum):
    """Types of questions that can be asked."""
    FACT_RETRIEVAL = "fact_retrieval"        # "What is X?"
    COMPARISON = "comparison"                # "What's the difference between X and Y?"
    PROCEDURAL = "procedural"                # "How do I do X?"
    CALCULATION = "calculation"              # "How much does X cost?"
    OPINION = "opinion"                      # "What's best for X?"
    TIMELINE = "timeline"                    # "When does X happen?"
    CAUSAL = "causal"                        # "Why does X happen?"
    HYPOTHETICAL = "hypothetical"            # "What if X?"


class ConfidenceLevel(Enum):
    """Confidence levels for hypothesis."""
    HIGH = "high"          # >80% confidence, clear intent
    MEDIUM = "medium"      # 50-80% confidence, some ambiguity
    LOW = "low"            # <50% confidence, unclear intent
    UNKNOWN = "unknown"    # Unable to determine


class GapSeverity(Enum):
    """Severity of information gaps."""
    CRITICAL = "critical"      # Cannot answer without this
    IMPORTANT = "important"    # Answer quality reduced without this
    OPTIONAL = "optional"      # Nice to have, not essential


@dataclass
class InformationGap:
    """
    Represents missing information needed to answer query.
    
    Attributes:
        gap_type: Type of missing information
        severity: How critical is this gap
        suggested_query: Suggested clarification question
        examples: Example values that could fill gap
    """
    gap_type: str
    severity: str
    suggested_query: str
    examples: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class Hypothesis:
    """
    Hypothesis about user query and required information.
    
    Generated by analyzing the query with LLM to understand:
    - What type of question is being asked
    - What information is needed to answer
    - What information is missing
    - What assumptions are being made
    
    Attributes:
        query: Original user query
        question_type: Type of question (fact, comparison, etc.)
        primary_intent: Main intent/goal of query
        confidence: Confidence level of hypothesis
        required_information: List of info needed to answer
        information_gaps: List of missing information
        assumptions: List of assumptions made
        suggested_steps: Suggested process steps
        expected_response_type: Expected format of response
        metadata: Additional metadata
        timestamp: When hypothesis was created
    """
    query: str
    question_type: QuestionType
    primary_intent: str
    confidence: ConfidenceLevel
    required_information: List[str] = field(default_factory=list)
    information_gaps: List[InformationGap] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    suggested_steps: List[str] = field(default_factory=list)
    expected_response_type: str = "text"
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'query': self.query,
            'question_type': self.question_type.value,
            'primary_intent': self.primary_intent,
            'confidence': self.confidence.value,
            'required_information': self.required_information,
            'information_gaps': [gap.to_dict() for gap in self.information_gaps],
            'assumptions': self.assumptions,
            'suggested_steps': self.suggested_steps,
            'expected_response_type': self.expected_response_type,
            'metadata': self.metadata,
            'timestamp': self.timestamp
        }
    
    def has_critical_gaps(self) -> bool:
        """Check if hypothesis has critical information gaps."""
        return any(
            gap.severity == GapSeverity.CRITICAL.value 
            for gap in self.information_gaps
        )
    
    def get_gap_count(self, severity: str = None) -> int:
        """Get count of information gaps, optionally filtered by severity."""
        if severity is None:
            return len(self.information_gaps)
        return sum(1 for gap in self.information_gaps if gap.severity == severity)
```

---

### Task 1.3: Hypothesis Prompts (~200 lines, 2h)

**File:** `backend/prompts/hypothesis_prompt.txt`

**Content:** (System prompt for LLM with examples)

---

### Task 1.4: Ollama Client Integration (+50 LOC, 1-2h)

**File:** `backend/services/veritas_ollama_client.py` (extend)

Add hypothesis-specific method to existing Ollama client.

---

### Task 1.5: Hypothesis Tests (~250 LOC, 4-6h)

**File:** `tests/test_hypothesis_service.py`

**Tests:**
1. `test_generate_hypothesis_fact_retrieval()` - Fact questions
2. `test_generate_hypothesis_comparison()` - Comparison questions
3. `test_generate_hypothesis_procedural()` - How-to questions
4. `test_generate_hypothesis_with_rag_context()` - With RAG results
5. `test_confidence_high()` - High confidence scenarios
6. `test_confidence_low()` - Low confidence scenarios
7. `test_information_gaps_detection()` - Gap detection
8. `test_invalid_json_fallback()` - Error handling
9. `test_llm_timeout()` - Timeout handling
10. `test_hypothesis_serialization()` - to_dict() method

---

## 📦 Part 2: Enhanced RAG Features (200 LOC)

### Task 2.1: Batch Search (+80 LOC, 2-3h)

**File:** `backend/services/rag_service.py` (extend)

**Implementation:**
```python
async def batch_search(
    self,
    queries: List[str],
    search_type: str = "hybrid",
    top_k: int = 3
) -> List[SearchResult]:
    """
    Execute multiple searches in parallel.
    
    Args:
        queries: List of query strings
        search_type: Type of search (vector, graph, relational, hybrid)
        top_k: Results per query
    
    Returns:
        List of SearchResult objects (one per query)
    """
    import asyncio
    
    # Create tasks for parallel execution
    tasks = []
    for query in queries:
        if search_type == "hybrid":
            task = asyncio.to_thread(self.hybrid_search, query, top_k=top_k)
        elif search_type == "vector":
            task = asyncio.to_thread(self.vector_search, query, top_k=top_k)
        elif search_type == "graph":
            task = asyncio.to_thread(self.graph_search, query, top_k=top_k)
        else:  # relational
            task = asyncio.to_thread(self.relational_search, query, top_k=top_k)
        
        tasks.append(task)
    
    # Execute in parallel
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Filter out exceptions
    valid_results = [r for r in results if not isinstance(r, Exception)]
    
    return valid_results
```

---

### Task 2.2: Query Expansion (+60 LOC, 2h)

**File:** `backend/services/rag_service.py` (extend)

**Implementation:**
```python
def expand_query(
    self,
    query: str,
    expansion_type: str = "synonyms"
) -> List[str]:
    """
    Expand query with synonyms or related terms.
    
    Args:
        query: Original query
        expansion_type: Type of expansion (synonyms, related, semantic)
    
    Returns:
        List of expanded queries
    """
    expanded = [query]  # Always include original
    
    if expansion_type == "synonyms":
        # Add synonym variations
        synonyms = self._get_synonyms(query)
        expanded.extend(synonyms)
    
    elif expansion_type == "related":
        # Add related terms
        related = self._get_related_terms(query)
        expanded.extend(related)
    
    return expanded[:5]  # Limit to 5 queries
```

---

### Task 2.3: LLM Re-ranking (~150 LOC, 3-4h)

**File:** `backend/services/rag_reranker.py` (new)

LLM-based result re-ranking for better relevance.

---

### Task 2.4: Redis Caching (~120 LOC, 3-4h)

**File:** `backend/services/rag_cache.py` (new)

TTL-based caching with Redis for frequent queries.

---

### Task 2.5: Performance Tests (~150 LOC, 2-3h)

**File:** `tests/test_rag_performance.py` (new)

Benchmarks for batch search, caching, parallel execution.

---

## 📅 Implementation Schedule

### Week 1: v5.0 Hypothesis Generation

**Day 1 (8h):**
- ✅ Morning (4h): Task 1.1 - Hypothesis Service Core (300 LOC)
- ✅ Afternoon (4h): Task 1.2 - Hypothesis Data Models (150 LOC)

**Day 2 (8h):**
- ✅ Morning (3h): Task 1.3 - Hypothesis Prompts (200 lines)
- ✅ Afternoon (5h): Task 1.4 + 1.5 - Ollama Integration + Tests (300 LOC)

**Day 3 (8h):**
- ✅ Morning (4h): Task 1.6 - ProcessExecutor Integration (100 LOC)
- ✅ Afternoon (4h): Task 12 - Documentation (1,000 lines)

### Week 2: Enhanced RAG Features

**Day 4 (8h):**
- ✅ Morning (3h): Task 2.1 - Batch Search (80 LOC)
- ✅ Afternoon (5h): Task 2.2 + 2.3 - Query Expansion + Re-ranking (210 LOC)

**Day 5 (optional):**
- ✅ Morning (4h): Task 2.4 - Redis Caching (120 LOC)
- ✅ Afternoon (4h): Task 2.5 + 13 - Performance Tests + Docs (550 LOC)

---

## 🎯 Success Criteria

### v5.0 Hypothesis Generation:
- ✅ HypothesisService generates valid hypotheses
- ✅ All 10 tests pass (100%)
- ✅ LLM integration working with Ollama
- ✅ ProcessExecutor uses hypotheses for planning
- ✅ Documentation complete (1,000+ lines)

### Enhanced RAG Features:
- ✅ Batch search 3-5x faster than sequential
- ✅ Query expansion improves recall by 20%+
- ✅ LLM re-ranking improves precision by 15%+
- ✅ Cache hit rate >60% for frequent queries
- ✅ All performance tests pass

---

## 📚 Documentation Deliverables

1. **docs/PHASE5_HYPOTHESIS_GENERATION.md** (~1,000 lines)
   - API reference
   - Usage examples
   - LLM prompts
   - Troubleshooting

2. **docs/PHASE4_RAG_INTEGRATION.md** (+400 lines)
   - Enhanced features section
   - Batch search guide
   - Caching configuration
   - Performance benchmarks

3. **TODO.md** (v3.25.0)
   - Phase 5 completion section
   - Updated statistics (9,090 LOC)
   - New test counts (80+ tests)

---

## 🔧 Dependencies

**Required:**
- ✅ Existing Ollama client (backend/services/veritas_ollama_client.py)
- ✅ Existing RAG Service (backend/services/rag_service.py)
- ✅ Existing ProcessExecutor (backend/services/process_executor.py)

**Optional:**
- ⏸️ Redis server (for caching)
- ⏸️ Running Ollama LLM (for hypothesis generation)

---

## 🚀 Getting Started

### 1. Start with Hypothesis Generation:

```bash
# Create files
mkdir -p backend/prompts
touch backend/services/hypothesis_service.py
touch backend/models/hypothesis.py
touch backend/prompts/hypothesis_prompt.txt
touch tests/test_hypothesis_service.py

# Start implementation
# See Task 1.1 above for code template
```

### 2. Then Enhanced RAG:

```bash
# Extend existing files
# backend/services/rag_service.py
# Add batch_search() and expand_query() methods

# Create new files
touch backend/services/rag_reranker.py
touch backend/services/rag_cache.py
touch tests/test_rag_performance.py
```

---

## ✅ Checklist

**v5.0 Hypothesis Generation:**
- [ ] Task 1.1: Hypothesis Service Core (300 LOC)
- [ ] Task 1.2: Hypothesis Data Models (150 LOC)
- [ ] Task 1.3: Hypothesis Prompts (200 lines)
- [ ] Task 1.4: Ollama Client Integration (+50 LOC)
- [ ] Task 1.5: Hypothesis Tests (250 LOC)
- [ ] Task 1.6: ProcessExecutor Integration (+100 LOC)

**Enhanced RAG Features:**
- [ ] Task 2.1: Batch Search (+80 LOC)
- [ ] Task 2.2: Query Expansion (+60 LOC)
- [ ] Task 2.3: LLM Re-ranking (150 LOC)
- [ ] Task 2.4: Redis Caching (120 LOC)
- [ ] Task 2.5: Performance Tests (150 LOC)

**Documentation:**
- [ ] Task 12: Phase 5 Documentation (1,000 lines)
- [ ] Task 13: Enhanced RAG Documentation (+400 lines)
- [ ] Task 14: Update TODO.md (v3.25.0)

---

**Status:** Ready to start implementation  
**Next Action:** Begin with Task 1.1 (Hypothesis Service Core)
