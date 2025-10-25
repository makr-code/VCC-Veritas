"""
VERITAS API v3 - User Router

User Management Endpoints:
- User Registration & Profile
- User Preferences
- User Feedback
- Query History

Phase: 4 (UDS3 & User)
Status: Implementation
"""

from fastapi import APIRouter, Request, HTTPException, Query as QueryParam
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import uuid
import hashlib

from backend.api.v3.models import (
    UserRegistration, UserProfile, UserPreferences,
    UserFeedback, UserQueryHistory
)
from backend.api.v3.service_integration import get_uds3_strategy

user_router = APIRouter(prefix="/user", tags=["User"])


@user_router.post("/register", response_model=UserProfile)
async def register_user(
    registration: UserRegistration,
    request: Request
):
    """
    User Registration - Neuen User registrieren
    
    Args:
        registration: UserRegistration mit username, email, password
        request: FastAPI Request
        
    Returns:
        UserProfile des neuen Users
        
    Example:
        POST /api/v3/user/register
        {
            "username": "analyst_max",
            "email": "max@example.com",
            "password": "secure_password_123",
            "full_name": "Max Mustermann",
            "organization": "VCC Analytics"
        }
    """
    uds3 = get_uds3_strategy(request)
    
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    
    # Validate: Check username/email uniqueness (in production)
    # In demo mode, always allow registration
    
    # Demo Mode
    if not uds3:
        return UserProfile(
            user_id=user_id,
            username=registration.username,
            email=registration.email,
            full_name=registration.full_name,
            organization=registration.organization,
            role="user",
            created_at=datetime.now(),
            last_login=None,
            query_count=0,
            preferences={
                "theme": "forest",
                "language": "de",
                "default_mode": "veritas"
            }
        )
    
    # Production: Store user in database
    try:
        # Hash password (in production use bcrypt)
        password_hash = hashlib.sha256(registration.password.encode()).hexdigest()
        
        user_data = {
            "user_id": user_id,
            "username": registration.username,
            "email": registration.email,
            "password_hash": password_hash,
            "full_name": registration.full_name,
            "organization": registration.organization,
            "role": "user",
            "created_at": datetime.now()
        }
        
        # Store in database
        uds3.store_user(user_data)
        
        # Return user profile (without password)
        return UserProfile(
            user_id=user_id,
            username=registration.username,
            email=registration.email,
            full_name=registration.full_name,
            organization=registration.organization,
            role="user",
            created_at=datetime.now(),
            last_login=None,
            query_count=0,
            preferences={}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"User registration failed: {str(e)}")


@user_router.get("/profile", response_model=UserProfile)
async def get_user_profile(
    user_id: str = QueryParam(..., description="User ID"),
    request: Request = None
):
    """
    Get User Profile - User-Profil abrufen
    
    Args:
        user_id: User ID
        request: FastAPI Request
        
    Returns:
        UserProfile mit allen User-Daten
        
    Example:
        GET /api/v3/user/profile?user_id=user_abc123
    """
    uds3 = get_uds3_strategy(request)
    
    # Demo Mode
    if not uds3:
        return UserProfile(
            user_id=user_id,
            username="demo_user",
            email="demo@veritas.ch",
            full_name="Demo User",
            organization="VERITAS Demo",
            role="analyst",
            created_at=datetime.now() - timedelta(days=30),
            last_login=datetime.now() - timedelta(hours=2),
            query_count=156,
            preferences={
                "theme": "forest",
                "language": "de",
                "default_mode": "veritas",
                "enable_llm_commentary": True
            }
        )
    
    # Production: Load user from database
    try:
        user = uds3.get_user(user_id)
        
        if not user:
            raise HTTPException(status_code=404, detail=f"User not found: {user_id}")
        
        return UserProfile(**user)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load user profile: {str(e)}")


