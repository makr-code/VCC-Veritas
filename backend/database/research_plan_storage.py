"""Fallback-only ResearchPlanStorage: delegate all operations to the JSON
fallback store while database-hardening is completed. This keeps the code
safe (no dynamic SQL) and provides a minimal, well-typed shim used by the
rest of the application.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from backend.database.json_fallback import get_fallback_store

logger = logging.getLogger(__name__)


class ResearchPlanStorage:
    """Fallback-only ResearchPlanStorage that delegates to JSON store."""

    def __init__(self) -> None:
        self._fallback = get_fallback_store()

    def create_plan(self, plan_data: Dict[str, Any]) -> Dict[str, Any]:
        return self._fallback.create_plan(plan_data)

    def get_plan(self, plan_id: str) -> Optional[Dict[str, Any]]:
        return self._fallback.get_plan(plan_id)

    def update_plan(self, plan_id: str, updates: Dict[str, Any]) -> bool:
        return self._fallback.update_plan(plan_id, updates)

    def list_plans(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        return self._fallback.list_plans(status)

    def create_step(self, step_data: Dict[str, Any]) -> Dict[str, Any]:
        return self._fallback.create_step(step_data)

    def get_step(self, step_id: str) -> Optional[Dict[str, Any]]:
        return self._fallback.get_step(step_id)

    def update_step(self, step_id: str, updates: Dict[str, Any]) -> bool:
        return self._fallback.update_step(step_id, updates)

    def list_steps(self, plan_id: str) -> List[Dict[str, Any]]:
        return self._fallback.list_steps(plan_id)

    def get_stats(self) -> Dict[str, Any]:
        return self._fallback.get_stats()


_storage: Optional[ResearchPlanStorage] = None


def get_storage() -> ResearchPlanStorage:
    global _storage
    if _storage is None:
        _storage = ResearchPlanStorage()
    return _storage
