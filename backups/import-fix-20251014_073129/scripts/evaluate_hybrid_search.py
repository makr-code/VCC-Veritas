"""
Phase 5 Hybrid Search Evaluation
A/B-Vergleich: BM25-only vs Hybrid (Dense + Sparse + RRF)
"""
import asyncio
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Tuple
import statistics

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tests.ground_truth_dataset import GROUND_TRUTH_DATASET, GroundTruthQuery


# =============================================================================
# EVALUATION METRICS
# =============================================================================

def calculate_dcg(results: List[Dict], relevance_scores: Dict[str, float], k: int = 10) -> float:
    """
    Calculate Discounted Cumulative Gain (DCG)
    
    DCG@k = Σ(i=1 to k) (2^relevance_i - 1) / log2(i + 1)
    """
    dcg = 0.0
    for i, result in enumerate(results[:k], 1):
        doc_id = result.get('doc_id', '')
        relevance = relevance_scores.get(doc_id, 0.0)
        dcg += (2 ** relevance - 1) / (i + 1).bit_length()  # log2(i+1)
    return dcg


def calculate_idcg(relevance_scores: Dict[str, float], k: int = 10) -> float:
    """
    Calculate Ideal DCG (perfect ranking)
    """
    sorted_scores = sorted(relevance_scores.values(), reverse=True)[:k]
    idcg = 0.0
    for i, relevance in enumerate(sorted_scores, 1):
        idcg += (2 ** relevance - 1) / (i + 1).bit_length()
    return idcg


def calculate_ndcg(results: List[Dict], relevance_scores: Dict[str, float], k: int = 10) -> float:
    """
    Calculate Normalized DCG (NDCG)
    
    NDCG@k = DCG@k / IDCG@k
    """
    dcg = calculate_dcg(results, relevance_scores, k)
    idcg = calculate_idcg(relevance_scores, k)
    return dcg / idcg if idcg > 0 else 0.0


def calculate_mrr(results: List[Dict], relevant_doc_ids: List[str]) -> float:
    """
    Calculate Mean Reciprocal Rank (MRR)
    
    MRR = 1 / rank_of_first_relevant_doc
    """
    for i, result in enumerate(results, 1):
        doc_id = result.get('doc_id', '')
        if doc_id in relevant_doc_ids:
            return 1.0 / i
    return 0.0


def calculate_recall_at_k(results: List[Dict], relevant_doc_ids: List[str], k: int = 10) -> float:
    """
    Calculate Recall@k
    
    Recall@k = (# relevant docs in top-k) / (# total relevant docs)
    """
    if not relevant_doc_ids:
        return 0.0
    
    retrieved_relevant = sum(
        1 for result in results[:k]
        if result.get('doc_id', '') in relevant_doc_ids
    )
    return retrieved_relevant / len(relevant_doc_ids)


def calculate_precision_at_k(results: List[Dict], relevant_doc_ids: List[str], k: int = 5) -> float:
    """
    Calculate Precision@k
    
    Precision@k = (# relevant docs in top-k) / k
    """
    if k == 0:
        return 0.0
    
    retrieved_relevant = sum(
        1 for result in results[:k]
        if result.get('doc_id', '') in relevant_doc_ids
    )
    return retrieved_relevant / k


def is_top1_correct(results: List[Dict], expected_top1: str) -> bool:
    """Check if Top-1 result is correct"""
    if not results:
        return False
    return results[0].get('doc_id', '') == expected_top1


# =============================================================================
# EVALUATION RUNNER
# =============================================================================

