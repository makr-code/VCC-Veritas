"""
ThemisDB Agent Framework
========================

OOP-basiertes Framework für RAG mit austauschbaren Database-Adaptern.

Design Patterns:
- Adapter Pattern: ThemisDB & UDS3 implementieren gemeinsames Interface
- Factory Pattern: Automatische Adapter-Erstellung
- Strategy Pattern: Austauschbare Query-Strategien
- Dependency Injection: Lose Kopplung der Komponenten

SOLID Principles:
✅ Single Responsibility - Jede Klasse hat eine klare Aufgabe
✅ Open/Closed - Erweiterbar ohne Änderung bestehenden Codes
✅ Liskov Substitution - Adapter sind austauschbar
✅ Interface Segregation - Klare, fokussierte Interfaces
✅ Dependency Inversion - Code gegen Abstraktion, nicht Implementierung

Author: VERITAS Backend Team
Date: 2025-12-03
Version: 2.0
"""

# Base classes and interfaces
from .base import (
    # Enums
    QueryType,
    QueryComplexity,
    CacheStrategy,
    
    # Data classes
    QueryContext,
    QueryPlan,
    QueryResult,
    RAGDocument,
    
    # Protocols
    EmbeddingProvider,
    CacheProvider,
    QueryExecutor,
    
    # Abstract classes
    QueryTemplate,
    QueryPlanner,
    ResultTransformer,
    QueryStrategy,
    
    # Exceptions
    ThemisDBAgentError,
    QueryPlanningError,
    QueryExecutionError,
    TransformationError,
    ValidationError,
)

# Concrete implementations
from .implementations import (
    # Templates
    VectorSearchTemplate,
    HybridQueryTemplate,
    ContextEnrichedTemplate,
    QueryTemplateFactory,
    
    # Planner
    AQLQueryPlanner,
    
    # Transformer
    RAGDocumentTransformer,
    
    # Strategy
    StandardQueryStrategy,
    
    # Cache
    InMemoryCache,
)

# Adapters
from .adapters import (
    # Enums & Data classes
    DatabaseType,
    DatabaseConfig,
    SearchOptions,
    DocumentResult,
    
    # Interface
    IDatabaseAdapter,
    
    # Implementations
    ThemisDBAdapter,
    UDS3Adapter,
    
    # Factory & Selector
    DatabaseAdapterFactory,
    AdapterSelector,
)

# Main RAG Agent
from .rag_agent import (
    ThemisDBRAGAgent,
    create_rag_agent,
    create_themisdb_agent,
    create_uds3_agent,
)

# Execution Plan Analysis
from .execution_plan_analysis import (
    # Enums
    ResourceType,
    QueryApproach,
    ExecutionMode,
    
    # Data Classes
    ResourceCost,
    ExecutionStep,
    ExecutionPlan,
    
    # Core Classes
    ResourceCostDatabase,
    QueryAnalyzer,
    ExecutionPlanBuilder,
    ExecutionPlanOptimizer,
    
    # Utilities
    format_execution_plan,
)

# Agent Framework Integration (NEW)
from .agent_framework_integration import (
    # Config Loader
    ResourceCostConfigLoader,
    
    # Mappers
    AgentCapabilityMapper,
    
    # Integrations
    ResearchPlanIntegration,
    IntelligentPipelineIntegration,
    UnifiedOrchestratorV7Integration,
    
    # Factory Functions
    create_intelligent_pipeline_integration,
    create_unified_orchestrator_integration,
    sync_costs_from_yaml,
)

__version__ = "2.2.0"
__author__ = "VERITAS Backend Team"

__all__ = [
    # Base
    "QueryType",
    "QueryComplexity",
    "CacheStrategy",
    "QueryContext",
    "QueryPlan",
    "QueryResult",
    "RAGDocument",
    "EmbeddingProvider",
    "CacheProvider",
    "QueryExecutor",
    "QueryTemplate",
    "QueryPlanner",
    "ResultTransformer",
    "QueryStrategy",
    "ThemisDBAgentError",
    
    # Implementations
    "VectorSearchTemplate",
    "HybridQueryTemplate",
    "ContextEnrichedTemplate",
    "QueryTemplateFactory",
    "AQLQueryPlanner",
    "RAGDocumentTransformer",
    "StandardQueryStrategy",
    "InMemoryCache",
    
    # Adapters
    "DatabaseType",
    "DatabaseConfig",
    "SearchOptions",
    "DocumentResult",
    "IDatabaseAdapter",
    "ThemisDBAdapter",
    "UDS3Adapter",
    "DatabaseAdapterFactory",
    "AdapterSelector",
    
    # Main Agent
    "ThemisDBRAGAgent",
    "create_rag_agent",
    "create_themisdb_agent",
    "create_uds3_agent",
    
    # Execution Plan Analysis
    "ResourceType",
    "QueryApproach",
    "ExecutionMode",
    "ResourceCost",
    "ExecutionStep",
    "ExecutionPlan",
    "ResourceCostDatabase",
    "QueryAnalyzer",
    "ExecutionPlanBuilder",
    "ExecutionPlanOptimizer",
    "format_execution_plan",
    
    # Agent Framework Integration
    "ResourceCostConfigLoader",
    "AgentCapabilityMapper",
    "ResearchPlanIntegration",
    "IntelligentPipelineIntegration",
    "UnifiedOrchestratorV7Integration",
    "create_intelligent_pipeline_integration",
    "create_unified_orchestrator_integration",
    "sync_costs_from_yaml",
]
