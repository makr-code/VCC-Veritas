#!/usr/bin/env python3
"""
VERITAS Backend OOP Refactoring Script
Reorganizes backend structure following OOP best practices
"""
import os
import shutil
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent
BACKEND_DIR = BASE_DIR / "backend"
AGENTS_DIR = BACKEND_DIR / "agents"

# File mappings: source -> destination
FILE_MOVES = {
    # Core - Orchestration
    "backend/orchestration/unified_orchestrator_v7.py": "backend/core/orchestration/unified_orchestrator_v7.py",
    
    # Core - Pipeline
    "backend/agents/veritas_intelligent_pipeline.py": "backend/core/pipeline/intelligent_pipeline.py",
    "backend/agents/veritas_pipeline_factory.py": "backend/core/pipeline/factory.py",
    "backend/agents/veritas_intelligent_pipeline_standalone.py": "backend/core/pipeline/standalone.py",
    
    # Core - Retrieval
    "backend/agents/veritas_hybrid_retrieval.py": "backend/core/retrieval/hybrid.py",
    "backend/agents/veritas_query_expansion.py": "backend/core/retrieval/query_expansion.py",
    "backend/agents/veritas_reciprocal_rank_fusion.py": "backend/core/retrieval/rrf.py",
    "backend/agents/veritas_sparse_retrieval.py": "backend/core/retrieval/sparse.py",
    
    # Core - LLM
    "backend/agents/veritas_ollama_client.py": "backend/core/llm/ollama_client.py",
    "backend/agents/veritas_vllm_client.py": "backend/core/llm/vllm_client.py",
    "backend/agents/veritas_llm_factory.py": "backend/core/llm/factory.py",
    
    # Core - Reranking
    "backend/agents/veritas_reranking_service.py": "backend/core/reranking/service.py",
    
    # Agents - Domain - Construction
    "backend/agents/veritas_api_agent_construction.py": "backend/agents/domain/construction/construction_agent.py",
    
    # Agents - Domain - Environmental
    "backend/agents/veritas_api_agent_environmental.py": "backend/agents/domain/environmental/environmental_agent.py",
    
    # Agents - Domain - Financial
    "backend/agents/veritas_api_agent_financial.py": "backend/agents/domain/financial/financial_agent.py",
    
    # Agents - Domain - Weather
    "backend/agents/veritas_api_agent_dwd_weather.py": "backend/agents/domain/weather/dwd_weather_agent.py",
    "backend/agents/veritas_api_agent_brightsky_weather.py": "backend/agents/domain/weather/brightsky_weather_agent.py",
    "backend/agents/veritas_api_agent_dwd_opendata.py": "backend/agents/domain/weather/dwd_opendata_agent.py",
    "backend/agents/veritas_dwd_simple.py": "backend/agents/domain/weather/dwd_simple.py",
    "backend/agents/veritas_api_agent_dwd_weather_v2.py": "backend/agents/domain/weather/dwd_weather_agent_v2.py",
    
    # Agents - Domain - Chemical
    "backend/agents/veritas_api_agent_chemical_data.py": "backend/agents/domain/chemical/chemical_data_agent.py",
    
    # Agents - Domain - Standards
    "backend/agents/veritas_api_agent_technical_standards.py": "backend/agents/domain/standards/technical_standards_agent.py",
    
    # Agents - Domain - Wikipedia
    "backend/agents/veritas_api_agent_wikipedia.py": "backend/agents/domain/wikipedia/wikipedia_agent.py",
    
    # Agents - Domain - Social
    "backend/agents/veritas_api_agent_social.py": "backend/agents/domain/social/social_agent.py",
    
    # Agents - Domain - Traffic
    "backend/agents/veritas_api_agent_traffic.py": "backend/agents/domain/traffic/traffic_agent.py",
    
    # Agents - Domain - Immissionsschutz
    "backend/agents/veritas_api_agent_immissionsschutz.py": "backend/agents/domain/immissionsschutz/immissionsschutz_agent.py",
    "backend/agents/veritas_api_agent_immissionschutz.py": "backend/agents/domain/immissionsschutz/immissionschutz_alt.py",
    "backend/agents/immissionsschutz_orchestrator.py": "backend/agents/domain/immissionsschutz/orchestrator.py",
    "backend/agents/immissionsschutz_agent_testserver_extension.py": "backend/agents/domain/immissionsschutz/testserver_extension.py",
    
    # Agents - Domain - Others
    "backend/agents/veritas_api_agent_boden_gewaesserschutz.py": "backend/agents/domain/environmental/boden_gewaesserschutz_agent.py",
    "backend/agents/veritas_api_agent_emissionen_monitoring.py": "backend/agents/domain/environmental/emissionen_monitoring_agent.py",
    "backend/agents/veritas_api_agent_genehmigung.py": "backend/agents/domain/construction/genehmigung_agent.py",
    "backend/agents/veritas_api_agent_naturschutz.py": "backend/agents/domain/environmental/naturschutz_agent.py",
    "backend/agents/veritas_api_agent_verwaltungsprozess.py": "backend/agents/domain/social/verwaltungsprozess_agent.py",
    "backend/agents/veritas_api_agent_verwaltungsrecht.py": "backend/agents/domain/social/verwaltungsrecht_agent.py",
    "backend/agents/veritas_verwaltungsrecht_worker.py": "backend/agents/domain/social/verwaltungsrecht_worker.py",
    "backend/agents/veritas_api_agent_rechtsrecherche.py": "backend/agents/domain/social/rechtsrecherche_agent.py",
    "backend/agents/veritas_api_agent_database.py": "backend/agents/domain/database_agent.py",
    
    # Agents - Registry
    "backend/agents/agent_registry.py": "backend/agents/registry/agent_registry.py",
    "backend/agents/veritas_api_agent_registry.py": "backend/agents/registry/api_agent_registry.py",
    "backend/agents/registry_agent_adapter.py": "backend/agents/registry/registry_adapter.py",
    
    # Agents - Orchestrator
    "backend/agents/veritas_api_agent_orchestrator.py": "backend/agents/orchestrator/agent_orchestrator.py",
    "backend/agents/veritas_api_agent_pipeline_manager.py": "backend/agents/orchestrator/pipeline_manager.py",
    
    # Agents - Supervisor
    "backend/agents/veritas_supervisor_agent.py": "backend/agents/supervisor/supervisor_agent.py",
    "backend/agents/veritas_supervisor_agent_message_extension.py": "backend/agents/supervisor/message_extension.py",
    
    # Agents - Core Components (keep as utilities)
    "backend/agents/veritas_api_agent_core_components.py": "backend/agents/core_components.py",
    
    # Agents - Database Extensions
    "backend/agents/database_agent_testserver_extension.py": "backend/agents/domain/database/testserver_extension.py",
    
    # Agents - UDS3 Adapters (move to adapters later)
    "backend/agents/veritas_uds3_adapter.py": "backend/adapters/uds3/uds3_adapter.py",
    "backend/agents/veritas_uds3_hybrid_agent.py": "backend/adapters/uds3/uds3_hybrid_agent.py",
    "backend/agents/veritas_uds3_hybrid_agent_v2.py": "backend/adapters/uds3/uds3_hybrid_agent_v2.py",
    
    # Agents - ThemisDB (already well-structured, keep as is)
    "backend/agents/veritas_themisdb_rag_agent.py": "backend/agents/themisdb/legacy_rag_agent.py",
    
    # Agents - Environmental Adapter
    "backend/agents/environmental_agent_adapter.py": "backend/adapters/environmental/environmental_adapter.py",
    
    # Helpers - Context
    "backend/agents/context_manager.py": "backend/helpers/context/context_manager.py",
    
    # Helpers - Prompts
    "backend/agents/veritas_enhanced_prompts.py": "backend/helpers/prompts/enhanced_prompts.py",
    
    # Helpers - Formatting
    "backend/agents/veritas_json_citation_formatter.py": "backend/helpers/formatting/citation_formatter.py",
    "backend/agents/veritas_rich_media_schema.py": "backend/helpers/formatting/rich_media_schema.py",
    "backend/agents/veritas_shared_enums.py": "backend/helpers/formatting/shared_enums.py",
    
    # Helpers - Messaging
    "backend/agents/agent_message_broker.py": "backend/helpers/messaging/message_broker.py",
    "backend/agents/agent_message_broker_enhanced.py": "backend/helpers/messaging/message_broker_enhanced.py",
    
    # Helpers - Generation
    "backend/agents/agent_generator.py": "backend/helpers/generation/agent_generator.py",
    
    # Services - RAG
    "backend/agents/rag_context_service.py": "backend/services/rag/context_service.py",
}