class EvaluationRunner:
    """Runs evaluation for a retriever"""
    
    def __init__(self, retriever, name: str):
        self.retriever = retriever
        self.name = name
        self.results = []
    
    async def evaluate_query(self, query: GroundTruthQuery, k: int = 10) -> Dict[str, Any]:
        """Evaluate a single query"""
        start = time.time()
        
        # Retrieve results
        results = await self.retriever.retrieve(query.query_text, top_k=k)
        
        latency_ms = (time.time() - start) * 1000
        
        # Convert to dict format
        results_dicts = [
            {'doc_id': r.doc_id, 'score': r.score, 'content': r.content}
            for r in results
        ]
        
        # Calculate metrics
        relevance_scores = query.get_dcg_weights()
        relevant_doc_ids = [doc.doc_id for doc in query.relevant_docs]
        
        metrics = {
            'query_id': query.query_id,
            'query_text': query.query_text,
            'category': query.category.value,
            'ndcg@10': calculate_ndcg(results_dicts, relevance_scores, k=10),
            'ndcg@5': calculate_ndcg(results_dicts, relevance_scores, k=5),
            'mrr': calculate_mrr(results_dicts, relevant_doc_ids),
            'recall@10': calculate_recall_at_k(results_dicts, relevant_doc_ids, k=10),
            'recall@5': calculate_recall_at_k(results_dicts, relevant_doc_ids, k=5),
            'precision@5': calculate_precision_at_k(results_dicts, relevant_doc_ids, k=5),
            'top1_correct': is_top1_correct(results_dicts, query.expected_top1),
            'latency_ms': latency_ms,
            'num_results': len(results),
        }
        
        return metrics
    
    async def evaluate_all(self, queries: List[GroundTruthQuery] = None) -> Dict[str, Any]:
        """Evaluate all queries in dataset"""
        if queries is None:
            queries = GROUND_TRUTH_DATASET
        
        print(f"\n{'=' * 80}")
        print(f"EVALUATING: {self.name}")
        print(f"{'=' * 80}\n")
        
        all_metrics = []
        
        for i, query in enumerate(queries, 1):
            print(f"[{i}/{len(queries)}] {query.query_text[:60]}...", end=" ", flush=True)
            
            try:
                metrics = await self.evaluate_query(query)
                all_metrics.append(metrics)
                print(f"✅ NDCG@10: {metrics['ndcg@10']:.3f}, Latency: {metrics['latency_ms']:.0f}ms")
            
            except Exception as e:
                print(f"❌ Error: {e}")
                all_metrics.append({
                    'query_id': query.query_id,
                    'query_text': query.query_text,
                    'category': query.category.value,
                    'error': str(e),
                    'ndcg@10': 0.0,
                    'mrr': 0.0,
                    'latency_ms': 0.0,
                })
        
        # Aggregate metrics
        aggregated = self._aggregate_metrics(all_metrics)
        
        self.results = all_metrics
        return aggregated
    
    def _aggregate_metrics(self, all_metrics: List[Dict]) -> Dict[str, Any]:
        """Aggregate metrics across all queries"""
        
        # Filter out errors
        valid_metrics = [m for m in all_metrics if 'error' not in m]
        
        if not valid_metrics:
            return {'error': 'No valid results'}
        
        aggregated = {
            'total_queries': len(all_metrics),
            'successful_queries': len(valid_metrics),
            'failed_queries': len(all_metrics) - len(valid_metrics),
            
            # Mean metrics
            'ndcg@10_mean': statistics.mean(m['ndcg@10'] for m in valid_metrics),
            'ndcg@5_mean': statistics.mean(m['ndcg@5'] for m in valid_metrics),
            'mrr_mean': statistics.mean(m['mrr'] for m in valid_metrics),
            'recall@10_mean': statistics.mean(m['recall@10'] for m in valid_metrics),
            'recall@5_mean': statistics.mean(m['recall@5'] for m in valid_metrics),
            'precision@5_mean': statistics.mean(m['precision@5'] for m in valid_metrics),
            
            # Top-1 accuracy
            'top1_accuracy': sum(m['top1_correct'] for m in valid_metrics) / len(valid_metrics),
            
            # Latency
            'latency_mean': statistics.mean(m['latency_ms'] for m in valid_metrics),
            'latency_p50': statistics.median(m['latency_ms'] for m in valid_metrics),
            'latency_p95': sorted(m['latency_ms'] for m in valid_metrics)[int(len(valid_metrics) * 0.95)] if len(valid_metrics) > 20 else max(m['latency_ms'] for m in valid_metrics),
        }
        
        # By category
        categories = set(m['category'] for m in valid_metrics)
        aggregated['by_category'] = {}
        
        for category in categories:
            cat_metrics = [m for m in valid_metrics if m['category'] == category]
            aggregated['by_category'][category] = {
                'count': len(cat_metrics),
                'ndcg@10': statistics.mean(m['ndcg@10'] for m in cat_metrics),
                'mrr': statistics.mean(m['mrr'] for m in cat_metrics),
            }
        
        return aggregated


# =============================================================================
# COMPARISON
# =============================================================================