@user_router.put("/profile", response_model=UserProfile)
async def update_user_profile(
    user_id: str = QueryParam(..., description="User ID"),
    full_name: Optional[str] = None,
    organization: Optional[str] = None,
    email: Optional[str] = None,
    request: Request = None
):
    """
    Update User Profile - User-Profil aktualisieren
    
    Args:
        user_id: User ID
        full_name: Optional neuer Name
        organization: Optional neue Organisation
        email: Optional neue Email
        request: FastAPI Request
        
    Returns:
        Aktualisiertes UserProfile
        
    Example:
        PUT /api/v3/user/profile?user_id=user_abc123
        {
            "full_name": "Max Mustermann PhD",
            "organization": "VCC Advanced Analytics"
        }
    """
    uds3 = get_uds3_strategy(request)
    
    # Demo Mode
    if not uds3:
        return UserProfile(
            user_id=user_id,
            username="demo_user",
            email=email or "demo@veritas.ch",
            full_name=full_name or "Demo User",
            organization=organization or "VERITAS Demo",
            role="analyst",
            created_at=datetime.now() - timedelta(days=30),
            last_login=datetime.now(),
            query_count=156,
            preferences={"theme": "forest"}
        )
    
    # Production: Update user in database
    try:
        update_data = {}
        if full_name:
            update_data["full_name"] = full_name
        if organization:
            update_data["organization"] = organization
        if email:
            update_data["email"] = email
        
        updated_user = uds3.update_user(user_id, update_data)
        
        if not updated_user:
            raise HTTPException(status_code=404, detail=f"User not found: {user_id}")
        
        return UserProfile(**updated_user)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update user profile: {str(e)}")


@user_router.get("/preferences", response_model=UserPreferences)
async def get_user_preferences(
    user_id: str = QueryParam(..., description="User ID"),
    request: Request = None
):
    """
    Get User Preferences - User-Einstellungen abrufen
    
    Args:
        user_id: User ID
        request: FastAPI Request
        
    Returns:
        UserPreferences mit allen Einstellungen
        
    Example:
        GET /api/v3/user/preferences?user_id=user_abc123
    """
    uds3 = get_uds3_strategy(request)
    
    # Demo Mode
    if not uds3:
        return UserPreferences(
            user_id=user_id,
            theme="forest",
            language="de",
            default_mode="veritas",
            enable_llm_commentary=True,
            results_per_page=20,
            auto_save_queries=True,
            notifications_enabled=True
        )
    
    # Production: Load preferences from database
    try:
        preferences = uds3.get_user_preferences(user_id)
        
        if not preferences:
            # Return default preferences
            return UserPreferences(
                user_id=user_id,
                theme="forest",
                language="de",
                default_mode="veritas",
                enable_llm_commentary=False,
                results_per_page=10,
                auto_save_queries=True,
                notifications_enabled=True
            )
        
        return UserPreferences(**preferences)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load preferences: {str(e)}")


@user_router.put("/preferences", response_model=UserPreferences)
async def update_user_preferences(
    preferences: UserPreferences,
    request: Request
):
    """
    Update User Preferences - User-Einstellungen aktualisieren
    
    Args:
        preferences: UserPreferences mit neuen Einstellungen
        request: FastAPI Request
        
    Returns:
        Aktualisierte UserPreferences
        
    Example:
        PUT /api/v3/user/preferences
        {
            "user_id": "user_abc123",
            "theme": "dark",
            "language": "en",
            "default_mode": "vpb",
            "enable_llm_commentary": true,
            "results_per_page": 50
        }
    """
    uds3 = get_uds3_strategy(request)
    
    # Demo Mode
    if not uds3:
        return preferences
    
    # Production: Update preferences in database
    try:
        updated_prefs = uds3.update_user_preferences(
            preferences.user_id,
            preferences.model_dump()
        )
        
        return UserPreferences(**updated_prefs)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update preferences: {str(e)}")


