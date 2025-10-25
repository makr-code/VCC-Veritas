"""
VERITAS Frontend API Client
============================

Unified API Client für das neue Backend v4.0.0

Unterstützt:
- Unified Query Endpoint (/api/query)
- Alle Modi: rag, hybrid, streaming, agent, ask
- UnifiedResponse Parsing
- IEEE Citations (35+ Felder)

Usage:
    client = VeritasAPIClient(base_url="http://localhost:5000")
    response = await client.query(
        query="Was regelt das BImSchG?",
        mode="rag",
        model="llama3.2"
    )
"""

import logging
import requests
from typing import Dict, Any, List, Optional, Literal
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)

# Type Aliases
QueryMode = Literal["rag", "hybrid", "streaming", "agent", "ask", "veritas"]


@dataclass
class SourceMetadata:
    """
    IEEE-Standard Source Metadata (35+ Felder)
    
    Alle Felder optional außer id, title, type
    """
    # Pflicht
    id: str
    title: str
    type: str = "document"
    
    # Basis
    file: Optional[str] = None
    page: Optional[int] = None
    url: Optional[str] = None
    excerpt: Optional[str] = None
    
    # IEEE Extended
    authors: Optional[str] = None
    ieee_citation: Optional[str] = None
    date: Optional[str] = None
    year: Optional[int] = None
    publisher: Optional[str] = None
    original_source: Optional[str] = None
    
    # Scoring
    similarity_score: Optional[float] = None
    rerank_score: Optional[float] = None
    quality_score: Optional[float] = None
    score: Optional[float] = None
    confidence: Optional[float] = None
    
    # Legal Domain
    rechtsgebiet: Optional[str] = None
    behörde: Optional[str] = None
    aktenzeichen: Optional[str] = None
    gericht: Optional[str] = None
    normtyp: Optional[str] = None
    fundstelle: Optional[str] = None
    
    # Assessment
    impact: Optional[str] = None
    relevance: Optional[str] = None
    
    # Agent Info
    agent: Optional[str] = None
    
    # Extra fields (für weitere IEEE-Felder)
    extra: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SourceMetadata':
        """Create from API response dict"""
        # Extrahiere bekannte Felder
        known_fields = {
            'id', 'title', 'type', 'file', 'page', 'url', 'excerpt',
            'authors', 'ieee_citation', 'date', 'year', 'publisher', 'original_source',
            'similarity_score', 'rerank_score', 'quality_score', 'score', 'confidence',
            'rechtsgebiet', 'behörde', 'aktenzeichen', 'gericht', 'normtyp', 'fundstelle',
            'impact', 'relevance', 'agent'
        }
        
        # Trenne bekannte von extra Feldern
        kwargs = {k: v for k, v in data.items() if k in known_fields}
        extra = {k: v for k, v in data.items() if k not in known_fields}
        
        return cls(**kwargs, extra=extra)


@dataclass
class ResponseMetadata:
    """Response Metadata"""
    model: str
    mode: str
    duration: float
    tokens_used: Optional[int] = None
    sources_count: int = 0
    complexity: Optional[str] = None
    domain: Optional[str] = None
    agents_involved: Optional[List[str]] = None
    search_method: Optional[str] = None
    quality_score: Optional[float] = None


@dataclass
class UnifiedResponse:
    """
    Unified Response von Backend v4.0.0
    
    Gilt für alle Query-Modi (rag, hybrid, streaming, agent, ask)
    """
    content: str
    sources: List[SourceMetadata]
    metadata: ResponseMetadata
    session_id: str
    timestamp: str
    
    # Optional
    agent_results: Optional[List[Dict[str, Any]]] = None
    external_data: Optional[List[Dict[str, Any]]] = None
    quality_metrics: Optional[Dict[str, Any]] = None
    processing_details: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UnifiedResponse':
        """Create from API response"""
        sources = [
            SourceMetadata.from_dict(src) 
            for src in data.get('sources', [])
        ]
        
        metadata = ResponseMetadata(**data['metadata'])
        
        return cls(
            content=data['content'],
            sources=sources,
            metadata=metadata,
            session_id=data['session_id'],
            timestamp=data['timestamp'],
            agent_results=data.get('agent_results'),
            external_data=data.get('external_data'),
            quality_metrics=data.get('quality_metrics'),
            processing_details=data.get('processing_details')
        )


