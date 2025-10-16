"""
VERITAS API - OpenAPI/Swagger Specification Generator
=====================================================

Comprehensive OpenAPI 3.1.0 specification for the VERITAS Framework API.
Includes all endpoints, schemas, authentication, and examples.

Features:
- Complete API documentation
- All endpoints with request/response schemas
- Authentication flows (JWT, API Keys, OAuth)
- WebSocket protocol documentation
- Interactive Swagger UI
- ReDoc documentation
- Code examples (Python, JavaScript, cURL)

Created: 2025-10-08
Version: 1.0.0
"""

from typing import Dict, Any, List, Optional
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


def get_veritas_openapi_schema(app: FastAPI) -> Dict[str, Any]:
    """
    Generate complete OpenAPI schema for VERITAS API.
    
    Args:
        app: FastAPI application instance
        
    Returns:
        Complete OpenAPI 3.1.0 specification
    """
    
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="VERITAS Framework API",
        version="1.0.0",
        description=_get_api_description(),
        routes=app.routes,
        tags=_get_tags_metadata(),
        servers=_get_servers(),
    )
    
    # Add custom components
    openapi_schema["components"] = {
        **openapi_schema.get("components", {}),
        **_get_security_schemes(),
        **_get_response_schemas(),
        **_get_example_schemas(),
    }
    
    # Add security requirements
    openapi_schema["security"] = _get_global_security()
    
    # Add webhooks (WebSocket documentation)
    openapi_schema["webhooks"] = _get_webhooks()
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


def _get_api_description() -> str:
    """Get detailed API description with features and usage."""
    return """
# VERITAS Framework API

**Version:** 1.0.0  
**Environment:** Production  
**Base URL:** https://api.veritas.example.com

---

## Overview

The VERITAS (Versatile Evidence-based Research and Intelligence Analysis System) Framework API 
provides a comprehensive set of endpoints for:

- **Agent Orchestration**: Multi-agent execution with quality gates
- **RAG (Retrieval-Augmented Generation)**: Context-aware document retrieval and generation
- **Quality Management**: Chunk quality assessment and optimization
- **Streaming**: Real-time WebSocket streaming for agent execution
- **Monitoring**: Prometheus metrics and health checks
- **Authentication**: JWT-based auth with RBAC and API keys

---

## Key Features

✅ **Agent Orchestration**
- Multi-agent execution plans
- Quality gate validation
- Parallel and sequential execution
- Real-time progress streaming

✅ **Quality Management**
- Chunk quality scoring (0-1 scale)
- Reranking and optimization
- Metrics tracking and reporting

✅ **Security**
- JWT authentication (HS256/RS256)
- Role-based access control (RBAC)
- API key management
- Rate limiting

✅ **Monitoring**
- Prometheus metrics export
- Health check endpoints
- Performance tracking
- Agent status monitoring

✅ **Streaming**
- WebSocket real-time updates
- Agent execution progress
- Quality gate events
- Metrics streaming

---

## Quick Start

### 1. Authentication

```bash
# Login to get JWT token
curl -X POST https://api.veritas.example.com/auth/login \\
  -H "Content-Type: application/json" \\
  -d '{"username": "user@example.com", "password": "your-password"}'

# Response
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### 2. Execute Agent Plan

```bash
# Execute agent orchestration plan
curl -X POST https://api.veritas.example.com/agents/execute \\
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "plan_id": "plan_001",
    "agents": ["financial", "environmental"],
    "streaming": true
  }'
```

### 3. WebSocket Streaming

```javascript
// Connect to WebSocket for real-time updates
const ws = new WebSocket('wss://api.veritas.example.com/api/v1/streaming/ws/client123?plan_id=plan_001');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Event:', data.type, data);
};
```

---

## Rate Limiting

All API endpoints are rate-limited:

- **Anonymous**: 100 requests / 60 seconds
- **Authenticated**: 1000 requests / 60 seconds
- **Premium**: 10000 requests / 60 seconds

Rate limit headers are included in all responses:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Requests remaining
- `X-RateLimit-Reset`: Time when limit resets (Unix timestamp)

---

## Error Handling

All errors follow a consistent format:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": {
      "field": "plan_id",
      "reason": "Plan ID is required"
    },
    "timestamp": "2025-10-08T14:30:00Z",
    "request_id": "req_abc123"
  }
}
```

Common error codes:
- `AUTHENTICATION_FAILED`: Invalid credentials or token
- `AUTHORIZATION_DENIED`: Insufficient permissions
- `VALIDATION_ERROR`: Invalid request parameters
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `RESOURCE_NOT_FOUND`: Requested resource doesn't exist
- `INTERNAL_ERROR`: Server-side error

---

## Support

- **Documentation**: https://docs.veritas.example.com
- **GitHub**: https://github.com/veritas/framework
- **Email**: support@veritas.example.com
- **Status**: https://status.veritas.example.com

---

## License

MIT License - See LICENSE file for details
"""


