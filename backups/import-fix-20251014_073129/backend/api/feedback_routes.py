#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VERITAS Backend: Feedback API Routes
Endpoints für User-Feedback Collection & Analytics
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

# FastAPI Router
router = APIRouter(
    prefix="/api/feedback",
    tags=["feedback"]
)

# ===== PYDANTIC MODELS =====

class FeedbackSubmit(BaseModel):
    """Request-Model für Feedback-Submission"""
    message_id: str = Field(..., description="Eindeutige Message-ID")
    rating: int = Field(..., ge=-1, le=1, description="Rating: 1=👍, -1=👎, 0=💬")
    category: Optional[str] = Field(None, description="Kategorie: helpful, incorrect, unclear, other")
    comment: Optional[str] = Field(None, max_length=1000, description="Optionaler Kommentar")
    user_id: Optional[str] = Field("anonymous", description="User-ID (optional)")
    
    @validator('category')
    def validate_category(cls, v):
        """Validiere Kategorie"""
        if v is not None:
            allowed = ['helpful', 'incorrect', 'unclear', 'other']
            if v not in allowed:
                raise ValueError(f"Category must be one of {allowed}")
        return v

class FeedbackResponse(BaseModel):
    """Response-Model nach Feedback-Submit"""
    success: bool
    feedback_id: int
    message: str
    timestamp: str

class FeedbackStats(BaseModel):
    """Response-Model für Feedback-Statistiken"""
    total_feedback: int
    positive_count: int
    negative_count: int
    neutral_count: int
    positive_ratio: float
    average_rating: float
    top_categories: List[Dict[str, Any]]
    recent_feedback: List[Dict[str, Any]]

# ===== DATABASE MANAGER =====

