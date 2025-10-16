# VERITAS API - Authentication Guide

**Version:** 1.0.0  
**Last Updated:** 2025-10-08  
**Status:** Production Ready

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication Methods](#authentication-methods)
3. [JWT Token Authentication](#jwt-token-authentication)
4. [API Key Authentication](#api-key-authentication)
5. [OAuth 2.0 Integration](#oauth-20-integration)
6. [Role-Based Access Control (RBAC)](#role-based-access-control-rbac)
7. [Code Examples](#code-examples)
8. [Security Best Practices](#security-best-practices)
9. [Troubleshooting](#troubleshooting)

---

## Overview

The VERITAS API supports three authentication methods:

1. **JWT (JSON Web Tokens)** - Primary method for user authentication
2. **API Keys** - For service-to-service authentication
3. **OAuth 2.0** - For third-party integrations

All authenticated requests must include credentials in the request headers. Unauthenticated requests are rate-limited to 100 requests per minute.

---

## Authentication Methods

### Comparison

| Method | Use Case | Expiration | Renewal |
|--------|----------|------------|---------|
| **JWT** | User authentication | 1 hour (access), 30 days (refresh) | Automatic via refresh token |
| **API Key** | Service-to-service | 1 year (configurable) | Manual regeneration |
| **OAuth 2.0** | Third-party apps | Varies by flow | Token refresh endpoint |

---

## JWT Token Authentication

### How It Works

1. User logs in with credentials (username/email + password)
2. Server validates credentials and returns JWT tokens
3. Client includes access token in subsequent requests
4. When access token expires, use refresh token to get new tokens
5. When refresh token expires, user must log in again

### Token Structure

**Access Token:**
```json
{
  "alg": "HS256",
  "typ": "JWT"
}
{
  "sub": "user@example.com",
  "user_id": "user_123",
  "role": "user",
  "permissions": ["read", "write", "agents:execute"],
  "exp": 1728396000,
  "iat": 1728392400,
  "jti": "token_abc123"
}
```

**Refresh Token:**
```json
{
  "alg": "HS256",
  "typ": "JWT"
}
{
  "sub": "user@example.com",
  "user_id": "user_123",
  "type": "refresh",
  "exp": 1730988000,
  "iat": 1728392400,
  "jti": "refresh_xyz789"
}
```

### Login Endpoint

**POST** `/auth/login`

**Request:**
```json
{
  "username": "user@example.com",
  "password": "your-secure-password"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "user_123",
    "username": "user@example.com",
    "email": "user@example.com",
    "role": "user",
    "permissions": ["read", "write", "agents:execute"],
    "created_at": "2025-01-01T00:00:00Z"
  }
}
```

**Error Response (401 Unauthorized):**
```json
{
  "error": {
    "code": "AUTHENTICATION_FAILED",
    "message": "Invalid username or password",
    "timestamp": "2025-10-08T14:30:00Z",
    "request_id": "req_abc123"
  }
}
```

### Using Access Tokens

Include the access token in the `Authorization` header:

```http
GET /agents/status HTTP/1.1
Host: api.veritas.example.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Refresh Tokens

**POST** `/auth/refresh`

**Request:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### Logout

**POST** `/auth/logout`

**Headers:**
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200 OK):**
```json
{
  "message": "Successfully logged out",
  "timestamp": "2025-10-08T14:30:00Z"
}
```

---

## API Key Authentication

### Overview

API keys are designed for:
- Service-to-service authentication
- Automated scripts and cron jobs
- Long-lived integrations
- Applications without interactive users

### Creating API Keys

**POST** `/auth/api-keys`

**Headers:**
```http
Authorization: Bearer YOUR_JWT_TOKEN
```

**Request:**
```json
{
  "name": "Production Server Integration",
  "description": "API key for production backend service",
  "permissions": ["read", "write", "agents:execute"],
  "expires_in_days": 365
}
```

**Response (201 Created):**
```json
{
  "api_key": "vrt_live_abc123xyz789...",
  "key_id": "key_001",
  "name": "Production Server Integration",
  "permissions": ["read", "write", "agents:execute"],
  "created_at": "2025-10-08T14:30:00Z",
  "expires_at": "2026-10-08T14:30:00Z",
  "last_used": null
}
```

⚠️ **Important:** The full API key is only shown once at creation time. Store it securely!

### Using API Keys

Include the API key in the `X-API-Key` header:

```http
GET /agents/status HTTP/1.1
Host: api.veritas.example.com
X-API-Key: vrt_live_abc123xyz789...
```

### Managing API Keys

**List API Keys:**
```http
GET /auth/api-keys
Authorization: Bearer YOUR_JWT_TOKEN
```

**Response:**
```json
{
  "api_keys": [
    {
      "key_id": "key_001",
      "name": "Production Server Integration",
      "permissions": ["read", "write", "agents:execute"],
      "created_at": "2025-10-08T14:30:00Z",
      "expires_at": "2026-10-08T14:30:00Z",
      "last_used": "2025-10-08T15:45:00Z"
    }
  ],
  "total": 1
}
```

**Revoke API Key:**
```http
DELETE /auth/api-keys/{key_id}
Authorization: Bearer YOUR_JWT_TOKEN
```

**Response:**
```json
{
  "message": "API key revoked successfully",
  "key_id": "key_001"
}
```

### API Key Security

- **Prefix:** All API keys start with `vrt_live_` (production) or `vrt_test_` (testing)
- **Storage:** Keys are hashed (SHA-256) before storage
- **Rotation:** Recommended rotation every 90 days
- **Scoping:** Keys can be scoped to specific permissions
- **Monitoring:** All API key usage is logged and audited

---

## OAuth 2.0 Integration

### Overview

OAuth 2.0 is used for third-party application integrations. VERITAS supports the **Authorization Code Flow** with PKCE.

### Authorization Code Flow

#### Step 1: Authorization Request

Redirect user to authorization endpoint:

```http
GET /oauth/authorize?
  response_type=code&
  client_id=YOUR_CLIENT_ID&
  redirect_uri=https://yourapp.com/callback&
  scope=read write agents:execute&
  state=random_state_string&
  code_challenge=BASE64URL(SHA256(code_verifier))&
  code_challenge_method=S256
```

**Parameters:**
- `response_type`: Always `code`
- `client_id`: Your application's client ID
- `redirect_uri`: Where to redirect after authorization
- `scope`: Space-separated list of requested permissions
- `state`: Random string to prevent CSRF attacks
- `code_challenge`: SHA-256 hash of code verifier (PKCE)
- `code_challenge_method`: Always `S256`

#### Step 2: User Authorization

User logs in and authorizes your application. They are redirected to:

```
https://yourapp.com/callback?
  code=AUTH_CODE&
  state=random_state_string
```

#### Step 3: Token Exchange

Exchange authorization code for access token:

**POST** `/oauth/token`

**Request:**
```http
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code&
code=AUTH_CODE&
client_id=YOUR_CLIENT_ID&
redirect_uri=https://yourapp.com/callback&
code_verifier=ORIGINAL_CODE_VERIFIER
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "scope": "read write agents:execute"
}
```

#### Step 4: Refresh Token

**POST** `/oauth/refresh`

**Request:**
```http
Content-Type: application/x-www-form-urlencoded

grant_type=refresh_token&
refresh_token=REFRESH_TOKEN&
client_id=YOUR_CLIENT_ID
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### Registering OAuth Applications

**POST** `/oauth/apps`

**Headers:**
```http
Authorization: Bearer YOUR_JWT_TOKEN
```

**Request:**
```json
{
  "name": "My Application",
  "redirect_uris": [
    "https://myapp.com/callback",
    "https://myapp.com/oauth/callback"
  ],
  "scopes": ["read", "write", "agents:execute"],
  "description": "My awesome integration with VERITAS"
}
```

**Response:**
```json
{
  "client_id": "app_abc123",
  "client_secret": "secret_xyz789",
  "name": "My Application",
  "redirect_uris": ["https://myapp.com/callback"],
  "scopes": ["read", "write", "agents:execute"],
  "created_at": "2025-10-08T14:30:00Z"
}
```

---

## Role-Based Access Control (RBAC)

### Roles

| Role | Description | Default Permissions |
|------|-------------|---------------------|
| **admin** | Full system access | All permissions |
| **manager** | Manage agents and quality | read, write, agents:*, quality:* |
| **user** | Standard user | read, write, agents:execute |
| **viewer** | Read-only access | read |

### Permissions

| Permission | Description | Required Role |
|------------|-------------|---------------|
| `read` | Read resources | All roles |
| `write` | Create/update resources | user, manager, admin |
| `delete` | Delete resources | manager, admin |
| `agents:execute` | Execute agent plans | user, manager, admin |
| `agents:manage` | Manage agent configurations | manager, admin |
| `quality:read` | Read quality metrics | All roles |
| `quality:write` | Update quality settings | manager, admin |
| `monitoring:read` | Read monitoring data | All roles |
| `monitoring:write` | Update monitoring configs | admin |
| `users:manage` | Manage users | admin |
| `system:admin` | System administration | admin |

### Permission Checking

Permissions are checked automatically for protected endpoints:

```python
from fastapi import Depends
from backend.api.security import require_permission

@app.post("/agents/execute")
async def execute_agents(
    user: User = Depends(require_permission("agents:execute"))
):
    # Only users with agents:execute permission can access
    ...
```

### Custom Roles

Create custom roles via the API:

**POST** `/auth/roles`

**Request:**
```json
{
  "name": "analyst",
  "description": "Data analyst role",
  "permissions": [
    "read",
    "agents:execute",
    "quality:read",
    "monitoring:read"
  ]
}
```

---

## Code Examples

### Python

#### Login and Execute Agent Plan

```python
import requests

# Configuration
API_BASE = "https://api.veritas.example.com"
USERNAME = "user@example.com"
PASSWORD = "your-password"

# 1. Login
login_response = requests.post(
    f"{API_BASE}/auth/login",
    json={"username": USERNAME, "password": PASSWORD}
)
login_response.raise_for_status()
tokens = login_response.json()

access_token = tokens["access_token"]
refresh_token = tokens["refresh_token"]

# 2. Create headers with token
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

# 3. Execute agent plan
plan_request = {
    "plan_id": "plan_001",
    "agents": ["financial", "environmental"],
    "query": "Analyze sustainability impact",
    "streaming": False
}

execute_response = requests.post(
    f"{API_BASE}/agents/execute",
    json=plan_request,
    headers=headers
)
execute_response.raise_for_status()
result = execute_response.json()

print(f"Plan Status: {result['status']}")
print(f"Quality Score: {result['quality_score']}")

# 4. Refresh token when needed
def refresh_access_token(refresh_token):
    response = requests.post(
        f"{API_BASE}/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    response.raise_for_status()
    return response.json()["access_token"]
```

#### Using API Keys

```python
import requests

API_BASE = "https://api.veritas.example.com"
API_KEY = "vrt_live_abc123xyz789..."

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# Execute agent plan with API key
response = requests.post(
    f"{API_BASE}/agents/execute",
    json={
        "plan_id": "plan_002",
        "agents": ["social"],
        "query": "Community impact analysis"
    },
    headers=headers
)

print(response.json())
```

### JavaScript/TypeScript

#### Login and Token Management

```javascript
const API_BASE = 'https://api.veritas.example.com';

class VeritasClient {
  constructor() {
    this.accessToken = null;
    this.refreshToken = null;
  }

  async login(username, password) {
    const response = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });

    if (!response.ok) {
      throw new Error(`Login failed: ${response.statusText}`);
    }

    const data = await response.json();
    this.accessToken = data.access_token;
    this.refreshToken = data.refresh_token;

    return data.user;
  }

  async refreshAccessToken() {
    const response = await fetch(`${API_BASE}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: this.refreshToken })
    });

    if (!response.ok) {
      throw new Error('Token refresh failed');
    }

    const data = await response.json();
    this.accessToken = data.access_token;
  }

  async request(endpoint, options = {}) {
    const headers = {
      'Authorization': `Bearer ${this.accessToken}`,
      'Content-Type': 'application/json',
      ...options.headers
    };

    let response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers
    });

    // Auto-refresh on 401
    if (response.status === 401) {
      await this.refreshAccessToken();
      headers['Authorization'] = `Bearer ${this.accessToken}`;
      response = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers
      });
    }

    if (!response.ok) {
      throw new Error(`Request failed: ${response.statusText}`);
    }

    return response.json();
  }

  async executeAgents(planRequest) {
    return this.request('/agents/execute', {
      method: 'POST',
      body: JSON.stringify(planRequest)
    });
  }
}

