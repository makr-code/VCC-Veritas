"""
OAuth2/JWT Authentication Module for VERITAS Backend
====================================================

Implements:
- OAuth2 Password Flow with JWT tokens
- Role-Based Access Control (RBAC)
- Token creation and validation
- User authentication

Based on Covina implementation.
Author: VERITAS Security Team
Date: 22. Oktober 2025
"""

import os
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import List, Optional

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel

# Load environment variables
try:
    from dotenv import load_dotenv

    # Load .env from project root
    project_root = Path(__file__).parent.parent.parent
    env_path = project_root / ".env"
    load_dotenv(env_path)
except ImportError:
    pass  # dotenv not available, use system env vars

# Import secrets manager for secure key storage
from backend.security.secrets import get_jwt_secret

# ============================================================================
# Configuration
# ============================================================================

SECRET_KEY = get_jwt_secret()  # Securely retrieve JWT secret from encrypted storage
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Feature flag for authentication
ENABLE_AUTH = os.getenv("ENABLE_AUTH", "false").lower() == "true"

# ============================================================================
# Security Components
# ============================================================================

# Password hashing using bcrypt directly (avoiding passlib compatibility issues)
import bcrypt


def _hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def _verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    password_bytes = plain_password.encode("utf-8")
    hashed_bytes = hashed_password.encode("utf-8")
    return bcrypt.checkpw(password_bytes, hashed_bytes)


# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token", auto_error=False)


# ============================================================================
# Data Models
# ============================================================================


class Role(str, Enum):
    """User roles for RBAC"""

    admin = "admin"
    manager = "manager"
    user = "user"
    guest = "guest"


class User(BaseModel):
    """User model"""

    username: str
    full_name: str
    email: str
    disabled: bool = False
    roles: List[Role] = []


class UserInDB(User):
    """User model with hashed password"""

    hashed_password: str


class TokenData(BaseModel):
    """Token payload data"""

    username: Optional[str] = None
    roles: List[Role] = []


# ============================================================================
# User Database (Temporary - Replace with Real Database Later)
# ============================================================================

# Default users for development
# NOTE: Passwords are hashed lazily on first access to avoid bcrypt initialization errors
_fake_users_db = None


def _get_fake_users_db():
    """Lazy initialization of user database with hashed passwords"""
    global _fake_users_db

    if _fake_users_db is None:
        _fake_users_db = {
            "admin": {
                "username": "admin",
                "full_name": "Admin User",
                "email": "admin@veritas.local",
                "hashed_password": _hash_password("admin123"),  # Change in production!
                "disabled": False,
                "roles": [Role.admin, Role.manager, Role.user],
            },
            "user": {
                "username": "user",
                "full_name": "Regular User",
                "email": "user@veritas.local",
                "hashed_password": _hash_password("user123"),  # Change in production!
                "disabled": False,
                "roles": [Role.user],
            },
            "guest": {
                "username": "guest",
                "full_name": "Guest User",
                "email": "guest@veritas.local",
                "hashed_password": _hash_password("guest123"),  # Change in production!
                "disabled": False,
                "roles": [Role.guest],
            },
        }

    return _fake_users_db


# ============================================================================
# Helper Functions
# ============================================================================


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against hashed password"""
    return _verify_password(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return _hash_password(password)


def get_user(username: str) -> Optional[UserInDB]:
    """Get user from database"""
    fake_users_db = _get_fake_users_db()
    if username in fake_users_db:
        user_dict = fake_users_db[username]
        return UserInDB(**user_dict)
    return None


def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    """Authenticate a user"""
    user = get_user(username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "iat": datetime.utcnow()})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# ============================================================================
# Dependencies
# ============================================================================


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    Get current user from JWT token

    If ENABLE_AUTH=false, returns a default admin user (development mode)
    """
    # Development mode: skip authentication
    if not ENABLE_AUTH:
        return User(
            username="dev_admin",
            full_name="Development Admin",
            email="dev@veritas.local",
            disabled=False,
            roles=[Role.admin, Role.manager, Role.user, Role.guest],
        )

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW - Authenticate": "Bearer"},
    )

    if token is None:
        raise credentials_exception

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")

        if username is None:
            raise credentials_exception

        # Extract roles from token
        roles_str = payload.get("roles", [])
        roles = [Role(r) for r in roles_str]

        token_data = TokenData(username=username, roles=roles)

    except JWTError:
        raise credentials_exception

    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exception

    if user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")

    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user"""
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


# ============================================================================
# Role-Based Access Control Dependencies
# ============================================================================


def require_role(required_roles: List[Role]):
    """
    Factory function to create role-based dependency

    Usage:
        @router.get("/admin-only")
        async def admin_endpoint(user: User = Depends(require_role([Role.admin]))):
            ...
    """

    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        # Development mode: allow all
        if not ENABLE_AUTH:
            return current_user

        # Check if user has any of the required roles
        user_has_role = any(role in current_user.roles for role in required_roles)

        if not user_has_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {[r.value for r in required_roles]}",
            )

        return current_user

    return role_checker


# Convenience dependencies for common role requirements
require_admin = require_role([Role.admin])
require_manager = require_role([Role.admin, Role.manager])
require_user = require_role([Role.admin, Role.manager, Role.user])
require_guest = require_role([Role.admin, Role.manager, Role.user, Role.guest])


# ============================================================================
# Optional Dependencies (don't raise errors if no token)
# ============================================================================


async def get_optional_user(token: str = Depends(oauth2_scheme)) -> Optional[User]:
    """
    Get current user if token is provided, otherwise return None
    Useful for endpoints that work with or without authentication
    """
    if not ENABLE_AUTH:
        return None

    if token is None:
        return None

    try:
        return await get_current_user(token)
    except HTTPException:
        return None
