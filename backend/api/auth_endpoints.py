"""
Authentication Endpoints for VERITAS Backend
============================================

Provides:
- POST /auth/token - Login with username/password
- GET /auth/me - Get current user info
- POST /auth/refresh - Refresh access token (future)

Author: VERITAS Security Team
Date: 22. Oktober 2025
"""

from datetime import timedelta
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from backend.security.auth import (
    authenticate_user,
    create_access_token,
    get_current_active_user,
    User,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ENABLE_AUTH
)


# ============================================================================
# Router Configuration
# ============================================================================

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


# ============================================================================
# Data Models
# ============================================================================

class Token(BaseModel):
    """Token response model"""
    access_token: str
    token_type: str
    expires_in: int  # seconds


class LoginResponse(BaseModel):
    """Extended login response with user info"""
    access_token: str
    token_type: str
    expires_in: int
    user: Dict


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()) -> Token:
    """
    OAuth2 compatible token login endpoint
    
    Usage:
        curl -X POST http://localhost:5000/auth/token \\
             -d "username=admin&password=admin123"
    
    Returns:
        {
            "access_token": "eyJ...",
            "token_type": "bearer",
            "expires_in": 1800
        }
    """
    # Development mode: return a test token
    if not ENABLE_AUTH:
        test_token = create_access_token(
            data={
                "sub": "dev_admin",
                "roles": ["admin", "manager", "user", "guest"]
            }
        )
        return Token(
            access_token=test_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    
    # Authenticate user
    user = authenticate_user(form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user.username,
            "roles": [role.value for role in user.roles]
        },
        expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.get("/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)) -> User:
    """
    Get current authenticated user information
    
    Usage:
        curl -H "Authorization: Bearer <token>" \\
             http://localhost:5000/auth/me
    
    Returns:
        {
            "username": "admin",
            "full_name": "Admin User",
            "email": "admin@veritas.local",
            "disabled": false,
            "roles": ["admin", "manager", "user"]
        }
    """
    return current_user


@router.get("/status")
async def auth_status() -> Dict:
    """
    Get authentication system status
    
    Returns:
        {
            "enabled": true,
            "method": "OAuth2 + JWT",
            "token_expire_minutes": 30
        }
    """
    return {
        "enabled": ENABLE_AUTH,
        "method": "OAuth2 Password Flow with JWT tokens",
        "algorithm": "HS256",
        "token_expire_minutes": ACCESS_TOKEN_EXPIRE_MINUTES,
        "rbac": {
            "roles": ["admin", "manager", "user", "guest"],
            "description": "Role-Based Access Control enabled"
        }
    }


# ============================================================================
# Future Endpoints (Placeholder)
# ============================================================================

# @router.post("/refresh", response_model=Token)
# async def refresh_token(current_user: User = Depends(get_current_active_user)) -> Token:
#     """Refresh access token (future implementation)"""
#     pass

# @router.post("/logout")
# async def logout(current_user: User = Depends(get_current_active_user)) -> Dict:
#     """Logout user (future implementation - token blacklist)"""
#     pass

# @router.post("/register", response_model=User)
# async def register(username: str, password: str, email: str) -> User:
#     """Register new user (future implementation)"""
#     pass
