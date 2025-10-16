#!/usr/bin/env python3
"""
VERITAS BASELINE EVALUATION
===========================

Etabliert Baseline-Metriken für RAG-Pipeline mit echtem UDS3 + Ollama.

Workflow:
---------
1. UDS3 initialisieren (hard requirement, no fallback)
2. Ollama-Client verbinden
3. IntelligentMultiAgentPipeline starten
4. Golden Dataset laden (5 Test-Cases)
5. Evaluation durchführen
6. Baseline-Report generieren

Expected Metrics:
-----------------
- Precision@5: ~60% (ohne Re-Ranking) → ~75% (mit Re-Ranking)
- Recall@20: ~70%
- MRR: ~0.65 → ~0.80
- Hallucination Rate: ~5%
- Pass Rate: ~60% → ~75%

Author: VERITAS System
Date: 2025-10-06
Version: 1.0
"""

import asyncio
import logging
import sys
from pathlib import Path

# Projekt-Root zum sys.path hinzufügen
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.agents.veritas_intelligent_pipeline import IntelligentMultiAgentPipeline
from backend.evaluation.veritas_rag_evaluator import RAGEvaluator

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def initialize_pipeline() -> IntelligentMultiAgentPipeline:
    """
    Initialisiert IntelligentMultiAgentPipeline.
    
    Die Pipeline initialisiert automatisch:
    - UDS3 Strategy
    - Ollama Client
    - VERITAS Agents
    - RAG Context Service
    
    Returns:
        Pipeline-Instanz
        
    Raises:
        RuntimeError: Wenn Pipeline nicht initialisiert werden kann
    """
    logger.info("🔄 Initialisiere IntelligentMultiAgentPipeline...")
    
    try:
        pipeline = IntelligentMultiAgentPipeline(max_workers=5)
        
        # Pipeline initialisieren (lädt UDS3, Ollama, Agents automatisch)
        success = await pipeline.initialize()
        
        if not success:
            raise RuntimeError("Pipeline-Initialisierung fehlgeschlagen")
        
        # Validierung
        if not pipeline.uds3_strategy:
            raise RuntimeError("Pipeline hat keine UDS3-Verbindung")
        
        logger.info("✅ Pipeline initialisiert mit UDS3 + Ollama + Agents")
        return pipeline
        
    except Exception as e:
        logger.error(f"❌ Pipeline-Initialisierung fehlgeschlagen: {e}")
        raise RuntimeError(
            "Pipeline konnte nicht initialisiert werden"
        ) from e


async def run_baseline_evaluation():
    """
    Führt vollständige Baseline-Evaluation durch.
    
    Steps:
    ------
    1. Pipeline initialisieren (inkl. UDS3 + Ollama)
    2. Golden Dataset laden (5 Test-Cases)
    3. Evaluation durchführen
    4. Baseline-Report generieren
    """
    logger.info("=" * 80)
    logger.info("VERITAS BASELINE EVALUATION")
    logger.info("=" * 80)
    
    pipeline = None
    
    try:
        # 1. Pipeline initialisieren (macht alles intern)
        pipeline = await initialize_pipeline()
        
        # 2. Evaluator erstellen
        logger.info("🔄 Erstelle RAG-Evaluator...")
        evaluator = RAGEvaluator(
            pipeline=pipeline,
            ollama_client=pipeline.ollama_client,
            strict_mode=False  # Nicht zu streng für Baseline
        )
        
        # 3. Golden Dataset laden
        golden_dataset_path = project_root / 'backend' / 'evaluation' / 'golden_dataset_examples.json'
        evaluator.load_golden_dataset(str(golden_dataset_path))
        
        # 4. Evaluation durchführen
        logger.info("🚀 Starte Baseline-Evaluation...")
        logger.info("-" * 80)
        
        summary = await evaluator.run_evaluation(verbose=True)
        
        # 5. Report speichern
        report_path = project_root / 'backend' / 'evaluation' / 'baseline_evaluation_report.json'
        evaluator.save_report(str(report_path))
        
        # 6. Summary ausgeben
        logger.info("-" * 80)
        evaluator.print_summary()
        
        logger.info("=" * 80)
        logger.info(f"✅ BASELINE EVALUATION COMPLETE")
        logger.info(f"📄 Report: {report_path}")
        logger.info("=" * 80)
        
        return summary
        
    except Exception as e:
        logger.error(f"❌ Baseline-Evaluation fehlgeschlagen: {e}")
        raise
    
    finally:
        # Cleanup
        if pipeline and hasattr(pipeline, 'executor'):
            try:
                pipeline.executor.shutdown(wait=True)
                logger.info("✅ Pipeline cleanup abgeschlossen")
            except Exception as e:
                logger.warning(f"⚠️ Pipeline-Cleanup-Fehler: {e}")


async def run_comparative_evaluation():
    """
    Führt vergleichende Evaluation durch: Mit vs. Ohne Re-Ranking.
    
    Generiert zwei Reports:
    -----------------------
    1. baseline_without_reranking.json (Re-Ranking OFF)
    2. baseline_with_reranking.json (Re-Ranking ON)
    
    Expected Improvements:
    ----------------------
    - Precision@5: +15%
    - MRR: +0.15
    - Pass Rate: +15%
    
    Note: Feature temporarily disabled - RAGContextService Re-Ranking
    integration needs to be verified first. Use baseline mode for now.
    """
    logger.warning("=" * 80)
    logger.warning("COMPARATIVE EVALUATION TEMPORARILY DISABLED")
    logger.warning("=" * 80)
    logger.warning("Reason: Re-Ranking toggle needs to be implemented in RAGContextService")
    logger.warning("Workaround: Run baseline evaluation instead")
    logger.warning("=" * 80)
    
    # Führe stattdessen einfache Baseline-Evaluation durch
    return await run_baseline_evaluation()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='VERITAS Baseline Evaluation')
    parser.add_argument(
        '--mode',
        choices=['baseline', 'comparative'],
        default='baseline',
        help='Evaluation-Modus'
    )
    
    args = parser.parse_args()
    
    if args.mode == 'baseline':
        asyncio.run(run_baseline_evaluation())
    else:
        asyncio.run(run_comparative_evaluation())
