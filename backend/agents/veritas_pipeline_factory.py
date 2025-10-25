#!/usr/bin/env python3
"""
VERITAS Pipeline Factory - Request-Scoped Pipeline Instances
============================================================
Factory Pattern für Intelligent Multi-Agent Pipelines mit:
- Request-scoped Pipeline-Instanzen
- Dependency Injection für Shared Resources
- Automatisches Cleanup nach Request
- Lazy Loading Support

Author: VERITAS Development Team
Date: 2025-10-16
Version: 1.0 (Production-Ready)
"""

import logging
from typing import Optional
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class PipelineFactory:
    """
    Factory für Request-scoped Pipeline-Instanzen.
    
    Diese Factory erstellt für jeden Request eine neue Pipeline-Instanz,
    während Shared Resources (Ollama, UDS3, Agent Registry) wiederverwendet werden.
    
    Features:
    - Request Isolation (keine Race Conditions)
    - Automatic Resource Cleanup
    - Dependency Injection
    - Lazy Loading Support
    
    Usage:
        >>> factory = PipelineFactory(ollama_client, uds3_strategy, agent_registry)
        >>> pipeline = await factory.create_pipeline(max_workers=5)
        >>> response = await pipeline.process_intelligent_query(request)
        >>> # Cleanup erfolgt automatisch in process_intelligent_query()
    """
    
    def __init__(
        self,
        ollama_client,  # Type: VeritasOllamaClient
        uds3_strategy,  # Type: UnifiedDatabaseStrategy
        agent_registry,  # Type: AgentRegistry
        progress_manager=None  # Type: Optional[VeritasProgressManager]
    ):
        """
        Initialisiert Factory mit SHARED Ressourcen.
        
        Args:
            ollama_client: Globaler Ollama LLM Client (Singleton)
            uds3_strategy: Globale UDS3 Database Strategy (Singleton)
            agent_registry: Globale Agent Registry (Singleton)
            progress_manager: Optionaler Progress Manager für Streaming
        """
        self.ollama_client = ollama_client
        self.uds3_strategy = uds3_strategy
        self.agent_registry = agent_registry
        self.progress_manager = progress_manager
        
        # Factory Statistics
        self.pipelines_created = 0
        self.pipelines_active = 0
        self.pipelines_completed = 0
        
        logger.info("✅ Pipeline Factory initialisiert mit Shared Resources")
    
    async def create_pipeline(
        self,
        max_workers: int = 5,
        enable_rag: bool = True,
        enable_supervisor: bool = False
    ):
        """
        Erstellt neue Pipeline-Instanz für einen Request.
        
        Diese Methode erstellt eine frische Pipeline-Instanz mit:
        - Eigenem ThreadPool
        - Eigenem State (active_pipelines, steps)
        - Injizierten Shared Resources
        
        Args:
            max_workers: Anzahl paralleler Worker-Threads
            enable_rag: RAG-Integration aktivieren
            enable_supervisor: Supervisor-Agent aktivieren
        
        Returns:
            IntelligentMultiAgentPipeline: Frische Pipeline-Instanz
        
        Example:
            >>> factory = PipelineFactory(ollama, uds3, registry)
            >>> pipeline = await factory.create_pipeline(max_workers=5)
            >>> response = await pipeline.process_intelligent_query(request)
        """
        from backend.agents.veritas_intelligent_pipeline import IntelligentMultiAgentPipeline
        
        # Erstelle neue Pipeline-Instanz
        pipeline = IntelligentMultiAgentPipeline(max_workers=max_workers)
        
        # ✅ DEPENDENCY INJECTION: Shared Resources injizieren
        pipeline.ollama_client = self.ollama_client
        pipeline.uds3_strategy = self.uds3_strategy
        pipeline.agent_registry = self.agent_registry
        pipeline.progress_manager = self.progress_manager
        
        # Request-scoped Ressourcen initialisieren
        await pipeline._initialize_request_scoped_resources(
            enable_rag=enable_rag,
            enable_supervisor=enable_supervisor
        )
        
        # Factory Stats aktualisieren
        self.pipelines_created += 1
        self.pipelines_active += 1
        
        logger.info(
            f"✅ Pipeline-Instanz erstellt (#{self.pipelines_created}, "
            f"aktiv: {self.pipelines_active})"
        )
        
        return pipeline
    
    def mark_pipeline_completed(self):
        """
        Markiert Pipeline als abgeschlossen (für Stats).
        
        Sollte von Pipeline nach Cleanup aufgerufen werden.
        """
        self.pipelines_active = max(0, self.pipelines_active - 1)
        self.pipelines_completed += 1
    
    def get_factory_stats(self) -> dict:
        """
        Holt Factory-Statistiken.
        
        Returns:
            dict: Factory-Status und Statistiken
        """
        return {
            "pipelines_created": self.pipelines_created,
            "pipelines_active": self.pipelines_active,
            "pipelines_completed": self.pipelines_completed,
            "shared_resources": {
                "ollama_available": self.ollama_client is not None,
                "uds3_available": self.uds3_strategy is not None,
                "agent_registry_available": self.agent_registry is not None,
                "progress_manager_available": self.progress_manager is not None
            }
        }