class VeritasAPIClient:
    """
    🎯 Unified API Client für VERITAS Backend v4.0.0
    
    Usage:
        client = VeritasAPIClient()
        
        # RAG Query
        response = client.query("Was regelt das BImSchG?", mode="rag")
        
        # Simple Ask
        response = client.ask("Erkläre mir das BImSchG")
        
        # Hybrid Search
        response = client.hybrid_search("Immissionsschutz", top_k=10)
    """
    
    def __init__(
        self,
        base_url: str = "http://localhost:5000",
        timeout: int = 60,
        session_id: Optional[str] = None
    ):
        """
        Initialize API Client
        
        Args:
            base_url: Backend Base URL
            timeout: Request timeout in seconds
            session_id: Session ID (auto-generated if None)
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session_id = session_id
        
        logger.info(f"✅ VeritasAPIClient initialized: {self.base_url}")
    
    def query(
        self,
        query: str,
        mode: QueryMode = "rag",
        model: str = "llama3.2",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        top_k: int = 5,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        **kwargs
    ) -> UnifiedResponse:
        """
        🎯 Unified Query Endpoint - Alle Modi
        
        Args:
            query: User Query
            mode: Query Mode (rag, hybrid, streaming, agent, ask)
            model: LLM Model
            temperature: Temperature
            max_tokens: Max Tokens
            top_k: Top-K Results
            conversation_history: Multi-Turn Conversation
            **kwargs: Additional parameters
        
        Returns:
            UnifiedResponse mit IEEE Citations
        """
        endpoint = "/api/query"
        
        payload = {
            "query": query,
            "mode": mode,
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_k": top_k,
            "session_id": self.session_id,
            "conversation_history": conversation_history
        }
        
        # Add extra kwargs
        payload.update(kwargs)
        
        logger.info(f"📤 Query: mode={mode}, query={query[:50]}...")
        
        return self._post(endpoint, payload)
    
    def ask(
        self,
        query: str,
        model: str = "llama3.2",
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> UnifiedResponse:
        """
        Simple Ask - Direct LLM ohne RAG
        
        Args:
            query: User Query
            model: LLM Model
            temperature: Temperature
            max_tokens: Max Tokens
        
        Returns:
            UnifiedResponse (sources may be empty)
        """
        endpoint = "/api/query/ask"
        
        payload = {
            "query": query,
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "session_id": self.session_id
        }
        
        logger.info(f"📤 Ask: {query[:50]}...")
        
        return self._post(endpoint, payload)
    
    def rag_query(
        self,
        query: str,
        model: str = "llama3.2",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        top_k: int = 5
    ) -> UnifiedResponse:
        """
        RAG Query - Retrieval-Augmented Generation
        
        Args:
            query: User Query
            model: LLM Model
            temperature: Temperature
            max_tokens: Max Tokens
            top_k: Top-K Results
        
        Returns:
            UnifiedResponse mit IEEE Citations
        """
        endpoint = "/api/query/rag"
        
        payload = {
            "query": query,
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_k": top_k,
            "session_id": self.session_id
        }
        
        logger.info(f"📤 RAG: {query[:50]}...")
        
        return self._post(endpoint, payload)
    
    def hybrid_search(
        self,
        query: str,
        top_k: int = 10,
        bm25_weight: float = 0.5,
        dense_weight: float = 0.5,
        enable_reranking: bool = True,
        model: str = "llama3.2"
    ) -> UnifiedResponse:
        """
        Hybrid Search - BM25 + Dense + RRF
        
        Args:
            query: User Query
            top_k: Top-K Results
            bm25_weight: BM25 Weight
            dense_weight: Dense Weight
            enable_reranking: Enable Re-Ranking
            model: LLM Model
        
        Returns:
            UnifiedResponse mit IEEE Citations
        """
        endpoint = "/api/query/hybrid"
        
        payload = {
            "query": query,
            "top_k": top_k,
            "bm25_weight": bm25_weight,
            "dense_weight": dense_weight,
            "enable_reranking": enable_reranking,
            "model": model,
            "session_id": self.session_id
        }
        
        logger.info(f"📤 Hybrid Search: {query[:50]}...")
        
        return self._post(endpoint, payload)
    
    def health_check(self) -> Dict[str, Any]:
        """
        System Health Check
        
        Returns:
            Health status dict
        """
        endpoint = "/api/system/health"
        
        try:
            response = requests.get(
                f"{self.base_url}{endpoint}",
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {"status": "error", "error": str(e)}
    
    def get_system_info(self) -> Dict[str, Any]:
        """
        Get System Info
        
        Returns:
            System info dict
        """
        endpoint = "/api/system/info"
        
        try:
            response = requests.get(
                f"{self.base_url}{endpoint}",
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Get system info failed: {e}")
            return {"error": str(e)}
    
    def get_available_modes(self) -> List[Dict[str, Any]]:
        """
        Get Available Query Modes
        
        Returns:
            List of available modes
        """
        endpoint = "/api/system/modes"
        
        try:
            response = requests.get(
                f"{self.base_url}{endpoint}",
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            return data.get('modes', {})
        except Exception as e:
            logger.error(f"Get modes failed: {e}")
            return {}
    
    def _post(self, endpoint: str, payload: Dict[str, Any]) -> UnifiedResponse:
        """
        Internal POST request
        
        Args:
            endpoint: API endpoint
            payload: Request payload
        
        Returns:
            UnifiedResponse
        
        Raises:
            requests.HTTPError: On HTTP errors
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            logger.debug(f"POST {url}")
            logger.debug(f"Payload: {payload}")
            
            response = requests.post(
                url,
                json=payload,
                timeout=self.timeout,
                headers={
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                }
            )
            
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"✅ Response: {response.status_code}")
            logger.debug(f"Response data: {data}")
            
            # Parse to UnifiedResponse
            unified_response = UnifiedResponse.from_dict(data)
            
            logger.info(f"📊 Sources: {len(unified_response.sources)}")
            logger.info(f"⏱️  Duration: {unified_response.metadata.duration:.2f}s")
            
            return unified_response
            
        except requests.HTTPError as e:
            logger.error(f"❌ HTTP Error: {e}")
            logger.error(f"Response: {e.response.text if e.response else 'No response'}")
            raise
        except Exception as e:
            logger.error(f"❌ Error: {e}", exc_info=True)
            raise


