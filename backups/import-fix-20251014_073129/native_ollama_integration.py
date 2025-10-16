"""Lightweight native Ollama integration for VERITAS.

This module provides a thin wrapper around the Ollama HTTP API so the
backend can talk to a local Ollama runtime without depending on LangChain.
If the server is not reachable we fall back to deterministic placeholder
responses so the surrounding system can continue to operate in a degraded
mode during local development or CI.
"""
from __future__ import annotations

import hashlib
import logging
import os
import random
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Optional

try:
    import requests
except Exception:  # pragma: no cover - requests is optional at runtime
    requests = None  # type: ignore

__all__ = [
    "OllamaError",
    "OllamaConnectionError",
    "OllamaModelError",
    "OllamaInvocationResult",
    "DirectOllamaLLM",
    "DirectOllamaEmbeddings",
    "SimplePromptTemplate",
    "SimplePipeline",
    "create_llm_instance",
    "create_embeddings_instance",
]

LOGGER = logging.getLogger(__name__)
DEFAULT_OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
DEFAULT_EMBEDDING_DIMENSION = 768


# ============================================================================
# Exceptions
# ============================================================================


class OllamaError(RuntimeError):
    """Base error for Ollama integration issues."""


class OllamaConnectionError(OllamaError):
    """Raised when the Ollama server cannot be reached."""


class OllamaModelError(OllamaError):
    """Raised when the Ollama server responds with an unexpected payload."""


# ============================================================================
# Data containers
# ============================================================================


@dataclass
class OllamaInvocationResult:
    """Container for LLM responses."""

    content: str
    raw_response: Dict[str, Any] = field(default_factory=dict)
    model: str = ""
    duration: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# Helper utilities
# ============================================================================


def _ensure_requests() -> None:
    if requests is None:
        raise OllamaConnectionError(
            "Das Paket 'requests' ist nicht verfügbar. Installiere es oder "
            "setze OLLAMA_HOST, falls kein Ollama-Server genutzt werden soll."
        )


def _stable_hash_int(text: str) -> int:
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest(), 16)


def _fallback_embedding(text: str, dimension: int) -> List[float]:
    rng = random.Random(_stable_hash_int(text))
    # Generate deterministic pseudo-random vector in [-1, 1]
    return [rng.uniform(-1.0, 1.0) for _ in range(dimension)]


def _fallback_text(prompt: str, error_message: str) -> str:
    snippet = prompt.strip().splitlines()
    snippet = snippet[0:1] if snippet else [""]
    preview = snippet[0][:120] + ("…" if len(snippet[0]) > 120 else "")
    return (
        "⚠️  Ollama nicht erreichbar. Der Prompt wurde lokal verarbeitet, "
        "aber es konnte keine Modellantwort generiert werden.\n\n"
        f"Prompt-Ausschnitt: {preview}\n"
        f"Fehlermeldung: {error_message}"
    )


# ============================================================================
# Direct Ollama LLM
# ============================================================================


