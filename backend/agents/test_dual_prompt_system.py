#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VERITAS Dual-Prompt System - Test Suite

Testet:
1. Internal RAG Query-Enrichment
2. External User-Response-Generierung
3. Vergleich Alt vs. Neu

Author: VERITAS System
Date: 2025-01-07
"""

import os
import sys
<<<<<<< Updated upstream
import asyncio
import json
from typing import Dict, Any
=======
from typing import Any, Dict, List, cast
>>>>>>> Stashed changes

# Projekt-Root für Paketimporte
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.append(REPO_ROOT)

from backend.agents.veritas_ollama_client import VeritasOllamaClient


class DualPromptTester:
    """Test Suite für Dual-Prompt-System"""
<<<<<<< Updated upstream
    
    TEST_QUERIES = [
=======

    TEST_QUERIES: List[Dict[str, Any]] = [
>>>>>>> Stashed changes
        {
            "query": "Was brauche ich für eine Baugenehmigung?",
            "domain": "building",
            "expected_keywords": ["Baugenehmigung", "Bauantrag", "BauGB"],
            "forbidden_phrases": [
                "Antwort auf die Frage",
                "Basierend auf den bereitgestellten Informationen",
                "Ich kann Ihnen folgendes mitteilen"
            ]
        },
        {
            "query": "Welche Emissionsgrenzwerte gelten für Industrieanlagen?",
            "domain": "environmental",
            "expected_keywords": ["Emissionsgrenzwerte", "BImSchG", "TA Luft"],
            "forbidden_phrases": [
                "Antwort auf die Frage",
                "Basierend auf"
            ]
        },
        {
            "query": "Wo kann ich in der Innenstadt parken?",
            "domain": "transport",
            "expected_keywords": ["Parken", "Parkplatz", "Innenstadt"],
            "forbidden_phrases": [
                "Antwort auf die Frage"
            ]
        }
    ]
    
    def __init__(self):
        self.results: Dict[str, Any] = {
            "query_enrichment": [],
            "user_responses": [],
            "validation": {
                "total_tests": 0,
                "passed_tests": 0,
                "failed_tests": 0
            }
        }
    
    async def test_query_enrichment(self, client: VeritasOllamaClient):
        """
        Test PHASE 1: Internal RAG Query-Enrichment
        """
        print("\n" + "=" * 60)
        print("🔍 TEST PHASE 1: Internal RAG Query-Enrichment")
        print("=" * 60)
        
        for test_case in self.TEST_QUERIES:
            print(f"\n📋 Query: {test_case['query']}")
            print(f"   Domain: {test_case['domain']}")
            
            try:
                # Query-Enrichment durchführen
<<<<<<< Updated upstream
                enriched = await client.enrich_query_for_rag(
                    query=test_case["query"],
                    domain=test_case["domain"],
                    user_context={}
                )
                
                # Validierung
                keywords_found = enriched.get("keywords", [])
                search_terms_found = enriched.get("search_terms", [])
                
=======
                # Normalize types for mypy: ensure we pass `str` values
                query: str = str(test_case.get("query", ""))
                domain: str = str(test_case.get("domain", ""))

                temp = await client.enrich_query_for_rag(
                    query=query, domain=domain, user_context={}
                )
                enriched: Dict[str, Any] = temp

                # Validierung
                keywords_found: List[str] = list(enriched.get("keywords", []))
                search_terms_found: List[str] = list(enriched.get("search_terms", []))

>>>>>>> Stashed changes
                # Check: Expected Keywords vorhanden?
                keywords_match = any(
                    expected_keyword.lower() in str(keywords_found).lower()
                    for expected_keyword in test_case["expected_keywords"]
                )
                
                # Check: Mindestens 5 Search-Terms?
                sufficient_search_terms = len(search_terms_found) >= 5
                
                # Ergebnis
                test_passed = keywords_match and sufficient_search_terms
                
                result = {
                    "query": test_case["query"],
                    "domain": test_case["domain"],
                    "keywords_found": keywords_found,
                    "search_terms_count": len(search_terms_found),
                    "keywords_match": keywords_match,
                    "sufficient_search_terms": sufficient_search_terms,
                    "test_passed": test_passed
                }
                
                self.results["query_enrichment"].append(result)
                
                # Output
                print(f"   Keywords: {keywords_found[:5]}")
                print(f"   Search-Terms: {len(search_terms_found)} terms")
                print(f"   ✅ PASSED" if test_passed else "   ❌ FAILED")
                
                if test_passed:
                    self.results["validation"]["passed_tests"] += 1
                else:
                    self.results["validation"]["failed_tests"] += 1
                    
            except Exception as e:
                print(f"   ❌ ERROR: {e}")
                self.results["validation"]["failed_tests"] += 1
            
            self.results["validation"]["total_tests"] += 1
    
    async def test_user_responses(self, client: VeritasOllamaClient):
        """
        Test PHASE 2: External User-Response-Generierung
        """
        print("\n" + "=" * 60)
        print("💬 TEST PHASE 2: External User-Response-Generierung")
        print("=" * 60)
        
        for test_case in self.TEST_QUERIES:
            print(f"\n📋 Query: {test_case['query']}")
            
            try:
                # Mock Agent-Results (simuliere RAG + Agents)
                mock_agent_results = {
                    "legal_framework": f"Relevante Gesetze für {test_case['domain']}",
                    "document_retrieval": "15 Dokumente gefunden"
                }
                
                mock_rag_context = {
                    "documents": ["Merkblatt", "Gesetzestext"],
                    "confidence": 0.85
                }
                
                # User-Response generieren
                # Normalize types for mypy: ensure we pass `str` values
                query: str = str(test_case.get("query", ""))

                response_temp = await client.synthesize_agent_results(
                    query=query,
                    agent_results=mock_agent_results,
                    rag_context=mock_rag_context,
                    aggregation_summary={},
                    consensus_summary={}
                )
<<<<<<< Updated upstream
                
                response_text = response.get("response_text", "")
                
=======
                response: Dict[str, Any] = response_temp

                response_text = str(response.get("response_text", ""))

>>>>>>> Stashed changes
                # Validierung: Forbidden Phrases dürfen NICHT vorkommen
                forbidden_found = []
                for forbidden_phrase in test_case["forbidden_phrases"]:
                    if forbidden_phrase.lower() in response_text.lower():
                        forbidden_found.append(forbidden_phrase)
                
                # Check: Response mindestens 100 Zeichen?
                sufficient_length = len(response_text) >= 100
                
                # Check: Strukturierte Formatierung? (Listen, Absätze)
                has_structure = ("•" in response_text or 
                                "1." in response_text or 
                                "\n\n" in response_text)
                
                # Ergebnis
                test_passed = (
                    len(forbidden_found) == 0 and 
                    sufficient_length and 
                    has_structure
                )
                
                result = {
                    "query": test_case["query"],
                    "response_length": len(response_text),
                    "forbidden_found": forbidden_found,
                    "sufficient_length": sufficient_length,
                    "has_structure": has_structure,
                    "test_passed": test_passed,
                    "response_preview": response_text[:200] + "..."
                }
                
                self.results["user_responses"].append(result)
                
                # Output
                print(f"   Response-Länge: {len(response_text)} Zeichen")
                print(f"   Forbidden Phrases: {len(forbidden_found)} gefunden")
                if forbidden_found:
                    print(f"      → {forbidden_found}")
                print(f"   Strukturiert: {'✅' if has_structure else '❌'}")
                print(f"   Preview: {response_text[:150]}...")
                print(f"   {'✅ PASSED' if test_passed else '❌ FAILED'}")
                
                if test_passed:
                    self.results["validation"]["passed_tests"] += 1
                else:
                    self.results["validation"]["failed_tests"] += 1
                    
            except Exception as e:
                print(f"   ❌ ERROR: {e}")
                self.results["validation"]["failed_tests"] += 1
            
            self.results["validation"]["total_tests"] += 1
    
    def print_summary(self):
        """Druckt Test-Zusammenfassung"""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total = self.results["validation"]["total_tests"]
        passed = self.results["validation"]["passed_tests"]
        failed = self.results["validation"]["failed_tests"]
        
        print(f"Total Tests: {total}")
        print(f"✅ Passed: {passed} ({passed/total*100:.1f}%)")
        print(f"❌ Failed: {failed} ({failed/total*100:.1f}%)")
        
        print("\n🔍 Query-Enrichment Details:")
<<<<<<< Updated upstream
        for result in self.results["query_enrichment"]:
            status = "✅" if result["test_passed"] else "❌"
            print(f"  {status} {result['query'][:50]}... → {result['search_terms_count']} search-terms")
        
        print("\n💬 User-Response Details:")
        for result in self.results["user_responses"]:
            status = "✅" if result["test_passed"] else "❌"
            forbidden_count = len(result["forbidden_found"])
            print(f"  {status} {result['query'][:50]}... → {forbidden_count} forbidden phrases")
        
=======
        for raw in self.results.get("query_enrichment", []):
            result = cast(Dict[str, Any], raw)
            status = "✅" if result.get("test_passed") else "❌"
            query_preview = str(result.get("query", ""))[:50]
            print(f"  {status} {query_preview}... → {result.get('search_terms_count', 0)} search-terms")

        print("\n💬 User-Response Details:")
        for raw in self.results.get("user_responses", []):
            result = cast(Dict[str, Any], raw)
            status = "✅" if result.get("test_passed") else "❌"
            forbidden_count = len(result.get("forbidden_found", []))
            query_preview = str(result.get("query", ""))[:50]
            print(f"  {status} {query_preview}... → {forbidden_count} forbidden phrases")

>>>>>>> Stashed changes
        print("\n" + "=" * 60)
        if failed == 0:
            print("🎉 ALL TESTS PASSED!")
        else:
            print(f"⚠️ {failed} TESTS FAILED - Review logs above")
        print("=" * 60)
    
    def save_results(self, filepath: str = "test_results_dual_prompt.json"):
        """Speichert Test-Ergebnisse als JSON"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Test results saved to: {filepath}")


