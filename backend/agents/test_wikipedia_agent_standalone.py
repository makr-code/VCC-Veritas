"""
VERITAS Wikipedia Agent - Standalone Test

Standalone-Test für den Wikipedia Agent ohne Abhängigkeiten
zum VERITAS-Hauptsystem.

Test-Kategorien:
- Wikipedia-Suche (verschiedene Themen)
- Artikelabruf (vollständige Artikel)
- Zusammenfassungen (kurze Übersichten)
- Mehrsprachige Abfragen
- Kategorien und Links
- Performance-Tests

Autor: VERITAS Agent System
Datum: 28. September 2025
"""

import asyncio
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

# Projekt-Root für Paketimporte sicherstellen
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from backend.agents.veritas_api_agent_wikipedia import (
    WikipediaAgent,
    WikipediaConfig,
    WikipediaLanguage,
    WikipediaQueryRequest,
    WikipediaQueryType,
    WikipediaSearchMode,
    create_wikipedia_agent,
)


class WikipediaAgentTester:
    """Standalone-Tester für den Wikipedia Agent"""

    def __init__(self):
        self.agent = None
        self.test_results = []

    def setup_agent(self):
        """Agent-Setup für Tests"""
        print("🔧 Setting up Wikipedia Agent...")

        config = WikipediaConfig(
            default_language="de",
            max_search_results=5,
            cache_enabled=True,
            timeout_seconds=10,
            extract_categories=True,
            extract_links=True,
        )

        self.agent = create_wikipedia_agent(config)
        print(f"✅ Wikipedia Agent ready (Mock-Mode: {not self.agent._stats['queries_processed']})")

    async def run_basic_search_tests(self):
        """Grundlegende Suchtests"""
        print("\n📋 === BASIC SEARCH TESTS ===")

        search_tests = [
            {
                "name": "Berlin Search",
                "query": "Berlin Deutschland Hauptstadt",
                "expected_keywords": ["berlin", "deutschland", "hauptstadt"],
            },
            {
                "name": "Science Search",
                "query": "Physik Quantenmechanik Wissenschaft",
                "expected_keywords": ["physik", "quantenmechanik"],
            },
            {
                "name": "Technology Search",
                "query": "Künstliche Intelligenz Machine Learning",
                "expected_keywords": ["künstliche", "intelligenz"],
            },
            {
                "name": "History Search",
                "query": "Geschichte Mittelalter Europa",
                "expected_keywords": ["geschichte", "mittelalter"],
            },
        ]

        for test in search_tests:
            await self._run_search_test(test)

    async def _run_search_test(self, test_config: Dict[str, Any]):
        """Einzelner Suchtest"""
        print(f"\n🔍 Test: {test_config['name']}")
        print(f"   Query: '{test_config['query']}'")

        request = WikipediaQueryRequest(
            query_id=f"search-{test_config['name'].lower().replace(' ', ' - ')}",
            query_text=test_config["query"],
            query_type=WikipediaQueryType.SEARCH,
            language=WikipediaLanguage.GERMAN,
            max_results=3,
            include_summary=True,
        )

        start_time = time.time()
        response = await self.agent.execute_query_async(request)
        execution_time = int((time.time() - start_time) * 1000)

        # Ergebnisse validieren
        success = response.success
        results_count = response.results_returned
        confidence = response.confidence_score

        print(f"   ✅ Status: {'SUCCESS' if success else 'FAILED'}")
        print(f"   📊 Results: {results_count}, Confidence: {confidence:.2f}")
        print(f"   ⏱️  Time: {execution_time}ms")

        # Erste Ergebnisse anzeigen
        for i, result in enumerate(response.search_results[:2], 1):
            print(f"      {i}. {result.title}")
            print(f"         {result.summary[:80]}...")
            print(f"         Score: {result.relevance_score:.2f}")

        # Test-Result speichern
        self.test_results.append(
            {
                "name": test_config["name"],
                "success": success,
                "results_count": results_count,
                "confidence": confidence,
                "execution_time_ms": execution_time,
                "query": test_config["query"],
            }
        )

    async def run_article_tests(self):
        """Artikel-Abruftests"""
        print("\n📄 === ARTICLE RETRIEVAL TESTS ===")

        article_tests = [
            {"name": "Specific Article - Berlin", "title": "Berlin", "language": WikipediaLanguage.GERMAN},
            {
                "name": "Specific Article - AI (English)",
                "title": "Artificial Intelligence",
                "language": WikipediaLanguage.ENGLISH,
            },
            {"name": "Technical Article - Quantum", "title": "Quantencomputer", "language": WikipediaLanguage.GERMAN},
        ]

        for test in article_tests:
            await self._run_article_test(test)

    async def _run_article_test(self, test_config: Dict[str, Any]):
        """Einzelner Artikel-Test"""
        print(f"\n📖 Test: {test_config['name']}")
        print(f"   Title: '{test_config['title']}'")
        print(f"   Language: {test_config['language'].value}")

        request = WikipediaQueryRequest(
            query_id=f"article-{test_config['name'].lower().replace(' ', ' - ')}",
            query_text=test_config["title"],
            query_type=WikipediaQueryType.ARTICLE,
            language=test_config["language"],
            include_content=True,
            include_categories=True,
            include_links=True,
        )

        start_time = time.time()
        response = await self.agent.execute_query_async(request)
        execution_time = int((time.time() - start_time) * 1000)

        # Artikel validieren
        if response.success and response.articles:
            article = response.articles[0]

            print(f"   ✅ Article loaded: {article.title}")
            print(f"   📊 Content: {article.word_count} words, {article.section_count} sections")
            print(f"   🏷️  Categories: {', '.join(article.categories[:3])}")
            print(f"   🔗 Links: {len(article.links)} internal links")
            print(f"   ⏱️  Time: {execution_time}ms")

            # Content-Preview
            if article.content:
                preview = article.content[:200].replace("\n", " ")
                print(f"   📝 Preview: {preview}...")
        else:
            print(f"   ❌ Failed: {response.error_message or 'Unknown error'}")

        # Test-Result
        self.test_results.append(
            {
                "name": test_config["name"],
                "success": response.success,
                "has_content": bool(response.articles and response.articles[0].content),
                "execution_time_ms": execution_time,
            }
        )

    async def run_multilingual_tests(self):
        """Mehrsprachige Tests"""
        print("\n🌍 === MULTILINGUAL TESTS ===")

        multilingual_tests = [
            {"query": "Berlin", "language": WikipediaLanguage.GERMAN, "expected": "deutsche Wikipedia"},
            {"query": "Berlin", "language": WikipediaLanguage.ENGLISH, "expected": "english Wikipedia"},
            {"query": "Paris", "language": WikipediaLanguage.FRENCH, "expected": "french Wikipedia"},
        ]

        for test in multilingual_tests:
            await self._run_multilingual_test(test)

    async def _run_multilingual_test(self, test_config: Dict[str, Any]):
        """Einzelner mehrsprachiger Test"""
        print(f"\n🌐 Language Test: {test_config['query']} ({test_config['language'].value})")

        request = WikipediaQueryRequest(
            query_id=f"lang-{test_config['language'].value}-{test_config['query']}",
            query_text=test_config["query"],
            query_type=WikipediaQueryType.SEARCH,
            language=test_config["language"],
            max_results=2,
        )

        response = await self.agent.execute_query_async(request)

        if response.success and response.search_results:
            result = response.search_results[0]
            print(f"   ✅ Found: {result.title}")
            print(f"   🌐 URL: {result.url}")
            print(f"   📝 Summary: {result.summary[:100]}...")
        else:
            print(f"   ⚠️  No results for {test_config['query']} in {test_config['language'].value}")

    async def run_performance_tests(self):
        """Performance-Tests"""
        print("\n⚡ === PERFORMANCE TESTS ===")

        # Multiple concurrent queries
        concurrent_queries = []
        for i in range(5):
            request = WikipediaQueryRequest(
                query_id=f"perf-{i}", query_text=f"Test Query {i}", query_type=WikipediaQueryType.SEARCH, max_results=3
            )
            concurrent_queries.append(self.agent.execute_query_async(request))

        print("🔄 Running 5 concurrent queries...")
        start_time = time.time()
        responses = await asyncio.gather(*concurrent_queries)
        total_time = int((time.time() - start_time) * 1000)

        successful_queries = sum(1 for r in responses if r.success)
        total_results = sum(r.results_returned for r in responses)

        print("   ✅ Concurrent execution completed")
        print(f"   📊 Success: {successful_queries}/5 queries")
        print(f"   📈 Total results: {total_results}")
        print(f"   ⏱️  Total time: {total_time}ms")
        print(f"   ⚡ Avg time per query: {total_time / 5:.1f}ms")

        # Cache-Test (zweite Ausführung sollte schneller sein)
        print("\n💾 Cache performance test...")
        cache_request = WikipediaQueryRequest(
            query_id="cache-test-1", query_text="Berlin Deutschland", query_type=WikipediaQueryType.SEARCH
        )

        # Erste Ausführung
        start_time = time.time()
        await self.agent.execute_query_async(cache_request)
        first_time = int((time.time() - start_time) * 1000)

        # Zweite Ausführung (sollte gecacht sein)
        start_time = time.time()
        await self.agent.execute_query_async(cache_request)
        second_time = int((time.time() - start_time) * 1000)

        print(f"   📊 First query: {first_time}ms")
        print(f"   📊 Cached query: {second_time}ms")
        print(f"   ⚡ Cache speedup: {first_time / max(1,second_time):.1f}x")

    async def run_specialized_query_tests(self):
        """Spezialisierte Query-Tests"""
        print("\n🎯 === SPECIALIZED QUERY TESTS ===")

        # Summary-Test
        print("\n📝 Summary Test:")
        summary_request = WikipediaQueryRequest(
            query_id="summary-test",
            query_text="Künstliche Intelligenz",
            query_type=WikipediaQueryType.SUMMARY,
            language=WikipediaLanguage.GERMAN,
        )

        response = await self.agent.execute_query_async(summary_request)
        if response.success and response.articles:
            article = response.articles[0]
            print(f"   ✅ Summary for: {article.title}")
            print(f"   📝 {article.summary}")

        # Random-Test
        print("\n🎲 Random Article Test:")
        random_request = WikipediaQueryRequest(
            query_id="random-test", query_text="", query_type=WikipediaQueryType.RANDOM, language=WikipediaLanguage.GERMAN
        )

        response = await self.agent.execute_query_async(random_request)
        if response.success and response.articles:
            article = response.articles[0]
            print(f"   🎯 Random article: {article.title}")
            print(f"   📝 {article.summary[:150]}...")

        # Categories-Test
        print("\n🏷️  Categories Test:")
        categories_request = WikipediaQueryRequest(
            query_id="categories-test",
            query_text="Wissenschaft",
            query_type=WikipediaQueryType.CATEGORIES,
            language=WikipediaLanguage.GERMAN,
        )

        response = await self.agent.execute_query_async(categories_request)
        if response.success and response.categories:
            print(f"   ✅ Found {len(response.categories)} categories:")
            for cat in response.categories:
                print(f"      📂 {cat.name} ({cat.articles_count} articles)")

    def print_test_summary(self):
        """Test-Zusammenfassung ausgeben"""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)

        if not self.test_results:
            print("❌ No test results available")
            return

        total_tests = len(self.test_results)
        successful_tests = sum(1 for r in self.test_results if r.get("success", False))
        total_results = sum(r.get("results_count", 0) for r in self.test_results)
        avg_time = sum(r.get("execution_time_ms", 0) for r in self.test_results) / max(1, total_tests)

        print(f"🧪 Total Tests: {total_tests}")
        print(f"✅ Successful: {successful_tests} ({successful_tests / total_tests:.1%})")
        print(f"❌ Failed: {total_tests - successful_tests}")
        print(f"📈 Total Results: {total_results}")
        print(f"⏱️  Average Time: {avg_time:.1f}ms")

        # Agent-Status
        if self.agent:
            status = self.agent.get_status()
            print("\n📊 Agent Performance:")
            print(f"   Queries processed: {status['performance']['queries_processed']}")
            print(f"   Success rate: {status['performance']['success_rate']:.1%}")
            print(f"   Cache hits: {status['performance']['cache_hits']}")
            print(f"   Languages used: {', '.join(status['capabilities']['languages_used'])}")

        print("\n🎯 Top performing tests:")
        sorted_results = sorted(
            [r for r in self.test_results if r.get("execution_time_ms") is not None],
            key=lambda x: x.get("execution_time_ms", 0),
        )

        for i, result in enumerate(sorted_results[:3], 1):
            print(f"   {i}. {result['name']}: {result['execution_time_ms']}ms")

    async def run_all_tests(self):
        """Alle Tests ausführen"""
        print("🧪 VERITAS Wikipedia Agent - Comprehensive Test Suite")
        print("=" * 60)

        self.setup_agent()

        # Test-Sequenz
        await self.run_basic_search_tests()
        await self.run_article_tests()
        await self.run_multilingual_tests()
        await self.run_specialized_query_tests()
        await self.run_performance_tests()

        # Zusammenfassung
        self.print_test_summary()

        print("\n🎉 Wikipedia Agent testing completed!")


async def main():
    """Hauptfunktion für Standalone-Tests"""
    tester = WikipediaAgentTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    # Ausführung
    asyncio.run(main())
