#!/usr/bin/env python3
"""
VERITAS VLLM CLIENT
===================

vLLM Client Adapter for VERITAS Multi-Agent-Pipeline
Compatible with OpenAI-like API provided by vLLM

Features:
- OpenAI-compatible API interface (vLLM native)
- Same interface as VeritasOllamaClient for seamless integration
- Model management and health checks
- Streaming and non-streaming responses
- Support for prompt templates and pipeline stages
- Error handling and retry logic

Author: VERITAS System
Date: 2025-11-22
Version: 1.0
"""

import os
import sys
import time
import json
import asyncio
import logging
import httpx
from typing import Dict, List, Any, Optional, AsyncGenerator, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone

# Projekt-Root für Paketimporte sicherstellen
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.append(REPO_ROOT)

# Import shared enums
from backend.agents.veritas_shared_enums import PipelineStage

logger = logging.getLogger(__name__)

# ============================================================================
# VLLM CLIENT CONFIGURATION
# ============================================================================

class VLLMModel(Enum):
    """Verfügbare vLLM-Modelle für verschiedene Aufgaben"""
    
    # Common open-source models that work well with vLLM
    LLAMA3_8B = "meta-llama/Meta-Llama-3-8B-Instruct"
    LLAMA3_70B = "meta-llama/Meta-Llama-3-70B-Instruct"
    LLAMA3_2_3B = "meta-llama/Llama-3.2-3B-Instruct"
    MISTRAL_7B = "mistralai/Mistral-7B-Instruct-v0.3"
    MIXTRAL_8X7B = "mistralai/Mixtral-8x7B-Instruct-v0.1"
    PHI3_MINI = "microsoft/Phi-3-mini-4k-instruct"
    GEMMA_7B = "google/gemma-7b-it"

@dataclass
class VLLMRequest:
    """vLLM API Request Structure (OpenAI-compatible)"""
    model: str
    prompt: str
    temperature: float = 0.7
    max_tokens: int = 1000
    stream: bool = False
    system: Optional[str] = None
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    
@dataclass
class VLLMResponse:
    """vLLM API Response Structure"""
    model: str
    response: str
    done: bool
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    confidence_score: Optional[float] = None

# ============================================================================
# VERITAS VLLM CLIENT
# ============================================================================