def create_init_files():
    """Create __init__.py files in all directories"""
    dirs_to_init = [
        "backend/core",
        "backend/core/orchestration",
        "backend/core/pipeline",
        "backend/core/retrieval",
        "backend/core/llm",
        "backend/core/reranking",
        "backend/agents/domain",
        "backend/agents/domain/construction",
        "backend/agents/domain/environmental",
        "backend/agents/domain/financial",
        "backend/agents/domain/weather",
        "backend/agents/domain/chemical",
        "backend/agents/domain/standards",
        "backend/agents/domain/wikipedia",
        "backend/agents/domain/social",
        "backend/agents/domain/traffic",
        "backend/agents/domain/immissionsschutz",
        "backend/agents/domain/database",
        "backend/agents/registry",
        "backend/agents/orchestrator",
        "backend/agents/supervisor",
        "backend/adapters/uds3",
        "backend/adapters/environmental",
        "backend/helpers",
        "backend/helpers/context",
        "backend/helpers/prompts",
        "backend/helpers/formatting",
        "backend/helpers/messaging",
        "backend/helpers/generation",
        "backend/services",
        "backend/services/rag",
    ]
    
    for dir_path in dirs_to_init:
        full_path = BASE_DIR / dir_path
        full_path.mkdir(parents=True, exist_ok=True)  # Ensure directory exists
        init_file = full_path / "__init__.py"
        if not init_file.exists():
            init_file.write_text("# Auto-generated __init__.py\n")
            print(f"✅ Created {init_file.relative_to(BASE_DIR)}")

def move_files():
    """Move files according to FILE_MOVES mapping"""
    moved = 0
    skipped = 0
    
    for source, dest in FILE_MOVES.items():
        source_path = BASE_DIR / source
        dest_path = BASE_DIR / dest
        
        if not source_path.exists():
            print(f"⚠️  Skip {source} (not found)")
            skipped += 1
            continue
        
        # Create destination directory if needed
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Move file
        shutil.move(str(source_path), str(dest_path))
        print(f"✅ Moved {source_path.relative_to(BASE_DIR)} → {dest_path.relative_to(BASE_DIR)}")
        moved += 1
    
    print(f"\n📊 Summary: {moved} files moved, {skipped} skipped")

def main():
    print("🏗️  VERITAS Backend OOP Refactoring")
    print("=" * 60)
    
    print("\n📁 Creating directory structure...")
    create_init_files()
    
    print("\n📦 Moving files...")
    move_files()
    
    print("\n✅ Refactoring complete!")
    print("\n⚠️  Next steps:")
    print("1. Update imports in moved files")
    print("2. Run tests to verify everything works")
    print("3. Clean up documentation")

if __name__ == "__main__":
    main()
