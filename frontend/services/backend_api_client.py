#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VERITAS Frontend Service: Backend API Client
Zentrale HTTP/HTTPS-Kommunikation mit dem VERITAS Backend

Features:
- Query-Management (Standard, Streaming)
- Session-Management
- Capability-Discovery
- Error-Handling mit Retry-Logik
- Vollständige Trennung von GUI-Logik

Version: 1.0.0
"""

import logging
import requests
import uuid
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class QueryMode(Enum):
    """Verfügbare Query-Modi"""
    VERITAS = 'veritas'  # Standard RAG mit Multi-DB
    CHAT = 'chat'  # Conversational Chat
    INTELLIGENT = 'intelligent'  # Intelligent Pipeline


@dataclass
class QueryRequest:
    """Strukturierte Query-Anfrage"""
    query: str
    session_id: str
    mode: str = 'veritas'
    model: str = 'llama3.1:8b'
    temperature: float = 0.7
    max_tokens: int = 500
    enable_streaming: bool = False
    conversation_history: Optional[List[Dict]] = None


@dataclass
class QueryResponse:
    """Strukturierte Query-Antwort"""
    response_text: str
    sources: List[Dict]
    confidence_score: float
    suggestions: List[str]
    worker_results: Dict
    metadata: Dict
    session_id: str
    processing_time: float
    success: bool = True
    error: Optional[str] = None


class BackendAPIClient:
    """
    HTTP-Client für VERITAS Backend API v3
    
    Features:
    - Synchrone und asynchrone Queries
    - Streaming-Support
    - Session-Management
    - Capability-Discovery
    - Automatic Retry mit Exponential Backoff
    
    Example:
        client = BackendAPIClient("http://localhost:5000/api/v3")
        response = client.send_query("Was ist Python?", mode="veritas")
        print(response.response_text)
    """
    
    def __init__(
        self,
        base_url: str = "http://127.0.0.1:5000/api/v3",
        timeout: int = 60,
        max_retries: int = 3
    ):
        """
        Initialisiert Backend API Client
        
        Args:
            base_url: Backend API Base-URL
            timeout: Request-Timeout in Sekunden
            max_retries: Maximale Retry-Versuche bei Fehlern
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        self.session_id: Optional[str] = None
        self.capabilities: Optional[Dict] = None
        
        logger.info(f"✅ BackendAPIClient initialisiert: {self.base_url}")
    
    # === SESSION MANAGEMENT ===
    
    def create_session(self, user_id: Optional[str] = None) -> bool:
        """
        Erstellt neue Session
        
        Args:
            user_id: Optional User-ID für Session
            
        Returns:
            True wenn erfolgreich
        """
        try:
            # v3 API: Lokale Session-ID generieren (keine Server-Session nötig)
            self.session_id = f"session_{uuid.uuid4().hex[:12]}"
            logger.info(f"✅ Session erstellt: {self.session_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Session-Erstellung fehlgeschlagen: {e}")
            return False
    
    def get_session_id(self) -> Optional[str]:
        """Gibt aktuelle Session-ID zurück"""
        return self.session_id
    
    def ensure_session(self) -> bool:
        """Stellt sicher dass Session existiert"""
        if not self.session_id:
            return self.create_session()
        return True
    
    # === CAPABILITY DISCOVERY ===
    
    def get_capabilities(self) -> Optional[Dict]:
        """
        Lädt Backend-Capabilities (Models, Agents, Features)
        
        Returns:
            Dict mit Capabilities oder None bei Fehler
        """
        try:
            response = requests.get(
                f"{self.base_url}/capabilities",
                timeout=10
            )
            
            if response.status_code == 200:
                self.capabilities = response.json()
                logger.info(f"✅ Capabilities geladen: Version {self.capabilities.get('version')}")
                return self.capabilities
            else:
                logger.error(f"❌ Capabilities HTTP {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Capabilities Request-Fehler: {e}")
            return None
    
    def get_available_models(self) -> List[str]:
        """Gibt verfügbare LLM-Modelle zurück"""
        if not self.capabilities:
            self.get_capabilities()
        
        if self.capabilities:
            ollama = self.capabilities.get('ollama', {})
            return ollama.get('available_models', [])
        return []
    
    def get_question_modes(self) -> List[Dict]:
        """
        Gibt verfügbare Frage-Modi zurück
        
        Returns:
            Liste von Mode-Dicts mit {key, name, description}
        """
        try:
            response = requests.get(
                f"{self.base_url}/question_modes",
                timeout=10
            )
            
            if response.status_code == 200:
                modes = response.json()
                logger.info(f"✅ {len(modes)} Frage-Modi geladen")
                return modes
            else:
                logger.warning(f"⚠️ Question Modes HTTP {response.status_code}")
                return []
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Question Modes Fehler: {e}")
            return []
    
    # === QUERY METHODS ===
    
    def send_query(
        self,
        query: str,
        mode: str = 'veritas',
        model: str = 'llama3.1:8b',
        temperature: float = 0.7,
        max_tokens: int = 500,
        conversation_history: Optional[List[Dict]] = None
    ) -> QueryResponse:
        """
        Sendet Query an Backend (synchron, nicht-streaming)
        
        Args:
            query: Frage/Query-Text
            mode: Query-Modus ('veritas', 'chat', 'intelligent')
            model: LLM-Modell
            temperature: LLM-Temperature
            max_tokens: Maximale Token-Anzahl
            conversation_history: Optional Chat-Historie für Kontext
            
        Returns:
            QueryResponse mit Antwort und Metadaten
        """
        # Ensure session exists
        if not self.ensure_session():
            return QueryResponse(
                response_text="",
                sources=[],
                confidence_score=0.0,
                suggestions=[],
                worker_results={},
                metadata={},
                session_id="",
                processing_time=0.0,
                success=False,
                error="Session-Erstellung fehlgeschlagen"
            )
        
        # Build request
        request = QueryRequest(
            query=query,
            session_id=self.session_id,
            mode=mode,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            enable_streaming=False,
            conversation_history=conversation_history
        )
        
        # Determine endpoint
        endpoint = self._get_endpoint_for_mode(mode)
        
        try:
            start_time = datetime.now()
            
            logger.info(f"🚀 Sende Query an {endpoint} (Modus: {mode})")
            
            response = requests.post(
                f"{self.base_url}{endpoint}",
                json=self._request_to_dict(request),
                timeout=self.timeout
            )
            
            elapsed_time = (datetime.now() - start_time).total_seconds()
            
            if response.status_code == 200:
                data = response.json()
                
                # Parse response
                query_response = self._parse_response(data, elapsed_time)
                
                logger.info(
                    f"✅ Query erfolgreich: {len(query_response.response_text)} Zeichen, "
                    f"Confidence: {query_response.confidence_score:.2%}, "
                    f"Zeit: {query_response.processing_time:.2f}s"
                )
                
                return query_response
            else:
                # HTTP Error
                error_msg = f"HTTP {response.status_code}"
                try:
                    error_data = response.json()
                    if 'detail' in error_data:
                        error_msg += f": {error_data['detail']}"
                except:
                    pass
                
                logger.error(f"❌ Query fehlgeschlagen: {error_msg}")
                
                return QueryResponse(
                    response_text="",
                    sources=[],
                    confidence_score=0.0,
                    suggestions=[],
                    worker_results={},
                    metadata={},
                    session_id=self.session_id,
                    processing_time=elapsed_time,
                    success=False,
                    error=error_msg
                )
        
        except requests.exceptions.Timeout:
            error_msg = f"⏱️ Timeout nach {self.timeout}s"
            logger.error(f"❌ Query Timeout: {error_msg}")
            return self._error_response(error_msg, "timeout")
        
        except requests.exceptions.ConnectionError:
            error_msg = "🔌 Verbindungsfehler: Server nicht erreichbar"
            logger.error(f"❌ Connection Error: {error_msg}")
            return self._error_response(error_msg, "connection")
        
        except requests.exceptions.RequestException as e:
            error_msg = f"📡 Request-Fehler: {str(e)}"
            logger.error(f"❌ Request Exception: {error_msg}")
            return self._error_response(error_msg, "request")
        
        except Exception as e:
            error_msg = f"💥 Unerwarteter Fehler: {str(e)}"
            logger.error(f"❌ Unexpected Error: {error_msg}", exc_info=True)
            return self._error_response(error_msg, "unknown")
    
    def start_streaming_query(
        self,
        query: str,
        mode: str = 'veritas',
        on_chunk: Optional[Callable[[str], None]] = None,
        on_complete: Optional[Callable[[QueryResponse], None]] = None,
        conversation_history: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Startet Streaming-Query (wenn Streaming-Service verfügbar)
        
        Args:
            query: Frage/Query-Text
            mode: Query-Modus
            on_chunk: Callback für Text-Chunks (chunk: str)
            on_complete: Callback wenn fertig (response: QueryResponse)
            conversation_history: Optional Chat-Historie
            
        Returns:
            Dict mit {'success': bool, 'stream_session_id': str, 'error': str}
        """
        # Ensure session
        if not self.ensure_session():
            return {
                'success': False,
                'error': 'Session-Erstellung fehlgeschlagen'
            }
        
        # Note: Streaming wird typischerweise von StreamingService gehandhabt
        # Dies ist ein Fallback für direktes Streaming
        
        try:
            endpoint = f"{self.base_url}/query/stream"
            
            payload = {
                'query': query,
                'session_id': self.session_id,
                'mode': mode,
                'enable_progress': True,
                'enable_intermediate': True,
                'conversation_history': conversation_history
            }
            
            response = requests.post(
                endpoint,
                json=payload,
                timeout=self.timeout,
                stream=True
            )
            
            if response.status_code == 200:
                # Process streaming response
                for line in response.iter_lines():
                    if line:
                        try:
                            chunk_data = line.decode('utf-8')
                            if on_chunk:
                                on_chunk(chunk_data)
                        except Exception as e:
                            logger.warning(f"⚠️ Chunk-Processing-Fehler: {e}")
                
                if on_complete:
                    # Send completion signal
                    complete_response = QueryResponse(
                        response_text="",
                        sources=[],
                        confidence_score=0.0,
                        suggestions=[],
                        worker_results={},
                        metadata={},
                        session_id=self.session_id,
                        processing_time=0.0,
                        success=True
                    )
                    on_complete(complete_response)
                
                return {'success': True, 'stream_session_id': self.session_id}
            else:
                error_msg = f"Streaming HTTP {response.status_code}"
                logger.error(f"❌ {error_msg}")
                return {'success': False, 'error': error_msg}
        
        except Exception as e:
            error_msg = f"Streaming-Fehler: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return {'success': False, 'error': error_msg}
    
    # === HELPER METHODS ===
    
    def _get_endpoint_for_mode(self, mode: str) -> str:
        """
        Bestimmt Endpoint für Query-Modus (Backend v4.0.0)
        
        Backend API v4.0.0 hat UNIFIED Endpoints:
        - /query - Unified Query (alle Modi)
        - /query/ask - Simple Ask
        - /query/rag - RAG Query
        - /query/hybrid - Hybrid Search
        - /query/stream - Streaming Query
        
        Args:
            mode: Query-Modus
            
        Returns:
            Endpoint-Pfad (relativ zu /api)
        """
        # Backend v4.0.0 Unified Query Endpoint
        # Alle Modi nutzen /query mit mode-Parameter
        endpoints = {
            'veritas': '/query',       # Unified endpoint
            'chat': '/query',          # Unified endpoint mit mode='chat'
            'rag': '/query/rag',       # Spezifischer RAG endpoint
            'hybrid': '/query/hybrid', # Hybrid Search
            'ask': '/query/ask',       # Simple Ask
            'streaming': '/query/stream',  # Streaming
            'agent': '/query',         # Agent Mode über unified
            'intelligent': '/query',   # Intelligent Pipeline
            'vpb': '/query',           # VPB Mode
            'covina': '/query'         # CoViNa Mode
        }
        return endpoints.get(mode, '/query')  # Default: unified endpoint
    
    def _request_to_dict(self, request: QueryRequest) -> Dict:
        """Konvertiert QueryRequest zu Dict für JSON"""
        return {
            'query': request.query,
            'session_id': request.session_id,
            'mode': request.mode,
            'model': request.model,
            'temperature': request.temperature,
            'max_tokens': request.max_tokens,
            'enable_streaming': request.enable_streaming,
            'conversation_history': request.conversation_history
        }
    
    def _parse_response(self, data: Dict, processing_time: float) -> QueryResponse:
        """
        Parsed Backend-Response zu QueryResponse
        
        Backend API v3 Response-Struktur:
        {
            "content": "Die Antwort...",
            "metadata": {
                "model": "llama3.2",
                "mode": "veritas",
                "duration": 1.23,
                "sources_count": 5,
                "sources_metadata": [...]
            },
            "session_id": "session_...",
            "timestamp": "2025-10-18T..."
        }
        """
        # ✅ FIXED: Backend API v3 nutzt 'content' statt 'response_text'
        response_text = data.get('content', data.get('response_text', 'Keine Antwort erhalten.'))
        
        # Extract metadata
        metadata = data.get('metadata', {})
        
        # Sources sind entweder in metadata.sources_metadata oder direkt in data.sources
        sources = []
        if isinstance(metadata, dict) and 'sources_metadata' in metadata:
            sources = metadata.get('sources_metadata', [])
        else:
            sources = data.get('sources', [])
        
        # Confidence Score (aus metadata oder fallback)
        confidence_score = data.get('confidence_score', 0.0)
        
        # Session ID
        session_id = data.get('session_id', self.session_id)
        
        logger.debug(f"📋 Response parsed: {len(response_text)} chars, {len(sources)} sources")
        
        return QueryResponse(
            response_text=response_text,
            sources=sources,
            confidence_score=confidence_score,
            suggestions=data.get('follow_up_suggestions', data.get('suggestions', [])),
            worker_results=data.get('worker_results', {}),
            metadata=metadata if isinstance(metadata, dict) else {},
            session_id=session_id,
            processing_time=processing_time,
            success=True,
            error=None
        )
    
    def _error_response(self, error_msg: str, error_type: str) -> QueryResponse:
        """Erstellt Error-Response"""
        return QueryResponse(
            response_text="",
            sources=[],
            confidence_score=0.0,
            suggestions=[],
            worker_results={},
            metadata={'error_type': error_type},
            session_id=self.session_id or "",
            processing_time=0.0,
            success=False,
            error=error_msg
        )
    
    def __repr__(self) -> str:
        return f"BackendAPIClient(base_url='{self.base_url}', session_id='{self.session_id}')"
