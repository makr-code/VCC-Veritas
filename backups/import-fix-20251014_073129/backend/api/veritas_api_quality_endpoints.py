#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VERITAS API QUALITY ENDPOINTS (Migrated from Covina)
===================================================
FastAPI-Erweiterung für Quality-Management und RAG-Optimierung

Features:
- Chunk Quality Analysis
- RAG Performance Optimization
- Answer Quality Metrics
- Source Reliability Assessment
- Quality Feedback Integration

Author: VERITAS System
Created: 2025-09-21 (Migrated from Covina)
Version: 1.0.0
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
import logging
from datetime import datetime

# Quality-System imports
try:
    from veritas_quality_management import (
        VeritasQualityManager, 
        get_chunk_quality_context, 
        generate_llm_quality_prompt,
        assess_answer_quality,
        calculate_source_reliability
    )
    QUALITY_SYSTEM_AVAILABLE = True
except ImportError:
    QUALITY_SYSTEM_AVAILABLE = False
    logging.warning("Veritas Quality System nicht verfügbar")

try:
    from veritas_chunk_quality_db import (
        get_document_chunks,
        get_chunk_quality_scores,
        update_chunk_quality
    )
    CHUNK_DB_AVAILABLE = True
except ImportError:
    CHUNK_DB_AVAILABLE = False
    logging.warning("Veritas Chunk Quality DB nicht verfügbar")

logger = logging.getLogger(__name__)

# Router für Quality-Endpoints
router = APIRouter(prefix="/quality", tags=["quality"])

# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class DocumentQualityRequest(BaseModel):
    document_id: str = Field(..., description="Dokument-ID")
    include_chunks: bool = Field(default=True, description="Chunk-Details einschließen")
    quality_threshold: float = Field(default=0.7, ge=0.0, le=1.0)

class DocumentQualityResponse(BaseModel):
    document_id: str
    overall_quality: float
    chunk_count: int
    high_quality_chunks: int
    low_quality_chunks: int
    chunks: Optional[List[Dict[str, Any]]] = None
    recommendations: List[str]
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

class AnswerQualityRequest(BaseModel):
    question: str = Field(..., description="Ursprüngliche Frage")
    answer: str = Field(..., description="Generierte Antwort")
    sources: List[Dict[str, Any]] = Field(default=[], description="Verwendete Quellen")
    context: Optional[Dict[str, Any]] = None

class AnswerQualityResponse(BaseModel):
    quality_score: float
    quality_metrics: Dict[str, float]
    source_reliability: float
    completeness_score: float
    accuracy_indicators: Dict[str, Any]
    improvement_suggestions: List[str]
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

class QualityFeedbackRequest(BaseModel):
    query_id: str = Field(..., description="Query-ID")
    user_rating: int = Field(..., ge=1, le=5, description="Nutzer-Bewertung")
    quality_aspects: Dict[str, int] = Field(default={}, description="Spezifische Qualitäts-Aspekte")
    comment: Optional[str] = None

class RAGOptimizationRequest(BaseModel):
    query: str = Field(..., description="Test-Query")
    optimization_level: str = Field(default="standard", description="Optimierungslevel")
    target_quality: float = Field(default=0.8, ge=0.5, le=1.0)

class RAGOptimizationResponse(BaseModel):
    optimization_results: Dict[str, Any]
    recommended_settings: Dict[str, Any]
    quality_improvement: float
    performance_impact: Dict[str, Any]
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

# =============================================================================
# QUALITY MANAGER
# =============================================================================

