#!/usr/bin/env python3
"""
VERITAS OLLAMA CLIENT
====================

Native Ollama Client für VERITAS Multi-Agent-Pipeline
Unterstützt Real-time LLM-Kommentare und Response-Generation

Features:
- Modell-Management (llama3.1:8b, llama3.1:8b-instruct, codellama:7b)
- Prompt-Templates für verschiedene Pipeline-Stages
- Real-time Kommentierung von Agent-Zwischenschritten
- Error-Handling und Retry-Logic
- Response-Generation mit Confidence-Scoring

Author: VERITAS System
Date: 2025-09-28
Version: 1.0
"""

import asyncio
import json
import logging
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, AsyncGenerator, Dict, List, Optional, Union

import httpx

# Projekt-Root für Paketimporte sicherstellen
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.append(REPO_ROOT)

from native_ollama_integration import DirectOllamaEmbeddings, DirectOllamaLLM, OllamaInvocationResult

# Import shared enums
from backend.agents.veritas_shared_enums import PipelineStage

logger = logging.getLogger(__name__)

# ============================================================================
# OLLAMA CLIENT CONFIGURATION
# ============================================================================


class OllamaModel(Enum):
    """Verfügbare Ollama-Modelle für verschiedene Aufgaben"""

    LLAMA3_MAIN = "llama3:latest"  # General Purpose (8B)
    LLAMA3_2 = "llama3.2:latest"  # Llama 3.2 (3.2B)
    LLAMA3_INSTRUCT = "llama3.1:8b-instruct"  # Instruction Tuning (falls verfügbar)
    CODELLAMA = "codellama:latest"  # Code Generation (7B)
    MIXTRAL = "mixtral:latest"  # Large Model (46.7B)
    GEMMA3 = "gemma3:latest"  # Alternative (4.3B)
    PHI3 = "phi3:latest"  # Lightweight Alternative (3.8B)


@dataclass
class OllamaRequest:
    """Ollama API Request Structure"""

    model: str
    prompt: str
    temperature: float = 0.7
    max_tokens: int = 1000
    stream: bool = False
    system: Optional[str] = None
    context: Optional[List[int]] = None


@dataclass
class OllamaResponse:
    """Ollama API Response Structure"""

    model: str
    response: str
    done: bool
    context: Optional[List[int]] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    eval_count: Optional[int] = None
    eval_duration: Optional[int] = None
    total_duration: Optional[int] = None
    confidence_score: Optional[float] = None


# ============================================================================
# VERITAS OLLAMA CLIENT
# ============================================================================


