#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VERITAS Frontend: Feedback API Client
Kommunikation mit Backend Feedback-Endpoints
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp

# Import zentrale Konfiguration
try:
    from frontend.config.frontend_config import BACKEND_URL, MAX_RETRIES, REQUEST_TIMEOUT
except ImportError:
    # Fallback wenn Konfiguration nicht importierbar
    BACKEND_URL = "http://localhost:5000"
    REQUEST_TIMEOUT = 30
    MAX_RETRIES = 3

logger = logging.getLogger(__name__)


class FeedbackAPIClient:
    """
    Async API-Client für Feedback-System

    Features:
    - Async HTTP-Requests (aiohttp)
    - Retry-Logik bei Netzwerkfehlern
    - Connection-Pooling
    - Timeout-Handling
    """

    def __init__(self, base_url: str = None, timeout: int = None, max_retries: int = None):
        """
        Initialisiert API-Client

        Args:
            base_url: Backend-URL (default: aus Config)
            timeout: Request-Timeout in Sekunden (default: aus Config)
            max_retries: Maximale Retry-Versuche (default: aus Config)
        """
        self.base_url = (base_url or BACKEND_URL).rstrip("/")
        self.timeout = aiohttp.ClientTimeout(total=timeout or REQUEST_TIMEOUT)
        self.max_retries = max_retries or MAX_RETRIES
        self._session: Optional[aiohttp.ClientSession] = None

        logger.info(f"✅ FeedbackAPIClient initialisiert: {self.base_url}")

    async def __aenter__(self):
        """Context Manager Entry"""
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context Manager Exit"""
        await self.close()

    async def _ensure_session(self):
        """Stellt sicher, dass Session existiert"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=self.timeout)
            logger.debug("✅ aiohttp Session erstellt")

    async def close(self):
        """Schließt HTTP-Session"""
        if self._session and not self._session.closed:
            await self._session.close()
            logger.debug("✅ aiohttp Session geschlossen")

    async def _request(
        self, method: str, endpoint: str, json: Optional[Dict] = None, params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Führt HTTP-Request mit Retry-Logik aus

        Args:
            method: HTTP-Methode (GET, POST)
            endpoint: API-Endpoint (z.B. /api/feedback/submit)
            json: JSON-Body für POST-Requests
            params: Query-Parameter für GET-Requests

        Returns:
            Response-Dictionary
        """
        await self._ensure_session()

        url = f"{self.base_url}{endpoint}"

        for attempt in range(1, self.max_retries + 1):
            try:
                async with self._session.request(method=method, url=url, json=json, params=params) as response:
                    # Check HTTP Status
                    if response.status >= 500:
                        raise aiohttp.ClientResponseError(
                            request_info=response.request_info,
                            history=response.history,
                            status=response.status,
                            message=f"Server Error: {response.status}",
                        )

                    # Parse JSON Response
                    data = await response.json()

                    if response.status >= 400:
                        logger.warning(f"⚠️ API-Fehler: {response.status} - {data}")
                        return {"success": False, "error": data}

                    logger.debug(f"✅ API-Request erfolgreich: {method} {endpoint}")
                    return data

            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                logger.warning(f"⚠️ Request fehlgeschlagen (Versuch {attempt}/{self.max_retries}): {e}")

                if attempt == self.max_retries:
                    logger.error(f"❌ Alle Retry-Versuche fehlgeschlagen: {endpoint}")
                    return {"success": False, "error": f"Connection failed after {self.max_retries} attempts: {str(e)}"}

                # Exponential Backoff
                await asyncio.sleep(2**attempt)

    # ===== FEEDBACK ENDPOINTS =====

    async def submit_feedback(
        self,
        message_id: str,
        rating: int,
        category: Optional[str] = None,
        comment: Optional[str] = None,
        user_id: str = "anonymous",
    ) -> Dict[str, Any]:
        """
        Sendet Feedback an Backend

        Args:
            message_id: Eindeutige Message-ID
            rating: Rating (1=👍, -1=👎, 0=💬)
            category: Kategorie (helpful, incorrect, unclear, other)
            comment: Optionaler Kommentar
            user_id: User-ID (default: anonymous)

        Returns:
            Response-Dictionary mit success, feedback_id, message, timestamp

        Example:
            >>> async with FeedbackAPIClient() as client:
            ...     response = await client.submit_feedback(
            ...         message_id="msg_123",
            ...         rating=1,
            ...         category="helpful",
            ...         comment="Great answer!"
            ...     )
            ...     print(response['success'])  # True
        """
        payload = {"message_id": message_id, "rating": rating, "user_id": user_id}

        if category:
            payload["category"] = category
        if comment:
            payload["comment"] = comment

        return await self._request(method="POST", endpoint="/api/feedback/submit", json=payload)

    async def get_stats(self, days: int = 30) -> Dict[str, Any]:
        """
        Holt aggregierte Feedback-Statistiken

        Args:
            days: Zeitraum in Tagen (default: 30)

        Returns:
            Stats-Dictionary mit total_feedback, positive_count, etc.

        Example:
            >>> async with FeedbackAPIClient() as client:
            ...     stats = await client.get_stats(days=7)
            ...     print(f"Positive Ratio: {stats['positive_ratio']}%")
        """
        return await self._request(method="GET", endpoint="/api/feedback/stats", params={"days": days})

    async def get_feedback_list(self, limit: int = 50, offset: int = 0, rating_filter: Optional[int] = None) -> Dict[str, Any]:
        """
        Holt Liste von Feedbacks mit Pagination

        Args:
            limit: Anzahl Ergebnisse (default: 50)
            offset: Offset für Pagination (default: 0)
            rating_filter: Filter nach Rating (1, -1, 0)

        Returns:
            Dictionary mit total, limit, offset, feedback-Liste

        Example:
            >>> async with FeedbackAPIClient() as client:
            ...     result = await client.get_feedback_list(limit=10, rating_filter=1)
            ...     print(f"Positive Feedback: {result['total']}")
        """
        params = {"limit": limit, "offset": offset}

        if rating_filter is not None:
            params["rating"] = rating_filter

        return await self._request(method="GET", endpoint="/api/feedback/list", params=params)

    async def health_check(self) -> Dict[str, Any]:
        """
        Prüft Verfügbarkeit des Feedback-Systems

        Returns:
            Health-Status Dictionary

        Example:
            >>> async with FeedbackAPIClient() as client:
            ...     health = await client.health_check()
            ...     print(health['status'])  # 'healthy'
        """
        return await self._request(method="GET", endpoint="/api/feedback/health")


# ===== SYNCHRONOUS WRAPPER (für Tkinter-Integration) =====


class FeedbackAPIClientSync:
    """
    Synchrone Wrapper-Klasse für Tkinter-Integration

    Features:
    - Synchrone API-Methoden für Tkinter-Event-Handler
    - Automatische Event-Loop-Verwaltung
    - Thread-safe Execution
    """

    def __init__(self, base_url: str = None, timeout: int = None):
        """
        Initialisiert Sync-Wrapper

        Args:
            base_url: Backend-URL (default: aus Config)
            timeout: Request-Timeout (default: aus Config)
        """
        self.base_url = base_url
        self.timeout = timeout
        self._loop = None

        logger.info(f"✅ FeedbackAPIClientSync initialisiert: {self.base_url}")

    def _get_event_loop(self) -> asyncio.AbstractEventLoop:
        """Holt oder erstellt Event-Loop"""
        if self._loop is None or self._loop.is_closed():
            try:
                self._loop = asyncio.get_event_loop()
            except RuntimeError:
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)
        return self._loop

    def _run_async(self, coro):
        """Führt Coroutine synchron aus"""
        loop = self._get_event_loop()
        return loop.run_until_complete(coro)

    def submit_feedback(
        self,
        message_id: str,
        rating: int,
        category: Optional[str] = None,
        comment: Optional[str] = None,
        user_id: str = "anonymous",
    ) -> Dict[str, Any]:
        """
        Sendet Feedback (synchron)

        Example (Tkinter Button):
            >>> client = FeedbackAPIClientSync()
            >>> def on_thumbs_up():
            ...     response = client.submit_feedback(
            ...         message_id="msg_123",
            ...         rating=1,
            ...         category="helpful"
            ...     )
            ...     print(response['success'])
        """

        async def _submit():
            async with FeedbackAPIClient(base_url=self.base_url, timeout=self.timeout) as client:
                return await client.submit_feedback(
                    message_id=message_id, rating=rating, category=category, comment=comment, user_id=user_id
                )

        return self._run_async(_submit())

    def get_stats(self, days: int = 30) -> Dict[str, Any]:
        """Holt Stats (synchron)"""

        async def _get_stats():
            async with FeedbackAPIClient(base_url=self.base_url, timeout=self.timeout) as client:
                return await client.get_stats(days=days)

        return self._run_async(_get_stats())

    def get_feedback_list(self, limit: int = 50, offset: int = 0, rating_filter: Optional[int] = None) -> Dict[str, Any]:
        """Holt Feedback-Liste (synchron)"""

        async def _get_list():
            async with FeedbackAPIClient(base_url=self.base_url, timeout=self.timeout) as client:
                return await client.get_feedback_list(limit=limit, offset=offset, rating_filter=rating_filter)

        return self._run_async(_get_list())

    def health_check(self) -> Dict[str, Any]:
        """Health-Check (synchron)"""

        async def _health():
            async with FeedbackAPIClient(base_url=self.base_url, timeout=self.timeout) as client:
                return await client.health_check()

        return self._run_async(_health())