def compare_results(baseline: Dict, hybrid: Dict):
    """Compare baseline vs hybrid results"""
    print(f"\n{'=' * 80}")
    print("A/B COMPARISON: BASELINE VS HYBRID")
    print(f"{'=' * 80}\n")
    
    # Overall comparison
    print("📊 Overall Metrics:")
    print(f"{'Metric':<25} {'Baseline':>12} {'Hybrid':>12} {'Improvement':>15}")
    print("-" * 80)
    
    metrics_to_compare = [
        ('NDCG@10', 'ndcg@10_mean'),
        ('NDCG@5', 'ndcg@5_mean'),
        ('MRR', 'mrr_mean'),
        ('Recall@10', 'recall@10_mean'),
        ('Recall@5', 'recall@5_mean'),
        ('Precision@5', 'precision@5_mean'),
        ('Top-1 Accuracy', 'top1_accuracy'),
    ]
    
    for label, key in metrics_to_compare:
        baseline_val = baseline.get(key, 0.0)
        hybrid_val = hybrid.get(key, 0.0)
        
        if baseline_val > 0:
            improvement = ((hybrid_val - baseline_val) / baseline_val) * 100
            improvement_str = f"+{improvement:.1f}%" if improvement > 0 else f"{improvement:.1f}%"
        else:
            improvement_str = "N/A"
        
        print(f"{label:<25} {baseline_val:>12.3f} {hybrid_val:>12.3f} {improvement_str:>15}")
    
    print()
    print("⏱️ Latency:")
    print(f"{'Metric':<25} {'Baseline':>12} {'Hybrid':>12} {'Change':>15}")
    print("-" * 80)
    
    latency_metrics = [
        ('Mean Latency (ms)', 'latency_mean'),
        ('P50 Latency (ms)', 'latency_p50'),
        ('P95 Latency (ms)', 'latency_p95'),
    ]
    
    for label, key in latency_metrics:
        baseline_val = baseline.get(key, 0.0)
        hybrid_val = hybrid.get(key, 0.0)
        change = hybrid_val - baseline_val
        change_str = f"+{change:.0f}ms" if change > 0 else f"{change:.0f}ms"
        
        print(f"{label:<25} {baseline_val:>12.0f} {hybrid_val:>12.0f} {change_str:>15}")
    
    # By category
    print()
    print("📂 Performance by Category:")
    print(f"{'Category':<20} {'Baseline NDCG':>15} {'Hybrid NDCG':>15} {'Improvement':>15}")
    print("-" * 80)
    
    all_categories = set(
        list(baseline.get('by_category', {}).keys()) +
        list(hybrid.get('by_category', {}).keys())
    )
    
    for category in sorted(all_categories):
        baseline_cat = baseline.get('by_category', {}).get(category, {})
        hybrid_cat = hybrid.get('by_category', {}).get(category, {})
        
        baseline_ndcg = baseline_cat.get('ndcg@10', 0.0)
        hybrid_ndcg = hybrid_cat.get('ndcg@10', 0.0)
        
        if baseline_ndcg > 0:
            improvement = ((hybrid_ndcg - baseline_ndcg) / baseline_ndcg) * 100
            improvement_str = f"+{improvement:.1f}%"
        else:
            improvement_str = "N/A"
        
        print(f"{category:<20} {baseline_ndcg:>15.3f} {hybrid_ndcg:>15.3f} {improvement_str:>15}")
    
    print()
    print("=" * 80)
    
    # Summary
    if 'error' in baseline or 'error' in hybrid:
        print("\n⚠️ EVALUATION INCOMPLETE - Errors occurred")
        print()
        return
    
    baseline_ndcg = baseline.get('ndcg@10_mean', 0.0)
    hybrid_ndcg = hybrid.get('ndcg@10_mean', 0.0)
    
    if baseline_ndcg > 0:
        overall_improvement = ((hybrid_ndcg - baseline_ndcg) / baseline_ndcg) * 100
        
        if overall_improvement >= 15:
            status = "🟢 TARGET MET"
        elif overall_improvement >= 10:
            status = "🟡 CLOSE TO TARGET"
        else:
            status = "🔴 BELOW TARGET"
        
        print(f"\n{status}")
        print(f"Overall NDCG@10 Improvement: {overall_improvement:+.1f}%")
        print(f"Target: +15-25%")
    else:
        print("\n⚠️ Baseline NDCG is 0.0 - Cannot calculate improvement")
        print(f"Baseline NDCG: {baseline_ndcg:.3f}")
        print(f"Hybrid NDCG: {hybrid_ndcg:.3f}")
    print()


