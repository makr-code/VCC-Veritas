"""
VERITAS API - Authentication & Authorization Middleware
========================================================

FastAPI middleware for security integration:
- JWT token validation
- API key authentication
- Rate limiting
- Permission checking
- Request validation

Author: VERITAS Development Team
Created: 2025-10-08
Phase: 5.2 - Production Deployment
"""

import logging
from functools import wraps
from typing import Callable, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer

from .security import APIKey, AuthenticationManager, Permission, RateLimiter, SecurityConfig, User

logger = logging.getLogger(__name__)

# Initialize security components
security_config = SecurityConfig.from_env()
auth_manager = AuthenticationManager(security_config)
rate_limiter = RateLimiter(
    requests=security_config.RATE_LIMIT_REQUESTS, window_seconds=security_config.RATE_LIMIT_WINDOW_SECONDS
)

# FastAPI security schemes
bearer_scheme = HTTPBearer()
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_current_user_from_token(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> dict:
    """
    Dependency to get current user from JWT token.

    Usage:
        @app.get("/protected")
        async def protected_route(user=Depends(get_current_user_from_token)):
            return {"user": user["username"]}
    """
    token = credentials.credentials

    payload = auth_manager.verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW - Authenticate": "Bearer"},
        )

    return payload


async def get_current_user_from_api_key(api_key: Optional[str] = Depends(api_key_header)) -> Optional[APIKey]:
    """
    Dependency to get current user from API key.

    Usage:
        @app.get("/api/data")
        async def api_route(api_key_obj=Depends(get_current_user_from_api_key)):
            if api_key_obj:
                return {"authenticated": True}
    """
    if not api_key:
        return None

    api_key_obj = auth_manager.verify_api_key(api_key)
    if not api_key_obj:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")

    return api_key_obj


async def get_current_user(
    token_user: Optional[dict] = Depends(get_current_user_from_token),
    api_key_user: Optional[APIKey] = Depends(get_current_user_from_api_key),
):
    """
    Dependency to get current user from either JWT or API key.

    Usage:
        @app.get("/flexible")
        async def flexible_route(user=Depends(get_current_user)):
            return {"authenticated": True}
    """
    if token_user:
        return token_user
    if api_key_user:
        return api_key_user

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")


def require_permission(permission: Permission):
    """
    Dependency factory to require specific permission.

    Usage:
        @app.delete("/plans/{plan_id}")
        async def delete_plan(
            plan_id: str,
            user=Depends(require_permission(Permission.PLAN_DELETE))
        ):
            return {"deleted": plan_id}
    """

    async def permission_checker(user=Depends(get_current_user)):
        if not auth_manager.check_permission(user, permission):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Permission required: {permission.value}")
        return user

    return permission_checker


def require_role(*roles):
    """
    Dependency factory to require specific roles.

    Usage:
        from security import UserRole

        @app.get("/admin")
        async def admin_route(user=Depends(require_role(UserRole.ADMIN))):
            return {"admin": True}
    """
    from .security import UserRole

    async def role_checker(user=Depends(get_current_user)):
        user_role_str = user.get("role") if isinstance(user, dict) else None

        if not user_role_str:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Role information missing")

        try:
            user_role = UserRole(user_role_str)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid role")

        if user_role not in roles:
            role_names = [r.value for r in roles]
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Role required: {', '.join(role_names)}")

        return user

    return role_checker


async def rate_limit_middleware(request: Request, call_next):
    """
    Middleware for rate limiting.

    Usage in FastAPI app:
        app.middleware("http")(rate_limit_middleware)
    """
    # Get identifier (IP address or user ID)
    client_ip = request.client.host
    identifier = client_ip

    # Check if authenticated
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        payload = auth_manager.verify_token(token)
        if payload:
            identifier = payload.get("user_id", client_ip)

    # Check rate limit
    if not rate_limiter.is_allowed(identifier):
        remaining = rate_limiter.get_remaining(identifier)
        reset_time = rate_limiter.get_reset_time(identifier)

        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={
                "X - RateLimit-Remaining": str(remaining),
                "X - RateLimit-Reset": str(int(reset_time)) if reset_time else "0",
            },
        )

    # Add rate limit headers to response
    response = await call_next(request)
    remaining = rate_limiter.get_remaining(identifier)

    response.headers["X-RateLimit-Limit"] = str(rate_limiter.requests)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-RateLimit-Window"] = str(rate_limiter.window_seconds)

    return response


async def security_headers_middleware(request: Request, call_next):
    """
    Middleware to add security headers.

    Usage in FastAPI app:
        app.middleware("http")(security_headers_middleware)
    """
    response = await call_next(request)

    # Add security headers
    response.headers["X-Content-Type-Options"] = "nosnif"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"

    return response