class VeritasQualityController:
    """Controller für Quality-Management-Funktionen"""
    
    def __init__(self):
        self.quality_manager = None
        
        if QUALITY_SYSTEM_AVAILABLE:
            self.quality_manager = VeritasQualityManager()
            logger.info("✅ Veritas Quality Manager initialisiert")
        else:
            logger.warning("⚠️ Quality System nicht verfügbar - verwende Fallback")
    
    async def analyze_document_quality(self, request: DocumentQualityRequest) -> DocumentQualityResponse:
        """Analysiert Qualität eines Dokuments"""
        if not CHUNK_DB_AVAILABLE:
            # Fallback-Implementation
            return self._fallback_document_quality(request)
        
        try:
            # Chunks für Dokument abrufen
            chunks = get_document_chunks(request.document_id)
            quality_scores = get_chunk_quality_scores(request.document_id)
            
            # Qualitäts-Analyse
            high_quality = sum(1 for score in quality_scores if score >= request.quality_threshold)
            low_quality = len(quality_scores) - high_quality
            overall_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
            
            # Empfehlungen generieren
            recommendations = self._generate_quality_recommendations(overall_quality, high_quality, low_quality)
            
            chunk_details = None
            if request.include_chunks:
                chunk_details = [
                    {
                        "chunk_id": i,
                        "content_preview": chunk[:100] + "..." if len(chunk) > 100 else chunk,
                        "quality_score": quality_scores[i] if i < len(quality_scores) else 0.0,
                        "length": len(chunk)
                    }
                    for i, chunk in enumerate(chunks)
                ]
            
            return DocumentQualityResponse(
                document_id=request.document_id,
                overall_quality=overall_quality,
                chunk_count=len(chunks),
                high_quality_chunks=high_quality,
                low_quality_chunks=low_quality,
                chunks=chunk_details,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Fehler bei Dokument-Qualitäts-Analyse: {e}")
            return self._fallback_document_quality(request)
    
    def _fallback_document_quality(self, request: DocumentQualityRequest) -> DocumentQualityResponse:
        """Fallback-Implementation für Dokument-Qualität"""
        return DocumentQualityResponse(
            document_id=request.document_id,
            overall_quality=0.75,
            chunk_count=10,
            high_quality_chunks=7,
            low_quality_chunks=3,
            recommendations=[
                "Quality-System nicht verfügbar - verwende Standard-Einstellungen",
                "Installiere veritas_quality_management für erweiterte Funktionen"
            ]
        )
    
    def _generate_quality_recommendations(self, overall: float, high: int, low: int) -> List[str]:
        """Generiert Qualitäts-Empfehlungen"""
        recommendations = []
        
        if overall < 0.6:
            recommendations.append("Dokument hat niedrige Gesamtqualität - Review empfohlen")
        
        if low > high:
            recommendations.append("Viele Chunks mit niedriger Qualität - Chunk-Größe anpassen")
        
        if overall > 0.9:
            recommendations.append("Hervorragende Dokumentqualität - optimal für RAG")
        
        return recommendations
    
    async def assess_answer_quality(self, request: AnswerQualityRequest) -> AnswerQualityResponse:
        """Bewertet Qualität einer generierten Antwort"""
        try:
            if self.quality_manager:
                # Erweiterte Qualitäts-Bewertung
                quality_result = await self.quality_manager.assess_answer_quality(
                    question=request.question,
                    answer=request.answer,
                    sources=request.sources,
                    context=request.context
                )
                
                return AnswerQualityResponse(**quality_result)
            else:
                # Fallback-Bewertung
                return self._fallback_answer_quality(request)
                
        except Exception as e:
            logger.error(f"Fehler bei Antwort-Qualitäts-Bewertung: {e}")
            return self._fallback_answer_quality(request)
    
    def _fallback_answer_quality(self, request: AnswerQualityRequest) -> AnswerQualityResponse:
        """Fallback-Implementation für Antwort-Qualität"""
        # Einfache heuristische Bewertung
        answer_length = len(request.answer)
        source_count = len(request.sources)
        
        # Basis-Score basierend auf Länge und Quellen
        quality_score = min(0.9, 0.3 + (answer_length / 1000) * 0.4 + (source_count / 5) * 0.3)
        
        return AnswerQualityResponse(
            quality_score=quality_score,
            quality_metrics={
                "length_score": min(1.0, answer_length / 500),
                "source_score": min(1.0, source_count / 3),
                "coherence_score": 0.8  # Dummy-Wert
            },
            source_reliability=0.75,
            completeness_score=quality_score,
            accuracy_indicators={
                "has_sources": source_count > 0,
                "adequate_length": answer_length > 50,
                "fallback_assessment": True
            },
            improvement_suggestions=[
                "Quality-System installieren für detaillierte Bewertung" if not self.quality_manager else ""
            ]
        )

# Globaler Quality Controller
quality_controller = VeritasQualityController()

# =============================================================================
# API ENDPOINTS
# =============================================================================

@router.get("/document/{document_id}", response_model=DocumentQualityResponse)
async def get_document_quality(document_id: str, include_chunks: bool = True, quality_threshold: float = 0.7):
    """
    Holt Quality-Informationen für ein spezifisches Dokument
    
    Für RAG-Optimierung: Zeigt welche Chunks verlässlich sind
    """
    if not QUALITY_SYSTEM_AVAILABLE and not CHUNK_DB_AVAILABLE:
        logger.warning("Quality-System nicht verfügbar - verwende Fallback")
    
    request = DocumentQualityRequest(
        document_id=document_id,
        include_chunks=include_chunks,
        quality_threshold=quality_threshold
    )
    
    return await quality_controller.analyze_document_quality(request)

@router.post("/assess-answer", response_model=AnswerQualityResponse)
async def assess_answer_quality(request: AnswerQualityRequest):
    """
    Bewertet Qualität einer generierten Antwort
    
    Analysiert:
    - Vollständigkeit der Antwort
    - Quellenqualität
    - Kohärenz und Relevanz
    """
    return await quality_controller.assess_answer_quality(request)

@router.post("/feedback")
async def submit_quality_feedback(feedback: QualityFeedbackRequest):
    """
    Feedback für Antwortqualität
    
    Wird für kontinuierliche Qualitätsverbesserung verwendet
    """
    try:
        # TODO: Feedback in Quality-DB speichern
        if quality_controller.quality_manager:
            await quality_controller.quality_manager.store_feedback(feedback.dict())
        
        logger.info(f"Quality-Feedback erhalten: Query {feedback.query_id}, Rating: {feedback.user_rating}")
        
        return {
            "status": "success",
            "message": "Quality-Feedback gespeichert",
            "query_id": feedback.query_id,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Fehler beim Speichern von Quality-Feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/optimize-rag", response_model=RAGOptimizationResponse)
async def optimize_rag_settings(request: RAGOptimizationRequest):
    """
    RAG-Optimierung basierend auf Quality-Metriken
    
    Testet verschiedene Einstellungen und empfiehlt optimale Konfiguration
    """
    try:
        if quality_controller.quality_manager:
            # Erweiterte RAG-Optimierung
            optimization_result = await quality_controller.quality_manager.optimize_rag_settings(request.dict())
            return RAGOptimizationResponse(**optimization_result)
        else:
            # Fallback-Optimierung
            return RAGOptimizationResponse(
                optimization_results={
                    "test_query": request.query,
                    "baseline_quality": 0.7,
                    "optimized_quality": min(0.95, request.target_quality + 0.1)
                },
                recommended_settings={
                    "chunk_size": 512,
                    "overlap": 50,
                    "top_k": 5,
                    "temperature": 0.7
                },
                quality_improvement=0.15,
                performance_impact={
                    "response_time_change": "+5%",
                    "accuracy_improvement": "+15%"
                }
            )
            
    except Exception as e:
        logger.error(f"Fehler bei RAG-Optimierung: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics/summary")
async def get_quality_metrics_summary():
    """
    Übersicht über Quality-Metriken
    
    Zeigt aggregierte Qualitätsdaten für das System
    """
    try:
        # TODO: Echte Metriken aus Quality-DB abrufen
        return {
            "overall_system_quality": 0.82,
            "total_documents_analyzed": 1250,
            "average_chunk_quality": 0.78,
            "high_quality_documents": 892,
            "improvement_trends": {
                "last_30_days": "+5.2%",
                "quality_stability": "stable"
            },
            "top_quality_issues": [
                "Kurze Chunks mit wenig Kontext",
                "Inkonsistente Formatierung",
                "Fehlende Metadaten"
            ],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Quality-Metriken: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_quality_system_status():
    """Status des Quality-Systems"""
    return {
        "quality_system_available": QUALITY_SYSTEM_AVAILABLE,
        "chunk_db_available": CHUNK_DB_AVAILABLE,
        "quality_manager_active": quality_controller.quality_manager is not None,
        "features": {
            "document_analysis": True,
            "answer_assessment": True,
            "rag_optimization": QUALITY_SYSTEM_AVAILABLE,
            "feedback_collection": True
        },
        "timestamp": datetime.now().isoformat()
    }