# =============================================================================
# MAIN
# =============================================================================

async def run_evaluation():
    """Run full evaluation"""
    print("\n" + "=" * 80)
    print("PHASE 5 HYBRID SEARCH EVALUATION")
    print("=" * 80)
    
    # Import retrievers
    from backend.agents.veritas_uds3_adapter import get_uds3_adapter
    from backend.agents.veritas_hybrid_retrieval import HybridRetriever
    from backend.agents.veritas_sparse_retrieval import SparseRetriever
    
    # Load demo corpus
    demo_corpus = [
        {"doc_id": "bgb_110", "content": "§ 110 BGB Taschengeldparagraph - Bewirken der Leistung mit eigenen Mitteln. Ein von dem Minderjährigen ohne Zustimmung des gesetzlichen Vertreters geschlossener Vertrag gilt als von Anfang an wirksam, wenn der Minderjährige die vertragsmäßige Leistung mit Mitteln bewirkt, die ihm zu diesem Zweck oder zu freier Verfügung von dem Vertreter oder mit dessen Zustimmung von einem Dritten überlassen worden sind."},
        {"doc_id": "bgb_433", "content": "§ 433 BGB Vertragstypische Pflichten beim Kaufvertrag. (1) Durch den Kaufvertrag wird der Verkäufer einer Sache verpflichtet, dem Käufer die Sache zu übergeben und das Eigentum an der Sache zu verschaffen. Der Verkäufer hat dem Käufer die Sache frei von Sach- und Rechtsmängeln zu verschaffen. (2) Der Käufer ist verpflichtet, dem Verkäufer den vereinbarten Kaufpreis zu zahlen und die gekaufte Sache abzunehmen."},
        {"doc_id": "vwvfg_35", "content": "§ 35 VwVfG Begriff des Verwaltungsaktes. Verwaltungsakt ist jede Verfügung, Entscheidung oder andere hoheitliche Maßnahme, die eine Behörde zur Regelung eines Einzelfalls auf dem Gebiet des öffentlichen Rechts trifft und die auf unmittelbare Rechtswirkung nach außen gerichtet ist."},
    ]
    
    print(f"\nℹ️ Using {len(demo_corpus)} demo documents (subset of full corpus)")
    print(f"ℹ️ Evaluating {len(GROUND_TRUTH_DATASET)} queries")
    print()
    
    # Setup Baseline: BM25-only
    print("🔧 Setting up BASELINE (BM25-only)...")
    baseline_bm25 = SparseRetriever()
    baseline_bm25.index_documents(demo_corpus)
    
    # BM25 already has async retrieve() method, use directly
    baseline = baseline_bm25
    
    # Setup Hybrid: Dense (UDS3 Adapter) + Sparse (BM25) + RRF
    print("🔧 Setting up HYBRID (UDS3 Adapter + BM25 + RRF)...")
    uds3_adapter = get_uds3_adapter()
    hybrid_bm25 = SparseRetriever()
    hybrid_bm25.index_documents(demo_corpus)
    
    hybrid = HybridRetriever(
        dense_retriever=uds3_adapter,
        sparse_retriever=hybrid_bm25,
        config=None
    )
    
    print("✅ Setup complete\n")
    
    # Run evaluations
    baseline_runner = EvaluationRunner(baseline, "BASELINE (BM25-only)")
    hybrid_runner = EvaluationRunner(hybrid, "HYBRID (UDS3 + BM25 + RRF)")
    
    # Only evaluate queries where we have demo docs
    available_doc_ids = {doc['doc_id'] for doc in demo_corpus}
    filtered_queries = [
        q for q in GROUND_TRUTH_DATASET
        if q.expected_top1 in available_doc_ids
    ]
    
    print(f"ℹ️ Evaluating {len(filtered_queries)} queries (filtered to available docs)\n")
    
    baseline_results = await baseline_runner.evaluate_all(filtered_queries)
    hybrid_results = await hybrid_runner.evaluate_all(filtered_queries)
    
    # Compare results
    compare_results(baseline_results, hybrid_results)
    
    print("=" * 80)
    print("✅ EVALUATION COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_evaluation())
