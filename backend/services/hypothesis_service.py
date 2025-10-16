"""
Hypothesis Service - LLM-based Query Hypothesis Generation

This service analyzes user queries and generates structured hypotheses about the query intent,
required information, potential gaps, and suggested processing steps.

Version: 1.0.0
Phase: 5 (v5.0 Hypothesis Generation)
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# Import dirtyjson for robust LLM JSON parsing
try:
    import dirtyjson
    DIRTYJSON_AVAILABLE = True
except ImportError:
    DIRTYJSON_AVAILABLE = False
    logging.warning("⚠️  dirtyjson not available, using standard json parser")

# Import Hypothesis models
import sys
sys.path.append(str(Path(__file__).parent.parent))
from models.hypothesis import (
    Hypothesis, 
    QuestionType, 
    ConfidenceLevel, 
    InformationGap, 
    GapSeverity
)

# Import Ollama client
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from native_ollama_integration import DirectOllamaLLM

logger = logging.getLogger(__name__)


class HypothesisService:
    """
    Service for generating query hypotheses using LLM analysis.
    
    The service:
    1. Analyzes user query intent
    2. Identifies missing information
    3. Generates structured hypothesis
    4. Provides confidence scoring
    5. Suggests clarification questions
    
    Example:
        >>> service = HypothesisService()
        >>> hypothesis = service.generate_hypothesis(
        ...     "Wie viel kostet ein Bauantrag?",
        ...     rag_context=["Stuttgart: 500€", "München: 800€"]
        ... )
        >>> print(hypothesis.confidence)
        ConfidenceLevel.LOW
        >>> print(hypothesis.information_gaps)
        [InformationGap(gap_type="location", severity="critical", ...)]
    """
    
    def __init__(
        self, 
        model_name: str = "llama3.1:8b",
        prompt_file: Optional[Path] = None,
        temperature: float = 0.3,
        max_tokens: int = 1000
    ):
        """
        Initialize HypothesisService.
        
        Args:
            model_name: Ollama model to use (default: llama2)
            prompt_file: Path to hypothesis prompt template (optional)
            temperature: LLM temperature (0.0-1.0, lower=more focused)
            max_tokens: Maximum response tokens
        """
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Initialize Ollama client
        try:
            self.ollama_client = DirectOllamaLLM(
                model=model_name,
                base_url="http://localhost:11434",
                temperature=temperature,
                num_predict=max_tokens
            )
            logger.info(f"✅ HypothesisService initialized with model: {model_name}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Ollama client: {e}")
            self.ollama_client = None
        
        # Load prompt template
        if prompt_file is None:
            prompt_file = Path(__file__).parent.parent / "prompts" / "hypothesis_prompt.txt"
        
        self.prompt_template = self._load_prompt_template(prompt_file)
        
        # Statistics
        self.stats = {
            "total_hypotheses": 0,
            "high_confidence": 0,
            "medium_confidence": 0,
            "low_confidence": 0,
            "unknown_confidence": 0,
            "with_gaps": 0,
            "with_critical_gaps": 0,
            "fallback_count": 0,
            "avg_generation_time_ms": 0.0
        }
    
    
    def _load_prompt_template(self, prompt_file: Path) -> str:
        """
        Load prompt template from file.
        
        Args:
            prompt_file: Path to prompt template
            
        Returns:
            Prompt template string
        """
        try:
            if prompt_file.exists():
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    template = f.read()
                logger.info(f"✅ Loaded prompt template from {prompt_file}")
                return template
            else:
                logger.warning(f"⚠️  Prompt file not found: {prompt_file}, using default")
                return self._get_default_prompt_template()
        except Exception as e:
            logger.error(f"❌ Error loading prompt template: {e}")
            return self._get_default_prompt_template()
    
    
    def _get_default_prompt_template(self) -> str:
        """
        Get default prompt template.
        
        Returns:
            Default prompt template string
        """
        return """You are an expert query analyzer for a German administrative document system.

Your task: Analyze user queries and generate a structured hypothesis about the query intent, required information, and processing steps.

USER QUERY: {query}

ADDITIONAL CONTEXT (optional):
{rag_context}

Please analyze this query and respond with a JSON object containing:
1. question_type: The type of question (fact_retrieval, comparison, procedural, calculation, opinion, timeline, causal, hypothetical)
2. primary_intent: The main goal of the query (1 sentence)
3. confidence: Your confidence level (high, medium, low, unknown)
4. required_information: List of information needed to answer fully
5. information_gaps: List of missing critical information (each with: gap_type, severity, suggested_query, examples)
6. assumptions: Any assumptions you're making
7. suggested_steps: Recommended processing steps
8. expected_response_type: Expected response format (text, table, list, document, etc.)