def _get_tags_metadata() -> List[Dict[str, Any]]:
    """Get tags metadata for endpoint organization."""
    return [
        {
            "name": "Authentication",
            "description": "User authentication and token management (JWT, OAuth, API keys)",
            "externalDocs": {
                "description": "Authentication Guide",
                "url": "https://docs.veritas.example.com/auth"
            }
        },
        {
            "name": "Agents",
            "description": "Agent orchestration and execution endpoints",
            "externalDocs": {
                "description": "Agent System Documentation",
                "url": "https://docs.veritas.example.com/agents"
            }
        },
        {
            "name": "RAG",
            "description": "Retrieval-Augmented Generation endpoints for context-aware queries",
        },
        {
            "name": "Quality",
            "description": "Quality management, chunk scoring, and optimization endpoints",
        },
        {
            "name": "Streaming",
            "description": "WebSocket streaming for real-time updates and agent progress",
        },
        {
            "name": "Monitoring",
            "description": "Health checks, metrics, and system status endpoints",
        },
        {
            "name": "System",
            "description": "System configuration and management endpoints",
        },
        {
            "name": "Workers",
            "description": "Worker management and configuration endpoints",
        },
    ]


def _get_servers() -> List[Dict[str, Any]]:
    """Get server configurations for different environments."""
    return [
        {
            "url": "https://api.veritas.example.com",
            "description": "Production Server",
        },
        {
            "url": "https://staging-api.veritas.example.com",
            "description": "Staging Server",
        },
        {
            "url": "http://localhost:8000",
            "description": "Local Development Server",
        },
    ]


def _get_security_schemes() -> Dict[str, Any]:
    """Get security scheme definitions."""
    return {
        "securitySchemes": {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "JWT token obtained from /auth/login endpoint. Include in Authorization header as 'Bearer {token}'",
            },
            "ApiKeyAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key",
                "description": "API key for service-to-service authentication. Obtain from /auth/api-keys endpoint",
            },
            "OAuth2": {
                "type": "oauth2",
                "flows": {
                    "authorizationCode": {
                        "authorizationUrl": "https://api.veritas.example.com/oauth/authorize",
                        "tokenUrl": "https://api.veritas.example.com/oauth/token",
                        "refreshUrl": "https://api.veritas.example.com/oauth/refresh",
                        "scopes": {
                            "read": "Read access to resources",
                            "write": "Write access to resources",
                            "admin": "Administrative access",
                            "agents:execute": "Execute agent plans",
                            "agents:manage": "Manage agent configurations",
                            "quality:read": "Read quality metrics",
                            "quality:write": "Update quality settings",
                            "monitoring:read": "Read monitoring data",
                        }
                    }
                },
                "description": "OAuth 2.0 authorization code flow for third-party integrations",
            },
        }
    }