// Usage
const client = new VeritasClient();

async function main() {
  // Login
  const user = await client.login('user@example.com', 'password');
  console.log('Logged in as:', user.username);

  // Execute agents
  const result = await client.executeAgents({
    plan_id: 'plan_003',
    agents: ['financial', 'environmental'],
    query: 'Sustainability analysis',
    streaming: false
  });

  console.log('Execution result:', result);
}

main().catch(console.error);
```

### cURL

#### Login

```bash
curl -X POST https://api.veritas.example.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "user@example.com",
    "password": "your-password"
  }'
```

#### Execute with JWT

```bash
# Save token to variable
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Execute agent plan
curl -X POST https://api.veritas.example.com/agents/execute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "plan_id": "plan_004",
    "agents": ["financial"],
    "query": "Financial analysis"
  }'
```

#### Execute with API Key

```bash
curl -X POST https://api.veritas.example.com/agents/execute \
  -H "X-API-Key: vrt_live_abc123xyz789..." \
  -H "Content-Type: application/json" \
  -d '{
    "plan_id": "plan_005",
    "agents": ["social"],
    "query": "Social impact"
  }'
```

---

## Security Best Practices

### 1. Token Storage

**❌ Don't:**
- Store tokens in localStorage (XSS vulnerable)
- Include tokens in URL parameters
- Log tokens to console or files

**✅ Do:**
- Use httpOnly cookies for web applications
- Store in memory for single-page apps
- Use secure storage (Keychain, Keystore) for mobile apps

### 2. Token Rotation

- Rotate access tokens every 1 hour
- Rotate refresh tokens every 30 days
- Rotate API keys every 90 days

### 3. HTTPS Only

- Always use HTTPS in production
- Never send credentials over HTTP
- Implement HSTS headers

### 4. Rate Limiting

Respect rate limits to avoid throttling:
```python
import time