class VeritasVLLMClient:
    """
    vLLM Client Adapter für VERITAS Multi-Agent-Pipeline
    
    Hauptfunktionen:
    - OpenAI-compatible API interface
    - Modell-Management und Health-Checks
    - Pipeline-Stage-spezifische Prompts
    - Real-time LLM-Kommentierung
    - Response-Generation mit Confidence-Scoring
    """
    
    def __init__(self, 
                 base_url: str = "http://localhost:8000",
                 api_key: Optional[str] = None,
                 timeout: int = 120,
                 max_retries: int = 3):
        """
        Initialisiert den Veritas vLLM Client
        
        Args:
            base_url: vLLM Server URL (OpenAI-compatible endpoint)
            api_key: Optional API key for authentication
            timeout: Request Timeout in Sekunden
            max_retries: Maximale Anzahl Wiederholungen
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        
        # HTTP Client with authentication headers if API key provided
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
            headers=headers
        )
        
        # Model Management
        self.available_models: Dict[str, Dict[str, Any]] = {}
        self.default_model = VLLMModel.LLAMA3_8B.value
        self.offline_mode = False
        
        # Prompt Templates (imported from Ollama client for compatibility)
        self.prompt_templates = self._initialize_prompt_templates()
        
        # Statistics
        self.stats: Dict[str, Any] = {
            "requests_sent": 0,
            "requests_successful": 0,
            "requests_failed": 0,
            "total_tokens": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_duration": 0.0,
            "average_response_time": 0.0,
            "model_usage": {},
        }
        
        logger.info(f"🤖 Veritas vLLM Client initialisiert (URL: {base_url})")
    
    async def __aenter__(self):
        """Async Context Manager Entry"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async Context Manager Exit"""
        await self.close()
    
    async def close(self):
        """Schließt HTTP Client"""
        await self.client.aclose()
    
    async def initialize(self) -> bool:
        """
        Initialisiert vLLM Client und prüft verfügbare Modelle
        
        Returns:
            bool: True wenn erfolgreich initialisiert
        """
        try:
            # Health Check
            if not await self.health_check():
                logger.warning("⚠️ vLLM Server nicht erreichbar – Offline-Fallback aktiviert")
                self.offline_mode = True
                if not self.available_models:
                    self.available_models = self._default_model_catalog()
                return False

            # Verfügbare Modelle laden
            await self.load_available_models()

            # Standard-Modell prüfen
            if self.default_model not in self.available_models:
                logger.warning(f"⚠️ Standard-Modell {self.default_model} nicht verfügbar")
                if self.available_models:
                    self.default_model = list(self.available_models.keys())[0]
                    logger.info(f"🔄 Verwende stattdessen: {self.default_model}")

            self.offline_mode = False
            logger.info("✅ vLLM Client erfolgreich initialisiert")
            return True

        except Exception as e:
            logger.error(f"❌ vLLM Client Initialisierung fehlgeschlagen: {e}")
            self.offline_mode = True
            return False
    
    async def health_check(self) -> bool:
        """
        Prüft vLLM Server Gesundheit
        
        Returns:
            bool: True wenn Server erreichbar
        """
        try:
            # Try OpenAI-compatible /v1/models endpoint
            response = await self.client.get(f"{self.base_url}/v1/models")
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"⚠️ vLLM Health Check fehlgeschlagen: {e}")
            return False
    
    async def load_available_models(self) -> Dict[str, Dict[str, Any]]:
        """
        Lädt Liste verfügbarer vLLM-Modelle via OpenAI-compatible API
        
        Returns:
            Dict: Verfügbare Modelle mit Metadaten
        """
        try:
            response = await self.client.get(f"{self.base_url}/v1/models")

            if response.status_code == 200:
                data = response.json()
                models: Dict[str, Dict[str, Any]] = {}

                for model_info in data.get('data', []):
                    model_id = model_info.get('id', '')
                    if not model_id:
                        continue
                    models[model_id] = {
                        'name': model_id,
                        'created': model_info.get('created', 0),
                        'owned_by': model_info.get('owned_by', 'unknown'),
                        'object': model_info.get('object', 'model'),
                    }

                if models:
                    self.available_models = models
                    self.offline_mode = False
                    logger.info(f"📋 {len(models)} vLLM-Modelle geladen: {list(models.keys())}")
                    return models

            raise httpx.HTTPStatusError(
                f"HTTP {response.status_code}", request=response.request, response=response
            )

        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Modell-Liste: {e}")
            self.offline_mode = True
            if not self.available_models:
                self.available_models = self._default_model_catalog()
            return self.available_models
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """
        Holt alle verfügbaren Modelle von vLLM für API-Endpoints
        
        Returns:
            List[Dict]: Liste von Modellen im Format [{"name": str, "size": str, "provider": str}]
        """
        try:
            response = await self.client.get(f"{self.base_url}/v1/models")
            
            if response.status_code == 200:
                data = response.json()
                models = []
                
                for model_info in data.get('data', []):
                    model_id = model_info.get('id', '')
                    if not model_id:
                        continue
                    
                    models.append({
                        "name": model_id,
                        "size": "Unknown",  # vLLM doesn't expose model size via API
                        "provider": "vllm",
                        "created": model_info.get('created', 0),
                        "owned_by": model_info.get('owned_by', '')
                    })
                
                # Sortiere alphabetisch
                models.sort(key=lambda x: x['name'])
                logger.info(f"✅ {len(models)} Modelle von vLLM abgerufen")
                return models
            
            logger.warning(f"⚠️ vLLM /v1/models returned status {response.status_code}")
            return []
            
        except Exception as e:
            logger.error(f"❌ list_models fehlgeschlagen: {e}")
            return []
    
    def _initialize_prompt_templates(self) -> Dict[PipelineStage, Dict[str, str]]:
        """
        Initialisiert Prompt-Templates für verschiedene Pipeline-Stages
        Identical to Ollama client for compatibility
        """
        # Import from Ollama client to maintain consistency
        from backend.agents.veritas_ollama_client import VeritasOllamaClient
        temp_client = VeritasOllamaClient()
        return temp_client.prompt_templates

    def _default_model_catalog(self) -> Dict[str, Dict[str, Any]]:
        """Fallback-Modellkatalog, falls vLLM nicht erreichbar ist."""

        return {
            model.value: {
                "name": model.value,
                "created": 0,
                "owned_by": "fallback",
                "object": "model"
            }
            for model in VLLMModel
        }

    async def generate_response(
        self, request: VLLMRequest, stream: bool = False
    ) -> Union[VLLMResponse, AsyncGenerator[VLLMResponse, None]]:
        """
        Sendet Anfrage an vLLM und verarbeitet Antwort (OpenAI-compatible)
        
        Args:
            request: vLLM Request Objekt
            stream: Stream Response aktivieren
            
        Returns:
            VLLMResponse oder AsyncGenerator für Streaming
        """
        
        last_error: Optional[str] = None

        for attempt in range(self.max_retries):
            try:
                self.stats['requests_sent'] += 1
                start_time = time.time()

                # Build messages for chat completion
                messages = []
                if request.system:
                    messages.append({"role": "system", "content": request.system})
                messages.append({"role": "user", "content": request.prompt})

                # Request Payload (OpenAI-compatible)
                payload: Dict[str, Any] = {
                    "model": request.model,
                    "messages": messages,
                    "temperature": request.temperature,
                    "max_tokens": request.max_tokens,
                    "top_p": request.top_p,
                    "frequency_penalty": request.frequency_penalty,
                    "presence_penalty": request.presence_penalty,
                    "stream": stream,
                }

                # HTTP Request senden to OpenAI-compatible endpoint
                response = await self.client.post(
                    f"{self.base_url}/v1/chat/completions",
                    json=payload,
                    timeout=self.timeout,
                )

                if response.status_code == 200:
                    duration = time.time() - start_time
                    self.stats['requests_successful'] += 1
                    self.stats['total_duration'] += duration
                    if self.stats['requests_successful']:
                        self.stats['average_response_time'] = (
                            self.stats['total_duration'] / self.stats['requests_successful']
                        )

                    # Model Usage Stats
                    model_key = request.model or self.default_model
                    self.stats['model_usage'].setdefault(model_key, 0)
                    self.stats['model_usage'][model_key] += 1

                    if stream:
                        return self._process_streaming_response(response, model_key)
                    return self._process_single_response(response.json(), model_key)

                raise httpx.HTTPStatusError(
                    f"HTTP {response.status_code}", request=response.request, response=response
                )

            except Exception as e:
                last_error = str(e)
                logger.warning(
                    "⚠️ vLLM Request Attempt %s/%s fehlgeschlagen: %s",
                    attempt + 1,
                    self.max_retries,
                    e,
                )
                if attempt == self.max_retries - 1:
                    self.stats['requests_failed'] += 1
                    # Return error response
                    return VLLMResponse(
                        model=request.model,
                        response=f"Error: {last_error}",
                        done=True,
                        confidence_score=0.0
                    )
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

        # Fallback error response
        return VLLMResponse(
            model=request.model,
            response=f"Error after {self.max_retries} retries: {last_error}",
            done=True,
            confidence_score=0.0
        )
    
    def _process_single_response(self, data: Dict[str, Any], model: str) -> VLLMResponse:
        """Verarbeitet einzelne vLLM Response (OpenAI format)"""
        
        # Extract response text from OpenAI format
        choices = data.get('choices', [])
        response_text = ""
        if choices:
            message = choices[0].get('message', {})
            response_text = message.get('content', '')
        
        # Extract token usage
        usage = data.get('usage', {})
        prompt_tokens = usage.get('prompt_tokens', 0)
        completion_tokens = usage.get('completion_tokens', 0)
        total_tokens = usage.get('total_tokens', 0)
        
        # Update stats
        self.stats['total_tokens'] += total_tokens
        self.stats['prompt_tokens'] += prompt_tokens
        self.stats['completion_tokens'] += completion_tokens
        
        # Confidence Score schätzen
        confidence_score = self._estimate_confidence_score(response_text, data)
        
        return VLLMResponse(
            model=model,
            response=response_text,
            done=True,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            confidence_score=confidence_score
        )
    
    async def _process_streaming_response(
        self, response, model: str
    ) -> AsyncGenerator[VLLMResponse, None]:
        """Verarbeitet Streaming vLLM Response (OpenAI SSE format)"""
        
        async for line in response.aiter_lines():
            if not line or not line.startswith('data: '):
                continue
            
            # Remove 'data: ' prefix
            json_str = line[6:]
            
            # Check for stream end
            if json_str.strip() == '[DONE]':
                break
            
            try:
                data = json.loads(json_str)
                choices = data.get('choices', [])
                if choices:
                    delta = choices[0].get('delta', {})
                    content = delta.get('content', '')
                    
                    if content:
                        yield VLLMResponse(
                            model=model,
                            response=content,
                            done=False,
                            confidence_score=0.7
                        )
            except json.JSONDecodeError:
                continue
    
    def _estimate_confidence_score(self, response_text: str, data: Dict[str, Any]) -> float:
        """
        Schätzt Confidence Score basierend auf Response-Charakteristika
        
        Args:
            response_text: Generierte Antwort
            data: vLLM Response Data
            
        Returns:
            float: Confidence Score zwischen 0.0 und 1.0
        """
        
        base_score = 0.7  # Basis-Vertrauen
        
        # Response-Länge berücksichtigen
        if len(response_text) > 100:
            base_score += 0.1
        
        # Strukturiertheit bewerten (vereinfacht)
        if any(marker in response_text for marker in ['**', '#', '1.', '-', '•']):
            base_score += 0.1
        
        # Token count berücksichtigen
        usage = data.get('usage', {})
        completion_tokens = usage.get('completion_tokens', 0)
        if completion_tokens > 50:
            base_score += 0.05
        
        return min(1.0, base_score)
    
    async def query_with_context(self,
                                query: str,
                                chat_session = None,
                                context_strategy: str = "sliding_window",
                                max_context_messages: int = 10,
                                model: Optional[str] = None,
                                temperature: float = 0.7,
                                max_tokens: int = 1000) -> VLLMResponse:
        """
        Sendet Query an LLM mit Chat-History-Context
        
        Args:
            query: Aktuelle Benutzeranfrage
            chat_session: ChatSession-Objekt mit Message-History
            context_strategy: Context-Strategie ("sliding_window", "relevance", "all")
            max_context_messages: Max. Anzahl Context-Messages
            model: Optionales Modell (default: self.default_model)
            temperature: Sampling-Temperature (0.0-1.0)
            max_tokens: Max. Response-Tokens
            
        Returns:
            VLLMResponse mit kontextueller Antwort
        """
        try:
            # Import Context Manager
            from backend.agents.context_manager import ConversationContextManager
            
            # Build conversation context
            context_manager = ConversationContextManager(max_tokens=2000)
            context_result = context_manager.build_conversation_context(
                chat_session=chat_session,
                current_query=query,
                strategy=context_strategy,
                max_messages=max_context_messages
            )
            
            conversation_context = context_result.get('context', '')
            token_count = context_result.get('token_count', 0)
            message_count = context_result.get('message_count', 0)
            
            logger.info(
                f"📝 Context erstellt: {message_count} Messages, "
                f"{token_count} Tokens, Strategie: {context_strategy}"
            )
            
            # Build enhanced system prompt with context
            if conversation_context:
                system_prompt = f"""Du bist VERITAS, ein KI-Assistent für deutsches Baurecht und Umweltrecht.

Bisherige Konversation:
{conversation_context}

Beantworte die aktuelle Frage unter Berücksichtigung der bisherigen Konversation.
Beziehe dich auf frühere Fragen und Antworten, wenn relevant.
"""
            else:
                # Fallback: Standard-System-Prompt ohne Context
                system_prompt = """Du bist VERITAS, ein KI-Assistent für deutsches Baurecht und Umweltrecht.

Beantworte die Frage präzise und fachlich korrekt.
"""
            
            # Create vLLM request with context-enhanced prompt
            request = VLLMRequest(
                model=model or self.default_model,
                prompt=query,
                system=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False
            )
            
            # Generate response
            response = await self.generate_response(request)
            
            logger.info(
                f"✅ Kontextuelle Antwort generiert: "
                f"{len(response.response)} Zeichen, "
                f"Confidence: {response.confidence_score:.2f}"
            )
            
            return response
            
        except Exception as e:
            logger.error(f"❌ query_with_context fehlgeschlagen: {e}")
            
            # Fallback: Query ohne Context
            logger.warning("⚠️ Fallback zu Query ohne Context")
            
            request = VLLMRequest(
                model=model or self.default_model,
                prompt=query,
                system="Du bist VERITAS, ein KI-Assistent für deutsches Baurecht und Umweltrecht.",
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False
            )
            
            return await self.generate_response(request)
    
    async def comment_pipeline_step(self, 
                                  current_step: str,
                                  progress_info: Dict[str, Any],
                                  context: Dict[str, Any] = None) -> str:
        """
        Generiert LLM-Kommentar für aktuellen Pipeline-Step
        
        Args:
            current_step: Name des aktuellen Pipeline-Steps
            progress_info: Progress-Informationen
            context: Zusätzlicher Kontext
            
        Returns:
            str: LLM-generierter Kommentar
        """
        
        template = self.prompt_templates[PipelineStage.STEP_COMMENTARY]

        context_payload = context or {}
        original_query = context_payload.get("original_query", "")
        stage_context = context_payload.get("stage_context", context_payload)

        prompt = template["user_template"].format(
            original_query=original_query or "",
            current_step=current_step,
            progress_info=json.dumps(progress_info, indent=2, ensure_ascii=False),
            context=json.dumps(stage_context, indent=2, ensure_ascii=False)
        )
        
        request = VLLMRequest(
            model=self.default_model,
            prompt=prompt,
            system=template["system"],
            temperature=0.8,  # Etwas kreativer für Kommentare
            max_tokens=100    # Kurze Kommentare
        )
        
        try:
            response = await self.generate_response(request)
            return response.response.strip()
        except Exception as e:
            logger.warning(f"⚠️ Pipeline-Step-Kommentar fehlgeschlagen: {e}")
            return f"Verarbeite {current_step}..."
    
    async def analyze_query(self, query: str, user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analysiert Query mit LLM für Agent-Pipeline-Erstellung
        
        Args:
            query: Benutzeranfrage
            user_context: Benutzerkontext
            
        Returns:
            Dict: Query-Analyse-Ergebnisse
        """
        
        template = self.prompt_templates[PipelineStage.QUERY_ANALYSIS]
        
        prompt = template["user_template"].format(
            query=query,
            user_context=json.dumps(user_context or {}, indent=2, ensure_ascii=False)
        )
        
        request = VLLMRequest(
            model=self.default_model,
            prompt=prompt,
            system=template["system"],
            temperature=0.3,  # Präzise Analyse
            max_tokens=500
        )
        
        try:
            response = await self.generate_response(request)
            
            # Versuche JSON zu parsen
            try:
                return json.loads(response.response)
            except json.JSONDecodeError:
                # Fallback bei JSON-Parse-Fehler
                return {
                    "complexity": "standard",
                    "domain": "general",
                    "required_agents": ["document_retrieval", "legal_framework"],
                    "estimated_time": 10,
                    "llm_analysis": response.response
                }
                
        except Exception as e:
            logger.error(f"❌ Query-Analyse fehlgeschlagen: {e}")
            return {
                "complexity": "standard",
                "domain": "general", 
                "required_agents": ["document_retrieval"],
                "estimated_time": 15,
                "error": str(e)
            }
    
    async def synthesize_agent_results(self,
                                     query: str,
                                     agent_results: Dict[str, Any],
                                     rag_context: Dict[str, Any] = None,
                                     aggregation_summary: Dict[str, Any] = None,
                                     consensus_summary: Dict[str, Any] = None,
                                     max_tokens: int = 1500) -> Dict[str, Any]:
        """
        Synthetisiert Multi-Agent-Ergebnisse zu finaler Antwort
        
        Args:
            query: Ursprüngliche Benutzeranfrage
            agent_results: Ergebnisse aller Agents
            rag_context: RAG-Kontext-Informationen
            aggregation_summary: Vorverarbeitete Aggregationsdaten
            consensus_summary: Statistische Konsensus-Informationen
            
        Returns:
            Dict: Synthetisierte finale Antwort
        """
        
        template = self.prompt_templates[PipelineStage.RESULT_AGGREGATION]
        
        prompt = template["user_template"].format(
            query=query,
            agent_results=json.dumps(agent_results, indent=2, ensure_ascii=False),
            rag_context=json.dumps(rag_context or {}, indent=2, ensure_ascii=False),
            aggregation_summary=json.dumps(aggregation_summary or {}, indent=2, ensure_ascii=False),
            consensus_summary=json.dumps(consensus_summary or {}, indent=2, ensure_ascii=False)
        )
        
        request = VLLMRequest(
            model=self.default_model,
            prompt=prompt,
            system=template["system"],
            temperature=0.5,  # Ausgewogen
            max_tokens=max_tokens
        )
        
        try:
            response = await self.generate_response(request)
            
            # Extract JSON from LLM response
            from backend.utils.json_extractor import extract_json_from_text, extract_next_steps, extract_related_topics
            
            clean_text, json_metadata = extract_json_from_text(response.response)
            
            # Confidence Score berechnen
            confidence_score = response.confidence_score or 0.8
            
            result = {
                "response_text": clean_text,
                "confidence_score": confidence_score,
                "model_used": request.model,
                "tokens_used": response.total_tokens,
                "prompt_tokens": response.prompt_tokens,
                "completion_tokens": response.completion_tokens,
                "llm_metadata": {
                    "temperature": request.temperature,
                    "max_tokens": request.max_tokens,
                }
            }
            
            # Add extracted JSON metadata
            if json_metadata:
                result["json_metadata"] = {
                    "next_steps": extract_next_steps(json_metadata),
                    "related_topics": extract_related_topics(json_metadata),
                    "raw": json_metadata
                }
                logger.info("✅ JSON-Metadaten aus LLM-Antwort extrahiert")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Agent-Result-Synthesis fehlgeschlagen: {e}", exc_info=True)
            return {
                "response_text": "Entschuldigung, bei der Verarbeitung Ihrer Anfrage ist ein Fehler aufgetreten.",
                "confidence_score": 0.0,
                "error": str(e)
            }
    
    def get_client_statistics(self) -> Dict[str, Any]:
        """Liefert Client-Statistiken"""
        
        return {
            "client_info": {
                "base_url": self.base_url,
                "timeout": self.timeout,
                "default_model": self.default_model,
                "available_models": list(self.available_models.keys()),
                "provider": "vllm"
            },
            "usage_stats": self.stats.copy(),
            "status": {
                "offline_mode": self.offline_mode,
            },
            "model_availability": {
                model.value: model.value in self.available_models
                for model in VLLMModel
            }
        }

# ============================================================================
# FACTORY FUNCTIONS & GLOBAL ACCESS
# ============================================================================

# Global vLLM Client Instance (Singleton Pattern)
_global_vllm_client: Optional[VeritasVLLMClient] = None

async def get_vllm_client() -> VeritasVLLMClient:
    """
    Liefert globale vLLM Client Instanz (Singleton Pattern)
    
    Returns:
        VeritasVLLMClient: Globale Client-Instanz
    """
    global _global_vllm_client
    
    if _global_vllm_client is None:
        _global_vllm_client = VeritasVLLMClient()
        await _global_vllm_client.initialize()
    
    return _global_vllm_client

def create_vllm_client(**kwargs) -> VeritasVLLMClient:
    """
    Factory für neue vLLM Client Instanz
    
    Returns:
        VeritasVLLMClient: Neue Client-Instanz
    """
    return VeritasVLLMClient(**kwargs)

# ============================================================================
# MAIN FOR TESTING
# ============================================================================

async def main():
    """Test des Veritas vLLM Clients"""
    
    async with VeritasVLLMClient() as client:
        print("🤖 Veritas vLLM Client Test")
        print("=" * 40)
        
        # Health Check
        health = await client.health_check()
        print(f"Health Check: {'✅ OK' if health else '❌ FAILED'}")
        
        if not health:
            print("❌ vLLM Server nicht erreichbar")
            print("Starte mit: python -m vllm.entrypoints.openai.api_server --model <model_name>")
            return
        
        # Verfügbare Modelle anzeigen
        print(f"Verfügbare Modelle: {list(client.available_models.keys())}")
        
        # Test Query Analysis
        print("\n📋 Test: Query Analysis")
        query_analysis = await client.analyze_query(
            "Wie ist die Luftqualität in München?",
            {"location": "München", "user_type": "citizen"}
        )
        print(f"Analyse: {json.dumps(query_analysis, indent=2, ensure_ascii=False)}")
        
        # Statistics
        print("\n📊 Client Statistics:")
        stats = client.get_client_statistics()
        print(f"Requests: {stats['usage_stats']['requests_successful']}/{stats['usage_stats']['requests_sent']}")
        print(f"Average Response Time: {stats['usage_stats']['average_response_time']:.2f}s")

if __name__ == "__main__":
    asyncio.run(main())