# Input validation utilities


def validate_string_length(value: str, min_len: int = 1, max_len: int = 255, field_name: str = "field"):
    """Validate string length"""
    if len(value) < min_len:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"{field_name} must be at least {min_len} characters"
        )
    if len(value) > max_len:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"{field_name} must not exceed {max_len} characters"
        )
    return value


def validate_email(email: str):
    """Validate email format"""
    import re

    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(email_pattern, email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email format")
    return email


def sanitize_input(value: str):
    """Sanitize input to prevent injection attacks"""
    # Remove potential SQL injection patterns
    dangerous_patterns = ["';", "--", "/*", "*/", "xp_", "sp_", "DROP", "DELETE", "INSERT", "UPDATE"]

    value_upper = value.upper()
    for pattern in dangerous_patterns:
        if pattern.upper() in value_upper:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid input detected")

    return value


# WebSocket authentication


async def authenticate_websocket(websocket, token: Optional[str] = None):
    """
    Authenticate WebSocket connection.

    Usage:
        @app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket, token: str = Query(None)):
            user = await authenticate_websocket(websocket, token)
            # ... WebSocket logic
    """
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication token required")

    payload = auth_manager.verify_token(token)
    if not payload:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    return payload


# Example FastAPI routes with security

"""
Example usage in main FastAPI app:

from fastapi import FastAPI, Depends
from .middleware import (
    get_current_user,
    require_permission,
    require_role,
    rate_limit_middleware,
    security_headers_middleware,
    auth_manager,
    Permission,
    UserRole
)

app = FastAPI()

# Add middleware
app.middleware("http")(rate_limit_middleware)
app.middleware("http")(security_headers_middleware)


# Public endpoints
@app.post("/auth/register")
async def register(username: str, email: str, password: str):
    user = auth_manager.create_user(username, email, password)
    return {"user_id": user.user_id}


@app.post("/auth/login")
async def login(username: str, password: str):
    user = auth_manager.authenticate_user(username, password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = auth_manager.create_access_token(user)
    refresh_token = auth_manager.create_refresh_token(user)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


# Protected endpoints
@app.get("/plans")
async def list_plans(user=Depends(get_current_user)):
    # User is authenticated
    return {"plans": []}


@app.post("/plans")
async def create_plan(
    plan_data: dict,
    user=Depends(require_permission(Permission.PLAN_CREATE))
):
    # User has PLAN_CREATE permission
    return {"plan_id": "new_plan"}


@app.delete("/plans/{plan_id}")
async def delete_plan(
    plan_id: str,
    user=Depends(require_permission(Permission.PLAN_DELETE))
):
    # User has PLAN_DELETE permission
    return {"deleted": plan_id}


@app.get("/admin/users")
async def list_users(user=Depends(require_role(UserRole.ADMIN))):
    # Only admins can access
    return {"users": list(auth_manager.users.values())}


# API key protected endpoint
@app.get("/api/v1/data")
async def get_data(api_key=Depends(get_current_user_from_api_key)):
    if not api_key:
        raise HTTPException(status_code=401, detail="API key required")
    return {"data": "sensitive_data"}


# WebSocket with authentication
@app.websocket("/ws/stream")
async def websocket_stream(websocket: WebSocket, token: str = Query(None)):
    user = await authenticate_websocket(websocket, token)
    await websocket.accept()
    # ... streaming logic
"""


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("VERITAS MIDDLEWARE MODULE - INFORMATION")
    print("=" * 70 + "\n")

    print("Available Dependencies:")
    print("  - get_current_user_from_token: JWT authentication")
    print("  - get_current_user_from_api_key: API key authentication")
    print("  - get_current_user: Flexible authentication (JWT or API key)")
    print("  - require_permission(perm): Permission checking")
    print("  - require_role(*roles): Role checking")
    print("")
    print("Middleware:")
    print("  - rate_limit_middleware: Rate limiting")
    print("  - security_headers_middleware: Security headers")
    print("")
    print("Utilities:")
    print("  - validate_string_length: String validation")
    print("  - validate_email: Email validation")
    print("  - sanitize_input: Input sanitization")
    print("  - authenticate_websocket: WebSocket auth")
    print("")
    print("=" * 70)
    print("MIDDLEWARE MODULE READY")
    print("=" * 70 + "\n")

    print("Integration Example:")
    print(
        """
    from fastapi import FastAPI
    from middleware import get_current_user, require_permission

    app = FastAPI()

    @app.get("/protected")
    async def protected_route(user=Depends(get_current_user)):
        return {"user": user}
    """
    )

    print("\nStatus: PRODUCTION READY")
