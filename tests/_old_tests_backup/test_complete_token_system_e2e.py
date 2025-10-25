"""
End-to-End Test für das komplette Token-Management-System

Testet die vollständige Integration aller Token-Budget-Komponenten:
1. TokenBudgetCalculator - Initiale Budget-Berechnung
2. HybridIntentClassifier - Intent-Erkennung und Gewichtung
3. ContextWindowManager - Model-Limits und Safety-Checks
4. TokenOverflowHandler - Overflow-Strategien
5. Pipeline Integration - Alle Komponenten zusammen

Test-Szenarien:
- Simple Query: Minimales Budget
- Complex Query: Mittleres Budget mit Multi-Source
- Verwaltungsrecht Query: Maximales Budget mit Domain-Boost
- Overflow Scenario: Context-Window-Limit überschritten
- Multi-Agent Scenario: Agent-Count Scaling
"""

import sys
import os
from typing import Dict, Any, List
from dataclasses import dataclass

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.services.token_budget_calculator import (
    TokenBudgetCalculator,
    QueryComplexityAnalyzer,
    TokenBudgetConfig
)
from backend.services.intent_classifier import (
    HybridIntentClassifier,
    UserIntent,
    IntentPrediction
)
from backend.services.context_window_manager import (
    ContextWindowManager,
    TokenBudgetContext
)
from backend.services.token_overflow_handler import (
    TokenOverflowHandler,
    OverflowStrategy,
    OverflowResult
)


@dataclass
class TestScenario:
    """Test-Szenario mit erwarteten Ergebnissen"""
    name: str
    query: str
    model_name: str
    expected_min_budget: int
    expected_max_budget: int
    expected_intent: UserIntent
    rag_chunks: List[Dict[str, Any]] = None
    agent_count: int = 1
    should_overflow: bool = False


@dataclass
class TestResult:
    """Ergebnis eines Test-Szenarios"""
    scenario_name: str
    success: bool
    initial_budget: int
    after_rag_budget: int
    after_agents_budget: int
    final_budget: int
    intent: UserIntent
    context_window_ok: bool
    overflow_triggered: bool
    overflow_strategy: str = None
    messages: List[str] = None
    
    def __post_init__(self):
        if self.messages is None:
            self.messages = []