# Convenience function
def create_api_client(
    base_url: str = "http://localhost:5000",
    session_id: Optional[str] = None
) -> VeritasAPIClient:
    """Create API Client instance"""
    return VeritasAPIClient(base_url=base_url, session_id=session_id)


# Example Usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 80)
    print("VERITAS API Client - Test")
    print("=" * 80)
    print()
    
    # Create client
    client = create_api_client()
    
    # Health Check
    print("🏥 Health Check...")
    health = client.health_check()
    print(f"   Status: {health.get('status')}")
    print()
    
    # Test Query
    print("🔍 Test Query...")
    try:
        response = client.query(
            query="Was regelt das BImSchG?",
            mode="rag",
            model="llama3.2"
        )
        
        print(f"✅ Response received!")
        print(f"   Content: {response.content[:100]}...")
        print(f"   Sources: {len(response.sources)}")
        print(f"   Duration: {response.metadata.duration:.2f}s")
        print()
        
        if response.sources:
            print("📚 Sources:")
            for src in response.sources[:3]:
                print(f"   [{src.id}] {src.title}")
                if src.ieee_citation:
                    print(f"       IEEE: {src.ieee_citation[:80]}...")
                if src.similarity_score:
                    print(f"       Score: {src.similarity_score:.2f}")
                print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("=" * 80)
