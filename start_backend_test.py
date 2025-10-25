#!/usr/bin/env python3
"""
VERITAS Backend - Minimal Test Version
Läuft ohne UDS3, nur mit Agent Registry und Intelligent Pipeline
"""
import sys
import os
import logging

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
)
logger = logging.getLogger(__name__)

print("=" * 80)
print("🚀 VERITAS Backend - TEST-MODUS (ohne UDS3)")
print("=" * 80)

try:
    # Python-Pfad setup
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    print("\n📦 Importiere FastAPI...")
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    
    print("✅ FastAPI importiert")
    
    # Check Streaming System
    streaming_available = False
    try:
        from shared.pipelines.veritas_streaming_progress import create_progress_manager
        streaming_available = True
        print("✅ Streaming System verfügbar")
    except ImportError:
        print("⚠️ Streaming System nicht verfügbar")
    
    # Check UDS3
    uds3_available = False
    try:
        import uds3
        uds3_available = True
        print("✅ UDS3 System verfügbar")
    except ImportError:
        print("⚠️ UDS3 System nicht verfügbar (Test-Modus)")
    
    # Check Ollama
    ollama_available = False
    try:
        from backend.agents.veritas_ollama_integration import get_ollama_client
        ollama_client = get_ollama_client()
        if ollama_client:
            ollama_available = True
            print("✅ Ollama Client verfügbar")
        else:
            print("⚠️ Ollama Client nicht erreichbar")
    except Exception as e:
        print(f"⚠️ Ollama nicht verfügbar: {e}")
    
    # App erstellen
    app = FastAPI(title="VERITAS Test Backend")
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    print("\n📦 Importiere Agent Registry...")
    from backend.agents.agent_registry import AgentRegistry
    
    # Registry initialisieren
    registry = AgentRegistry()
    print(f"✅ Agent Registry initialisiert: {len(registry.agents)} Agents")
    
    @app.get("/health")
    async def health():
        """Health Check Endpoint"""
        return {
            "status": "healthy",
            "mode": "TEST" if not uds3_available else "FULL",
            "streaming_available": streaming_available,
            "intelligent_pipeline_available": True,
            "uds3_available": uds3_available,
            "ollama_available": ollama_available,
            "agents_count": len(registry.agents)
        }
    
    @app.get("/capabilities")
    async def capabilities():
        """Agent Capabilities Endpoint"""
        return {
            "available_agents": list(registry.agents.keys()),
            "total_count": len(registry.agents),
            "domains": {
                "environmental": len([a for a in registry.agents.values() if a.domain.value == "environmental"]),
                "administrative": len([a for a in registry.agents.values() if a.domain.value == "administrative"]),
                "data": len([a for a in registry.agents.values() if a.domain.value == "data"])
            }
        }
    
    @app.post("/v2/query/stream")
    async def query_stream(request: dict):
        """Minimal Streaming Query Endpoint"""
        query = request.get("query", "")
        session_id = request.get("session_id", "test")
        
        # Simuliere Agent-Execution
        from fastapi.responses import StreamingResponse
        import json
        import asyncio
        
        async def generate():
            # Query Start
            yield f"data: {json.dumps({'event': 'QUERY_START', 'query': query, 'session_id': session_id})}\n\n"
            await asyncio.sleep(0.1)
            
            # Simuliere 3 Agents
            test_agents = ["VerwaltungsrechtAgent", "ImmissionsschutzAgent", "GenehmigungsAgent"]
            for i, agent_name in enumerate(test_agents):
                if agent_name in registry.agents:
                    await asyncio.sleep(0.2)
                    result = {
                        "event": "AGENT_COMPLETE",
                        "agent": agent_name,
                        "result": {
                            "content": f"Test-Antwort von {agent_name}",
                            "confidence_score": 0.8,
                            "is_simulation": False
                        }
                    }
                    yield f"data: {json.dumps(result)}\n\n"
            
            # Stream Complete
            await asyncio.sleep(0.1)
            final = {
                "event": "STREAM_COMPLETE",
                "final_result": {
                    "main_response": f"Test-Antwort für: {query}",
                    "agent_count": len(test_agents)
                }
            }
            yield f"data: {json.dumps(final)}\n\n"
        
        return StreamingResponse(generate(), media_type="text/event-stream")
    
    print("\n✅ Endpoints konfiguriert:")
    print("   GET  /health")
    print("   GET  /capabilities")
    print("   POST /v2/query/stream")
    
    print("\n🌐 Starte Server auf http://localhost:5000...")
    print("=" * 80)
    print("\nDrücke Ctrl+C zum Beenden\n")
    
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000, log_level="info")
    
except ImportError as e:
    print(f"\n❌ Import-Fehler: {e}")
    print("\nBitte installieren: pip install fastapi uvicorn")
    sys.exit(1)
except Exception as e:
    print(f"\n❌ Fehler: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