def _get_response_schemas() -> Dict[str, Any]:
    """Get common response schemas."""
    return {
        "schemas": {
            "Error": {
                "type": "object",
                "properties": {
                    "error": {
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "Error code",
                                "example": "VALIDATION_ERROR"
                            },
                            "message": {
                                "type": "string",
                                "description": "Human-readable error message",
                                "example": "Invalid request parameters"
                            },
                            "details": {
                                "type": "object",
                                "description": "Additional error details",
                                "additionalProperties": True
                            },
                            "timestamp": {
                                "type": "string",
                                "format": "date-time",
                                "description": "Error timestamp (ISO 8601)",
                                "example": "2025-10-08T14:30:00Z"
                            },
                            "request_id": {
                                "type": "string",
                                "description": "Unique request identifier for tracking",
                                "example": "req_abc123xyz"
                            }
                        },
                        "required": ["code", "message", "timestamp"]
                    }
                },
                "required": ["error"]
            },
            "HealthCheck": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["healthy", "degraded", "unhealthy"],
                        "description": "Overall health status",
                        "example": "healthy"
                    },
                    "version": {
                        "type": "string",
                        "description": "API version",
                        "example": "1.0.0"
                    },
                    "timestamp": {
                        "type": "string",
                        "format": "date-time",
                        "example": "2025-10-08T14:30:00Z"
                    },
                    "checks": {
                        "type": "object",
                        "description": "Individual component health checks",
                        "properties": {
                            "database": {"type": "boolean"},
                            "redis": {"type": "boolean"},
                            "ollama": {"type": "boolean"},
                            "agents": {"type": "boolean"}
                        }
                    },
                    "metrics": {
                        "type": "object",
                        "description": "Health metrics",
                        "properties": {
                            "uptime_seconds": {"type": "number"},
                            "request_count": {"type": "integer"},
                            "error_rate": {"type": "number"}
                        }
                    }
                },
                "required": ["status", "version", "timestamp"]
            },
            "AgentExecutionPlan": {
                "type": "object",
                "properties": {
                    "plan_id": {
                        "type": "string",
                        "description": "Unique plan identifier",
                        "example": "plan_001"
                    },
                    "agents": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of agent types to execute",
                        "example": ["financial", "environmental", "social"]
                    },
                    "query": {
                        "type": "string",
                        "description": "User query or task description",
                        "example": "Analyze sustainability impact"
                    },
                    "context": {
                        "type": "object",
                        "description": "Additional context for execution",
                        "additionalProperties": True
                    },
                    "streaming": {
                        "type": "boolean",
                        "description": "Enable real-time streaming",
                        "default": False
                    },
                    "quality_gates": {
                        "type": "object",
                        "description": "Quality gate thresholds",
                        "properties": {
                            "min_score": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 1,
                                "default": 0.6
                            },
                            "require_review": {"type": "boolean", "default": False}
                        }
                    }
                },
                "required": ["plan_id", "agents", "query"]
            },
            "AgentExecutionResult": {
                "type": "object",
                "properties": {
                    "plan_id": {"type": "string"},
                    "status": {
                        "type": "string",
                        "enum": ["pending", "running", "completed", "failed", "cancelled"],
                        "example": "completed"
                    },
                    "result": {
                        "type": "object",
                        "description": "Execution results",
                        "additionalProperties": True
                    },
                    "agents": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "agent_id": {"type": "string"},
                                "agent_type": {"type": "string"},
                                "status": {"type": "string"},
                                "result": {"type": "object"}
                            }
                        }
                    },
                    "quality_score": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 1,
                        "description": "Overall quality score"
                    },
                    "execution_time": {
                        "type": "number",
                        "description": "Execution time in seconds"
                    },
                    "created_at": {"type": "string", "format": "date-time"},
                    "completed_at": {"type": "string", "format": "date-time"}
                },
                "required": ["plan_id", "status"]
            },
            "StreamEvent": {
                "type": "object",
                "properties": {
                    "event_type": {
                        "type": "string",
                        "enum": [
                            "PLAN_STARTED",
                            "PLAN_COMPLETED",
                            "PLAN_FAILED",
                            "STEP_STARTED",
                            "STEP_COMPLETED",
                            "STEP_FAILED",
                            "QUALITY_CHECK",
                            "REVIEW_REQUIRED",
                            "METRICS_UPDATE",
                            "LOG_MESSAGE"
                        ],
                        "example": "STEP_COMPLETED"
                    },
                    "plan_id": {"type": "string"},
                    "step_id": {"type": "string", "nullable": True},
                    "agent_id": {"type": "string", "nullable": True},
                    "timestamp": {"type": "string", "format": "date-time"},
                    "data": {
                        "type": "object",
                        "description": "Event-specific data",
                        "additionalProperties": True
                    },
                    "message": {"type": "string", "nullable": True}
                },
                "required": ["event_type", "plan_id", "timestamp"]
            },
            "QualityScore": {
                "type": "object",
                "properties": {
                    "score": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 1,
                        "description": "Quality score (0-1)",
                        "example": 0.85
                    },
                    "metrics": {
                        "type": "object",
                        "properties": {
                            "relevance": {"type": "number"},
                            "coherence": {"type": "number"},
                            "completeness": {"type": "number"},
                            "accuracy": {"type": "number"}
                        }
                    },
                    "passed": {
                        "type": "boolean",
                        "description": "Whether quality gate passed"
                    },
                    "threshold": {
                        "type": "number",
                        "description": "Quality gate threshold"
                    }
                },
                "required": ["score", "passed"]
            },
            "MetricsSnapshot": {
                "type": "object",
                "properties": {
                    "timestamp": {"type": "string", "format": "date-time"},
                    "agent_metrics": {
                        "type": "object",
                        "additionalProperties": {
                            "type": "object",
                            "properties": {
                                "total_executions": {"type": "integer"},
                                "successful_executions": {"type": "integer"},
                                "failed_executions": {"type": "integer"},
                                "average_duration": {"type": "number"},
                                "average_quality": {"type": "number"}
                            }
                        }
                    },
                    "system_metrics": {
                        "type": "object",
                        "properties": {
                            "cpu_usage": {"type": "number"},
                            "memory_usage": {"type": "number"},
                            "active_agents": {"type": "integer"},
                            "queue_length": {"type": "integer"}
                        }
                    }
                },
                "required": ["timestamp"]
            }
        }
    }


