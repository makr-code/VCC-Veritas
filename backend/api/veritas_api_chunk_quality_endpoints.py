#!/usr/bin/env python3
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VERITAS Protected Module
WARNING: This file contains embedded protection keys.
Modification will be detected and may result in license violations.
"""


"""
VERITAS API CHUNK QUALITY ENDPOINTS
====================================
FastAPI-Erweiterung für Chunk-Quality-Management und RAG-Optimierung
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException

# Chunk-Quality-System imports
try:
    from chunk_quality_management import chunk_quality_db, generate_llm_quality_prompt, get_chunk_quality_context

    CHUNK_QUALITY_AVAILABLE = True
except ImportError:
    CHUNK_QUALITY_AVAILABLE = False

logger = logging.getLogger(__name__)

# Router für Chunk-Quality-Endpoints
chunk_quality_router = APIRouter(prefix="/chunk-quality", tags=["chunk-quality"])


@chunk_quality_router.get("/document/{document_id}")
async def get_document_chunk_quality(document_id: str) -> Dict[str, Any]:
    """
    Holt Chunk-Quality-Informationen für ein spezifisches Dokument

    Für RAG-Optimierung: Zeigt welche Chunks verlässlich sind
    """
    if not CHUNK_QUALITY_AVAILABLE:
        raise HTTPException(status_code=503, detail="Chunk-Quality-System nicht verfügbar")

    try:
        # Chunk-Quality-Context abrufen
        quality_context = get_chunk_quality_context(document_id)

        if not quality_context:
            raise HTTPException(status_code=404, detail=f"Keine Chunk-Quality-Daten für Dokument {document_id}")

        return {
            "success": True,
            "document_id": document_id,
            "chunk_quality": quality_context,
            "rag_recommendations": _generate_rag_recommendations(quality_context),
        }

    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Chunk-Quality für {document_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@chunk_quality_router.get("/high-quality-chunks")
async def get_high_quality_chunks(
    min_score: float = 0.8, limit: int = 50, document_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Holt hochqualitative Chunks für RAG-Context

    Parameter:
    - min_score: Minimaler Quality-Score (default: 0.8)
    - limit: Maximale Anzahl Chunks (default: 50)
    - document_type: Filter nach Dokument-Typ (optional)
    """
    if not CHUNK_QUALITY_AVAILABLE:
        raise HTTPException(status_code=503, detail="Chunk-Quality-System nicht verfügbar")

    try:
        # High-Quality-Chunks aus DB abrufen
        chunks = chunk_quality_db.get_high_quality_chunks(min_score=min_score, limit=limit)

        # Nach Document-Type filtern falls gewünscht
        if document_type:
            # TODO: Document-Type-Filter implementieren
            pass

        chunk_data = []
        for chunk in chunks:
            chunk_data.append(
                {
                    "document_id": chunk.document_id,
                    "chunk_id": chunk.chunk_id,
                    "chunk_index": chunk.chunk_index,
                    "quality_score": chunk.quality_score,
                    "semantic_coherence": chunk.semantic_coherence,
                    "entity_density": chunk.entity_density,
                    "content_completeness": chunk.content_completeness,
                    "content_preview": chunk.chunk_content[:200] + "..."
                    if len(chunk.chunk_content) > 200
                    else chunk.chunk_content,
                    "embedding_available": chunk.chunk_embedding_available,
                    "reliability_level": _get_reliability_level(chunk.quality_score),
                }
            )

        return {
            "success": True,
            "total_chunks": len(chunk_data),
            "min_score_filter": min_score,
            "chunks": chunk_data,
            "usage_recommendation": "Diese Chunks sind für RAG - Context besonders geeignet",
        }

    except Exception as e:
        logger.error(f"Fehler beim Abrufen der High-Quality-Chunks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@chunk_quality_router.post("/enhance-prompt")
async def enhance_prompt_with_quality(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Erweitert LLM-Prompt um Chunk-Quality-Informationen

    Request Body:
    {
        "document_id": "doc_123",
        "base_prompt": "Analysiere das Dokument...",
        "include_chunk_details": false
    }
    """
    if not CHUNK_QUALITY_AVAILABLE:
        raise HTTPException(status_code=503, detail="Chunk-Quality-System nicht verfügbar")

    try:
        document_id = request.get("document_id")
        base_prompt = request.get("base_prompt", "")
        include_details = request.get("include_chunk_details", False)

        if not document_id:
            raise HTTPException(status_code=400, detail="document_id erforderlich")

        if not base_prompt:
            raise HTTPException(status_code=400, detail="base_prompt erforderlich")

        # Prompt mit Quality-Informationen erweitern
        enhanced_prompt = generate_llm_quality_prompt(document_id, base_prompt)

        response = {
            "success": True,
            "document_id": document_id,
            "original_prompt": base_prompt,
            "enhanced_prompt": enhanced_prompt,
            "enhancement_applied": enhanced_prompt != base_prompt,
        }

        # Optional: Detaillierte Chunk-Informationen hinzufügen
        if include_details:
            quality_context = get_chunk_quality_context(document_id)
            response["chunk_quality_details"] = quality_context

        return response

    except Exception as e:
        logger.error(f"Fehler beim Prompt-Enhancement: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@chunk_quality_router.get("/statistics")
async def get_chunk_quality_statistics() -> Dict[str, Any]:
    """
    Holt allgemeine Chunk-Quality-Statistiken für Monitoring
    """
    if not CHUNK_QUALITY_AVAILABLE:
        raise HTTPException(status_code=503, detail="Chunk-Quality-System nicht verfügbar")

    try:
        # Basis-Statistiken aus DB
        high_quality = chunk_quality_db.get_high_quality_chunks(min_score=0.8, limit=1000)
        medium_quality = chunk_quality_db.get_high_quality_chunks(min_score=0.6, limit=1000)
        all_chunks = chunk_quality_db.get_high_quality_chunks(min_score=0.0, limit=10000)

        total_chunks = len(all_chunks)
        high_count = len([c for c in all_chunks if c.quality_score >= 0.8])
        medium_count = len([c for c in all_chunks if 0.6 <= c.quality_score < 0.8])
        low_count = len([c for c in all_chunks if 0.4 <= c.quality_score < 0.6])
        unreliable_count = len([c for c in all_chunks if c.quality_score < 0.4])

        # Durchschnittswerte berechnen
        avg_score = sum(c.quality_score for c in all_chunks) / total_chunks if total_chunks > 0 else 0
        avg_coherence = sum(c.semantic_coherence for c in all_chunks) / total_chunks if total_chunks > 0 else 0
        avg_entity_density = sum(c.entity_density for c in all_chunks) / total_chunks if total_chunks > 0 else 0

        # Embedding-Verfügbarkeit
        chunks_with_embeddings = len([c for c in all_chunks if c.chunk_embedding_available])
        embedding_coverage = (chunks_with_embeddings / total_chunks) * 100 if total_chunks > 0 else 0

        return {
            "success": True,
            "total_chunks": total_chunks,
            "quality_distribution": {
                "high_quality": {
                    "count": high_count,
                    "percentage": (high_count / total_chunks) * 100 if total_chunks > 0 else 0,
                },
                "medium_quality": {
                    "count": medium_count,
                    "percentage": (medium_count / total_chunks) * 100 if total_chunks > 0 else 0,
                },
                "low_quality": {"count": low_count, "percentage": (low_count / total_chunks) * 100 if total_chunks > 0 else 0},
                "unreliable": {
                    "count": unreliable_count,
                    "percentage": (unreliable_count / total_chunks) * 100 if total_chunks > 0 else 0,
                },
            },
            "average_metrics": {
                "quality_score": round(avg_score, 3),
                "semantic_coherence": round(avg_coherence, 3),
                "entity_density": round(avg_entity_density, 3),
            },
            "embedding_coverage": {
                "chunks_with_embeddings": chunks_with_embeddings,
                "coverage_percentage": round(embedding_coverage, 1),
            },
            "rag_readiness": {
                "high_quality_chunks_available": high_count >= 10,
                "embedding_coverage_sufficient": embedding_coverage >= 80.0,
                "overall_quality_acceptable": avg_score >= 0.6,
                "rag_recommendation": "Geeignet für RAG"
                if (high_count >= 10 and avg_score >= 0.6)
                else "RAG - Qualität prüfen",
            },
        }

    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Chunk-Quality-Statistiken: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@chunk_quality_router.get("/rag-context/{document_id}")
async def get_rag_optimized_context(document_id: str, max_chunks: int = 10, min_quality: float = 0.6) -> Dict[str, Any]:
    """
    Holt optimierten RAG-Context basierend auf Chunk-Quality

    Liefert die besten Chunks für RAG-basierte Antworten
    """
    if not CHUNK_QUALITY_AVAILABLE:
        raise HTTPException(status_code=503, detail="Chunk-Quality-System nicht verfügbar")

    try:
        # Document-spezifische Chunks holen
        chunks = chunk_quality_db.get_chunk_quality_for_document(document_id)

        if not chunks:
            raise HTTPException(status_code=404, detail=f"Keine Chunks für Dokument {document_id}")

        # Nach Quality sortieren und filtern
        quality_chunks = [c for c in chunks if c.quality_score >= min_quality]
        quality_chunks.sort(key=lambda x: x.quality_score, reverse=True)

        # Top-Chunks für RAG-Context auswählen
        rag_chunks = quality_chunks[:max_chunks]

        context_data = []
        for chunk in rag_chunks:
            context_data.append(
                {
                    "chunk_id": chunk.chunk_id,
                    "chunk_index": chunk.chunk_index,
                    "content_preview": chunk.chunk_content,
                    "quality_score": chunk.quality_score,
                    "semantic_coherence": chunk.semantic_coherence,
                    "reliability_level": _get_reliability_level(chunk.quality_score),
                    "rag_weight": _calculate_rag_weight(chunk.quality_score),
                    "embedding_available": chunk.chunk_embedding_available,
                }
            )

        # RAG-Empfehlungen generieren
        avg_quality = sum(c.quality_score for c in rag_chunks) / len(rag_chunks) if rag_chunks else 0

        return {
            "success": True,
            "document_id": document_id,
            "total_available_chunks": len(chunks),
            "selected_chunks": len(context_data),
            "average_quality": round(avg_quality, 3),
            "rag_chunks": context_data,
            "rag_recommendations": {
                "context_quality": "High" if avg_quality >= 0.8 else "Medium" if avg_quality >= 0.6 else "Low",
                "confidence_level": "High"
                if avg_quality >= 0.8 and len(rag_chunks) >= 5
                else "Medium"
                if avg_quality >= 0.6
                else "Low",
                "usage_note": f"Verwende diese {len(rag_chunks)} Chunks für optimale RAG-Performance",
            },
        }

    except Exception as e:
        logger.error(f"Fehler beim Erstellen des RAG-Contexts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Hilfsfunktionen
def _generate_rag_recommendations(quality_context: Dict[str, Any]) -> Dict[str, Any]:
    """Generiert RAG-Empfehlungen basierend auf Quality-Context"""
    high_count = quality_context.get("chunk_quality_distribution", {}).get("high", 0)
    medium_count = quality_context.get("chunk_quality_distribution", {}).get("medium", 0)
    low_count = quality_context.get("chunk_quality_distribution", {}).get("low", 0)
    unreliable_count = quality_context.get("chunk_quality_distribution", {}).get("unreliable", 0)
    overall_quality = quality_context.get("overall_document_quality", 0)

    recommendations = {
        "primary_chunks": "high_quality" if high_count >= 2 else "medium_quality" if medium_count >= 2 else "all_available",
        "confidence_level": "high" if high_count >= 3 else "medium" if high_count + medium_count >= 3 else "low",
        "exclude_unreliable": unreliable_count > 0,
        "quality_warning": overall_quality < 0.6,
        "rag_strategy": _get_rag_strategy(high_count, medium_count, low_count, unreliable_count),
    }

    return recommendations


def _get_reliability_level(score: float) -> str:
    """Bestimmt Reliability-Level basierend auf Quality-Score"""
    if score >= 0.8:
        return "high"
    elif score >= 0.6:
        return "medium"
    elif score >= 0.4:
        return "low"
    else:
        return "unreliable"


def _calculate_rag_weight(score: float) -> float:
    """Berechnet RAG-Gewichtung basierend auf Quality-Score"""
    if score >= 0.9:
        return 1.0
    elif score >= 0.8:
        return 0.9
    elif score >= 0.7:
        return 0.7
    elif score >= 0.6:
        return 0.5
    elif score >= 0.4:
        return 0.3
    else:
        return 0.1


def _get_rag_strategy(high: int, medium: int, low: int, unreliable: int) -> str:
    """Empfiehlt RAG-Strategie basierend auf Chunk-Quality-Verteilung"""
    if high >= 3:
        return "use_high_quality_only"
    elif high + medium >= 3:
        return "combine_high_medium_quality"
    elif high + medium + low >= 3:
        return "use_all_reliable_chunks"
    else:
        return "insufficient_quality_data"


# Export des Routers
__all__ = ["chunk_quality_router"]

"""
VERITAS Protected Module
WARNING: This file contains embedded protection keys.
Modification will be detected and may result in license violations.
"""

# === VERITAS PROTECTION KEYS (DO NOT MODIFY) ===
module_name = "api_chunk_quality_endpoints"
module_licenced_organization = "VERITAS_TECH_GMBH"
module_licence_key = "eyJjbGllbnRfaWQi...NzRkYzhl"  # Gekuerzt fuer Sicherheit
module_organization_key = "6f5304c29594443086e1ace0011c094614b612c22aa16af9f1a63f02a0c9bf5c"
module_file_key = "0f74c5348bf8144d48af153510e61aff6e8ea45fd38fad56c2efd221498c04e9"
module_version = "1.0"
module_protection_level = 3
# === END PROTECTION KEYS ===
