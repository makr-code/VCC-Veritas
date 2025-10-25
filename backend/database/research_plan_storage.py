"""
Research Plan Storage with automatic DB/JSON fallback

Provides a unified interface that automatically switches between PostgreSQL
and JSON file storage depending on DB availability.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

# Try importing pool-based connection
try:
    from backend.database.connection_pool import get_cursor
    POOL_AVAILABLE = True
except Exception:
    POOL_AVAILABLE = False

# JSON fallback
from backend.database.json_fallback import get_fallback_store

logger = logging.getLogger(__name__)


class ResearchPlanStorage:
    """
    Unified storage interface for research plans.
    
    Automatically uses PostgreSQL when available, falls back to JSON files otherwise.
    """
    
    def __init__(self, prefer_db: bool = True):
        """
        Initialize storage layer.
        
        Args:
            prefer_db: If True (default), attempt DB first, then fallback to JSON.
        """
        self.prefer_db = prefer_db
        self._db_available = None  # Lazy check
        self._fallback = get_fallback_store()
    
    def _check_db_available(self) -> bool:
        """Check if PostgreSQL is available."""
        if self._db_available is not None:
            return self._db_available
        
        if not POOL_AVAILABLE:
            self._db_available = False
            return False
        
        try:
            with get_cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
            self._db_available = True
            logger.info("✅ PostgreSQL connection available")
            return True
        except Exception as e:
            self._db_available = False
            logger.warning(f"⚠️  PostgreSQL unavailable, using JSON fallback: {e}")
            return False
    
    @property
    def using_db(self) -> bool:
        """Check if currently using database (vs JSON fallback)."""
        return self.prefer_db and self._check_db_available()
    
    # ========================================================================
    # Research Plans
    # ========================================================================
    
    def create_plan(self, plan_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new research plan."""
        if self.using_db:
            try:
                with get_cursor() as cur:
                    cur.execute("""
                        INSERT INTO research_plans (
                            plan_id, research_question, status, plan_document,
                            total_steps, uds3_databases, phase5_hybrid_search,
                            security_level, source_domains
                        ) VALUES (
                            %(plan_id)s, %(research_question)s, %(status)s, %(plan_document)s,
                            %(total_steps)s, %(uds3_databases)s, %(phase5_hybrid_search)s,
                            %(security_level)s, %(source_domains)s
                        )
                        RETURNING *
                    """, plan_data)
                    result = cur.fetchone()
                    if result:
                        columns = [desc[0] for desc in cur.description]
                        return dict(zip(columns, result))
                logger.info(f"✅ Plan created in PostgreSQL: {plan_data['plan_id']}")
                return plan_data
            except Exception as e:
                logger.warning(f"DB insert failed, using JSON fallback: {e}")
                self._db_available = False  # Mark as unavailable
        
        # Fallback to JSON
        logger.info(f"📝 Plan created in JSON fallback: {plan_data['plan_id']}")
        return self._fallback.create_plan(plan_data)
    
    def get_plan(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a plan by ID."""
        if self.using_db:
            try:
                with get_cursor() as cur:
                    cur.execute("SELECT * FROM research_plans WHERE plan_id = %s", (plan_id,))
                    result = cur.fetchone()
                    if result:
                        columns = [desc[0] for desc in cur.description]
                        return dict(zip(columns, result))
                return None
            except Exception as e:
                logger.warning(f"DB query failed, using JSON fallback: {e}")
                self._db_available = False
        
        return self._fallback.get_plan(plan_id)
    
    def update_plan(self, plan_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing plan."""
        if self.using_db:
            try:
                set_clause = ", ".join([f"{k} = %({k})s" for k in updates.keys()])
                with get_cursor() as cur:
                    cur.execute(
                        f"UPDATE research_plans SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE plan_id = %(plan_id)s",
                        {**updates, "plan_id": plan_id}
                    )
                return True
            except Exception as e:
                logger.warning(f"DB update failed, using JSON fallback: {e}")
                self._db_available = False
        
        return self._fallback.update_plan(plan_id, updates)
    
    def list_plans(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all plans, optionally filtered by status."""
        if self.using_db:
            try:
                query = "SELECT * FROM research_plans"
                params = {}
                if status:
                    query += " WHERE status = %(status)s"
                    params["status"] = status
                query += " ORDER BY created_at DESC"
                
                with get_cursor() as cur:
                    cur.execute(query, params)
                    results = cur.fetchall()
                    columns = [desc[0] for desc in cur.description]
                    return [dict(zip(columns, row)) for row in results]
            except Exception as e:
                logger.warning(f"DB query failed, using JSON fallback: {e}")
                self._db_available = False
        
        return self._fallback.list_plans(status)
    
    # ========================================================================
    # Research Plan Steps
    # ========================================================================
    
    def create_step(self, step_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new step."""
        if self.using_db:
            try:
                with get_cursor() as cur:
                    cur.execute("""
                        INSERT INTO research_plan_steps (
                            step_id, plan_id, step_index, step_name, step_type,
                            agent_name, agent_type, status, step_config
                        ) VALUES (
                            %(step_id)s, %(plan_id)s, %(step_index)s, %(step_name)s, %(step_type)s,
                            %(agent_name)s, %(agent_type)s, %(status)s, %(step_config)s
                        )
                    """, step_data)
                logger.info(f"✅ Step created in PostgreSQL: {step_data['step_id']}")
                return step_data
            except Exception as e:
                logger.warning(f"DB insert failed, using JSON fallback: {e}")
                self._db_available = False
        
        logger.info(f"📝 Step created in JSON fallback: {step_data['step_id']}")
        return self._fallback.create_step(step_data)
    
    def get_step(self, step_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a step by ID."""
        if self.using_db:
            try:
                with get_cursor() as cur:
                    cur.execute("SELECT * FROM research_plan_steps WHERE step_id = %s", (step_id,))
                    result = cur.fetchone()
                    if result:
                        columns = [desc[0] for desc in cur.description]
                        return dict(zip(columns, result))
                return None
            except Exception as e:
                logger.warning(f"DB query failed, using JSON fallback: {e}")
                self._db_available = False
        
        return self._fallback.get_step(step_id)
    
    def update_step(self, step_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing step."""
        if self.using_db:
            try:
                set_clause = ", ".join([f"{k} = %({k})s" for k in updates.keys()])
                with get_cursor() as cur:
                    cur.execute(
                        f"UPDATE research_plan_steps SET {set_clause} WHERE step_id = %(step_id)s",
                        {**updates, "step_id": step_id}
                    )
                return True
            except Exception as e:
                logger.warning(f"DB update failed, using JSON fallback: {e}")
                self._db_available = False
        
        return self._fallback.update_step(step_id, updates)
    
    def list_steps(self, plan_id: str) -> List[Dict[str, Any]]:
        """List all steps for a given plan."""
        if self.using_db:
            try:
                with get_cursor() as cur:
                    cur.execute(
                        "SELECT * FROM research_plan_steps WHERE plan_id = %s ORDER BY step_index",
                        (plan_id,)
                    )
                    results = cur.fetchall()
                    columns = [desc[0] for desc in cur.description]
                    return [dict(zip(columns, row)) for row in results]
            except Exception as e:
                logger.warning(f"DB query failed, using JSON fallback: {e}")
                self._db_available = False
        
        return self._fallback.list_steps(plan_id)
    
    # ========================================================================
    # Utilities
    # ========================================================================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        stats = {"backend": "json" if not self.using_db else "postgresql"}
        
        if self.using_db:
            try:
                with get_cursor() as cur:
                    cur.execute("""
                        SELECT 
                            (SELECT COUNT(*) FROM research_plans) as research_plans,
                            (SELECT COUNT(*) FROM research_plan_steps) as research_plan_steps,
                            (SELECT COUNT(*) FROM step_results) as step_results,
                            (SELECT COUNT(*) FROM agent_execution_log) as agent_execution_log
                    """)
                    result = cur.fetchone()
                    columns = [desc[0] for desc in cur.description]
                    stats.update(dict(zip(columns, result)))
            except Exception as e:
                logger.warning(f"DB stats failed: {e}")
                stats.update(self._fallback.get_stats())
        else:
            stats.update(self._fallback.get_stats())
        
        return stats


# Singleton
_storage: Optional[ResearchPlanStorage] = None


def get_storage() -> ResearchPlanStorage:
    """Get or create the global storage instance."""
    global _storage
    if _storage is None:
        _storage = ResearchPlanStorage()
    return _storage