class CompleteTokenSystemE2ETest:
    """End-to-End Test für das komplette Token-System"""
    
    def __init__(self):
        """Initialisiere alle Komponenten"""
        self.budget_calculator = TokenBudgetCalculator()
        self.intent_classifier = HybridIntentClassifier()
        self.context_window_manager = ContextWindowManager(safety_factor=0.8)
        self.overflow_handler = TokenOverflowHandler()
        
        print("✅ Alle Token-Management-Komponenten initialisiert")
        print(f"   - TokenBudgetCalculator: Base={self.budget_calculator.config.base_tokens}")
        print(f"   - IntentClassifier: Hybrid (Rule-based + LLM)")
        print(f"   - ContextWindowManager: Safety Factor={self.context_window_manager.safety_factor}")
        print(f"   - OverflowHandler: 4 Strategien verfügbar")
        print()
    
    def simulate_pipeline_flow(self, scenario: TestScenario) -> TestResult:
        """
        Simuliert den kompletten Pipeline-Flow
        
        Flow:
        1. STEP 0: Query → Intent Classification → Initial Budget
        2. STEP 2: +RAG Chunks → Budget Update
        3. STEP 3: +Agent Selection → Final Budget
        4. STEP 5: Context-Window Check → Overflow Handling
        """
        print(f"\n{'='*80}")
        print(f"TEST: {scenario.name}")
        print(f"{'='*80}")
        print(f"Query: '{scenario.query}'")
        print(f"Model: {scenario.model_name}")
        print()
        
        result = TestResult(
            scenario_name=scenario.name,
            success=True,
            initial_budget=0,
            after_rag_budget=0,
            after_agents_budget=0,
            final_budget=0,
            intent=UserIntent.EXPLANATION,
            context_window_ok=True,
            overflow_triggered=False
        )
        
        try:
            # ============================================================
            # STEP 0: Intent Classification + Initial Budget
            # ============================================================
            print("📋 STEP 0: Intent Classification + Initial Budget")
            print("-" * 80)
            
            # Intent erkennen
            intent_prediction = self.intent_classifier.classify_sync(scenario.query)
            result.intent = intent_prediction.intent
            
            print(f"   Intent erkannt: {intent_prediction.intent.value}")
            print(f"   Confidence: {intent_prediction.confidence:.2%}")
            print(f"   Methode: {intent_prediction.method}")
            
            # Initiales Budget berechnen (ohne RAG/Agents)
            initial_budget, initial_breakdown = self.budget_calculator.calculate_budget(
                query=scenario.query,
                chunk_count=0,
                source_types=['vector'],
                agent_count=1,
                intent=intent_prediction.intent
            )
            result.initial_budget = initial_budget
            
            print(f"   Initial Budget: {initial_budget} tokens")
            print()
            
            # ============================================================
            # STEP 2: RAG Chunks → Budget Update
            # ============================================================
            print("📚 STEP 2: RAG Integration → Budget Update")
            print("-" * 80)
            
            # Chunks simulieren wenn vorhanden
            if scenario.rag_chunks:
                chunk_count = len(scenario.rag_chunks)
                source_types = list(set([chunk.get('source_type', 'vector') 
                                        for chunk in scenario.rag_chunks]))
                
                print(f"   RAG Chunks gefunden: {chunk_count}")
                print(f"   Source Types: {', '.join(source_types)}")
                
                # Budget update mit RAG-Daten
                after_rag_budget, rag_breakdown = self.budget_calculator.calculate_budget(
                    query=scenario.query,
                    intent=intent_prediction.intent,
                    chunk_count=chunk_count,
                    source_types=source_types,
                    agent_count=1
                )
                result.after_rag_budget = after_rag_budget
                
                print(f"   Budget nach RAG: {after_rag_budget} tokens")
                print(f"   Erhöhung: +{after_rag_budget - initial_budget} tokens")
            else:
                result.after_rag_budget = initial_budget
                print(f"   Keine RAG Chunks → Budget unverändert: {initial_budget} tokens")
            print()
            
            # ============================================================
            # STEP 3: Agent Selection → Final Budget
            # ============================================================
            print("🤖 STEP 3: Agent Selection → Final Budget")
            print("-" * 80)
            
            print(f"   Ausgewählte Agenten: {scenario.agent_count}")
            
            # Budget update mit Agent-Count
            final_budget, final_breakdown = self.budget_calculator.calculate_budget(
                query=scenario.query,
                intent=intent_prediction.intent,
                chunk_count=len(scenario.rag_chunks) if scenario.rag_chunks else 0,
                source_types=list(set([chunk.get('source_type', 'vector') 
                                      for chunk in scenario.rag_chunks])) if scenario.rag_chunks else ['vector'],
                agent_count=scenario.agent_count
            )
            result.after_agents_budget = final_budget
            
            print(f"   Budget nach Agent-Scaling: {final_budget} tokens")
            print(f"   Erhöhung: +{final_budget - result.after_rag_budget} tokens")
            print()
            
            # ============================================================
            # STEP 5: Context-Window Check + Overflow Handling
            # ============================================================
            print("🔍 STEP 5: Context-Window Check + Overflow Handling")
            print("-" * 80)
            
            # Context für Check vorbereiten
            system_prompt = "Du bist VERITAS, ein KI-Assistent für Verwaltungsrecht."
            user_prompt = scenario.query
            
            # RAG-Kontext vorbereiten
            rag_context = ""
            if scenario.rag_chunks:
                for i, chunk in enumerate(scenario.rag_chunks, 1):
                    rag_context += f"\n[Quelle {i}] {chunk.get('content', 'Mock content')}\n"
            
            # Context-Window Check
            adjusted_tokens, context_check = self.context_window_manager.adjust_token_budget(
                model_name=scenario.model_name,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                rag_context=rag_context,
                requested_tokens=final_budget
            )
            
            # Check ob Budget reduziert wurde
            budget_was_reduced = (adjusted_tokens < final_budget)
            result.context_window_ok = not budget_was_reduced
            
            print(f"   Model: {scenario.model_name}")
            print(f"   Available Output: {context_check.available_output_tokens:,} tokens")
            print(f"   Requested Budget: {final_budget} tokens")
            print(f"   Adjusted Budget: {adjusted_tokens} tokens")
            
            # Overflow-Handling falls nötig
            if budget_was_reduced:
                result.overflow_triggered = True
                result.context_window_ok = False
                
                print(f"\n   ⚠️ OVERFLOW DETECTED!")
                print(f"   Requested: {final_budget} > Available: {context_check.available_output_tokens}")
                print(f"   Adjusted: {adjusted_tokens}")
                
                if context_check.needs_model_upgrade:
                    print(f"   💡 Empfehlung: Model-Upgrade zu {context_check.recommended_models if hasattr(context_check, 'recommended_models') else context_check.recommended_model}")
                
                # Overflow-Strategie anwenden
                overflow_result = self.overflow_handler.handle_overflow(
                    available_tokens=adjusted_tokens,
                    required_tokens=final_budget,
                    rag_chunks=scenario.rag_chunks or [],
                    rag_context=rag_context if isinstance(rag_context, dict) else {"text": rag_context},
                    query=scenario.query,
                    agent_count=scenario.agent_count
                )
                
                result.overflow_strategy = overflow_result.strategy_used.value
                result.final_budget = overflow_result.reduced_tokens
                result.messages.append(overflow_result.user_message)
                
                print(f"\n   ✅ Overflow-Strategie angewendet: {overflow_result.strategy_used.value}")
                print(f"   Reduced Budget: {overflow_result.reduced_tokens} tokens")
                print(f"   Tokens Saved: {overflow_result.tokens_saved} tokens")
                print(f"   Quality Impact: {overflow_result.quality_impact:.0%}")
                print(f"   User Message: {overflow_result.user_message}")
                
            else:
                result.final_budget = adjusted_tokens
                print(f"\n   ✅ Context-Window OK")
                print(f"   Final Budget: {result.final_budget} tokens")
            
            print()
            
            # ============================================================
            # Validierung der Erwartungen
            # ============================================================
            print("🎯 ERWARTUNGS-VALIDIERUNG")
            print("-" * 80)
            
            # Budget-Range Check
            budget_in_range = (scenario.expected_min_budget <= result.final_budget <= scenario.expected_max_budget)
            print(f"   Budget in Range ({scenario.expected_min_budget}-{scenario.expected_max_budget}): {'✅' if budget_in_range else '❌'} ({result.final_budget})")
            
            # Intent Check
            intent_correct = (result.intent == scenario.expected_intent)
            print(f"   Intent korrekt ({scenario.expected_intent.value}): {'✅' if intent_correct else '❌'} ({result.intent.value})")
            
            # Overflow Check
            overflow_as_expected = (result.overflow_triggered == scenario.should_overflow)
            print(f"   Overflow erwartet ({scenario.should_overflow}): {'✅' if overflow_as_expected else '❌'} ({result.overflow_triggered})")
            
            result.success = budget_in_range and intent_correct and overflow_as_expected
            
            print()
            print(f"{'✅ TEST BESTANDEN' if result.success else '❌ TEST FEHLGESCHLAGEN'}")
            
        except Exception as e:
            result.success = False
            result.messages.append(f"Error: {str(e)}")
            print(f"\n❌ ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
        
        return result
    
    def run_all_tests(self) -> Dict[str, TestResult]:
        """Führt alle Test-Szenarien aus"""
        
        # ============================================================
        # Test-Szenarien definieren
        # ============================================================
        scenarios = [
            # Szenario 1: Simple Query
            TestScenario(
                name="Simple Quick-Answer Query",
                query="Was ist ein Bauantrag?",
                model_name="phi3",
                expected_min_budget=250,
                expected_max_budget=500,
                expected_intent=UserIntent.QUICK_ANSWER,
                rag_chunks=[
                    {"content": "Ein Bauantrag ist...", "source_type": "vector", "relevance": 0.9}
                ],
                agent_count=1,
                should_overflow=False
            ),
            
            # Szenario 2: Complex Multi-Domain Query
            TestScenario(
                name="Complex Multi-Domain Analysis",
                query="Analysiere die rechtlichen und finanziellen Auswirkungen der neuen Bauverordnung auf bestehende Genehmigungsverfahren.",
                model_name="llama3.1:8b",
                expected_min_budget=1500,
                expected_max_budget=3000,
                expected_intent=UserIntent.ANALYSIS,
                rag_chunks=[
                    {"content": "Bauverordnung §1...", "source_type": "vector", "relevance": 0.95},
                    {"content": "Genehmigungsverfahren...", "source_type": "graph", "relevance": 0.88},
                    {"content": "Finanzielle Aspekte...", "source_type": "relational", "relevance": 0.82},
                    {"content": "Rechtsprechung...", "source_type": "vector", "relevance": 0.79},
                    {"content": "Verwaltungsvorschriften...", "source_type": "vector", "relevance": 0.75},
                ],
                agent_count=3,
                should_overflow=False
            ),
            
            # Szenario 3: Verwaltungsrecht Maximum Budget
            TestScenario(
                name="Verwaltungsrecht Maximum Budget",
                query="Wie ist das Ermessen der Behörde im Verwaltungsverfahren nach VwVfG zu beurteilen? Analysiere die Rechtsprechung und erläutere die Ermessensfehler.",
                model_name="llama3.1:70b",
                expected_min_budget=3000,
                expected_max_budget=4000,
                expected_intent=UserIntent.ANALYSIS,  # Kann auch RESEARCH sein
                rag_chunks=[
                    {"content": "VwVfG §40 Ermessen...", "source_type": "vector", "relevance": 0.98},
                    {"content": "BVerwG Urteil Ermessensfehler...", "source_type": "graph", "relevance": 0.96},
                    {"content": "Verwaltungsakt Aufhebung...", "source_type": "vector", "relevance": 0.93},
                    {"content": "Ermessensreduzierung...", "source_type": "relational", "relevance": 0.91},
                    {"content": "Intendiertes Ermessen...", "source_type": "vector", "relevance": 0.89},
                    {"content": "Ermessensüberschreitung...", "source_type": "vector", "relevance": 0.87},
                    {"content": "Ermessensfehlgebrauch...", "source_type": "vector", "relevance": 0.85},
                ],
                agent_count=5,
                should_overflow=False
            ),
            
            # Szenario 4: Overflow mit phi3
            TestScenario(
                name="Overflow Scenario (phi3 Context-Window)",
                query="Erstelle eine umfassende Analyse aller Aspekte des Verwaltungsrechts unter Berücksichtigung von Baurecht, Umweltrecht, Planungsrecht und Genehmigungsverfahren.",
                model_name="phi3",  # Nur 4k Context-Window
                expected_min_budget=1000,
                expected_max_budget=3000,  # Wird reduziert durch Overflow-Handling
                expected_intent=UserIntent.RESEARCH,
                rag_chunks=[
                    {"content": "Verwaltungsrecht Grundlagen..." * 50, "source_type": "vector", "relevance": 0.95},
                    {"content": "Baurecht Details..." * 50, "source_type": "graph", "relevance": 0.92},
                    {"content": "Umweltrecht Aspekte..." * 50, "source_type": "relational", "relevance": 0.90},
                    {"content": "Planungsrecht..." * 50, "source_type": "vector", "relevance": 0.88},
                    {"content": "Genehmigungsverfahren..." * 50, "source_type": "vector", "relevance": 0.85},
                    {"content": "Rechtsprechung..." * 50, "source_type": "graph", "relevance": 0.83},
                    {"content": "Verwaltungsvorschriften..." * 50, "source_type": "vector", "relevance": 0.80},
                    {"content": "Weitere Details..." * 50, "source_type": "relational", "relevance": 0.75},
                ],
                agent_count=5,
                should_overflow=True
            ),
            
            # Szenario 5: Multi-Agent Scaling
            TestScenario(
                name="Multi-Agent Scaling (7 Agents)",
                query="Untersuche alle Aspekte: Rechtlich, Finanziell, Umwelt, Verkehr, Sozial, Konstruktion, Zeitplan",
                model_name="llama3.1:70b",
                expected_min_budget=2000,
                expected_max_budget=4000,
                expected_intent=UserIntent.RESEARCH,
                rag_chunks=[
                    {"content": "Rechtliche Analyse...", "source_type": "vector", "relevance": 0.95},
                    {"content": "Finanzielle Bewertung...", "source_type": "relational", "relevance": 0.93},
                    {"content": "Umweltauswirkungen...", "source_type": "vector", "relevance": 0.91},
                    {"content": "Verkehrsplanung...", "source_type": "graph", "relevance": 0.89},
                ],
                agent_count=7,  # Viele Agenten → hoher Scaling-Faktor
                should_overflow=False
            ),
        ]
        
        # ============================================================
        # Tests ausführen
        # ============================================================
        results = {}
        
        for scenario in scenarios:
            result = self.simulate_pipeline_flow(scenario)
            results[scenario.name] = result
        
        # ============================================================
        # Zusammenfassung
        # ============================================================
        print("\n" + "="*80)
        print("TEST-ZUSAMMENFASSUNG")
        print("="*80)
        
        total_tests = len(results)
        passed_tests = sum(1 for r in results.values() if r.success)
        
        print(f"\nGesamt: {passed_tests}/{total_tests} Tests bestanden")
        print()
        
        for name, result in results.items():
            status = "✅ PASS" if result.success else "❌ FAIL"
            print(f"{status} - {name}")
            print(f"         Initial: {result.initial_budget} → RAG: {result.after_rag_budget} → Agents: {result.after_agents_budget} → Final: {result.final_budget}")
            print(f"         Intent: {result.intent.value} | Overflow: {result.overflow_triggered}")
            if result.overflow_strategy:
                print(f"         Strategy: {result.overflow_strategy}")
            print()
        
        if passed_tests == total_tests:
            print("🎉 ALLE TESTS BESTANDEN! System ist production-ready.")
        else:
            print(f"⚠️ {total_tests - passed_tests} Tests fehlgeschlagen. Bitte überprüfen.")
        
        return results


def main():
    """Hauptfunktion"""
    print("\n" + "="*80)
    print("VERITAS TOKEN-MANAGEMENT-SYSTEM - END-TO-END TEST")
    print("="*80)
    print()
    print("Testet die vollständige Integration aller 9 Komponenten:")
    print("  1. TokenBudgetCalculator - Dynamische Budget-Berechnung")
    print("  2. QueryComplexityAnalyzer - Komplexitäts-Scoring")
    print("  3. HybridIntentClassifier - Intent-Erkennung")
    print("  4. ContextWindowManager - Model-Limit-Checks")
    print("  5. TokenOverflowHandler - Overflow-Strategien")
    print("  6. Domain Weighting - Verwaltungsrecht Priorisierung")
    print("  7. Multi-Source Boost - Source-Diversität")
    print("  8. Agent-Count Scaling - Agent-basierte Anpassung")
    print("  9. Progressive Updates - 3-Stage Budget-Flow")
    print()
    
    # Test ausführen
    tester = CompleteTokenSystemE2ETest()
    results = tester.run_all_tests()
    
    # Exit-Code setzen
    all_passed = all(r.success for r in results.values())
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
