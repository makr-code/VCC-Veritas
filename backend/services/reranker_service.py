"""
LLM-Based Reranker Service (Phase 5 - Task 2.3)

This service improves search result relevance through LLM-based contextual
understanding. It re-scores search results based on semantic relevance to
the user's query intent.

Features:
- LLM-based relevance scoring
- Batch processing for efficiency
- Configurable scoring prompts
- Fallback to original scores
- Performance tracking

Author: VERITAS AI
Created: 14. Oktober 2025
Version: 1.0
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum
import logging
import json
import time

# Import LLM client
try:
    from backend.agents.llm.direct_ollama_llm import DirectOllamaLLM
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    logging.warning("DirectOllamaLLM not available - RerankerService will use fallback scoring")


class ScoringMode(Enum):
    """Reranking scoring modes"""
    RELEVANCE = "relevance"      # Pure relevance to query
    INFORMATIVENESS = "informativeness"  # Information quality
    COMBINED = "combined"        # Both factors


@dataclass
class RerankingResult:
    """Result of reranking operation"""
    document_id: str
    original_score: float
    reranked_score: float
    score_delta: float  # Change from original
    confidence: float   # LLM confidence in scoring
    reasoning: Optional[str] = None  # Why this score was given
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'document_id': self.document_id,
            'original_score': self.original_score,
            'reranked_score': self.reranked_score,
            'score_delta': self.score_delta,
            'confidence': self.confidence,
            'reasoning': self.reasoning
        }


class RerankerService:
    """
    LLM-Based Document Reranker
    
    Uses large language models to re-score search results based on
    contextual relevance to the user's query intent.
    """
    
    def __init__(
        self,
        model_name: str = "llama3.1:8b",
        scoring_mode: ScoringMode = ScoringMode.COMBINED,
        temperature: float = 0.1  # Low temperature for consistent scoring
    ):
        """
        Initialize Reranker Service
        
        Args:
            model_name: Ollama model to use for scoring
            scoring_mode: Scoring strategy
            temperature: LLM temperature (lower = more consistent)
        """
        self.logger = logging.getLogger(__name__)
        self.model_name = model_name
        self.scoring_mode = scoring_mode
        self.temperature = temperature
        
        # Initialize LLM client
        self.llm: Optional[DirectOllamaLLM] = None
        if LLM_AVAILABLE:
            try:
                self.llm = DirectOllamaLLM(model_name=model_name)
                self.logger.info(f"✅ RerankerService initialized with {model_name}")
            except Exception as e:
                self.logger.warning(f"Failed to initialize LLM: {e}")
                self.llm = None
        
        # Statistics
        self.stats = {
            'total_rerankings': 0,
            'llm_successes': 0,
            'fallback_count': 0,
            'avg_reranking_time_ms': 0.0,
            'score_improvements': 0,  # Documents with improved scores
            'score_degradations': 0   # Documents with lower scores
        }
    
    def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: Optional[int] = None,
        batch_size: int = 5
    ) -> List[RerankingResult]:
        """
        Rerank documents using LLM-based scoring
        
        Args:
            query: User's search query
            documents: List of document dicts with 'content', 'relevance_score', 'document_id'
            top_k: Return only top K results (None = all)
            batch_size: Process documents in batches of this size
            
        Returns:
            List of RerankingResult objects, sorted by reranked_score
            
        Example:
            >>> reranker = RerankerService()
            >>> documents = [
            ...     {'document_id': 'doc1', 'content': '...', 'relevance_score': 0.8},
            ...     {'document_id': 'doc2', 'content': '...', 'relevance_score': 0.7}
            ... ]
            >>> results = reranker.rerank("Bauantrag Stuttgart", documents, top_k=5)
        """
        start_time = time.time()
        
        if not documents:
            return []
        
        self.logger.info(f"Reranking {len(documents)} documents for query: '{query}'")
        
        results = []
        
        # Process in batches for efficiency
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i+batch_size]
            batch_results = self._rerank_batch(query, batch)
            results.extend(batch_results)
        
        # Sort by reranked score
        results.sort(key=lambda r: r.reranked_score, reverse=True)
        
        # Apply top_k limit
        if top_k:
            results = results[:top_k]
        
        # Update statistics
        reranking_time = (time.time() - start_time) * 1000
        self.stats['total_rerankings'] += 1
        self.stats['avg_reranking_time_ms'] = (
            (self.stats['avg_reranking_time_ms'] * (self.stats['total_rerankings'] - 1) + reranking_time)
            / self.stats['total_rerankings']
        )
        
        # Count improvements/degradations
        for result in results:
            if result.score_delta > 0:
                self.stats['score_improvements'] += 1
            elif result.score_delta < 0:
                self.stats['score_degradations'] += 1
        
        self.logger.info(
            f"Reranking complete: {len(results)} documents, "
            f"time: {reranking_time:.2f}ms"
        )
        
        return results
    
    def _rerank_batch(
        self,
        query: str,
        documents: List[Dict[str, Any]]
    ) -> List[RerankingResult]:
        """Rerank a batch of documents"""
        if self.llm is None:
            # Fallback: Return original scores
            return self._fallback_scoring(documents)
        
        try:
            # Build scoring prompt
            prompt = self._build_scoring_prompt(query, documents)
            
            # Call LLM
            response = self.llm.generate(
                prompt=prompt,
                temperature=self.temperature,
                max_tokens=500
            )
            
            # Parse scores
            scores = self._parse_llm_scores(response, len(documents))
            
            # Create RerankingResult objects
            results = []
            for i, doc in enumerate(documents):
                original_score = doc.get('relevance_score', 0.5)
                reranked_score = scores.get(i, original_score)
                
                results.append(RerankingResult(
                    document_id=doc['document_id'],
                    original_score=original_score,
                    reranked_score=reranked_score,
                    score_delta=reranked_score - original_score,
                    confidence=0.8  # Default confidence
                ))
            
            self.stats['llm_successes'] += 1
            return results
            
        except Exception as e:
            self.logger.error(f"LLM reranking failed: {e}")
            self.stats['fallback_count'] += 1
            return self._fallback_scoring(documents)
    
    def _build_scoring_prompt(
        self,
        query: str,
        documents: List[Dict[str, Any]]
    ) -> str:
        """Build prompt for LLM scoring"""
        prompt = f"""You are a search result relevance evaluator. Rate each document's relevance to the user's query on a scale of 0.0 to 1.0.

