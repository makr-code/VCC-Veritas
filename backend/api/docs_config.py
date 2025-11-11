"""
VERITAS API - Interactive Documentation Configuration
=====================================================

Configure Swagger UI and ReDoc for interactive API exploration.

Features:
- Custom Swagger UI with VERITAS branding
- ReDoc alternative documentation
- OAuth 2.0 integration
- Code examples in multiple languages
- Try-it-out functionality
- Downloadable OpenAPI spec

Created: 2025-10-08
Version: 1.0.0
"""

import json
from typing import Optional

from fastapi import FastAPI
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles


def configure_api_docs(
    app: FastAPI,
    title: str = "VERITAS Framework API",
    description: str = "Comprehensive API for agent orchestration and RAG",
    version: str = "1.0.0",
    docs_url: str = "/docs",
    redoc_url: str = "/redoc",
    openapi_url: str = "/openapi.json",
    enable_oauth: bool = True,
) -> FastAPI:
    """
    Configure interactive API documentation with custom branding.

    Args:
        app: FastAPI application instance
        title: API title
        description: API description
        version: API version
        docs_url: Swagger UI endpoint path
        redoc_url: ReDoc endpoint path
        openapi_url: OpenAPI spec JSON endpoint
        enable_oauth: Enable OAuth 2.0 in Swagger UI

    Returns:
        Configured FastAPI app
    """

    # Update app metadata
    app.title = title
    app.description = description
    app.version = version

    # Custom Swagger UI endpoint
    @app.get(docs_url, include_in_schema=False)
    async def custom_swagger_ui():
        return get_swagger_ui_html(
            openapi_url=openapi_url,
            title=f"{title} - Swagger UI",
            oauth2_redirect_url=f"{docs_url}/oauth2-redirect",
            swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
            swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
            swagger_favicon_url="/static/favicon.ico",
            init_oauth={
                "clientId": "veritas - swagger-ui",
                "appName": "VERITAS API Explorer",
                "usePkceWithAuthorizationCodeGrant": True,
            }
            if enable_oauth
            else None,
            swagger_ui_parameters={
                "deepLinking": True,
                "persistAuthorization": True,
                "displayRequestDuration": True,
                "filter": True,
                "syntaxHighlight.theme": "monokai",
                "tryItOutEnabled": True,
                "defaultModelsExpandDepth": 2,
                "defaultModelExpandDepth": 2,
                "docExpansion": "list",
                "operationsSorter": "alpha",
                "tagsSorter": "alpha",
            },
        )

    # OAuth 2.0 redirect endpoint for Swagger UI
    @app.get(f"{docs_url}/oauth2-redirect", include_in_schema=False)
    async def swagger_ui_redirect():
        return HTMLResponse(
            """
        <!doctype html>
        <html lang="en-US">
        <head>
            <title>Swagger UI: OAuth2 Redirect</title>
        </head>
        <body>
        <script>
            'use strict';
            function run () {
                var oauth2 = window.opener.swaggerUIRedirectOauth2;
                var sentState = oauth2.state;
                var redirectUrl = oauth2.redirectUrl;
                var isValid, qp, arr;

                if ( / code|token|error / .test(window.location.hash)) {
                    qp = window.location.hash.substring(1);
                } else {
                    qp = location.search.substring(1);
                }

                arr = qp.split("&");
                arr.forEach(function (v,i,_arr) { _arr[i] = '"' + v.replace('=', '":"') + '"';});
                qp = qp ? JSON.parse('{' + arr.join() + '}',
                        function (key, value) {
                            return key === "" ? value : decodeURIComponent(value);
                        }
                ) : {};

                isValid = qp.state === sentState;

                if ((
                  oauth2.auth.schema.get("flow") === "accessCode" ||
                  oauth2.auth.schema.get("flow") === "authorizationCode" ||
                  oauth2.auth.schema.get("flow") === "authorization_code"
                ) && !oauth2.auth.code) {
                    if (!isValid) {
                        oauth2.errCb({
                            authId: oauth2.auth.name,
                            source: "auth",
                            level: "warning",
                            message: "Authorization may be unsafe, passed state was changed in server Passed state wasn't returned from auth server"
                        });
                    }

                    if (qp.code) {
                        delete oauth2.state;
                        oauth2.auth.code = qp.code;
                        oauth2.callback({auth: oauth2.auth, redirectUrl: redirectUrl});
                    } else {
                        let oauthErrorMsg;
                        if (qp.error) {
                            oauthErrorMsg = "[" + qp.error+"]: " +
                                (qp.error_description ? qp.error_description+ ". " : "no accessCode received from the server. ") +
                                (qp.error_uri ? "More info: " + qp.error_uri : "");
                        }

                        oauth2.errCb({
                            authId: oauth2.auth.name,
                            source: "auth",
                            level: "error",
                            message: oauthErrorMsg || "[Authorization failed]: no accessCode received from the server"
                        });
                    }
                } else {
                    oauth2.callback({auth: oauth2.auth, token: qp, isValid: isValid, redirectUrl: redirectUrl});
                }
                window.close();
            }

            window.addEventListener('DOMContentLoaded', function () {
              run();
            });
        </script>
        </body>
        </html>
        """
        )

    # Custom ReDoc endpoint
    @app.get(redoc_url, include_in_schema=False)
    async def custom_redoc():
        return get_redoc_html(
            openapi_url=openapi_url,
            title=f"{title} - ReDoc",
            redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js",
            redoc_favicon_url="/static/favicon.ico",
            with_google_fonts=True,
        )

    # OpenAPI JSON endpoint
    @app.get(openapi_url, include_in_schema=False)
    async def get_openapi_json():
        return JSONResponse(app.openapi())

    # Download OpenAPI spec
    @app.get(f"{openapi_url}.yaml", include_in_schema=False)
    async def get_openapi_yaml():
        """Download OpenAPI specification as YAML."""
        try:
            import yaml

            spec = app.openapi()
            yaml_content = yaml.dump(spec, default_flow_style=False, sort_keys=False)
            return HTMLResponse(
                content=yaml_content,
                media_type="application/x-yaml",
                headers={"Content - Disposition": "attachment; filename=openapi.yaml"},
            )
        except ImportError:
            return JSONResponse({"error": "PyYAML not installed. Install with: pip install pyyaml"}, status_code=500)

    # API documentation landing page
    @app.get("/", include_in_schema=False, response_class=HTMLResponse)
    async def api_root():
        """API documentation landing page."""
        return HTMLResponse(
            """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{title}</title>
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box - sizing: border - box;
                }}
                body {{
                    font - family: -apple - system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans - serif;
                    background: linear - gradient(135deg, #667eea 0%, #764ba2 100%);
                    min - height: 100vh;
                    display: flex;
                    align - items: center;
                    justify - content: center;
                    color: #333;
                }}
                .container {{
                    background: white;
                    border - radius: 20px;
                    padding: 60px;
                    max - width: 800px;
                    box - shadow: 0 20px 60px rgba(0,0,0,0.3);
                    text - align: center;
                }}
                h1 {{
                    font - size: 3em;
                    margin - bottom: 20px;
                    background: linear - gradient(135deg, #667eea 0%, #764ba2 100%);
                    -webkit - background-clip: text;
                    -webkit - text-fill - color: transparent;
                    background - clip: text;
                }}
                .version {{
                    color: #666;
                    font - size: 1.2em;
                    margin - bottom: 30px;
                }}
                .description {{
                    color: #555;
                    font - size: 1.1em;
                    line - height: 1.6;
                    margin - bottom: 40px;
                }}
                .buttons {{
                    display: flex;
                    gap: 20px;
                    justify - content: center;
                    flex - wrap: wrap;
                }}
                .btn {{
                    display: inline - block;
                    padding: 15px 40px;
                    border - radius: 50px;
                    text - decoration: none;
                    font - weight: 600;
                    font - size: 1.1em;
                    transition: all 0.3s ease;
                    box - shadow: 0 4px 15px rgba(0,0,0,0.2);
                }}
                .btn-primary {{
                    background: linear - gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                }}
                .btn-primary:hover {{
                    transform: translateY( - 2px);
                    box - shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
                }}
                .btn-secondary {{
                    background: white;
                    color: #667eea;
                    border: 2px solid #667eea;
                }}
                .btn-secondary:hover {{
                    background: #667eea;
                    color: white;
                    transform: translateY( - 2px);
                }}
                .features {{
                    margin - top: 50px;
                    display: grid;
                    grid - template-columns: repeat(auto - fit, minmax(200px, 1fr));
                    gap: 20px;
                    text - align: left;
                }}
                .feature {{
                    padding: 20px;
                    background: #f8f9fa;
                    border - radius: 10px;
                }}
                .feature h3 {{
                    color: #667eea;
                    margin - bottom: 10px;
                    font - size: 1.2em;
                }}
                .feature p {{
                    color: #666;
                    line - height: 1.5;
                }}
                .footer {{
                    margin - top: 50px;
                    padding - top: 30px;
                    border - top: 1px solid #eee;
                    color: #999;
                    font - size: 0.9em;
                }}
                .footer a {{
                    color: #667eea;
                    text - decoration: none;
                }}
                .footer a:hover {{
                    text - decoration: underline;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚀 {title}</h1>
                <div class="version">Version {version}</div>
                <div class="description">
                    {description}
                </div>

                <div class="buttons">
                    <a href="{docs_url}" class="btn btn-primary">
                        📚 Swagger UI
                    </a>
                    <a href="{redoc_url}" class="btn btn-primary">
                        📖 ReDoc
                    </a>
                    <a href="{openapi_url}" class="btn btn-secondary">
                        ⬇️ OpenAPI Spec
                    </a>
                    <a href="/health" class="btn btn-secondary">
                        ❤️ Health Check
                    </a>
                </div>

                <div class="features">
                    <div class="feature">
                        <h3>🤖 Agent Orchestration</h3>
                        <p>Multi-agent execution with quality gates and streaming</p>
                    </div>
                    <div class="feature">
                        <h3>🔐 Authentication</h3>
                        <p>JWT, API keys, and OAuth 2.0 support</p>
                    </div>
                    <div class="feature">
                        <h3>📊 Monitoring</h3>
                        <p>Prometheus metrics and health checks</p>
                    </div>
                    <div class="feature">
                        <h3>⚡ Streaming</h3>
                        <p>Real-time WebSocket streaming</p>
                    </div>
                </div>

                <div class="footer">
                    <p>
                        <a href="https://docs.veritas.example.com">Documentation</a> |
                        <a href="https://github.com/veritas/framework">GitHub</a> |
                        <a href="mailto:support@veritas.example.com">Support</a>
                    </p>
                    <p>© 2025 VERITAS Framework. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        )

    return app


def add_code_samples_to_openapi(app: FastAPI) -> FastAPI:
    """
    Add code samples to OpenAPI spec for multiple languages.

    Args:
        app: FastAPI application instance

    Returns:
        App with enhanced OpenAPI spec
    """

    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema

        openapi_schema = app.openapi()

        # Add code samples to endpoints
        for path, path_item in openapi_schema.get("paths", {}).items():
            for method, operation in path_item.items():
                if method not in ["get", "post", "put", "patch", "delete"]:
                    continue

                # Add code samples
                operation["x-codeSamples"] = generate_code_samples(path, method, operation)

        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi
    return app


def generate_code_samples(path: str, method: str, operation: dict) -> list:
    """Generate code samples for an operation."""

    samples = []

    # Python sample
    samples.append(
        {
            "lang": "Python",
            "source": """
import requests

url = "https://api.veritas.example.com{path}"
headers = {{
    "Authorization": "Bearer YOUR_JWT_TOKEN",
    "Content - Type": "application / json"
}}

response = requests.{method}(url, headers=headers)
print(response.json())
        """.strip(),
        }
    )

    # JavaScript sample
    samples.append(
        {
            "lang": "JavaScript",
            "source": """
const response = await fetch('https://api.veritas.example.com{path}', {{
  method: '{method.upper()}',
  headers: {{
    'Authorization': 'Bearer YOUR_JWT_TOKEN',
    'Content - Type': 'application / json'
  }}
}});

const data = await response.json();
console.log(data);
        """.strip(),
        }
    )

    # cURL sample
    samples.append(
        {
            "lang": "cURL",
            "source": """
curl -X {method.upper()} https://api.veritas.example.com{path} \\
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \\
  -H "Content-Type: application/json"
        """.strip(),
        }
    )

    return samples


# Example usage
if __name__ == "__main__":
    from fastapi import FastAPI

    app = FastAPI()

    # Add some example endpoints
    @app.get("/health", tags=["Monitoring"])
    async def health():
        """Health check endpoint."""
        return {"status": "healthy"}

    @app.post("/agents/execute", tags=["Agents"])
    async def execute_agents(plan_id: str):
        """Execute agent orchestration plan."""
        return {"plan_id": plan_id, "status": "pending"}

    # Configure documentation
    configure_api_docs(
        app,
        title="VERITAS Framework API",
        description="Comprehensive API for agent orchestration and RAG",
        version="1.0.0",
        enable_oauth=True,
    )

    # Add code samples
    add_code_samples_to_openapi(app)

    print("✅ Interactive API documentation configured")
    print("   Swagger UI: http://localhost:8000/docs")
    print(f"   ReDoc: http://localhost:8000/redoc")
    print(f"   OpenAPI JSON: http://localhost:8000/openapi.json")
    print(f"   OpenAPI YAML: http://localhost:8000/openapi.json.yaml")

    # To run:
    # uvicorn docs_config:app --reload