EXAMPLE RESPONSE:
{{
  "question_type": "procedural",
  "primary_intent": "Explain the building permit application process",
  "confidence": "high",
  "required_information": ["Process steps", "Required documents", "Timeline"],
  "information_gaps": [],
  "assumptions": ["User refers to residential building permit"],
  "suggested_steps": [
    "Search for building permit procedures",
    "Identify required documents",
    "Explain submission process"
  ],
  "expected_response_type": "text"
}}

Respond ONLY with valid JSON. Do not include explanations outside the JSON."""
    
    
    def generate_hypothesis(
        self, 
        query: str,
        rag_context: Optional[List[str]] = None,
        timeout: float = 30.0
    ) -> Hypothesis:
        """
        Generate hypothesis for a user query.
        
        Args:
            query: User query string
            rag_context: Optional RAG context (search results, document snippets)
            timeout: LLM timeout in seconds
            
        Returns:
            Hypothesis object with analysis results
        """
        start_time = datetime.now()
        
        try:
            # Build prompt
            rag_context_str = "\n".join(rag_context) if rag_context else "No additional context provided"
            
            # Use replace() instead of format() to avoid issues with JSON examples in template
            prompt = self.prompt_template.replace("{query}", query).replace("{rag_context}", rag_context_str)
            
            # Call LLM
            logger.info(f"🔍 Generating hypothesis for query: {query[:50]}...")
            
            if self.ollama_client is None:
                logger.warning("⚠️  Ollama client not available, using fallback hypothesis")
                return self._create_fallback_hypothesis(query)
            
            # Call DirectOllamaLLM.invoke()
            result = self.ollama_client.invoke(prompt=prompt)
            
            # Extract response text
            if hasattr(result, 'content') and result.content:
                response = result.content
            elif hasattr(result, 'response') and result.response:
                response = result.response
            elif hasattr(result, 'text') and result.text:
                response = result.text
            else:
                response = str(result)
            
            # Parse response
            hypothesis = self._parse_llm_response(query, response)
            
            # Update statistics
            generation_time = (datetime.now() - start_time).total_seconds() * 1000
            self._update_stats(hypothesis, generation_time)
            
            logger.info(f"✅ Hypothesis generated: {hypothesis.question_type.value}, "
                       f"confidence={hypothesis.confidence.value}, "
                       f"gaps={len(hypothesis.information_gaps)}, "
                       f"time={generation_time:.0f}ms")
            
            return hypothesis
            
        except Exception as e:
            logger.error(f"❌ Error generating hypothesis: {e}")
            generation_time = (datetime.now() - start_time).total_seconds() * 1000
            fallback = self._create_fallback_hypothesis(query)
            self._update_stats(fallback, generation_time, is_fallback=True)
            return fallback
    
    
    def _parse_llm_response(self, query: str, response: str) -> Hypothesis:
        """
        Parse LLM JSON response into Hypothesis object.
        
        Args:
            query: Original user query
            response: LLM response string
            
        Returns:
            Hypothesis object
        """
        try:
            # Extract JSON from response (handle markdown code blocks)
            json_str = response.strip()
            
            # Remove markdown code blocks
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0]
            elif "```" in json_str:
                # Try to find JSON block
                parts = json_str.split("```")
                for part in parts:
                    part = part.strip()
                    if part.startswith("{") and part.endswith("}"):
                        json_str = part
                        break
            
            # Remove leading/trailing whitespace
            json_str = json_str.strip()
            
            # If response starts with explanation, try to extract JSON
            if not json_str.startswith("{"):
                # Look for first { to last }
                start_idx = json_str.find("{")
                end_idx = json_str.rfind("}")
                if start_idx >= 0 and end_idx > start_idx:
                    json_str = json_str[start_idx:end_idx+1]
            
            # Parse JSON with dirtyjson (more robust) or fallback to standard json
            if DIRTYJSON_AVAILABLE:
                try:
                    data = dirtyjson.loads(json_str)
                    logger.debug("✓ Parsed JSON with dirtyjson")
                except Exception as e:
                    logger.warning(f"⚠️  dirtyjson failed: {e}, trying standard json")
                    data = json.loads(json_str)
            else:
                data = json.loads(json_str)
            
            # Validate required fields
            required_fields = ["question_type", "primary_intent", "confidence"]
            missing_fields = [f for f in required_fields if f not in data]
            if missing_fields:
                logger.error(f"❌ Missing required fields in LLM response: {missing_fields}")
                logger.info(f"Available keys: {list(data.keys())}")
                logger.info(f"Full response:\n{response[:1000]}")
                return self._create_fallback_hypothesis(query)
            
            # Convert question_type string to enum (handle case-insensitivity)
            question_type_str = data.get("question_type", "fact_retrieval").lower()
            valid_types = [qt.value for qt in QuestionType]
            if question_type_str not in valid_types:
                question_type_str = "fact_retrieval"  # default
            question_type = QuestionType(question_type_str)
            
            # Convert confidence string to enum (handle both lowercase and uppercase)
            confidence_str = data.get("confidence", "medium").lower()
            if confidence_str not in ["high", "medium", "low", "unknown"]:
                confidence_str = "medium"  # default
            confidence = ConfidenceLevel(confidence_str)
            
            # Parse information gaps
            gaps_data = data.get("information_gaps", [])
            information_gaps = []
            for gap_data in gaps_data:
                # Handle severity case-insensitivity
                severity_str = gap_data.get("severity", "optional").lower()
                if severity_str not in ["critical", "important", "optional"]:
                    severity_str = "optional"  # default
                
                gap = InformationGap(
                    gap_type=gap_data.get("gap_type", "unknown"),
                    severity=GapSeverity(severity_str),
                    suggested_query=gap_data.get("suggested_query", ""),
                    examples=gap_data.get("examples", [])
                )
                information_gaps.append(gap)
            
            # Create Hypothesis
            hypothesis = Hypothesis(
                query=query,
                question_type=question_type,
                primary_intent=data.get("primary_intent", "Answer user query"),
                confidence=confidence,
                required_information=data.get("required_information", []),
                information_gaps=information_gaps,
                assumptions=data.get("assumptions", []),
                suggested_steps=data.get("suggested_steps", []),
                expected_response_type=data.get("expected_response_type", "text"),
                metadata={
                    "model": self.model_name,
                    "temperature": self.temperature,
                    "raw_response": response[:500]  # Store first 500 chars
                }
            )
            
            return hypothesis
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse JSON response: {e}")
            logger.debug(f"Response was: {response[:500]}")
            logger.info(f"Full response for debugging:\n{response}")
            return self._create_fallback_hypothesis(query)
        except KeyError as e:
            logger.error(f"❌ Missing key in parsed JSON: {e}")
            logger.info(f"Available keys: {list(data.keys()) if 'data' in locals() else 'N/A'}")
            logger.info(f"Full response:\n{response[:1000]}")
            return self._create_fallback_hypothesis(query)
        except Exception as e:
            logger.error(f"❌ Error parsing LLM response: {e}")
            logger.info(f"Exception type: {type(e).__name__}")
            logger.info(f"Full response:\n{response[:1000]}")
            return self._create_fallback_hypothesis(query)
    
    
    def _create_fallback_hypothesis(self, query: str) -> Hypothesis:
        """
        Create fallback hypothesis when LLM fails.
        
        Args:
            query: User query
            
        Returns:
            Basic hypothesis with unknown confidence
        """
        return Hypothesis(
            query=query,
            question_type=QuestionType.FACT_RETRIEVAL,
            primary_intent="Answer user query (fallback mode)",
            confidence=ConfidenceLevel.UNKNOWN,
            required_information=["Query analysis unavailable"],
            information_gaps=[
                InformationGap(
                    gap_type="llm_failure",
                    severity=GapSeverity.IMPORTANT,
                    suggested_query="Unable to analyze query intent",
                    examples=[]
                )
            ],
            assumptions=["Fallback hypothesis due to LLM error"],
            suggested_steps=["Perform basic RAG search", "Return available results"],
            expected_response_type="text",
            metadata={
                "fallback": True,
                "reason": "LLM unavailable or error"
            }
        )
    
    
    def _update_stats(self, hypothesis: Hypothesis, generation_time_ms: float, is_fallback: bool = False):
        """
        Update service statistics.
        
        Args:
            hypothesis: Generated hypothesis
            generation_time_ms: Generation time in milliseconds
            is_fallback: Whether this was a fallback hypothesis
        """
        self.stats["total_hypotheses"] += 1
        
        if is_fallback:
            self.stats["fallback_count"] += 1
        
        # Update confidence stats
        if hypothesis.confidence == ConfidenceLevel.HIGH:
            self.stats["high_confidence"] += 1
        elif hypothesis.confidence == ConfidenceLevel.MEDIUM:
            self.stats["medium_confidence"] += 1
        elif hypothesis.confidence == ConfidenceLevel.LOW:
            self.stats["low_confidence"] += 1
        else:
            self.stats["unknown_confidence"] += 1
        
        # Update gap stats
        if len(hypothesis.information_gaps) > 0:
            self.stats["with_gaps"] += 1
        if hypothesis.has_critical_gaps():
            self.stats["with_critical_gaps"] += 1
        
        # Update average generation time
        total_time = self.stats["avg_generation_time_ms"] * (self.stats["total_hypotheses"] - 1)
        self.stats["avg_generation_time_ms"] = (total_time + generation_time_ms) / self.stats["total_hypotheses"]
    
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get service statistics.
        
        Returns:
            Dictionary with statistics
        """
        total = self.stats["total_hypotheses"]
        
        # If no hypotheses generated yet, return zeros
        if total == 0:
            return {
                **self.stats,
                "high_confidence_pct": 0.0,
                "medium_confidence_pct": 0.0,
                "low_confidence_pct": 0.0,
                "unknown_confidence_pct": 0.0,
                "with_gaps_pct": 0.0,
                "with_critical_gaps_pct": 0.0,
                "fallback_pct": 0.0
            }
        
        return {
            **self.stats,
            "high_confidence_pct": (self.stats["high_confidence"] / total) * 100,
            "medium_confidence_pct": (self.stats["medium_confidence"] / total) * 100,
            "low_confidence_pct": (self.stats["low_confidence"] / total) * 100,
            "unknown_confidence_pct": (self.stats["unknown_confidence"] / total) * 100,
            "with_gaps_pct": (self.stats["with_gaps"] / total) * 100,
            "with_critical_gaps_pct": (self.stats["with_critical_gaps"] / total) * 100,
            "fallback_pct": (self.stats["fallback_count"] / total) * 100
        }
    
    
    def reset_statistics(self):
        """Reset service statistics."""
        self.stats = {
            "total_hypotheses": 0,
            "high_confidence": 0,
            "medium_confidence": 0,
            "low_confidence": 0,
            "unknown_confidence": 0,
            "with_gaps": 0,
            "with_critical_gaps": 0,
            "fallback_count": 0,
            "avg_generation_time_ms": 0.0
        }
        logger.info("📊 Statistics reset")


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 80)
    print("HYPOTHESIS SERVICE - EXAMPLE USAGE")
    print("=" * 80)
    
    # Initialize service
    service = HypothesisService(model_name="llama3.1:8b")
    
    # Test queries
    test_queries = [
        {
            "query": "Bauantrag für Einfamilienhaus in Stuttgart",
            "context": [
                "Building permits in Stuttgart require 3 documents",
                "Processing time: 6-8 weeks"
            ]
        },
        {
            "query": "Wie viel kostet ein Bauantrag?",
            "context": None
        },
        {
            "query": "Was ist besser: Holz oder Stein für ein Gartenhaus?",
            "context": ["Material comparison guide available"]
        }
    ]
    
    # Generate hypotheses
    for i, test in enumerate(test_queries, 1):
        print(f"\n{i}. Testing query: {test['query']}")
        print("-" * 80)
        
        hypothesis = service.generate_hypothesis(
            query=test["query"],
            rag_context=test.get("context")
        )
        
        print(f"   Type: {hypothesis.question_type.value}")
        print(f"   Intent: {hypothesis.primary_intent}")
        print(f"   Confidence: {hypothesis.confidence.value}")
        print(f"   Information gaps: {len(hypothesis.information_gaps)}")
        
        if hypothesis.requires_clarification():
            print(f"   ! Requires clarification!")
            questions = hypothesis.get_clarification_questions()
            for j, q in enumerate(questions, 1):
                print(f"      {j}. {q}")
        else:
            print(f"   OK No clarification needed")
        
        if hypothesis.suggested_steps:
            print(f"   Suggested steps:")
            for j, step in enumerate(hypothesis.suggested_steps, 1):
                print(f"      {j}. {step}")
    
    # Show statistics
    print("\n" + "=" * 80)
    print("SERVICE STATISTICS")
    print("=" * 80)
    stats = service.get_statistics()
    print(f"Total hypotheses: {stats['total_hypotheses']}")
    print(f"High confidence: {stats['high_confidence_pct']:.1f}%")
    print(f"With gaps: {stats['with_gaps_pct']:.1f}%")
    print(f"Avg generation time: {stats['avg_generation_time_ms']:.0f}ms")
    print(f"Fallback rate: {stats['fallback_pct']:.1f}%")
    
    print("\nOK All examples completed!")