def make_request_with_retry(url, headers, max_retries=3):
    for attempt in range(max_retries):
        response = requests.get(url, headers=headers)
        
        if response.status_code == 429:  # Rate limited
            retry_after = int(response.headers.get('Retry-After', 60))
            time.sleep(retry_after)
            continue
        
        return response
    
    raise Exception("Max retries exceeded")
```

### 5. Secret Management

- Never commit credentials to version control
- Use environment variables or secret managers
- Rotate secrets regularly

```bash
# .env file (never commit!)
VERITAS_API_KEY=vrt_live_abc123...
VERITAS_USERNAME=user@example.com
VERITAS_PASSWORD=secure-password
```

### 6. Error Handling

Don't expose sensitive information in error messages:

```python
try:
    response = requests.post(API_URL, headers=headers)
    response.raise_for_status()
except requests.exceptions.HTTPError as e:
    # Log full error internally
    logger.error(f"API error: {e}")
    
    # Return generic error to user
    return {"error": "An error occurred"}
```

---

## Troubleshooting

### "Invalid token" (401 Unauthorized)

**Possible causes:**
1. Token expired
2. Token malformed
3. Invalid signature

**Solution:**
```python
# Check token expiration
import jwt

try:
    decoded = jwt.decode(
        access_token,
        options={"verify_signature": False}
    )
    print(f"Token expires at: {decoded['exp']}")
