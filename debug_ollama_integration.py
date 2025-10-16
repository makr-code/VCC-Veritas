#!/usr/bin/env python3
"""Debug-Skript für Ollama-Integration"""

import asyncio
import sys
import os

# Pfad anpassen
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_ollama():
    print("🔍 Testing Ollama Integration...\n")
    
    # 1. Import Backend-Module
    try:
        from backend.agents.veritas_ollama_client import get_ollama_client
        print("✅ veritas_ollama_client importiert")
    except Exception as e:
        print(f"❌ Import Error: {e}")
        return
    
    # 2. Ollama-Client initialisieren
    try:
        ollama_client = await get_ollama_client()
        print(f"✅ Ollama-Client initialisiert: {ollama_client}")
        print(f"   Type: {type(ollama_client)}")
        print(f"   Has generate_response: {hasattr(ollama_client, 'generate_response')}")
    except Exception as e:
        print(f"❌ Ollama-Client Init Error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 3. Stage-Reflection-Service initialisieren
    try:
        from backend.services.stage_reflection_service import get_reflection_service, ReflectionStage
        reflection_service = get_reflection_service(ollama_client)
        print(f"✅ ReflectionService initialisiert")
        print(f"   reflection_enabled: {reflection_service.reflection_enabled}")
        print(f"   ollama_client: {reflection_service.ollama_client is not None}")
    except Exception as e:
        print(f"❌ ReflectionService Init Error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 4. Test LLM-Call
    try:
        print("\n🧠 Testing LLM Call...")
        test_prompt = "Antworte mit genau einem Wort: Hallo"
        response = await reflection_service._call_llm_reflection(test_prompt, ReflectionStage.HYPOTHESIS)
        print(f"✅ LLM Response: '{response}'")
        print(f"   Length: {len(response)} chars")
    except Exception as e:
        print(f"❌ LLM Call Error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 5. Test Reflection
    try:
        print("\n🔍 Testing Full Reflection...")
        reflection = await reflection_service.reflect_on_stage(
            stage=ReflectionStage.HYPOTHESIS,
            user_query="Test-Query",
            stage_data={'hypotheses': ['Test Hypothese 1', 'Test Hypothese 2']},
            context={}
        )
        print(f"✅ Reflection erstellt:")
        print(f"   completion_percent: {reflection.completion_percent}")
        print(f"   fulfillment_status: {reflection.fulfillment_status}")
        print(f"   identified_gaps: {reflection.identified_gaps}")
        print(f"   gathered_info: {reflection.gathered_info}")
        print(f"   confidence: {reflection.confidence}")
        print(f"   llm_reasoning: {reflection.llm_reasoning[:100] if reflection.llm_reasoning else 'None'}...")
    except Exception as e:
        print(f"❌ Reflection Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ollama())
