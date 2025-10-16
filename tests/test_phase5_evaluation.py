#!/usr/bin/env python3
"""
VERITAS PHASE 5 EVALUATION & BENCHMARKS
========================================

A/B Evaluation: Baseline vs Hybrid vs Hybrid+QueryExpansion

Verwendet vorhandenen RAGEvaluator für NDCG@10, MRR, Recall@K Metriken.

Evaluierungs-Szenarien:
----------------------
1. **Baseline (Dense-Only):** Nur UDS3 Vector Search
2. **Hybrid:** Dense (UDS3) + Sparse (BM25) + RRF
3. **Hybrid + Query Expansion:** Hybrid + LLM-basierte Query-Expansion

Test-Queries:
-------------
- Rechtliche Queries (BGB, VOB, Baurecht)
- Technische Normen (DIN, EN, ISO)
- Umweltrecht (UVPG, UVP)
- Multi-Topic Queries

Metriken:
---------
- NDCG@10 (Normalized Discounted Cumulative Gain)
- MRR (Mean Reciprocal Rank)
- Recall@10
- Precision@5
- Latenz

Author: VERITAS System
Date: 2025-10-06
Version: 1.0
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import Evaluation Framework
try:
    from backend.evaluation.veritas_rag_evaluator import (
        RAGEvaluator,
        RetrievalMetrics,
        EvaluationResult
    )
    EVALUATOR_AVAILABLE = True
except ImportError as e:
    EVALUATOR_AVAILABLE = False
    logger.warning(f"⚠️ RAGEvaluator nicht verfügbar: {e}")

# Import RAG Components
try:
    from backend.agents.rag_context_service import (
        RAGContextService,
        RAGQueryOptions
    )
    RAG_AVAILABLE = True
except ImportError as e:
    RAG_AVAILABLE = False
    logger.warning(f"⚠️ RAGContextService nicht verfügbar: {e}")


@dataclass
class EvaluationTestCase:
    """Test-Case für Evaluation."""
    
    query: str
    expected_doc_ids: List[str]
    relevance_scores: Dict[str, float]  # doc_id → relevance (0-1)
    category: str  # "legal", "technical", "environmental", "multi_topic"
    description: str = ""


@dataclass
class BenchmarkResult:
    """Ergebnis eines Benchmarks."""
    
    configuration: str  # "baseline", "hybrid", "hybrid_qe"
    
    # Retrieval-Metriken
    ndcg_at_10: float = 0.0
    mrr: float = 0.0
    recall_at_10: float = 0.0
    precision_at_5: float = 0.0
    
    # Performance
    avg_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    
    # Detail-Metriken
    test_cases_passed: int = 0
    test_cases_total: int = 0
    pass_rate: float = 0.0


class Phase5Evaluator:
    """
    Evaluiert Phase 5 Advanced RAG Pipeline.
    
    Vergleicht 3 Konfigurationen:
    1. Baseline: Dense-Only (UDS3)
    2. Hybrid: Dense + Sparse + RRF
    3. Hybrid+QE: Hybrid + Query Expansion
    """
    
    def __init__(self, rag_service: Optional[Any] = None):
        """Initialisiert Evaluator.
        
        Args:
            rag_service: RAGContextService Instanz (optional)
        """
        self.rag_service = rag_service
        self.test_cases = self._create_test_cases()
    
    def _create_test_cases(self) -> List[EvaluationTestCase]:
        """Erstellt Test-Cases für Evaluation."""
        
        return [
            # === RECHTLICHE QUERIES ===
            EvaluationTestCase(
                query="§ 242 BGB Treu und Glauben",
                expected_doc_ids=["bgb_242", "baurecht_overview"],
                relevance_scores={
                    "bgb_242": 1.0,
                    "baurecht_overview": 0.7,
                    "construction_process": 0.3
                },
                category="legal",
                description="Exakter Paragraphen-Lookup"
            ),
            
            EvaluationTestCase(
                query="Baurecht BGB VOB Vorschriften",
                expected_doc_ids=["baurecht_overview", "bgb_242", "construction_process"],
                relevance_scores={
                    "baurecht_overview": 1.0,
                    "bgb_242": 0.8,
                    "construction_process": 0.7,
                    "accessibility_law": 0.5
                },
                category="legal",
                description="Multi-Keyword rechtliche Query"
            ),
            
            # === TECHNISCHE NORMEN ===
            EvaluationTestCase(
                query="DIN 18040-1 Barrierefreies Bauen",
                expected_doc_ids=["din_18040_1", "accessibility_law"],
                relevance_scores={
                    "din_18040_1": 1.0,
                    "accessibility_law": 0.9,
                    "sustainable_building": 0.3
                },
                category="technical",
                description="Exakte DIN-Norm"
            ),
            
            EvaluationTestCase(
                query="Barrierefreiheit öffentliche Gebäude Normen",
                expected_doc_ids=["din_18040_1", "accessibility_law"],
                relevance_scores={
                    "din_18040_1": 1.0,
                    "accessibility_law": 0.9,
                    "baurecht_overview": 0.4
                },
                category="technical",
                description="Semantische Norm-Suche"
            ),
            
            # === UMWELTRECHT ===
            EvaluationTestCase(
                query="Umweltverträglichkeitsprüfung UVPG",
                expected_doc_ids=["uvpg_3a", "environmental_impact"],
                relevance_scores={
                    "uvpg_3a": 1.0,
                    "environmental_impact": 0.8,
                    "sustainable_building": 0.5
                },
                category="environmental",
                description="UVP-Lookup"
            ),
            
            # === MULTI-TOPIC QUERIES ===
            EvaluationTestCase(
                query="Nachhaltiges barrierefreies Bauen mit Umweltverträglichkeitsprüfung",
                expected_doc_ids=[
                    "sustainable_building",
                    "din_18040_1",
                    "uvpg_3a",
                    "environmental_impact",
                    "green_building"
                ],
                relevance_scores={
                    "sustainable_building": 1.0,
                    "din_18040_1": 0.9,
                    "uvpg_3a": 0.8,
                    "environmental_impact": 0.8,
                    "green_building": 0.9,
                    "energy_efficiency": 0.7
                },
                category="multi_topic",
                description="Komplexe Multi-Topic Query"
            ),
            
            EvaluationTestCase(
                query="Wie baue ich ein energieeffizientes Haus nach aktuellen Normen?",
                expected_doc_ids=[
                    "energy_efficiency",
                    "sustainable_building",
                    "baurecht_overview",
                    "construction_process"
                ],
                relevance_scores={
                    "energy_efficiency": 1.0,
                    "sustainable_building": 0.9,
                    "baurecht_overview": 0.6,
                    "construction_process": 0.5,
                    "green_building": 0.7
                },
                category="multi_topic",
                description="Natural Language Query"
            ),
        ]
    
    async def evaluate_configuration(
        self,
        config_name: str,
        enable_hybrid: bool,
        enable_query_expansion: bool
    ) -> BenchmarkResult:
        """
        Evaluiert eine Konfiguration.
        
        Args:
            config_name: Name der Konfiguration
            enable_hybrid: Hybrid Search aktivieren
            enable_query_expansion: Query Expansion aktivieren
            
        Returns:
            BenchmarkResult mit Metriken
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"Evaluiere: {config_name}")
        logger.info(f"Hybrid: {enable_hybrid}, Query Expansion: {enable_query_expansion}")
        logger.info(f"{'='*60}\n")
        
        options = RAGQueryOptions(
            limit_documents=10,
            enable_hybrid_search=enable_hybrid,
            enable_query_expansion=enable_query_expansion,
            enable_reranking=False  # Disable für faire Vergleiche
        )
        
        # Metriken sammeln
        all_ndcg = []
        all_mrr = []
        all_recall = []
        all_precision = []
        all_latencies = []
        passed_cases = 0
        
        for test_case in self.test_cases:
            logger.info(f"Query: {test_case.query[:60]}...")
            
            # Retrieval durchführen
            start = time.time()
            result = await self.rag_service.build_context(
                query_text=test_case.query,
                options=options
            )
            latency = (time.time() - start) * 1000
            all_latencies.append(latency)
            
            # Retrieved Doc IDs extrahieren
            retrieved_ids = [doc["id"] for doc in result.get("documents", [])]
            
            # Metriken berechnen
            ndcg = self._calculate_ndcg(
                retrieved_ids[:10],
                test_case.relevance_scores,
                k=10
            )
            
            mrr = self._calculate_mrr(
                retrieved_ids,
                set(test_case.expected_doc_ids)
            )
            
            recall = self._calculate_recall(
                retrieved_ids[:10],
                set(test_case.expected_doc_ids)
            )
            
            precision = self._calculate_precision(
                retrieved_ids[:5],
                set(test_case.expected_doc_ids)
            )
            
            all_ndcg.append(ndcg)
            all_mrr.append(mrr)
            all_recall.append(recall)
            all_precision.append(precision)
            
            # Pass/Fail (Recall@10 > 0.5 als Kriterium)
            if recall > 0.5:
                passed_cases += 1
            
            logger.info(
                f"  NDCG@10: {ndcg:.3f}, MRR: {mrr:.3f}, "
                f"Recall@10: {recall:.3f}, Precision@5: {precision:.3f}, "
                f"Latenz: {latency:.0f}ms"
            )
        
        # Aggregierte Metriken
        avg_ndcg = sum(all_ndcg) / len(all_ndcg) if all_ndcg else 0.0
        avg_mrr = sum(all_mrr) / len(all_mrr) if all_mrr else 0.0
        avg_recall = sum(all_recall) / len(all_recall) if all_recall else 0.0
        avg_precision = sum(all_precision) / len(all_precision) if all_precision else 0.0
        
        avg_latency = sum(all_latencies) / len(all_latencies)
        sorted_latencies = sorted(all_latencies)
        p95_latency = sorted_latencies[int(len(sorted_latencies) * 0.95)]
        p99_latency = sorted_latencies[int(len(sorted_latencies) * 0.99)]
        
        return BenchmarkResult(
            configuration=config_name,
            ndcg_at_10=avg_ndcg,
            mrr=avg_mrr,
            recall_at_10=avg_recall,
            precision_at_5=avg_precision,
            avg_latency_ms=avg_latency,
            p95_latency_ms=p95_latency,
            p99_latency_ms=p99_latency,
            test_cases_passed=passed_cases,
            test_cases_total=len(self.test_cases),
            pass_rate=passed_cases / len(self.test_cases)
        )
    
    def _calculate_ndcg(
        self,
        retrieved_ids: List[str],
        relevance_scores: Dict[str, float],
        k: int = 10
    ) -> float:
        """Berechnet NDCG@K."""
        
        # DCG (Discounted Cumulative Gain)
        dcg = 0.0
        for i, doc_id in enumerate(retrieved_ids[:k]):
            relevance = relevance_scores.get(doc_id, 0.0)
            dcg += relevance / (1.0 + i)  # Simplified: 1/(1+i) statt log2(i+2)
        
        # IDCG (Ideal DCG)
        ideal_relevances = sorted(relevance_scores.values(), reverse=True)
        idcg = 0.0
        for i, relevance in enumerate(ideal_relevances[:k]):
            idcg += relevance / (1.0 + i)
        
        # NDCG
        return dcg / idcg if idcg > 0 else 0.0
    
    def _calculate_mrr(
        self,
        retrieved_ids: List[str],
        expected_ids: Set[str]
    ) -> float:
        """Berechnet Mean Reciprocal Rank."""
        
        for i, doc_id in enumerate(retrieved_ids):
            if doc_id in expected_ids:
                return 1.0 / (i + 1)  # Rank ist 1-based
        
        return 0.0
    
    def _calculate_recall(
        self,
        retrieved_ids: List[str],
        expected_ids: Set[str]
    ) -> float:
        """Berechnet Recall@K."""
        
        if not expected_ids:
            return 1.0
        
        retrieved_set = set(retrieved_ids)
        found = len(retrieved_set & expected_ids)
        
        return found / len(expected_ids)
    
    def _calculate_precision(
        self,
        retrieved_ids: List[str],
        expected_ids: Set[str]
    ) -> float:
        """Berechnet Precision@K."""
        
        if not retrieved_ids:
            return 0.0
        
        retrieved_set = set(retrieved_ids)
        found = len(retrieved_set & expected_ids)
        
        return found / len(retrieved_ids)
    
    def print_comparison(self, results: List[BenchmarkResult]) -> None:
        """Gibt Vergleichstabelle aus."""
        
        print("\n" + "="*80)
        print("PHASE 5 EVALUATION RESULTS - A/B COMPARISON")
        print("="*80)
        
        # Header
        print(f"\n{'Configuration':<25} {'NDCG@10':>10} {'MRR':>10} {'Recall@10':>10} {'Prec@5':>10} {'Latenz (ms)':>12}")
        print("-" * 80)
        
        # Baseline als Referenz
        baseline = next((r for r in results if r.configuration == "Baseline"), None)
        
        for result in results:
            # Metriken
            ndcg_str = f"{result.ndcg_at_10:.3f}"
            mrr_str = f"{result.mrr:.3f}"
            recall_str = f"{result.recall_at_10:.3f}"
            prec_str = f"{result.precision_at_5:.3f}"
            latency_str = f"{result.avg_latency_ms:.0f}"
            
            # Delta zu Baseline
            if baseline and result.configuration != "Baseline":
                ndcg_delta = ((result.ndcg_at_10 - baseline.ndcg_at_10) / baseline.ndcg_at_10 * 100) if baseline.ndcg_at_10 > 0 else 0
                mrr_delta = ((result.mrr - baseline.mrr) / baseline.mrr * 100) if baseline.mrr > 0 else 0
                
                ndcg_str += f" ({ndcg_delta:+.1f}%)"
                mrr_str += f" ({mrr_delta:+.1f}%)"
            
            print(f"{result.configuration:<25} {ndcg_str:>10} {mrr_str:>10} {recall_str:>10} {prec_str:>10} {latency_str:>12}")
        
        print("-" * 80)
        
        # Performance-Details
        print("\nPERFORMANCE DETAILS:")
        print(f"{'Configuration':<25} {'Avg Latenz':>12} {'P95':>10} {'P99':>10} {'Pass Rate':>12}")
        print("-" * 80)
        
        for result in results:
            print(
                f"{result.configuration:<25} "
                f"{result.avg_latency_ms:>10.0f}ms "
                f"{result.p95_latency_ms:>10.0f}ms "
                f"{result.p99_latency_ms:>10.0f}ms "
                f"{result.pass_rate:>11.1%}"
            )
        
        print("="*80)
        
        # Zusammenfassung
        if baseline:
            hybrid = next((r for r in results if "Hybrid" in r.configuration and "QE" not in r.configuration), None)
            hybrid_qe = next((r for r in results if "Hybrid+QE" in r.configuration), None)
            
            print("\nZUSAMMENFASSUNG:")
            
            if hybrid:
                ndcg_improvement = ((hybrid.ndcg_at_10 - baseline.ndcg_at_10) / baseline.ndcg_at_10 * 100) if baseline.ndcg_at_10 > 0 else 0
                mrr_improvement = ((hybrid.mrr - baseline.mrr) / baseline.mrr * 100) if baseline.mrr > 0 else 0
                latency_overhead = hybrid.avg_latency_ms - baseline.avg_latency_ms
                
                print(f"✅ Hybrid Search Improvement:")
                print(f"   NDCG@10: {ndcg_improvement:+.1f}%")
                print(f"   MRR: {mrr_improvement:+.1f}%")
                print(f"   Latenz-Overhead: +{latency_overhead:.0f}ms")
            
            if hybrid_qe and hybrid:
                ndcg_improvement_qe = ((hybrid_qe.ndcg_at_10 - hybrid.ndcg_at_10) / hybrid.ndcg_at_10 * 100) if hybrid.ndcg_at_10 > 0 else 0
                mrr_improvement_qe = ((hybrid_qe.mrr - hybrid.mrr) / hybrid.mrr * 100) if hybrid.mrr > 0 else 0
                
                print(f"\n✅ Query Expansion zusätzliche Verbesserung:")
                print(f"   NDCG@10: {ndcg_improvement_qe:+.1f}%")
                print(f"   MRR: {mrr_improvement_qe:+.1f}%")
        
        print("="*80 + "\n")