except jwt.DecodeError:
    print("Invalid token format")

# Refresh token if expired
if token_expired:
    new_token = refresh_access_token(refresh_token)
```

### "Insufficient permissions" (403 Forbidden)

**Possible causes:**
1. User role doesn't have required permission
2. API key doesn't have required scope

**Solution:**
```bash
# Check current permissions
curl https://api.veritas.example.com/auth/me \
  -H "Authorization: Bearer $TOKEN"

# Response shows your permissions
{
  "user_id": "user_123",
  "role": "user",
  "permissions": ["read", "write"]  # Missing "agents:execute"
}
```

Contact admin to upgrade your role or create a new API key with required scopes.

### "Rate limit exceeded" (429 Too Many Requests)

**Solution:**
```python
import time

# Implement exponential backoff
def make_request_with_backoff(url, headers):
    max_retries = 5
    base_delay = 1
    
    for attempt in range(max_retries):
        response = requests.get(url, headers=headers)
        
        if response.status_code != 429:
            return response
        
        # Exponential backoff
        delay = base_delay * (2 ** attempt)
        print(f"Rate limited. Waiting {delay}s...")
        time.sleep(delay)
    
    raise Exception("Max retries exceeded")
```

### Token Refresh Loop

If you're stuck in a refresh loop:

1. **Clear all stored tokens**
2. **Logout and login again**
3. **Check server time sync** (JWT exp/iat timing)

```python
# Force logout and re-login
def reset_authentication():
    # Clear tokens
    access_token = None
    refresh_token = None
    
    # Login fresh
    response = requests.post(
        f"{API_BASE}/auth/login",
        json={"username": USERNAME, "password": PASSWORD}
    )
    
    tokens = response.json()
    return tokens["access_token"], tokens["refresh_token"]
```

---

## Support

For authentication issues:

- **Documentation**: https://docs.veritas.example.com/auth
- **Status Page**: https://status.veritas.example.com
- **Email**: security@veritas.example.com
- **GitHub Issues**: https://github.com/veritas/framework/issues

---

**Last Updated:** 2025-10-08  
**Version:** 1.0.0  
**License:** MIT
