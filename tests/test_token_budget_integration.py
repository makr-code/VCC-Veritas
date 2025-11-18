#!/usr/bin/env python3
"""
Integration Test: Token Budget Calculator + Intent Classifier in Pipeline
==========================================================================
Testet die Integration der beiden Services in die IntelligentMultiAgentPipeline

Author: VERITAS System
Date: 2025-10-17
"""

import asyncio
import os
import sys

# Repo-Root hinzufügen
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

# Direct imports
sys.path.insert(0, os.path.join(REPO_ROOT, "backend", "services"))
from intent_classifier import HybridIntentClassifier
from token_budget_calculator import TokenBudgetCalculator, UserIntent


async def test_token_budget_integration():
    """Testet Token Budget Calculator"""

    print("=" * 80)
    print("TOKEN BUDGET CALCULATOR - Integration Test")
    print("=" * 80)

    calculator = TokenBudgetCalculator()

    test_cases = [
        {
            "name": "Einfache Frage",
            "query": "Was ist eine Baugenehmigung?",
            "chunk_count": 2,
            "source_types": ["vector"],
            "agent_count": 0,
            "intent": UserIntent.QUICK_ANSWER,
        },
        {
            "name": "Verwaltungsrecht - Komplex",
            "query": """
            Welche verwaltungsrechtlichen Voraussetzungen müssen für einen Bescheid
            zur Baugenehmigung einer Windkraftanlage erfüllt sein? Dabei ist insbesondere
            die Abwägung zwischen Ermessensspielraum der Behörde und Verhältnismäßigkeitsgrundsatz
            zu beachten.
            """,
            "chunk_count": 12,
            "source_types": ["vector", "graph", "relational"],
            "agent_count": 5,
            "intent": UserIntent.RESEARCH,
        },
        {
            "name": "Multi-Aspekt Analyse",
            "query": """
            Analysiere bitte folgende Aspekte:
            1) Rechtliche Rahmenbedingungen
            2) Umweltrechtliche Auflagen
            3) Finanzielle Förderung
            """,
            "chunk_count": 15,
            "source_types": ["vector", "graph", "relational"],
            "agent_count": 7,
            "intent": UserIntent.RESEARCH,
        },
    ]

    for test in test_cases:
        print(f"\n{'─' * 80}")
        print(f"Test: {test['name']}")
        print(f"{'─' * 80}")
        print(f"Query: {test['query'][:70]}...")

        budget, breakdown = calculator.calculate_budget(
            query=test["query"],
            chunk_count=test["chunk_count"],
            source_types=test["source_types"],
            agent_count=test["agent_count"],
            intent=test["intent"],
        )

        print(f"\n💰 Token Budget: {budget} tokens")
        print(f"🎯 Intent: {test['intent'].value}")
        print(f"📊 Complexity: {breakdown['complexity_score']:.1f}/10")
        print(f"📦 Chunks: {breakdown['chunk_count']} (+{breakdown['chunk_bonus']} tokens)")
        print(f"🗃️ Sources: {len(test['source_types'])} (Diversität: {breakdown['source_diversity']:.2f}x)")
        print(f"🤖 Agents: {breakdown['agent_count']} (Faktor: {breakdown['agent_factor']:.2f}x)")
        print(f"⚖️ Intent Weight: {breakdown['intent_weight']:.1f}x")


