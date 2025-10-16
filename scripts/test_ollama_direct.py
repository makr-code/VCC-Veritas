#!/usr/bin/env python3
"""
Quick Ollama API Test
"""

import httpx
import asyncio

async def test_ollama():
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "llama3.2:latest",
        "prompt": "Say hello in one word",
        "stream": False,
        "options": {
            "temperature": 0.7,
            "num_predict": 10
        }
    }
    
    print(f"Testing Ollama API: {url}")
    print(f"Model: {payload['model']}")
    print(f"Prompt: {payload['prompt']}")
    print("-" * 60)
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"\n✅ SUCCESS!")
                print(f"Generated Text: {result.get('response', 'N/A')}")
            else:
                print(f"\n❌ ERROR: {response.status_code}")
                
    except Exception as e:
        print(f"\n❌ EXCEPTION: {e}")

if __name__ == "__main__":
    asyncio.run(test_ollama())
