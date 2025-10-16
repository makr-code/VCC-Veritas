#!/usr/bin/env python3
"""
Test Phase 5 Hybrid Search API Endpoint
"""

import httpx
import asyncio
import json

async def test_hybrid_search():
    base_url = "http://localhost:5000"
    
    print("=" * 80)
    print("🧪 TESTING PHASE 5 HYBRID SEARCH API")
    print("=" * 80)
    
    # Test 1: Health Check
    print("\n📋 Test 1: API Health Check")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{base_url}/health")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ API is running")
                if "phase5_hybrid_search" in data:
                    print(f"   Phase 5 Status: {data['phase5_hybrid_search']}")
                else:
                    print(f"   ⚠️ Phase 5 info not in health check")
            else:
                print(f"   ❌ API not healthy: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Health check failed: {e}")
    
    # Test 2: Hybrid Search Endpoint
    print("\n📋 Test 2: Hybrid Search Endpoint")
    test_query = "BGB Taschengeldparagraph Minderjährige"
    print(f"   Query: '{test_query}'")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{base_url}/v2/hybrid/search",
                params={"query": test_query, "top_k": 5}
            )
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Hybrid search successful!")
                print(f"\n   Results:")
                print(f"      Total: {data['total_results']}")
                print(f"      Latency: {data['latency_ms']:.0f}ms")
                print(f"      Mode: {data['mode']}")
                
                if data['results']:
                    print(f"\n   Top 3 Results:")
                    for i, result in enumerate(data['results'][:3], 1):
                        print(f"\n      {i}. doc_id: {result['doc_id']}")
                        print(f"         score: {result['score']:.4f}")
                        print(f"         dense: {result['dense_score']:.4f}, sparse: {result['sparse_score']:.4f}")
                        print(f"         content: {result['content'][:100]}...")
                else:
                    print(f"   ⚠️ No results returned")
                    
            elif response.status_code == 503:
                print(f"   ⚠️ Service unavailable: {response.json()}")
            else:
                print(f"   ❌ Request failed: {response.status_code}")
                print(f"      {response.text}")
                
        except Exception as e:
            print(f"   ❌ Hybrid search failed: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    asyncio.run(test_hybrid_search())
