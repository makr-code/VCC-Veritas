"""
JSON Fallback Storage for VERITAS Research Plans

Provides a local JSON file-based persistence layer when PostgreSQL is unavailable.
Mimics the core tables structure: research_plans, research_plan_steps, step_results.
"""
from __future__ import annotations

import json
import os
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class JSONFallbackStore:
    """Thread-safe JSON file storage for research plans when DB is down."""

    def __init__(self, storage_dir: Optional[str] = None):
        if storage_dir is None:
            storage_dir = os.path.join("data", "fallback_db")
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.plans_file = self.storage_dir / "research_plans.json"
        self.steps_file = self.storage_dir / "research_plan_steps.json"
        self.results_file = self.storage_dir / "step_results.json"
        self.logs_file = self.storage_dir / "agent_execution_log.json"

        self._lock = threading.Lock()
        self._ensure_files_exist()

    def _ensure_files_exist(self):
        """Initialize JSON files if they don't exist."""
        for file in [self.plans_file, self.steps_file, self.results_file, self.logs_file]:
            if not file.exists():
                file.write_text("[]")

    def _read_json(self, file_path: Path) -> List[Dict[str, Any]]:
        """Thread-safe JSON read."""
        with self._lock:
            try:
                return json.loads(file_path.read_text())
            except Exception:
                return []

    def _write_json(self, file_path: Path, data: List[Dict[str, Any]]):
        """Thread-safe JSON write."""
        with self._lock:
            file_path.write_text(json.dumps(data, indent=2, default=str))

    # ========================================================================
    # Research Plans
    # ========================================================================

    def create_plan(self, plan_data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a new research plan."""
        plans = self._read_json(self.plans_file)

        # Add timestamps
        now = datetime.now().isoformat()
        plan_data.setdefault("created_at", now)
        plan_data.setdefault("updated_at", now)
        plan_data.setdefault("status", "pending")
        plan_data.setdefault("current_step_index", 0)
        plan_data.setdefault("total_steps", 0)
        plan_data.setdefault("progress_percentage", 0.0)

        plans.append(plan_data)
        self._write_json(self.plans_file, plans)
        return plan_data

    def get_plan(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a plan by ID."""
        plans = self._read_json(self.plans_file)
        for plan in plans:
            if plan.get("plan_id") == plan_id:
                return plan
        return None

    def update_plan(self, plan_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing plan."""
        plans = self._read_json(self.plans_file)
        for plan in plans:
            if plan.get("plan_id") == plan_id:
                plan.update(updates)
                plan["updated_at"] = datetime.now().isoformat()
                self._write_json(self.plans_file, plans)
                return True
        return False

    def list_plans(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all plans, optionally filtered by status."""
        plans = self._read_json(self.plans_file)
        if status:
            return [p for p in plans if p.get("status") == status]
        return plans

    # ========================================================================
    # Research Plan Steps
    # ========================================================================

    def create_step(self, step_data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a new step."""
        steps = self._read_json(self.steps_file)
        step_data.setdefault("status", "pending")
        step_data.setdefault("retry_count", 0)
        steps.append(step_data)
        self._write_json(self.steps_file, steps)
        return step_data

    def get_step(self, step_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a step by ID."""
        steps = self._read_json(self.steps_file)
        for step in steps:
            if step.get("step_id") == step_id:
                return step
        return None

    def update_step(self, step_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing step."""
        steps = self._read_json(self.steps_file)
        for step in steps:
            if step.get("step_id") == step_id:
                step.update(updates)
                self._write_json(self.steps_file, steps)
                return True
        return False

    def list_steps(self, plan_id: str) -> List[Dict[str, Any]]:
        """List all steps for a given plan."""
        steps = self._read_json(self.steps_file)
        return [s for s in steps if s.get("plan_id") == plan_id]

    # ========================================================================
    # Step Results
    # ========================================================================

    def create_result(self, result_data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a step result."""
        results = self._read_json(self.results_file)
        result_data.setdefault("created_at", datetime.now().isoformat())
        # Auto-increment result_id
        result_data["result_id"] = max([r.get("result_id", 0) for r in results], default=0) + 1
        results.append(result_data)
        self._write_json(self.results_file, results)
        return result_data

    def list_results(self, step_id: Optional[str] = None, plan_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List results, optionally filtered by step_id or plan_id."""
        results = self._read_json(self.results_file)
        if step_id:
            results = [r for r in results if r.get("step_id") == step_id]
        if plan_id:
            results = [r for r in results if r.get("plan_id") == plan_id]
        return results

    # ========================================================================
    # Agent Execution Logs
    # ========================================================================

    def create_log(self, log_data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert an execution log."""
        logs = self._read_json(self.logs_file)
        log_data.setdefault("timestamp", datetime.now().isoformat())
        log_data["log_id"] = max([l.get("log_id", 0) for l in logs], default=0) + 1
        logs.append(log_data)
        self._write_json(self.logs_file, logs)
        return log_data

    def list_logs(
        self, plan_id: Optional[str] = None, step_id: Optional[str] = None, log_level: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List logs with optional filters."""
        logs = self._read_json(self.logs_file)
        if plan_id:
            logs = [l for l in logs if l.get("plan_id") == plan_id]
        if step_id:
            logs = [l for l in logs if l.get("step_id") == step_id]
        if log_level:
            logs = [l for l in logs if l.get("log_level") == log_level]
        return logs

    # ========================================================================
    # Utilities
    # ========================================================================

    def clear_all(self):
        """Clear all stored data (useful for testing)."""
        self._write_json(self.plans_file, [])
        self._write_json(self.steps_file, [])
        self._write_json(self.results_file, [])
        self._write_json(self.logs_file, [])

    def get_stats(self) -> Dict[str, int]:
        """Get count statistics."""
        return {
            "research_plans": len(self._read_json(self.plans_file)),
            "research_plan_steps": len(self._read_json(self.steps_file)),
            "step_results": len(self._read_json(self.results_file)),
            "agent_execution_log": len(self._read_json(self.logs_file)),
        }


# Singleton instance
_fallback_store: Optional[JSONFallbackStore] = None


def get_fallback_store() -> JSONFallbackStore:
    """Get or create the global fallback store instance."""
    global _fallback_store
    if _fallback_store is None:
        _fallback_store = JSONFallbackStore()
    return _fallback_store