def _get_example_schemas() -> Dict[str, Any]:
    """Get example request/response schemas."""
    return {
        "examples": {
            "LoginRequest": {
                "summary": "Login with credentials",
                "value": {
                    "username": "user@example.com",
                    "password": "your-secure-password"
                }
            },
            "LoginResponse": {
                "summary": "Successful login",
                "value": {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyQGV4YW1wbGUuY29tIiwicm9sZSI6InVzZXIiLCJleHAiOjE3MjgzOTYwMDB9.abc123",
                    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyQGV4YW1wbGUuY29tIiwidHlwZSI6InJlZnJlc2giLCJleHAiOjE3MzA5ODgwMDB9.xyz789",
                    "token_type": "bearer",
                    "expires_in": 3600,
                    "user": {
                        "id": "user_123",
                        "username": "user@example.com",
                        "role": "user",
                        "permissions": ["read", "write"]
                    }
                }
            },
            "AgentExecutionRequest": {
                "summary": "Execute multi-agent plan",
                "value": {
                    "plan_id": "plan_sustainability_001",
                    "agents": ["financial", "environmental", "social"],
                    "query": "Analyze the sustainability impact of renewable energy investments",
                    "context": {
                        "company": "Green Energy Corp",
                        "year": 2025,
                        "focus_areas": ["carbon_emissions", "roi", "community_impact"]
                    },
                    "streaming": True,
                    "quality_gates": {
                        "min_score": 0.7,
                        "require_review": False
                    }
                }
            },
            "AgentExecutionResponse": {
                "summary": "Execution result",
                "value": {
                    "plan_id": "plan_sustainability_001",
                    "status": "completed",
                    "result": {
                        "summary": "Comprehensive sustainability analysis completed",
                        "findings": {
                            "financial": {
                                "roi": 0.15,
                                "payback_period": 7.2,
                                "risk_level": "moderate"
                            },
                            "environmental": {
                                "carbon_reduction": 45000,
                                "renewable_percentage": 85,
                                "impact_score": 0.92
                            },
                            "social": {
                                "jobs_created": 150,
                                "community_benefit": 0.88,
                                "public_support": 0.76
                            }
                        }
                    },
                    "agents": [
                        {
                            "agent_id": "fin_001",
                            "agent_type": "financial",
                            "status": "completed",
                            "quality_score": 0.89
                        },
                        {
                            "agent_id": "env_001",
                            "agent_type": "environmental",
                            "status": "completed",
                            "quality_score": 0.92
                        },
                        {
                            "agent_id": "soc_001",
                            "agent_type": "social",
                            "status": "completed",
                            "quality_score": 0.78
                        }
                    ],
                    "quality_score": 0.86,
                    "execution_time": 12.45,
                    "created_at": "2025-10-08T14:30:00Z",
                    "completed_at": "2025-10-08T14:30:12Z"
                }
            },
            "StreamEventExample": {
                "summary": "WebSocket stream event",
                "value": {
                    "event_type": "STEP_COMPLETED",
                    "plan_id": "plan_sustainability_001",
                    "step_id": "step_financial_analysis",
                    "agent_id": "fin_001",
                    "timestamp": "2025-10-08T14:30:05Z",
                    "data": {
                        "result": {
                            "roi": 0.15,
                            "confidence": 0.89
                        },
                        "quality_score": 0.89,
                        "duration": 5.2
                    },
                    "message": "Financial analysis completed successfully"
                }
            },
            "HealthCheckResponse": {
                "summary": "Healthy system",
                "value": {
                    "status": "healthy",
                    "version": "1.0.0",
                    "timestamp": "2025-10-08T14:30:00Z",
                    "checks": {
                        "database": True,
                        "redis": True,
                        "ollama": True,
                        "agents": True
                    },
                    "metrics": {
                        "uptime_seconds": 86400,
                        "request_count": 15420,
                        "error_rate": 0.002
                    }
                }
            },
            "ErrorResponse": {
                "summary": "Validation error",
                "value": {
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Invalid request parameters",
                        "details": {
                            "field": "agents",
                            "reason": "At least one agent must be specified"
                        },
                        "timestamp": "2025-10-08T14:30:00Z",
                        "request_id": "req_abc123xyz"
                    }
                }
            }
        }
    }