Query: "{query}"

Documents to evaluate:
"""
        
        for i, doc in enumerate(documents):
            content_preview = doc.get('content', '')[:300]  # First 300 chars
            prompt += f"\nDocument {i}:\n{content_preview}\n"
        
        if self.scoring_mode == ScoringMode.RELEVANCE:
            prompt += "\n\nRate each document based on RELEVANCE to the query."
        elif self.scoring_mode == ScoringMode.INFORMATIVENESS:
            prompt += "\n\nRate each document based on INFORMATIVENESS and detail quality."
        else:  # COMBINED
            prompt += "\n\nRate each document based on both RELEVANCE and INFORMATIVENESS."
        
        prompt += """

Respond with ONLY a JSON array of scores, one per document:
[0.9, 0.7, 0.5, ...]

Scores:"""
        
        return prompt
    
    def _parse_llm_scores(
        self,
        response: str,
        expected_count: int
    ) -> Dict[int, float]:
        """Parse LLM response to extract scores"""
        try:
            # Try to find JSON array in response
            import re
            # Updated regex to handle negative numbers and decimals
            json_match = re.search(r'\[[\d\s,\.\-]+\]', response)
            
            if json_match:
                scores_array = json.loads(json_match.group(0))
                
                # Validate and normalize scores
                scores = {}
                for i, score in enumerate(scores_array[:expected_count]):
                    # Clamp to 0.0-1.0 range
                    normalized_score = max(0.0, min(1.0, float(score)))
                    scores[i] = normalized_score
                
                return scores
            
            # If JSON parsing fails, return empty dict (will use fallback)
            self.logger.warning("Failed to parse LLM scores, using fallback")
            return {}
            
        except Exception as e:
            self.logger.error(f"Score parsing error: {e}")
            return {}
    
    def _fallback_scoring(
        self,
        documents: List[Dict[str, Any]]
    ) -> List[RerankingResult]:
        """Fallback scoring when LLM is unavailable"""
        results = []
        
        for doc in documents:
            original_score = doc.get('relevance_score', 0.5)
            
            results.append(RerankingResult(
                document_id=doc['document_id'],
                original_score=original_score,
                reranked_score=original_score,  # No change
                score_delta=0.0,
                confidence=1.0,  # We're certain about the fallback
                reasoning="Fallback: LLM unavailable"
            ))
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get reranking statistics"""
        return {
            **self.stats,
            'llm_success_rate': (
                self.stats['llm_successes'] / self.stats['total_rerankings']
                if self.stats['total_rerankings'] > 0 else 0.0
            ),
            'fallback_rate': (
                self.stats['fallback_count'] / self.stats['total_rerankings']
                if self.stats['total_rerankings'] > 0 else 0.0
            )
        }
    
    def reset_statistics(self):
        """Reset statistics counters"""
        for key in self.stats:
            self.stats[key] = 0 if isinstance(self.stats[key], int) else 0.0


# Test function
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("="*80)
    print("RERANKER SERVICE - STANDALONE TEST")
    print("="*80)
    
    # Initialize service
    reranker = RerankerService(model_name="llama3.1:8b")
    print(f"\n✅ RerankerService initialized (LLM available: {LLM_AVAILABLE})")
    
    # Test documents
    query = "Bauantrag für Einfamilienhaus in Stuttgart"
    documents = [
        {
            'document_id': 'doc1',
            'content': 'Ein Bauantrag in Stuttgart erfordert verschiedene Unterlagen...',
            'relevance_score': 0.85
        },
        {
            'document_id': 'doc2',
            'content': 'Die Geschichte der Automobilindustrie in Stuttgart...',
            'relevance_score': 0.60
        },
        {
            'document_id': 'doc3',
            'content': 'Bauantragsverfahren für Wohngebäude: Schritt-für-Schritt Anleitung...',
            'relevance_score': 0.75
        }
    ]
    
    print(f"\n📝 Test Query: \"{query}\"")
    print(f"   Documents: {len(documents)}")
    
    # Rerank
    print("\n🔄 Reranking...")
    results = reranker.rerank(query, documents)
    
    # Display results
    print("\n📊 Reranking Results:")
    print("   " + "-"*76)
    for i, result in enumerate(results, 1):
        print(f"\n   {i}. Document: {result.document_id}")
        print(f"      Original score:  {result.original_score:.3f}")
        print(f"      Reranked score:  {result.reranked_score:.3f}")
        print(f"      Delta:           {result.score_delta:+.3f}")
        if result.reasoning:
            print(f"      Reasoning:       {result.reasoning}")
    
    # Statistics
    print("\n" + "   " + "-"*76)
    print("\n📈 Statistics:")
    stats = reranker.get_statistics()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("\n" + "="*80)
    print("✅ RerankerService test complete!")
    print("="*80)
