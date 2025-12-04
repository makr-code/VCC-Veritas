# VERITAS Agent System - Migrations-Strategie v2.0

**Datum:** 4. Dezember 2025
**Status:** 🚀 Migration gestartet
**Ziel:** 100% Framework-Integration aller 38 Domain Agents

## 📋 Migrations-Plan (Vollständige Umsetzung)

### Phase 0: Vorbereitung (Tag 1)

**Ziel:** Framework-Template, Adapter, Registry-Struktur

#### 0.1 BaseAgent Migration Template

**Datei:** `backend/agents/templates/baseagent_migration_template.py`

```python
"""
VERITAS Domain Agent Migration Template
========================================

Vorlage für die Migration von Legacy Domain Agents zu BaseAgent Framework.

Verwendung:
1. Kopiere diese Datei als neuen Agent
2. Ersetze [DOMAIN_NAME] Platzhalter
3. Migriere Legacy-Logik in process_query()
4. Implementiere get_capabilities()
5. Registriere in domain_agent_registration.py
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from backend.agents.framework.agent_monitoring import AgentMonitor

# Framework Imports
from backend.agents.framework.base_agent import BaseAgent
from backend.agents.framework.quality_gate import QualityGate
from backend.agents.framework.retry_handler import RetryHandler
from backend.agents.registry.api_agent_registry import AgentCapability, AgentLifecycleType, AgentStatus, get_agent_registry

logger = logging.getLogger(__name__)


class [DOMAIN_NAME]Agent(BaseAgent):
    """
    [DOMAIN_DESCRIPTION]

    Capabilities:
    - [CAP_1]
    - [CAP_2]
    - [CAP_3]

    Example:
        >>> agent = [DOMAIN_NAME]Agent()
        >>> result = await agent.process_query("query text")
        >>> print(result)
    """

    # =====================================================================
    # Konfiguration
    # =====================================================================

    AGENT_TYPE = "[domain_name]"  # z.B. "weather_dwd", "genehmigung", "construction"
    AGENT_DOMAIN = "[DOMAIN]"     # z.B. "ENVIRONMENTAL", "LEGAL", "TECHNICAL"
    AGENT_VERSION = "2.0"         # nach Migration

    # =====================================================================
    # Lifecycle & Status
    # =====================================================================

    def __init__(self, agent_id: Optional[str] = None):
        """Initialize Domain Agent with Framework Support"""
        super().__init__(agent_id=agent_id)

        self.logger = logging.getLogger(f"{__name__}.{self.AGENT_TYPE}")
        self.monitor = AgentMonitor(self.AGENT_TYPE)
        self.quality_gate = QualityGate(
            min_confidence=0.6,
            max_response_time=5.0
        )
        self.retry_handler = RetryHandler(max_retries=3)

        # Legacy Agent Eigenschaften (falls nötig)
        self.knowledge_base: Dict[str, List[Dict]] = {}
        self._initialize_knowledge_base()

        self.logger.info(f"✅ {self.AGENT_TYPE} Agent v{self.AGENT_VERSION} initialized")

    # =====================================================================
    # Framework: Abstract Methods (MUSS implementiert werden)
    # =====================================================================

    def get_agent_type(self) -> str:
        """Return unique agent type identifier"""
        return self.AGENT_TYPE

    def get_capabilities(self) -> List[AgentCapability]:
        """Return list of capabilities this agent provides"""
        return [
            AgentCapability.QUERY_PROCESSING,  # Alle Agents können queries verarbeiten
            # Füge domain-spezifische Capabilities hinzu:
            # AgentCapability.LEGAL_FRAMEWORK,
            # AgentCapability.WEATHER_DATA,
            # AgentCapability.ENVIRONMENTAL_DATA,
            # AgentCapability.EXTERNAL_API,
        ]

    # =====================================================================
    # Framework: Query Processing Pipeline
    # =====================================================================

    async def process_query(self, query: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Main query processing pipeline with monitoring and quality gates

        Pipeline:
        1. Input Validation
        2. Query Enrichment (optional context)
        3. Legacy Query Processing
        4. Result Validation
        5. Monitoring & Metrics
        """
        query_id = f"{self.AGENT_TYPE}_{datetime.now().timestamp()}"

        try:
            self.logger.info(f"🔄 Processing query: {query[:50]}...")

            # 1. Input Validation
            if not self._validate_input(query):
                return {
                    "success": False,
                    "error": "Invalid query format",
                    "agent": self.AGENT_TYPE,
                    "query_id": query_id
                }

            # 2. Query Enrichment
            enriched_query = query
            if context:
                enriched_query = self._enrich_query(query, context)

            # 3. Process Query (Legacy Logik)
            result = await self._process_query_with_retry(enriched_query)

            # 4. Result Validation
            if not self._validate_result(result):
                return {
                    "success": False,
                    "error": "Invalid result format",
                    "agent": self.AGENT_TYPE
                }

            # 5. Quality Gate Check
            if not self.quality_gate.check(result):
                self.logger.warning(f"⚠️ Quality gate failed for query: {query[:30]}")
                # Optional: Return partial result oder error

            # Add Metadata
            result.update({
                "agent": self.AGENT_TYPE,
                "query_id": query_id,
                "timestamp": datetime.now().isoformat(),
                "version": self.AGENT_VERSION
            })

            self.monitor.record_success(response_time=result.get("processing_time", 0))
            self.logger.info(f"✅ Query processed successfully")

            return result

        except Exception as e:
            self.logger.error(f"❌ Query processing failed: {str(e)}", exc_info=True)
            self.monitor.record_failure(error=str(e))
            return {
                "success": False,
                "error": str(e),
                "agent": self.AGENT_TYPE
            }

    # =====================================================================
    # Legacy Agent Integration
    # =====================================================================

    async def _process_query_with_retry(self, query: str) -> Dict[str, Any]:
        """Execute query with automatic retry on failure"""

        async def query_func():
            # MIGRATE: Legacy query() Logik hier einfügen
            return self._legacy_query(query)

        result = await self.retry_handler.execute_with_retry(query_func)
        return result

    def _legacy_query(self, text: str) -> Dict[str, Any]:
        """
        Legacy Query Processing
        ========================

        HINWEIS: Dieser Code wurde vom alten Agent migriert.
        Optimization & Refactoring beim nächsten Sprint.
        """
        # TODO: Ersetze mit originaler Legacy-Logik
        results = []
        confidence = 0.0

        # Beispiel aus GenehmigungsAgent:
        for cap in getattr(self, 'capabilities', []):
            if cap in text.lower():
                kb = self.knowledge_base.get(cap, [])
                results.extend(kb)
                confidence = 0.8

        if not results:
            for cap, kb in self.knowledge_base.items():
                for entry in kb:
                    if any(word in text.lower() for word in
                           [entry.get("gesetz", "").lower(),
                            entry.get("inhalt", "").lower()]):
                        results.append(entry)
                        confidence = 0.6

        return {
            "success": bool(results),
            "results": results,
            "confidence": confidence,
            "processing_time": 0.0
        }

    def _initialize_knowledge_base(self) -> None:
        """
        Initialize Legacy Knowledge Base
        ================================

        TODO: Ersetze mit originaler Knowledge Base des Agents
        """
        self.knowledge_base = {}

    # =====================================================================
    # Validation & Enrichment
    # =====================================================================

    def _validate_input(self, query: str) -> bool:
        """Validate input query format"""
        if not query or not isinstance(query, str):
            return False
        if len(query) > 10000:  # Max length
            return False
        return True

    def _validate_result(self, result: Dict) -> bool:
        """Validate result structure"""
        if not isinstance(result, dict):
            return False
        if "success" not in result:
            return False
        return True

    def _enrich_query(self, query: str, context: Dict) -> str:
        """Add context information to query"""
        # Optional: Ergänze Query mit Kontext
        return query

    # =====================================================================
    # Monitoring & Metrics
    # =====================================================================

    def get_metrics(self) -> Dict[str, Any]:
        """Return agent performance metrics"""
        return {
            "agent_type": self.AGENT_TYPE,
            "version": self.AGENT_VERSION,
            "monitor": self.monitor.get_metrics(),
            "status": self.get_status()
        }


# =========================================================================
# Helper Function: Quick Registration
# =========================================================================

def register_[DOMAIN_NAME]_agent():
    """
    Register [DOMAIN_NAME]Agent in global registry

    Usage:
        from backend.agents.domain.[domain_name].[domain_name]_agent import register_[DOMAIN_NAME]_agent
        register_[DOMAIN_NAME]_agent()
    """
    try:
        registry = get_agent_registry()
        registry.register_agent(
            agent_type="[domain_name]",
            agent_class=[DOMAIN_NAME]Agent,
            capabilities=[[CAP_1], [CAP_2]],
            lifecycle_type=AgentLifecycleType.ON_DEMAND,  # oder POOLED, PERSISTENT
            max_concurrent_instances=2,
            priority=1,
            description="[DOMAIN_DESCRIPTION]"
        )
        logger.info(f"✅ {[DOMAIN_NAME]Agent.__name__} registered successfully")
    except Exception as e:
        logger.error(f"❌ Failed to register {[DOMAIN_NAME]Agent.__name__}: {e}")


if __name__ == "__main__":
    # Quick Test
    import asyncio

    async def test():
        agent = [DOMAIN_NAME]Agent()
        result = await agent.process_query("test query")
        print(result)

    asyncio.run(test())