class DirectOllamaLLM:
    """Minimal HTTP client for Ollama's `/api/generate` endpoint."""

    def __init__(
        self,
        model: str = "llama3:latest",
        *,
        base_url: Optional[str] = None,
        temperature: float = 0.7,
        num_predict: Optional[int] = None,
        top_p: Optional[float] = None,
        timeout: float = 60.0,
        raise_on_failure: bool = False,
    ) -> None:
        self.model = model
        self.base_url = (base_url or DEFAULT_OLLAMA_HOST).rstrip("/")
        self.temperature = temperature
        self.num_predict = num_predict
        self.top_p = top_p
        self.timeout = timeout
        self.raise_on_failure = raise_on_failure

    # ------------------------------------------------------------------
    def invoke(
        self,
        prompt: str,
        *,
        system: Optional[str] = None,
        stream: bool = False,
        context: Optional[List[int]] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> OllamaInvocationResult:
        """Execute a prompt against Ollama and return a structured result."""

        if stream:
            LOGGER.info("Streaming wird derzeit nicht unterstützt – es wird ein synchroner Aufruf ausgeführt.")

        payload: Dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.temperature,
            },
        }
        if self.num_predict is not None:
            payload["options"]["num_predict"] = self.num_predict
        if self.top_p is not None:
            payload["options"]["top_p"] = self.top_p
        if system:
            payload["system"] = system
        if context:
            payload["context"] = context
        if options:
            payload["options"].update(options)

        start = time.perf_counter()

        try:
            _ensure_requests()
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
        except Exception as exc:  # pragma: no cover - network dependent
            LOGGER.warning("Ollama-Aufruf fehlgeschlagen: %s", exc)
            if self.raise_on_failure:
                raise OllamaConnectionError(str(exc)) from exc
            duration = time.perf_counter() - start
            return OllamaInvocationResult(
                content=_fallback_text(prompt, str(exc)),
                raw_response={},
                model=self.model,
                duration=duration,
                metadata={"fallback": True, "error": str(exc)},
            )

        duration = time.perf_counter() - start
        text = data.get("response")
        if not isinstance(text, str):
            error_message = "Antwort der Ollama-API enthält kein 'response'-Feld."
            LOGGER.warning(error_message)
            if self.raise_on_failure:
                raise OllamaModelError(error_message)
            return OllamaInvocationResult(
                content=_fallback_text(prompt, error_message),
                raw_response=data,
                model=self.model,
                duration=duration,
                metadata={"fallback": True, "error": error_message},
            )

        return OllamaInvocationResult(
            content=text,
            raw_response=data,
            model=self.model,
            duration=duration,
            metadata={"fallback": False},
        )

    # ------------------------------------------------------------------
    def generate(self, prompt: str, **kwargs: Any) -> OllamaInvocationResult:
        """Compatibility alias used by some legacy code paths."""

        return self.invoke(prompt, **kwargs)

    # ------------------------------------------------------------------
    def __call__(self, prompt: str, **kwargs: Any) -> OllamaInvocationResult:
        return self.invoke(prompt, **kwargs)


# ============================================================================
# Direct Ollama Embeddings
# ============================================================================


class DirectOllamaEmbeddings:
    """Simple wrapper for Ollama's `/api/embeddings` endpoint."""

    def __init__(
        self,
        model: str = "nomic-embed-text",
        *,
        base_url: Optional[str] = None,
        timeout: float = 60.0,
        dimension: int = DEFAULT_EMBEDDING_DIMENSION,
        raise_on_failure: bool = False,
    ) -> None:
        self.model = model
        self.base_url = (base_url or DEFAULT_OLLAMA_HOST).rstrip("/")
        self.timeout = timeout
        self.dimension = dimension
        self.raise_on_failure = raise_on_failure

    # ------------------------------------------------------------------
    def embed_query(self, text: str) -> List[float]:
        embeddings = self.embed_documents([text])
        return embeddings[0]

    # ------------------------------------------------------------------
    def embed_documents(self, texts: Iterable[str]) -> List[List[float]]:
        vectors: List[List[float]] = []

        for text in texts:
            payload = {"model": self.model, "prompt": text}
            try:
                _ensure_requests()
                response = requests.post(
                    f"{self.base_url}/api/embeddings",
                    json=payload,
                    timeout=self.timeout,
                )
                response.raise_for_status()
                data = response.json()
                vector = data.get("embedding")
                if not isinstance(vector, list):
                    raise ValueError("embedding fehlt")
                vectors.append(vector)
            except Exception as exc:  # pragma: no cover - network dependent
                LOGGER.warning("Embedding-Aufruf fehlgeschlagen: %s", exc)
                if self.raise_on_failure:
                    raise OllamaConnectionError(str(exc)) from exc
                vectors.append(_fallback_embedding(text, self.dimension))

        return vectors


# ============================================================================
# Utility classes compatible with legacy imports
# ============================================================================


class SimplePromptTemplate:
    """Minimal string template helper."""

    def __init__(self, template: str) -> None:
        self.template = template

    def format(self, **kwargs: Any) -> str:
        return self.template.format(**kwargs)

    def render(self, **kwargs: Any) -> str:
        return self.format(**kwargs)


class SimplePipeline:
    """Very small pipeline helper that chains callables."""

    def __init__(self, *steps: Callable[[Any], Any]) -> None:
        self.steps = list(steps)

    def add_step(self, step: Callable[[Any], Any]) -> None:
        self.steps.append(step)

    def __call__(self, initial_input: Any) -> Any:
        value = initial_input
        for step in self.steps:
            value = step(value)
        return value


# ============================================================================
# Factory helpers
# ============================================================================


def create_llm_instance(**kwargs: Any) -> DirectOllamaLLM:
    return DirectOllamaLLM(**kwargs)


def create_embeddings_instance(**kwargs: Any) -> DirectOllamaEmbeddings:
    return DirectOllamaEmbeddings(**kwargs)