class FeedbackDatabase:
    """Database Manager für Feedback"""
    
    def __init__(self, db_path: str = "data/veritas_backend.sqlite"):
        """
        Initialisiert Feedback-Datenbank
        
        Args:
            db_path: Pfad zur SQLite-Datenbank
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialisiere Tabellen
        self._init_tables()
        logger.info(f"✅ Feedback-Datenbank initialisiert: {self.db_path}")
    
    def _init_tables(self):
        """Erstellt Feedback-Tabelle"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Feedback-Tabelle
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id TEXT NOT NULL,
                    user_id TEXT DEFAULT 'anonymous',
                    rating INTEGER NOT NULL CHECK(rating BETWEEN -1 AND 1),
                    category TEXT,
                    comment TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    
                    -- Indizes für Performance
                    UNIQUE(message_id, user_id) ON CONFLICT REPLACE
                )
            ''')
            
            # Index für schnelle Abfragen
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_feedback_message_id 
                ON feedback(message_id)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_feedback_timestamp 
                ON feedback(timestamp DESC)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_feedback_rating 
                ON feedback(rating)
            ''')
            
            conn.commit()
            logger.debug("✅ Feedback-Tabellen erstellt")
    
    def submit_feedback(
        self, 
        message_id: str, 
        rating: int, 
        category: Optional[str] = None,
        comment: Optional[str] = None,
        user_id: str = "anonymous"
    ) -> int:
        """
        Speichert Feedback in Datenbank
        
        Args:
            message_id: Message-ID
            rating: Rating (1, -1, 0)
            category: Kategorie
            comment: Kommentar
            user_id: User-ID
            
        Returns:
            feedback_id: ID des gespeicherten Feedbacks
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO feedback 
                (message_id, user_id, rating, category, comment)
                VALUES (?, ?, ?, ?, ?)
            ''', (message_id, user_id, rating, category, comment))
            
            feedback_id = cursor.lastrowid
            conn.commit()
            
            logger.info(f"✅ Feedback gespeichert: ID={feedback_id}, message_id={message_id}, rating={rating}")
            return feedback_id
    
    def get_stats(self, days: int = 30) -> Dict[str, Any]:
        """
        Holt aggregierte Feedback-Statistiken
        
        Args:
            days: Zeitraum in Tagen (default: 30)
            
        Returns:
            Stats-Dictionary
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Zeitraum-Filter
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            # Gesamt-Counts
            cursor.execute('''
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN rating = 1 THEN 1 ELSE 0 END) as positive,
                    SUM(CASE WHEN rating = -1 THEN 1 ELSE 0 END) as negative,
                    SUM(CASE WHEN rating = 0 THEN 1 ELSE 0 END) as neutral,
                    AVG(rating) as avg_rating
                FROM feedback
                WHERE timestamp >= ?
            ''', (cutoff_date,))
            
            row = cursor.fetchone()
            total, positive, negative, neutral, avg_rating = row
            
            # Positive Ratio (Prozent)
            positive_ratio = (positive / total * 100) if total > 0 else 0.0
            
            # Top-Kategorien
            cursor.execute('''
                SELECT category, COUNT(*) as count
                FROM feedback
                WHERE timestamp >= ? AND category IS NOT NULL
                GROUP BY category
                ORDER BY count DESC
                LIMIT 5
            ''', (cutoff_date,))
            
            top_categories = [
                {'category': row[0], 'count': row[1]}
                for row in cursor.fetchall()
            ]
            
            # Recent Feedback (letzte 10)
            cursor.execute('''
                SELECT message_id, rating, category, comment, timestamp
                FROM feedback
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
                LIMIT 10
            ''', (cutoff_date,))
            
            recent_feedback = [
                {
                    'message_id': row[0],
                    'rating': row[1],
                    'category': row[2],
                    'comment': row[3],
                    'timestamp': row[4]
                }
                for row in cursor.fetchall()
            ]
            
            return {
                'total_feedback': total or 0,
                'positive_count': positive or 0,
                'negative_count': negative or 0,
                'neutral_count': neutral or 0,
                'positive_ratio': round(positive_ratio, 2),
                'average_rating': round(avg_rating or 0.0, 3),
                'top_categories': top_categories,
                'recent_feedback': recent_feedback
            }
    
    def get_feedback_list(
        self, 
        limit: int = 50, 
        offset: int = 0,
        rating_filter: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Holt Liste von Feedbacks mit Pagination
        
        Args:
            limit: Anzahl Ergebnisse
            offset: Offset für Pagination
            rating_filter: Filter nach Rating (1, -1, 0)
            
        Returns:
            Liste von Feedback-Dictionaries
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Query mit optionalem Rating-Filter
            if rating_filter is not None:
                cursor.execute('''
                    SELECT id, message_id, user_id, rating, category, comment, timestamp
                    FROM feedback
                    WHERE rating = ?
                    ORDER BY timestamp DESC
                    LIMIT ? OFFSET ?
                ''', (rating_filter, limit, offset))
            else:
                cursor.execute('''
                    SELECT id, message_id, user_id, rating, category, comment, timestamp
                    FROM feedback
                    ORDER BY timestamp DESC
                    LIMIT ? OFFSET ?
                ''', (limit, offset))
            
            feedback_list = [
                {
                    'id': row[0],
                    'message_id': row[1],
                    'user_id': row[2],
                    'rating': row[3],
                    'category': row[4],
                    'comment': row[5],
                    'timestamp': row[6]
                }
                for row in cursor.fetchall()
            ]
            
            return feedback_list

# ===== GLOBAL DATABASE INSTANCE =====
feedback_db = FeedbackDatabase()

# ===== API ENDPOINTS =====

@router.post("/submit", response_model=FeedbackResponse)
async def submit_feedback(feedback: FeedbackSubmit):
    """
    Speichert User-Feedback
    
    **Request Body:**
    ```json
    {
        "message_id": "msg_123",
        "rating": 1,
        "category": "helpful",
        "comment": "Sehr gute Antwort!",
        "user_id": "user_456"
    }
    ```
    
    **Response:**
    ```json
    {
        "success": true,
        "feedback_id": 42,
        "message": "Feedback gespeichert",
        "timestamp": "2025-10-09T14:23:45"
    }
    ```
    """
    try:
        feedback_id = feedback_db.submit_feedback(
            message_id=feedback.message_id,
            rating=feedback.rating,
            category=feedback.category,
            comment=feedback.comment,
            user_id=feedback.user_id
        )
        
        return FeedbackResponse(
            success=True,
            feedback_id=feedback_id,
            message="Feedback erfolgreich gespeichert",
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"❌ Fehler beim Speichern von Feedback: {e}")
        raise HTTPException(status_code=500, detail=f"Fehler beim Speichern: {str(e)}")

@router.get("/stats", response_model=FeedbackStats)
async def get_feedback_stats(days: int = 30):
    """
    Holt aggregierte Feedback-Statistiken
    
    **Query Parameters:**
    - `days` (optional): Zeitraum in Tagen (default: 30)
    
    **Response:**
    ```json
    {
        "total_feedback": 150,
        "positive_count": 120,
        "negative_count": 20,
        "neutral_count": 10,
        "positive_ratio": 80.0,
        "average_rating": 0.667,
        "top_categories": [...],
        "recent_feedback": [...]
    }
    ```
    """
    try:
        stats = feedback_db.get_stats(days=days)
        return FeedbackStats(**stats)
        
    except Exception as e:
        logger.error(f"❌ Fehler beim Abrufen der Stats: {e}")
        raise HTTPException(status_code=500, detail=f"Fehler beim Abrufen: {str(e)}")

@router.get("/list")
async def get_feedback_list(
    limit: int = 50,
    offset: int = 0,
    rating: Optional[int] = None
):
    """
    Holt Liste von Feedbacks mit Pagination
    
    **Query Parameters:**
    - `limit` (optional): Anzahl Ergebnisse (default: 50)
    - `offset` (optional): Offset für Pagination (default: 0)
    - `rating` (optional): Filter nach Rating (1, -1, 0)
    
    **Response:**
    ```json
    [
        {
            "id": 1,
            "message_id": "msg_123",
            "user_id": "anonymous",
            "rating": 1,
            "category": "helpful",
            "comment": "Great!",
            "timestamp": "2025-10-09T14:23:45"
        },
        ...
    ]
    ```
    """
    try:
        feedback_list = feedback_db.get_feedback_list(
            limit=limit,
            offset=offset,
            rating_filter=rating
        )
        
        return {
            "total": len(feedback_list),
            "limit": limit,
            "offset": offset,
            "feedback": feedback_list
        }
        
    except Exception as e:
        logger.error(f"❌ Fehler beim Abrufen der Feedback-Liste: {e}")
        raise HTTPException(status_code=500, detail=f"Fehler beim Abrufen: {str(e)}")

# ===== HEALTH CHECK =====

@router.get("/health")
async def feedback_health():
    """Health-Check für Feedback-System"""
    try:
        stats = feedback_db.get_stats(days=1)
        return {
            "status": "healthy",
            "database": "connected",
            "today_feedback": stats['total_feedback']
        }
    except Exception as e:
        logger.error(f"❌ Health-Check fehlgeschlagen: {e}")
        raise HTTPException(status_code=503, detail="Feedback-System nicht verfügbar")