# ===== SINGLETON FACTORY MANAGEMENT =====

_pipeline_factory: Optional[PipelineFactory] = None


def create_pipeline_factory(
    ollama_client,
    uds3_strategy,
    agent_registry,
    progress_manager=None
) -> PipelineFactory:
    """
    Erstellt oder aktualisiert die globale Pipeline Factory.
    
    Args:
        ollama_client: Ollama LLM Client
        uds3_strategy: UDS3 Database Strategy
        agent_registry: Agent Registry
        progress_manager: Optional Progress Manager
    
    Returns:
        PipelineFactory: Factory-Instanz
    """
    global _pipeline_factory
    
    _pipeline_factory = PipelineFactory(
        ollama_client=ollama_client,
        uds3_strategy=uds3_strategy,
        agent_registry=agent_registry,
        progress_manager=progress_manager
    )
    
    return _pipeline_factory


def get_pipeline_factory() -> Optional[PipelineFactory]:
    """
    Holt die globale Pipeline Factory.
    
    Returns:
        Optional[PipelineFactory]: Factory-Instanz oder None
    
    Raises:
        RuntimeError: Falls Factory noch nicht initialisiert
    """
    global _pipeline_factory
    
    if _pipeline_factory is None:
        raise RuntimeError(
            "Pipeline Factory nicht initialisiert! "
            "Rufe zuerst create_pipeline_factory() auf."
        )
    
    return _pipeline_factory


def reset_pipeline_factory():
    """
    Reset Factory (für Tests).
    """
    global _pipeline_factory
    _pipeline_factory = None


# ===== CONVENIENCE WRAPPER =====

async def create_request_scoped_pipeline(
    max_workers: int = 5,
    enable_rag: bool = True,
    enable_supervisor: bool = False
):
    """
    Convenience-Funktion: Erstellt Request-scoped Pipeline.
    
    Nutzt die globale Factory.
    
    Args:
        max_workers: Worker-Threads
        enable_rag: RAG aktivieren
        enable_supervisor: Supervisor aktivieren
    
    Returns:
        IntelligentMultiAgentPipeline: Neue Pipeline-Instanz
    
    Example:
        >>> pipeline = await create_request_scoped_pipeline(max_workers=5)
        >>> response = await pipeline.process_intelligent_query(request)
    """
    factory = get_pipeline_factory()
    return await factory.create_pipeline(
        max_workers=max_workers,
        enable_rag=enable_rag,
        enable_supervisor=enable_supervisor
    )


if __name__ == "__main__":
    print("=" * 80)
    print("VERITAS PIPELINE FACTORY - INFO")
    print("=" * 80)
    print()
    print("Diese Factory erstellt Request-scoped Pipeline-Instanzen.")
    print()
    print("Features:")
    print("  ✅ Request Isolation (kein Shared State)")
    print("  ✅ Automatic Cleanup (ThreadPool.shutdown())")
    print("  ✅ Dependency Injection (Shared Resources)")
    print("  ✅ Lazy Loading Support")
    print()
    print("Usage:")
    print("  1. Backend-Start: create_pipeline_factory(ollama, uds3, registry)")
    print("  2. Pro Request: pipeline = await factory.create_pipeline()")
    print("  3. Cleanup: Automatisch in pipeline.process_intelligent_query()")
    print()
    print("=" * 80)