class VeritasOllamaClient:
    """
    Native Ollama Client für VERITAS Multi-Agent-Pipeline

    Hauptfunktionen:
    - Modell-Management und Health-Checks
    - Pipeline-Stage-spezifische Prompts
    - Real-time LLM-Kommentierung
    - Response-Generation mit Confidence-Scoring
    """

    def __init__(self, base_url: str = "http://localhost:11434", timeout: int = 30, max_retries: int = 3):
        """
        Initialisiert den Veritas Ollama Client

        Args:
            base_url: Ollama Server URL
            timeout: Request Timeout in Sekunden
            max_retries: Maximale Anzahl Wiederholungen
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries

        # HTTP Client
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout), limits=httpx.Limits(max_connections=10, max_keepalive_connections=5)
        )

        # Model Management
        self.available_models: Dict[str, Dict[str, Any]] = {}
        self.default_model = OllamaModel.LLAMA3_MAIN.value
        self.offline_mode = False
        self._fallback_llm: Optional[DirectOllamaLLM] = None
        self._fallback_embeddings: Optional[DirectOllamaEmbeddings] = None

        # Prompt Templates
        self.prompt_templates = self._initialize_prompt_templates()

        # Statistics
        self.stats: Dict[str, Any] = {
            "requests_sent": 0,
            "requests_successful": 0,
            "requests_failed": 0,
            "total_tokens": 0,
            "total_duration": 0.0,
            "average_response_time": 0.0,
            "model_usage": {},
            "fallback_requests": 0,
        }

        logger.info(f"🤖 Veritas Ollama Client initialisiert (URL: {base_url})")

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
        Initialisiert Ollama Client und prüft verfügbare Modelle

        Returns:
            bool: True wenn erfolgreich initialisiert
        """
        try:
            # Health Check
            if not await self.health_check():
                logger.warning("⚠️ Ollama Server nicht erreichbar – Offline-Fallback aktiviert")
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
            logger.info("✅ Ollama Client erfolgreich initialisiert")
            return True

        except Exception as e:
            logger.error(f"❌ Ollama Client Initialisierung fehlgeschlagen: {e}")
            self.offline_mode = True
            return False

    async def health_check(self) -> bool:
        """
        Prüft Ollama Server Gesundheit

        Returns:
            bool: True wenn Server erreichbar
        """
        try:
            response = await self.client.get(f"{self.base_url}/api/version")
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"⚠️ Ollama Health Check fehlgeschlagen: {e}")
            return False

    async def load_available_models(self) -> Dict[str, Dict[str, Any]]:
        """
        Lädt Liste verfügbarer Ollama-Modelle

        Returns:
            Dict: Verfügbare Modelle mit Metadaten
        """
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")

            if response.status_code == 200:
                data = response.json()
                models: Dict[str, Dict[str, Any]] = {}

                for model_info in data.get("models", []):
                    model_name = model_info.get("name") or model_info.get("model", "")
                    if not model_name:
                        continue
                    models[model_name] = {
                        "name": model_name,
                        "size": model_info.get("size", 0),
                        "modified_at": model_info.get("modified_at", ""),
                        "digest": model_info.get("digest", ""),
                        "details": model_info.get("details", {}),
                    }

                if models:
                    self.available_models = models
                    self.offline_mode = False
                    logger.info(f"📋 {len(models)} Ollama-Modelle geladen: {list(models.keys())}")
                    return models

            raise httpx.HTTPStatusError(f"HTTP {response.status_code}", request=response.request, response=response)

        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Modell-Liste: {e}")
            self.offline_mode = True
            if not self.available_models:
                self.available_models = self._default_model_catalog()
            return self.available_models

    async def list_models(self) -> List[Dict[str, Any]]:
        """
        Holt alle verfügbaren Modelle von Ollama für API-Endpoints

        Returns:
            List[Dict]: Liste von Modellen im Format [{"name": str, "size": str, "provider": str}]
        """
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")

            if response.status_code == 200:
                data = response.json()
                models = []

                for model_info in data.get("models", []):
                    model_name = model_info.get("name") or model_info.get("model", "")
                    if not model_name:
                        continue

                    # Formatiere Größe in GB
                    size_bytes = model_info.get("size", 0)
                    size_gb = size_bytes / (1024**3)  # Bytes to GB
                    size_str = f"{size_gb:.1f}GB" if size_gb > 0 else "Unknown"

                    models.append(
                        {
                            "name": model_name,
                            "size": size_str,
                            "provider": "ollama",
                            "modified_at": model_info.get("modified_at", ""),
                            "digest": model_info.get("digest", "")[:16] + "..." if model_info.get("digest") else "",
                        }
                    )

                # Sortiere alphabetisch
                models.sort(key=lambda x: x["name"])
                logger.info(f"✅ {len(models)} Modelle von Ollama abgerufen")
                return models

            logger.warning(f"⚠️ Ollama /api/tags returned status {response.status_code}")
            return []

        except Exception as e:
            logger.error(f"❌ list_models fehlgeschlagen: {e}")
            return []

    def _initialize_prompt_templates(self) -> Dict[PipelineStage, Dict[str, str]]:
        """Initialisiert Prompt-Templates für verschiedene Pipeline-Stages"""

        return {
            PipelineStage.QUERY_ANALYSIS: {
                "system": "Du bist ein Experte für die Analyse von Benutzeranfragen in einem Verwaltungskontext. Analysiere Queries hinsichtlich Komplexität, Domäne und benötigter Ressourcen.",
                "user_template": """Analysiere die folgende Benutzeranfrage:

**Query:** {query}
**Benutzerkontext:** {user_context}

Bestimme:
1. **Komplexität:** basic/standard/advanced
2. **Domäne:** environmental/building/transport/social/business/other
3. **Benötigte Agent-Typen:** Liste der erforderlichen Agenten
4. **Geschätzte Bearbeitungszeit:** in Sekunden

Antworte im JSON-Format.""",
            },
            PipelineStage.STEP_COMMENTARY: {
                "system": "Du bist der innere Gedankenprozess eines Multi-Agent-Systems. Formuliere transparente, reflektierende Zwischenstände: Welcher Gedanke entsteht gerade? Welche Hypothesen prüfst du? Wie hängt der Schritt mit der ursprünglichen Bürgerfrage zusammen? Markiere Unsicherheiten ehrlich und vermeide Floskeln.",
                "user_template": """Gib einen introspektiven Kommentar zum aktuellen Arbeitsschritt ab.

**Ausgangsfrage:** {original_query}
**Aktueller Schritt:** {current_step}
**Fortschritt/Status:** {progress_info}
**Kontextinfos:** {context}

Formuliere 1-2 Sätze aus der Ich-Perspektive, die
- den gedanklichen Fokus dieses Schritts beschreiben,
- den Bezug zur Ausgangsfrage oder offenen Punkten herstellen,
- ggf. Unsicherheiten oder anstehende Prüfungen benennen.
Vermeide generische Floskeln und liefere konkrete Beobachtungen.""",
            },
            PipelineStage.RAG_SEARCH: {
                "system": "Du hilfst bei der Interpretation von RAG-Suchergebnissen und der Auswahl relevanter Dokumente.",
                "user_template": """Bewerte die RAG-Suchergebnisse für die folgende Query:

**Query:** {query}
**Gefundene Dokumente:** {documents}
**Vector Scores:** {vector_scores}

Wähle die 5 relevantesten Dokumente aus und erkläre kurz warum sie relevant sind.""",
            },
            PipelineStage.AGENT_SELECTION: {
                "system": "Du bist Experte für die Auswahl der optimalen Agent-Kombination basierend auf Query-Analyse und verfügbaren Ressourcen.",
                "user_template": """Wähle die optimalen Agenten für diese Aufgabe:

**Query:** {query}
**Query-Analyse:** {query_analysis}
**Verfügbare Agenten:** {available_agents}
**RAG-Kontext:** {rag_context}

Erstelle eine JSON-Pipeline mit den passenden Agenten, deren Prioritäten und Ausführungsreihenfolge.""",
            },
            PipelineStage.RESULT_AGGREGATION: {
                "system": """Du bist ein hilfreicher Assistent für Verwaltungsfragen.

PERSÖNLICHKEIT:
- Freundlich, zugänglich
- Präzise, aber nicht steif
- Erklärt komplexe Sachverhalte verständlich

STIL:
- Natürliche Sprache (keine Meta-Kommentare wie "Antwort auf...")
- Strukturiert (Absätze, Listen, Hervorhebungen)
- Direkt zur Sache

VERBOTEN:
- "Antwort auf die Frage..."
- "Basierend auf den bereitgestellten Informationen..."
- "Ich kann Ihnen folgendes mitteilen..."
- Generische Floskeln

ERLAUBT:
- Direkte Antworten: "Für eine Baugenehmigung benötigen Sie..."
- Persönlich: "Das hängt von Ihrem konkreten Fall ab..."
- Empathisch: "Das ist eine häufige Frage - hier die wichtigsten Punkte:"

FORMAT (MARKDOWN-STRUKTURIERUNG NACH BEDARF!):
✅ VERWENDE FREI:
- Überschriften (##, ###) für Struktur
- **Fettdruck** für wichtige Begriffe
- Listen (•, -, 1.) für Aufzählungen
- Absätze für Lesbarkeit
- Tabellen (|) wenn sinnvoll
- Code-Blöcke (```) für Beispiele

✅ ANTWORT-STRUKTUR:
Beginne direkt mit einem zusammenhängenden Fließtext, der die Frage beantwortet.
Kombiniere Direkt-Antwort und Details zu einem natürlichen, gut lesbaren Text.
Nutze Markdown-Strukturierung (Überschriften, Listen, Hervorhebungen) dort, wo es die Lesbarkeit verbessert.

✅ NÄCHSTE SCHRITTE (JSON-Format am Ende - COMPLIANCE-PFLICHT):
Wenn sinnvoll, füge am ENDE der Antwort folgendes JSON an:
```json
{{
  "next_steps": [
    {{"action": "Beschreibung der Handlung", "type": "link"}},
    {{"action": "Weitere Aktion", "type": "info"}},
    {{"action": "Dokumentation prüfen", "type": "document"}}
  ],
  "related_topics": ["Thema 1", "Thema 2", "Thema 3"]
}}
```

**Types:**
- "link" = Externe Ressource/Link
- "info" = Informationshinweis
- "document" = Dokument/Formular

❌ VERBOTEN:
- Separate "## Direkte Antwort" und "## Details" Sections
- "## Nächste Schritte" als Markdown-Text (nur JSON!)
- Abrupte Strukturbrüche zwischen Sections""",
                "user_template": """**User fragte:** {query}

**Kontext aus Dokumenten:**
{rag_context}

**Agent-Erkenntnisse:**
{agent_results}

**Aggregierte Analyse:**
{aggregation_summary}

**Consensus-Übersicht:**
{consensus_summary}

**Deine Aufgabe:**
Beantworte die User-Frage direkt, natürlich und hilfreich.

WICHTIG:
- Beginne NICHT mit "Antwort auf die Frage..."
- Gehe DIREKT zur Sache
- Nutze die Informationen aus Dokumenten und Agents
- Strukturiere die Antwort übersichtlich
- Sei konkret und präzise

**Beispiel (GUT - FLIESSTEXT MIT STRUKTURIERUNG):**

Für eine Baugenehmigung in Brandenburg benötigen Sie mehrere Unterlagen, die beim zuständigen Bauordnungsamt eingereicht werden müssen. Die Bearbeitungsdauer beträgt in der Regel 2-3 Monate.

### Erforderliche Unterlagen

Die wichtigsten Dokumente sind:

• **Bauantrag:** Amtliches Formular des Bauordnungsamts
• **Lageplan:** Mit Grundstücksgrenzen und Gebäudepositionierung
• **Bauvorlagen:** Grundrisse, Schnitte und Ansichten
• **Statische Berechnungen:** Von zugelassenem Statiker
• **Baubeschreibung:** Detaillierte Beschreibung des Bauvorhabens

Der Bauantrag wird beim zuständigen Bauordnungsamt eingereicht. Bei komplexeren Vorhaben kann eine **Bauvoranfrage** sinnvoll sein, um Grundsatzfragen vorab zu klären.

```json
{{
  "next_steps": [
    {{"action": "Vollständige Unterlagen zusammenstellen", "type": "info"}},
    {{"action": "Termin mit Bauordnungsamt vereinbaren", "type": "link"}},
    {{"action": "Bei Unsicherheit: Bauvoranfrage stellen", "type": "document"}}
  ],
  "related_topics": ["Bauvoranfrage", "Baugenehmigungsverfahren", "Bauordnungsamt Brandenburg"]
}}
```

**Beispiel (SCHLECHT - FLOSKELHAFTE EINLEITUNG):**
"Antwort auf die Frage 'Was brauche ich für eine Baugenehmigung?':
Basierend auf den bereitgestellten Informationen kann ich Ihnen mitteilen, dass Sie verschiedene Unterlagen benötigen..."

**Beispiel (SCHLECHT - GETRENNTE SECTIONS):**
"## Direkte Antwort
Sie brauchen Unterlagen.

## Details
Hier sind die Details..."

**Jetzt beantworte die User-Frage:**""",
            },
            PipelineStage.RESPONSE_GENERATION: {
                "system": "Du bist ein Experte für die Erstellung klarer, strukturierter Antworten auf Verwaltungsanfragen. Antworte präzise, hilfreich und benutzerfreundlich.",
                "user_template": """Erstelle eine finale Antwort basierend auf der folgenden Analyse:

**Query:** {query}
**Aggregierte Erkenntnisse:** {aggregated_insights}
**Confidence Score:** {confidence_score}
**Quellen:** {sources}

Formatiere die Antwort professionell mit:
- Klarer Hauptantwort
- Strukturierten Details
- Quellenangaben
- Handlungsempfehlungen
- Weiterführenden Hinweisen""",
            },
        }

    def _default_model_catalog(self) -> Dict[str, Dict[str, Any]]:
        """Fallback-Modellkatalog, falls Ollama nicht erreichbar ist."""

        return {
            model.value: {
                "name": model.value,
                "size": 0,
                "modified_at": None,
                "digest": None,
                "details": {"source": "fallback"},
            }
            for model in OllamaModel
        }

    def _ensure_fallback_llm(
        self,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> DirectOllamaLLM:
        """Liefert eine DirectOllamaLLM-Instanz für Offline-Fallbacks."""

        if self._fallback_llm is None or (model and self._fallback_llm.model != model):
            self._fallback_llm = DirectOllamaLLM(
                model=model or self.default_model,
                base_url=self.base_url,
                temperature=temperature or 0.7,
                num_predict=max_tokens,
                raise_on_failure=False,
            )
        return self._fallback_llm

    def _ensure_fallback_embeddings(self) -> DirectOllamaEmbeddings:
        """Liefert eine Embedding-Instanz für Offline-Fallbacks."""

        if self._fallback_embeddings is None:
            self._fallback_embeddings = DirectOllamaEmbeddings(
                base_url=self.base_url,
                raise_on_failure=False,
            )
        return self._fallback_embeddings

    def _build_response_from_invocation(
        self,
        invocation: OllamaInvocationResult,
        requested_model: str,
    ) -> OllamaResponse:
        """Konvertiert einen OllamaInvocationResult in eine OllamaResponse."""

        data = {
            "response": invocation.content,
            "done": True,
            "context": invocation.raw_response.get("context") if invocation.raw_response else None,
            "eval_count": invocation.raw_response.get("eval_count") if invocation.raw_response else None,
            "eval_duration": invocation.raw_response.get("eval_duration") if invocation.raw_response else None,
            "total_duration": invocation.raw_response.get("total_duration") if invocation.raw_response else None,
        }
        response = self._process_single_response(data, invocation.model or requested_model)

        # Kennzeichne Fallbacks mit konservativem Confidence Score
        if invocation.metadata.get("fallback"):
            response.confidence_score = min(response.confidence_score or 0.5, 0.4)

        return response

    async def _generate_response_via_fallback(
        self,
        request: OllamaRequest,
        stream: bool,
        error_message: str,
    ) -> Union[OllamaResponse, AsyncGenerator[OllamaResponse, None]]:
        """Erstellt eine LLM-Antwort über den Offline-Fallback."""

        self.offline_mode = True
        loop = asyncio.get_running_loop()

        def _invoke() -> OllamaInvocationResult:
            llm = self._ensure_fallback_llm(
                model=request.model,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            )
            return llm.invoke(
                request.prompt,
                system=request.system,
                context=request.context,
            )

        invocation = await loop.run_in_executor(None, _invoke)

        # Statistik aktualisieren
        self.stats["fallback_requests"] += 1
        self.stats["requests_successful"] += 1
        self.stats["total_duration"] += invocation.duration
        if self.stats["requests_successful"]:
            self.stats["average_response_time"] = self.stats["total_duration"] / self.stats["requests_successful"]
        model_key = request.model or self.default_model
        self.stats["model_usage"].setdefault(model_key, 0)
        self.stats["model_usage"][model_key] += 1

        response = self._build_response_from_invocation(invocation, model_key)

        # Ergänze Hinweis auf Fallback im Response-Text
        if invocation.metadata.get("fallback"):
            response.response = f"[Fallback-Antwort – Ollama offline]\n\n{response.response}"

        if stream:

            async def _generator() -> AsyncGenerator[OllamaResponse, None]:
                logger.warning(
                    "⚠️ Streaming-Fallback aktiviert – sende Einzelantwort (Grund: %s)",
                    error_message,
                )
                yield response

            return _generator()

        logger.warning("⚠️ Ollama Fallback-Antwort genutzt: %s", error_message)
        return response

    async def generate_response(self, request: OllamaRequest, stream: bool = False) -> Any:
        """
        Sendet Anfrage an Ollama und verarbeitet Antwort

        Args:
            request: Ollama Request Objekt
            stream: Stream Response aktivieren

        Returns:
            OllamaResponse oder AsyncGenerator für Streaming
        """

        last_error: Optional[str] = None

        for attempt in range(self.max_retries):
            try:
                self.stats["requests_sent"] += 1
                start_time = time.time()

                # Request Payload
                payload: Dict[str, Any] = {
                    "model": request.model,
                    "prompt": request.prompt,
                    "stream": stream,
                    "options": {
                        "temperature": request.temperature,
                    },
                }

                if request.max_tokens is not None:
                    payload["options"]["num_predict"] = request.max_tokens

                if request.system:
                    payload["system"] = request.system

                if request.context:
                    payload["context"] = request.context

                # HTTP Request senden
                response = await self.client.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=self.timeout,
                )

                if response.status_code == 200:
                    duration = time.time() - start_time
                    self.stats["requests_successful"] += 1
                    self.stats["total_duration"] += duration
                    if self.stats["requests_successful"]:
                        self.stats["average_response_time"] = self.stats["total_duration"] / self.stats["requests_successful"]

                    # Model Usage Stats
                    model_key = request.model or self.default_model
                    self.stats["model_usage"].setdefault(model_key, 0)
                    self.stats["model_usage"][model_key] += 1

                    if stream:
                        return self._process_streaming_response(response)
                    return self._process_single_response(response.json(), model_key)

                raise httpx.HTTPStatusError(f"HTTP {response.status_code}", request=response.request, response=response)

            except Exception as e:
                last_error = str(e)
                logger.warning(
                    "⚠️ Ollama Request Attempt %s/%s fehlgeschlagen: %s",
                    attempt + 1,
                    self.max_retries,
                    e,
                )
                if attempt == self.max_retries - 1:
                    self.stats["requests_failed"] += 1
                    return await self._generate_response_via_fallback(request, stream, last_error)
                await asyncio.sleep(2**attempt)  # Exponential backoff

        # Sollte eigentlich nie erreicht werden, aber zur Sicherheit Fallback
        return await self._generate_response_via_fallback(
            request,
            stream,
            last_error or "Unbekannter Fehler",
        )

    def _process_single_response(self, data: Dict[str, Any], model: str) -> OllamaResponse:
        """Verarbeitet einzelne Ollama Response"""

        response_text = data.get("response", "")

        # Confidence Score schätzen (vereinfacht)
        confidence_score = self._estimate_confidence_score(response_text, data)

        # Token Count aktualisieren
        eval_count = data.get("eval_count")
        if isinstance(eval_count, (int, float)):
            self.stats["total_tokens"] += int(eval_count)

        return OllamaResponse(
            model=model,
            response=response_text,
            done=data.get("done", False),
            context=data.get("context"),
            eval_count=data.get("eval_count"),
            eval_duration=data.get("eval_duration"),
            total_duration=data.get("total_duration"),
            confidence_score=confidence_score,
        )

    async def _process_streaming_response(self, response) -> AsyncGenerator[OllamaResponse, None]:
        """Verarbeitet Streaming Ollama Response"""

        async for line in response.aiter_lines():
            if line:
                try:
                    data = json.loads(line)
                    yield self._process_single_response(data, data.get("model", "unknown"))
                except json.JSONDecodeError:
                    continue

    def _estimate_confidence_score(self, response_text: str, data: Dict[str, Any]) -> float:
        """
        Schätzt Confidence Score basierend auf Response-Charakteristika

        Args:
            response_text: Generierte Antwort
            data: Ollama Response Data

        Returns:
            float: Confidence Score zwischen 0.0 und 1.0
        """

        base_score = 0.7  # Basis-Vertrauen

        # Response-Länge berücksichtigen
        if len(response_text) > 100:
            base_score += 0.1

        # Strukturiertheit bewerten (vereinfacht)
        if any(marker in response_text for marker in ["**", "#", "1.", "-", "•"]):
            base_score += 0.1

        # Eval Duration berücksichtigen (längere Verarbeitung = durchdachter)
        eval_duration = data.get("eval_duration")
        if isinstance(eval_duration, (int, float)) and eval_duration > 1_000_000:  # > 1 Sekunde in ns
            base_score += 0.05

        return min(1.0, base_score)

    async def query_with_context(
        self,
        query: str,
        chat_session=None,
        context_strategy: str = "sliding_window",
        max_context_messages: int = 10,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> OllamaResponse:
        """
        🆕 Sendet Query an LLM mit Chat-History-Context

        Args:
            query: Aktuelle Benutzeranfrage
            chat_session: ChatSession-Objekt mit Message-History
            context_strategy: Context-Strategie ("sliding_window", "relevance", "all")
            max_context_messages: Max. Anzahl Context-Messages
            model: Optionales Modell (default: self.default_model)
            temperature: Sampling-Temperature (0.0-1.0)
            max_tokens: Max. Response-Tokens

        Returns:
            OllamaResponse mit kontextueller Antwort
        """
        try:
            # Import Context Manager
            from backend.agents.context_manager import ConversationContextManager

            # Build conversation context
            context_manager = ConversationContextManager(max_tokens=2000)
            context_result = context_manager.build_conversation_context(
                chat_session=chat_session, current_query=query, strategy=context_strategy, max_messages=max_context_messages
            )

            conversation_context = context_result.get("context", "")
            token_count = context_result.get("token_count", 0)
            message_count = context_result.get("message_count", 0)

            logger.info(
                f"📝 Context erstellt: {message_count} Messages, " f"{token_count} Tokens, Strategie: {context_strategy}"
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

            # Create Ollama request with context-enhanced prompt
            request = OllamaRequest(
                model=model or self.default_model,
                prompt=query,
                system=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False,
            )

            # Generate response
            response = await self.generate_response(request)

            # Add context metadata to response
            if isinstance(response, OllamaResponse):
                response.context = context_result  # Store context info

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

            request = OllamaRequest(
                model=model or self.default_model,
                prompt=query,
                system="Du bist VERITAS, ein KI-Assistent für deutsches Baurecht und Umweltrecht.",
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False,
            )

            return await self.generate_response(request)

    async def comment_pipeline_step(
        self, current_step: str, progress_info: Dict[str, Any], context: Dict[str, Any] = None
    ) -> str:
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
            context=json.dumps(stage_context, indent=2, ensure_ascii=False),
        )

        request = OllamaRequest(
            model=self.default_model,
            prompt=prompt,
            system=template["system"],
            temperature=0.8,  # Etwas kreativer für Kommentare
            max_tokens=100,  # Kurze Kommentare
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
            query=query, user_context=json.dumps(user_context or {}, indent=2, ensure_ascii=False)
        )

        request = OllamaRequest(
            model=self.default_model,
            prompt=prompt,
            system=template["system"],
            temperature=0.3,  # Präzise Analyse
            max_tokens=500,
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
                    "llm_analysis": response.response,
                }

        except Exception as e:
            logger.error(f"❌ Query-Analyse fehlgeschlagen: {e}")
            return {
                "complexity": "standard",
                "domain": "general",
                "required_agents": ["document_retrieval"],
                "estimated_time": 15,
                "error": str(e),
            }

    async def enrich_query_for_rag(
        self, query: str, domain: str = "general", user_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        🔍 Erweitert User-Query mit Fachbegriffen, Synonymen und Kontext für RAG-Retrieval

        INTERNAL PROCESSING: Nutzt Anweisungssprache für optimale RAG-Qualität

        Args:
            query: Original-Query vom User
            domain: Fachdomäne (building, environmental, transport, etc.)
            user_context: Benutzerkontext

        Returns:
            Dict: {
                "keywords": [...],        # Hauptbegriffe
                "synonyms": {...},        # Alternative Begriffe
                "context": "...",         # Fachlicher Rahmen
                "search_terms": [...]     # Optimierte Suchbegriffe
            }
        """

        # Internal RAG Query-Enrichment Prompt (Instruction Language)
        system_prompt = """Du bist ein interner Query-Analyzer für ein RAG-System.

AUFGABE: Erweitere die User-Query mit relevanten Fachbegriffen, Synonymen und Kontext für optimale Dokumenten-Retrieval.

STIL:
- Präzise, technisch
- Strukturiert (Keywords, Synonyme, Kontext)
- Optimiert für Vektor-Suche

OUTPUT: JSON mit {keywords, synonyms, context, search_terms}"""

        user_prompt = f"""Analysiere und erweitere folgende Query für RAG-Retrieval:

**User-Query:** {query}
**Domäne:** {domain}
**Kontext:** {json.dumps(user_context or {}, ensure_ascii=False)}

Erstelle:
1. **Keywords:** Hauptbegriffe (5-10)
2. **Synonyme:** Alternative Begriffe (3-5 pro Keyword)
3. **Kontext:** Fachlicher Rahmen (1-2 Sätze)
4. **Search-Terms:** Optimierte Suchbegriffe für Vektor-DB (10-15)

Beispiel:
{{
  "keywords": ["Baugenehmigung", "Bauantrag", "BauGB"],
  "synonyms": {{"Baugenehmigung": ["Baubewilligung", "Bauerlaubnis"]}},
  "context": "Baurecht, Genehmigungsverfahren nach BauGB",
  "search_terms": ["Baugenehmigung", "Bauantrag", "BauGB", "Bauordnung", ...]
}}"""

        request = OllamaRequest(
            model=self.default_model,
            prompt=user_prompt,
            system=system_prompt,
            temperature=0.3,  # Präzise Analyse
            max_tokens=800,
        )

        try:
            response = await self.generate_response(request)

            # JSON parsen
            try:
                enriched = json.loads(response.response)
                logger.info(f"✅ Query enriched: {len(enriched.get('search_terms', []))} search terms generated")
                return enriched
            except json.JSONDecodeError:
                # Fallback bei JSON-Parse-Fehler
                logger.warning("⚠️ Query-Enrichment JSON-Parsing fehlgeschlagen, nutze Fallback")
                return {
                    "keywords": query.split()[:5],  # Erste 5 Wörter als Keywords
                    "synonyms": {},
                    "context": f"Query im Kontext: {domain}",
                    "search_terms": query.split() + [domain],
                    "llm_raw_response": response.response,
                }

        except Exception as e:
            logger.error(f"❌ Query-Enrichment fehlgeschlagen: {e}")
            return {
                "keywords": query.split()[:5],
                "synonyms": {},
                "context": "Allgemeine Anfrage",
                "search_terms": query.split(),
                "error": str(e),
            }

    async def synthesize_agent_results(
        self,
        query: str,
        agent_results: Dict[str, Any],
        rag_context: Dict[str, Any] = None,
        aggregation_summary: Dict[str, Any] = None,
        consensus_summary: Dict[str, Any] = None,
        max_tokens: int = 1500,
    ) -> Dict[str, Any]:
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
            consensus_summary=json.dumps(consensus_summary or {}, indent=2, ensure_ascii=False),
        )

        request = OllamaRequest(
            model=self.default_model,
            prompt=prompt,
            system=template["system"],
            temperature=0.5,  # Ausgewogen
            max_tokens=max_tokens,  # 🆕 Dynamisches Token-Budget übergeben
        )

        try:
            response = await self.generate_response(request)

            # 🔧 Extrahiere JSON aus LLM-Antwort (Compliance-konform)
            # Import hier um zirkuläre Imports zu vermeiden
            from backend.utils.json_extractor import extract_json_from_text, extract_next_steps, extract_related_topics

            clean_text, json_metadata = extract_json_from_text(response.response)

            # Confidence Score berechnen
            confidence_score = response.confidence_score or 0.8

            result = {
                "response_text": clean_text,  # ✅ Sauberer Text ohne JSON
                "confidence_score": confidence_score,
                "model_used": request.model,
                "tokens_used": response.eval_count,
                "processing_time": (response.total_duration or 0) / 1_000_000_000,  # Convert nanoseconds to seconds
                "llm_metadata": {
                    "temperature": request.temperature,
                    "max_tokens": request.max_tokens,
                    "eval_duration": response.eval_duration,
                },
            }

            # ✅ Füge extrahierte JSON-Metadaten hinzu
            if json_metadata:
                result["json_metadata"] = {
                    "next_steps": extract_next_steps(json_metadata),
                    "related_topics": extract_related_topics(json_metadata),
                    "raw": json_metadata,
                }
                logger.info("✅ JSON-Metadaten aus LLM-Antwort extrahiert")

            return result

        except Exception as e:
            logger.error(f"❌ Agent-Result-Synthesis fehlgeschlagen: {e}", exc_info=True)
            return {
                "response_text": "Entschuldigung, bei der Verarbeitung Ihrer Anfrage ist ein Fehler aufgetreten.",
                "confidence_score": 0.0,
                "error": str(e),
            }

    def get_client_statistics(self) -> Dict[str, Any]:
        """Liefert Client-Statistiken"""

        return {
            "client_info": {
                "base_url": self.base_url,
                "timeout": self.timeout,
                "default_model": self.default_model,
                "available_models": list(self.available_models.keys()),
            },
            "usage_stats": self.stats.copy(),
            "status": {
                "offline_mode": self.offline_mode,
            },
            "model_availability": {model.value: model.value in self.available_models for model in OllamaModel},
        }


# ============================================================================
# FACTORY FUNCTIONS & GLOBAL ACCESS
# ============================================================================

# Global Ollama Client Instance (Singleton Pattern)
_global_ollama_client: Optional[VeritasOllamaClient] = None


async def get_ollama_client() -> VeritasOllamaClient:
    """
    Liefert globale Ollama Client Instanz (Singleton Pattern)

    Returns:
        VeritasOllamaClient: Globale Client-Instanz
    """
    global _global_ollama_client

    if _global_ollama_client is None:
        _global_ollama_client = VeritasOllamaClient()
        await _global_ollama_client.initialize()

    return _global_ollama_client


def create_ollama_client(**kwargs) -> VeritasOllamaClient:
    """
    Factory für neue Ollama Client Instanz

    Returns:
        VeritasOllamaClient: Neue Client-Instanz
    """
    return VeritasOllamaClient(**kwargs)


# ============================================================================
# MAIN FOR TESTING
# ============================================================================


async def main():
    """Test des Veritas Ollama Clients"""

    async with VeritasOllamaClient() as client:
        print("🤖 Veritas Ollama Client Test")
        print("=" * 40)

        # Health Check
        health = await client.health_check()
        print(f"Health Check: {'✅ OK' if health else '❌ FAILED'}")

        if not health:
            print("❌ Ollama Server nicht erreichbar - starte mit: ollama serve")
            return

        # Verfügbare Modelle anzeigen
        print(f"Verfügbare Modelle: {list(client.available_models.keys())}")

        # Test Query Analysis
        print("\n📋 Test: Query Analysis")
        query_analysis = await client.analyze_query(
            "Wie ist die Luftqualität in München?", {"location": "München", "user_type": "citizen"}
        )
        print(f"Analyse: {json.dumps(query_analysis, indent=2, ensure_ascii=False)}")

        # Test Step Commentary
        print("\n💬 Test: Step Commentary")
        comment = await client.comment_pipeline_step(
            "RAG Database Search",
            {"documents_found": 15, "search_time": "1.2s"},
            {"original_query": "Wie ist die Luftqualität in München?", "stage_context": {"documents_found": 15}},
        )
        print(f"Kommentar: {comment}")

        # Statistics
        print("\n📊 Client Statistics:")
        stats = client.get_client_statistics()
        print(f"Requests: {stats['usage_stats']['requests_successful']}/{stats['usage_stats']['requests_sent']}")
        print(f"Average Response Time: {stats['usage_stats']['average_response_time']:.2f}s")


if __name__ == "__main__":
    asyncio.run(main())