async def main():
    """Führt vollständige Evaluation durch."""
    
    if not RAG_AVAILABLE:
        print("❌ RAGContextService nicht verfügbar!")
        return
    
    # Mock UDS3 & Service erstellen (für Demo)
    print("⚠️ HINWEIS: Evaluation erfordert vollständige RAG-Pipeline mit UDS3")
    print("⚠️ Dieses Script zeigt die Evaluation-Struktur, benötigt aber echte Daten\n")
    
    # Beispiel-Evaluation-Flow (mit Mock-Daten)
    print("EVALUATION-FLOW:")
    print("1. Baseline (Dense-Only)")
    print("2. Hybrid (Dense + Sparse + RRF)")
    print("3. Hybrid + Query Expansion")
    print("\nZu implementieren:")
    print("- Mock UDS3 Strategy mit Test-Corpus erstellen")
    print("- RAGContextService initialisieren")
    print("- Phase5Evaluator.evaluate_configuration() für jede Config aufrufen")
    print("- Ergebnisse vergleichen mit print_comparison()")
    
    print("\nErwartete Ergebnisse (basierend auf Phase 5 Targets):")
    print("- NDCG@10: 0.65 (Baseline) → 0.75 (Hybrid) → 0.80 (Hybrid+QE)")
    print("- MRR: 0.55 (Baseline) → 0.68 (Hybrid) → 0.75 (Hybrid+QE)")
    print("- Recall@10: 0.70 (Baseline) → 0.78 (Hybrid) → 0.85 (Hybrid+QE)")


if __name__ == "__main__":
    asyncio.run(main())