async def test_intent_classifier_integration():
    """Testet Intent Classifier (nur Rule-Based ohne LLM)"""

    print("\n" + "=" * 80)
    print("INTENT CLASSIFIER - Integration Test (Rule-Based)")
    print("=" * 80)

    classifier = HybridIntentClassifier(llm_threshold=0.7)

    test_queries = [
        "Was ist eine Baugenehmigung?",
        "Wie funktioniert das Genehmigungsverfahren?",
        "Vergleiche die Umweltauflagen für Onshore- und Offshore-Windparks.",
        """Analysiere bitte folgende Aspekte:
        1) Rechtliche Rahmenbedingungen
        2) Umweltrechtliche Auflagen
        3) Finanzielle Förderung""",
        "Welche verwaltungsrechtlichen Voraussetzungen gelten für die Anfechtung eines Bescheids?",
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n{'─' * 80}")
        print(f"Query {i}: {query[:70]}...")

        # Nur Rule-Based (ohne LLM)
        prediction = await classifier.classify_async(query=query, ollama_service=None)  # Kein LLM-Fallback

        print(f"\n🎯 Intent: {prediction.intent.value.upper()}")
        print(f"📊 Confidence: {prediction.confidence:.2%}")
        print(f"🔍 Method: {prediction.method}")
        print(f"💡 Reasoning: {prediction.reasoning}")


async def test_pipeline_simulation():
    """Simuliert Pipeline-Flow mit beiden Services"""

    print("\n" + "=" * 80)
    print("PIPELINE SIMULATION - Full Integration")
    print("=" * 80)

    calculator = TokenBudgetCalculator()
    classifier = HybridIntentClassifier(llm_threshold=0.7)

    query = """
    Welche verwaltungsrechtlichen Voraussetzungen müssen für einen Bescheid
    zur Baugenehmigung einer Windkraftanlage erfüllt sein? Dabei ist insbesondere
    die Abwägung zwischen Ermessensspielraum der Behörde und Verhältnismäßigkeitsgrundsatz
    zu beachten. Welche Rechtsbehelfe stehen bei Anfechtung des Verwaltungsakts zur Verfügung?
    """

    print(f"\nQuery: {query[:100]}...")

    # STEP 0: Intent Classification
    print("\n📍 STEP 0: Intent Classification")
    intent_prediction = await classifier.classify_async(query, ollama_service=None)
    print(f"  → Intent: {intent_prediction.intent.value} (Confidence: {intent_prediction.confidence:.2%})")

    # STEP 1: Initial Token Budget (before RAG)
    print("\n📍 STEP 1: Initial Token Budget")
    budget_v1, breakdown_v1 = calculator.calculate_budget(
        query=query, chunk_count=0, source_types=[], agent_count=0, intent=intent_prediction.intent
    )
    print(f"  → Budget: {budget_v1} tokens (Complexity: {breakdown_v1['complexity_score']:.1f}/10)")

    # STEP 2: Token Budget after RAG (simulate 12 chunks, 3 sources)
    print("\n📍 STEP 2: Token Budget Update (after RAG)")
    chunk_count = 12
    source_types = ["vector", "graph", "relational"]
    budget_v2, breakdown_v2 = calculator.calculate_budget(
        query=query, chunk_count=chunk_count, source_types=source_types, agent_count=0, intent=intent_prediction.intent
    )
    print(f"  → Budget: {budget_v2} tokens (Chunks: {chunk_count}, Sources: {len(source_types)})")
    print(f"  → Delta: +{budget_v2 - budget_v1} tokens")

    # STEP 3: Final Token Budget (after Agent Selection)
    print("\n📍 STEP 3: Final Token Budget (after Agent Selection)")
    agent_count = 5
    budget_v3, breakdown_v3 = calculator.calculate_budget(
        query=query,
        chunk_count=chunk_count,
        source_types=source_types,
        agent_count=agent_count,
        intent=intent_prediction.intent,
    )
    print(f"  → Final Budget: {budget_v3} tokens (Agents: {agent_count})")
    print(f"  → Delta: +{budget_v3 - budget_v2} tokens")

    # Summary
    print("\n" + "─" * 80)
    print("📊 BUDGET PROGRESSION SUMMARY")
    print("─" * 80)
    print(f"  • Initial:             {budget_v1:>5} tokens")
    print(f"  • After RAG:           {budget_v2:>5} tokens (+{budget_v2 - budget_v1})")
    print(f"  • After Agent Select:  {budget_v3:>5} tokens (+{budget_v3 - budget_v2})")
    print(f"  • Total Increase:      {budget_v3 - budget_v1:>5} tokens ({((budget_v3 / budget_v1) - 1) * 100:.1f}%)")

    print("\n📊 FINAL BREAKDOWN")
    print("─" * 80)
    print(f"  • Base:                {breakdown_v3['base_tokens']} tokens")
    print(f"  • Complexity Factor:   {breakdown_v3['complexity_factor']:.2f}x")
    print(f"  • Chunk Bonus:         +{breakdown_v3['chunk_bonus']} tokens")
    print(f"  • Source Diversity:    {breakdown_v3['source_diversity']:.2f}x")
    print(f"  • Agent Factor:        {breakdown_v3['agent_factor']:.2f}x")
    print(f"  • Intent Weight:       {breakdown_v3['intent_weight']:.1f}x")


async def main():
    """Führt alle Tests aus"""

    print("\n" + "=" * 80)
    print("VERITAS TOKEN BUDGET & INTENT CLASSIFIER - INTEGRATION TESTS")
    print("=" * 80)

    await test_token_budget_integration()
    await test_intent_classifier_integration()
    await test_pipeline_simulation()

    print("\n" + "=" * 80)
    print("✅ All Integration Tests Completed!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
