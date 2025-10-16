import asyncio
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from backend.agents.veritas_ollama_client import VeritasOllamaClient, OllamaRequest


async def main() -> None:
    client = VeritasOllamaClient(base_url="http://127.0.0.1:11434", timeout=2, max_retries=1)
    await client.initialize()
    request = OllamaRequest(
        model=client.default_model,
        prompt="Testfall für Offline-Fallback",
        temperature=0.1,
        max_tokens=64,
    )
    response = await client.generate_response(request)
    print(
        json.dumps(
            {
                "offline_mode": client.offline_mode,
                "fallback_used": "Fallback-Antwort" in response.response,
                "model": response.model,
                "confidence": response.confidence_score,
            },
            ensure_ascii=False,
        )
    )
    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
