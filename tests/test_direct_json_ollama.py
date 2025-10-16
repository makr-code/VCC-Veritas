"""
Direct Test: Sende JSON-Prompt an Ollama
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.agents.veritas_json_citation_formatter import JSONCitationFormatter
from backend.agents.veritas_ollama_client import VeritasOllamaClient, OllamaRequest
import asyncio

async def test_direct_json_prompt():
    """
    Test: Sende JSON-Prompt direkt an Ollama
    """
    
    print("="*80)
    print("🧪 DIRECT JSON PROMPT TEST")
    print("="*80)
    
    # Get JSON prompt
    json_prompts = JSONCitationFormatter.get_json_prompt_template()
    
    query = "Was regelt § 58 LBO BW?"
    source_list = "[1] LBO BW Gesetzestext\n[2] Bauordnungsamt Leitfaden"
    rag_context = "[1] RAG: § 58 LBO BW behandelt Bauanträge und Genehmigungen"
    agent_results = "BuildingAgent: § 58 regelt formale Anforderungen"
    
    system_prompt = json_prompts["system"]
    user_prompt = json_prompts["user_template"].format(
        query=query,
        source_list=source_list,
        rag_context=rag_context,
        agent_results=agent_results
    )
    
    full_prompt = f"{system_prompt}\n\n{user_prompt}"
    
    print("\n📝 PROMPT LENGTH:", len(full_prompt), "chars")
    print("\n🔍 PROMPT PREVIEW (first 500 chars):")
    print("-"*80)
    print(full_prompt[:500])
    print("...")
    print("-"*80)
    
    print("\n⏳ Sende an Ollama...")
    
    # Send to Ollama
    ollama_client = VeritasOllamaClient()
    
    request = OllamaRequest(
        model="llama3.2:latest",
        prompt=full_prompt,
        temperature=0.5,
        max_tokens=2000
    )
    
    response = await ollama_client.generate_response(request)
    
    print("\n✅ Antwort erhalten:")
    print("="*80)
    print(response.response)
    print("="*80)
    
    # Check if JSON
    print("\n📊 ANALYSIS:")
    
    is_json_like = response.response.strip().startswith('{')
    print(f"\n  Starts with '{{': {'✅' if is_json_like else '❌'} {is_json_like}")
    
    if is_json_like:
        print("\n  🎉 LLM generierte JSON! Versuche zu parsen...")
        try:
            import json
            parsed = json.loads(response.response.strip())
            print(f"  ✅ Valid JSON mit keys: {list(parsed.keys())}")
            
            # Format to IEEE
            print("\n📝 FORMATIERE ZU IEEE:")
            print("="*80)
            formatted, success = JSONCitationFormatter.format_with_fallback(response.response)
            print(formatted)
            print("="*80)
            
            # Check for citations
            import re
            citations = re.findall(r'\[(\d+)\]', formatted)
            print(f"\n✅ Citations gefunden: {len(citations)} → {citations}")
            
        except Exception as e:
            print(f"  ❌ JSON parsing error: {e}")
    else:
        print("\n  ❌ LLM generierte KEIN JSON (normale Text-Antwort)")
        print("\n  💡 MÖGLICHE URSACHEN:")
        print("     1. LLM ignoriert JSON-Anweisungen")
        print("     2. Prompt nicht klar genug")
        print("     3. Model kann kein strukturiertes Output")
        print("     4. Temperature zu niedrig/hoch")

if __name__ == "__main__":
    asyncio.run(test_direct_json_prompt())