@user_router.post("/feedback", response_model=Dict[str, Any])
async def submit_feedback(
    feedback: UserFeedback,
    request: Request
):
    """
    Submit Feedback - User-Feedback einreichen
    
    Args:
        feedback: UserFeedback mit type, title, description
        request: FastAPI Request
        
    Returns:
        Dict mit feedback_id und status
        
    Example:
        POST /api/v3/user/feedback
        {
            "user_id": "user_abc123",
            "feedback_type": "feature",
            "title": "Export zu Excel",
            "description": "Wäre super wenn man Query-Results als Excel exportieren könnte",
            "priority": "medium",
            "related_query_id": "query_xyz789"
        }
    """
    uds3 = get_uds3_strategy(request)
    
    feedback_id = f"feedback_{uuid.uuid4().hex[:12]}"
    
    # Demo Mode
    if not uds3:
        return {
            "feedback_id": feedback_id,
            "status": "submitted",
            "message": "Vielen Dank für Ihr Feedback!",
            "created_at": datetime.now().isoformat(),
            "tracking_url": f"/feedback/{feedback_id}"
        }
    
    # Production: Store feedback in database
    try:
        feedback_data = feedback.model_dump()
        feedback_data["feedback_id"] = feedback_id
        feedback_data["created_at"] = datetime.now()
        feedback_data["status"] = "open"
        
        uds3.store_feedback(feedback_data)
        
        return {
            "feedback_id": feedback_id,
            "status": "submitted",
            "message": "Vielen Dank für Ihr Feedback!",
            "created_at": datetime.now().isoformat(),
            "tracking_url": f"/feedback/{feedback_id}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit feedback: {str(e)}")


@user_router.get("/history", response_model=List[UserQueryHistory])
async def get_query_history(
    user_id: str = QueryParam(..., description="User ID"),
    limit: int = QueryParam(50, ge=1, le=500, description="Max Results"),
    offset: int = QueryParam(0, ge=0, description="Offset"),
    mode: Optional[str] = QueryParam(None, description="Filter by mode"),
    bookmarked_only: bool = QueryParam(False, description="Only bookmarked queries"),
    request: Request = None
):
    """
    Get Query History - User Query-Historie abrufen
    
    Args:
        user_id: User ID
        limit: Max results
        offset: Pagination offset
        mode: Optional filter by mode (veritas, vpb, covina, etc.)
        bookmarked_only: Nur gebookmarkte Queries
        request: FastAPI Request
        
    Returns:
        Liste von UserQueryHistory Entries
        
    Example:
        GET /api/v3/user/history?user_id=user_abc123&limit=20&mode=vpb&bookmarked_only=false
    """
    uds3 = get_uds3_strategy(request)
    
    # Demo Mode
    if not uds3:
        history = [
            UserQueryHistory(
                query_id=f"query_{i}",
                user_id=user_id,
                query_text=f"Beispiel Query {i}: Windkraftanlage Abstand",
                mode="veritas" if i % 3 == 0 else "vpb" if i % 3 == 1 else "covina",
                results_count=10 + i,
                confidence=0.85 + (i % 10) / 100,
                duration=1.2 + (i % 5) / 10,
                timestamp=datetime.now() - timedelta(days=i),
                bookmarked=(i % 5 == 0)
            )
            for i in range(20)
        ]
        
        # Filter by mode
        if mode:
            history = [h for h in history if h.mode == mode]
        
        # Filter by bookmarked
        if bookmarked_only:
            history = [h for h in history if h.bookmarked]
        
        # Pagination
        return history[offset:offset + limit]
    
    # Production: Load history from database
    try:
        filters = {"user_id": user_id}
        if mode:
            filters["mode"] = mode
        if bookmarked_only:
            filters["bookmarked"] = True
        
        history = uds3.get_query_history(
            filters=filters,
            limit=limit,
            offset=offset
        )
        
        return [UserQueryHistory(**entry) for entry in history]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load query history: {str(e)}")
