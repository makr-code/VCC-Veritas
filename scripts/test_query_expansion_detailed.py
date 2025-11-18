#!/usr/bin/env python3
"""
Test QueryExpander with detailed logging
"""

import asyncio
import logging
import sys
import time
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.DEBUG)

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.agents.veritas_query_expansion import QueryExpander, QueryExpansionConfig


async def test_query_expander():
    print("=" * 60)
    print("QUERY EXPANDER TEST - WITH OLLAMA")
    print("=" * 60)

    # Test 1: Default Config
    print("\n📋 Test 1: Default Configuration")
    print("-" * 60)

    config = QueryExpansionConfig()
    print(f"Model: {config.model}")
    print(f"Ollama URL: {config.ollama_base_url}")
    print(f"Num Expansions: {config.num_expansions}")
    print(f"Timeout: {config.timeout}s")

    expander = QueryExpander(config)

    # Test Query
    query = "BGB Taschengeldparagraph"
    print(f"\n🔍 Query: '{query}'")
    print(f"⏱️  Starting expansion...")

    start_time = time.time()

    try:
        results = await expander.expand(query, num_expansions=2)

        elapsed = (time.time() - start_time) * 1000

        print(f"\n✅ Expansion completed in {elapsed:.0f}ms")
        print(f"📊 Results: {len(results)} variants")
        print("-" * 60)

        for i, result in enumerate(results, 1):
            print(f"\n{i}. Text: {result.text}")
            print(f"   Strategy: {result.strategy}")
            print(f"   Confidence: {result.confidence:.2f}")
            print(f"   Metadata: {result.metadata}")

        # Performance Analysis
        print("\n" + "=" * 60)
        print("PERFORMANCE ANALYSIS")
        print("=" * 60)

        if elapsed < 100:
            print(f"✅ EXCELLENT: {elapsed:.0f}ms (Target: <100ms)")
        elif elapsed < 500:
            print(f"🟡 GOOD: {elapsed:.0f}ms (Target: <100ms, Acceptable: <500ms)")
        elif elapsed < 1000:
            print(f"⚠️  SLOW: {elapsed:.0f}ms (Warning: Approaching 1s)")
        else:
            print(f"❌ TOO SLOW: {elapsed:.0f}ms (Critical: >1s)")
            print(f"   Recommendation: DISABLE Query Expansion")

    except Exception as e:
        elapsed = (time.time() - start_time) * 1000
        print(f"\n❌ ERROR after {elapsed:.0f}ms:")
        print(f"   {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_query_expander())