async def main():
    """Haupttestfunktion"""
    
    print("🤖 VERITAS Dual-Prompt System - Test Suite")
    print("=" * 60)
    
    tester = DualPromptTester()
    
    async with VeritasOllamaClient() as client:
        # Health Check
        health = await client.health_check()
        print(f"\n🏥 Ollama Health Check: {'✅ OK' if health else '❌ FAILED'}")
        
        if not health:
            print("\n❌ Ollama Server nicht erreichbar!")
            print("   Starte Ollama mit: ollama serve")
            return
<<<<<<< Updated upstream
        
        print(f"   Available Models: {list(client.available_models.keys())}")
        print(f"   Default Model: {client.default_model}")
        
=======

        # Cast for mypy so we don't index unknown container types
        available_models_list = [str(k) for k in list(getattr(client, "available_models", {}).keys())]
        default_model = str(getattr(client, "default_model", ""))
        print(f"   Available Models: {available_models_list}")
        print(f"   Default Model: {default_model}")

>>>>>>> Stashed changes
        # Test PHASE 1: Query-Enrichment
        await tester.test_query_enrichment(client)
        
        # Test PHASE 2: User-Responses
        await tester.test_user_responses(client)
        
        # Summary
        tester.print_summary()
        
        # Save Results
        tester.save_results()


if __name__ == "__main__":
    asyncio.run(main())