def _get_global_security() -> List[Dict[str, List[str]]]:
    """Get global security requirements."""
    return [
        {"BearerAuth": []},
        {"ApiKeyAuth": []},
    ]


def _get_webhooks() -> Dict[str, Any]:
    """Get WebSocket protocol documentation as webhooks."""
    return {
        "agentExecutionStream": {
            "post": {
                "summary": "WebSocket: Agent Execution Stream",
                "description": """
Real-time WebSocket streaming for agent execution progress.

**Connection URL:**
```
wss://api.veritas.example.com/api/v1/streaming/ws/{client_id}?plan_id={plan_id}
```

**Event Types:**
- `PLAN_STARTED`: Execution plan started
- `PLAN_COMPLETED`: Execution plan completed
- `PLAN_FAILED`: Execution plan failed
- `STEP_STARTED`: Step started
- `STEP_COMPLETED`: Step completed  
- `STEP_FAILED`: Step failed
- `QUALITY_CHECK`: Quality gate check
- `REVIEW_REQUIRED`: Manual review required
- `METRICS_UPDATE`: Metrics update
- `LOG_MESSAGE`: Log message

**Example Client (JavaScript):**
```javascript
const ws = new WebSocket('wss://api.veritas.example.com/api/v1/streaming/ws/client123?plan_id=plan_001');

ws.onopen = () => {
  console.log('Connected to execution stream');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(`Event: ${data.event_type}`, data);
  
  switch(data.event_type) {
    case 'STEP_COMPLETED':
      console.log(`Step ${data.step_id} completed`);
      break;
    case 'QUALITY_CHECK':
      console.log(`Quality score: ${data.data.score}`);
      break;
    case 'PLAN_COMPLETED':
      console.log('Execution completed!');
      ws.close();
      break;
  }
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('Connection closed');
};
```

**Example Client (Python):**
```python
import asyncio
import websockets
import json

async def stream_execution():
    uri = "wss://api.veritas.example.com/api/v1/streaming/ws/client123?plan_id=plan_001"
    
    async with websockets.connect(uri) as websocket:
        print("Connected to execution stream")
        
        async for message in websocket:
            data = json.loads(message)
            print(f"Event: {data['event_type']}", data)
            
            if data['event_type'] == 'PLAN_COMPLETED':
                print("Execution completed!")
                break

asyncio.run(stream_execution())
```
                """,
                "requestBody": {
                    "description": "No request body - connection via WebSocket URL",
                    "required": False
                },
                "responses": {
                    "200": {
                        "description": "Stream event",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/StreamEvent"},
                                "examples": {
                                    "stepCompleted": {"$ref": "#/components/examples/StreamEventExample"}
                                }
                            }
                        }
                    }
                }
            }
        }
    }


def customize_openapi(app: FastAPI):
    """
    Customize FastAPI app with enhanced OpenAPI documentation.
    
    Args:
        app: FastAPI application instance
    """
    
    def custom_openapi():
        return get_veritas_openapi_schema(app)
    
    app.openapi = custom_openapi
    
    # Customize Swagger UI
    app.swagger_ui_init_oauth = {
        "clientId": "veritas-swagger-ui",
        "appName": "VERITAS API Explorer",
        "usePkceWithAuthorizationCodeGrant": True,
    }
    
    return app


# Example usage
if __name__ == "__main__":
    from fastapi import FastAPI
    
    app = FastAPI()
    
    # Add some example endpoints
    @app.get("/health", tags=["Monitoring"])
    async def health():
        return {"status": "healthy"}
    
    @app.post("/agents/execute", tags=["Agents"])
    async def execute_agents():
        return {"status": "executing"}
    
    # Customize OpenAPI
    customize_openapi(app)
    
    # Generate schema
    schema = get_veritas_openapi_schema(app)
    
    print("OpenAPI Schema Generated:")
    print(f"- Title: {schema['info']['title']}")
    print(f"- Version: {schema['info']['version']}")
    print(f"- Servers: {len(schema['servers'])}")
    print(f"- Security Schemes: {len(schema['components']['securitySchemes'])}")
    print(f"- Schemas: {len(schema['components']['schemas'])}")
    print(f"- Examples: {len(schema['components']['examples'])}")
    print("\n✅ OpenAPI schema ready for Swagger UI and ReDoc")
