# Backend - VERITAS Core Services

## Overview

The `backend/` directory contains all server-side services, APIs, and core logic for the VERITAS legal AI system.

## Structure

```
backend/
├── api/                      # FastAPI endpoints and routers
│   ├── v3/                   # Version 3 API (current)
│   ├── sse_endpoints.py      # Server-Sent Events streaming
│   └── veritas_api_*.py      # Various API implementations
├── agents/                   # AI agents for specialized domains
│   ├── domain/               # Domain-specific agents (admin law, finance, etc.)
│   ├── orchestrator/         # Agent orchestration
│   └── registry/             # Agent registry and management
├── services/                 # Core business services
│   ├── rag_service.py        # Retrieval-Augmented Generation
│   ├── hypothesis_service.py # Hypothesis generation
│   ├── process_executor.py   # Process execution engine
│   └── nlp_service.py        # NLP operations
├── core/                     # Core system components
│   ├── llm/                  # LLM client integrations
│   ├── orchestration/        # Unified orchestration
│   ├── pipeline/             # Processing pipelines
│   └── retrieval/            # Retrieval strategies
├── models/                   # Data models and schemas
├── helpers/                  # Utility functions
├── adapters/                 # External system adapters
└── app.py                    # Main application entry point
```

## Key Components

### API Layer (`api/`)
- RESTful endpoints for query processing
- Server-Sent Events (SSE) for real-time updates
- WebSocket support for bidirectional communication
- Authentication and authorization middleware

### Agents (`agents/`)
- **Administrative Law Agent** - BImSchG, legal procedures
- **RAG Agent** - Knowledge retrieval and augmentation
- **Supervisor Agent** - Process coordination
- **Database Agent** - ThemisDB integration

### Services (`services/`)
- **RAG Service** - Vector search and context retrieval
- **Hypothesis Service** - Generate query hypotheses
- **Process Executor** - Execute business processes
- **NLP Service** - Natural language processing

### Core (`core/`)
- **LLM Client** - Ollama and VLLM integration
- **Orchestrator** - Unified pipeline orchestration
- **Retrieval** - BM25 and vector search

## Configuration

Key configuration files:
- `config/` - Application configuration
- `.env` - Environment variables
- `pyproject.toml` - Python project configuration

## Development

### Running the Backend

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
python backend/app.py

# Run with Ollama LLM
OLLAMA_HOST=localhost:11434 python backend/app.py
```

### Testing

```bash
# Run all tests
pytest tests/

# Run backend-specific tests
pytest tests/ -k backend

# Run with coverage
pytest tests/ --cov=backend
```

### Key Services

- **API Server** - FastAPI application on port 8000
- **Ollama** - LLM server on port 11434
- **Vector DB** - Milvus or similar on port 19530

## API Documentation

Full API documentation available at:
- OpenAPI/Swagger: `/docs` (when server running)
- Postman: See `postman/` directory

## Key Features

✅ **Multi-domain support** - Admin law, finance, environment, etc.
✅ **Real-time streaming** - SSE-based progress updates
✅ **RAG pipeline** - Semantic search + LLM generation
✅ **Process execution** - Complex workflow support
✅ **Agent orchestration** - Coordinated multi-agent systems

## Security

- ✅ Authentication & authorization
- ✅ mTLS support for client certificates
- ✅ Input validation and sanitization
- ✅ Rate limiting and throttling

## Performance

- Retrieval latency: ~110ms (vector) + ~50ms (keyword)
- Inference latency: ~570ms
- SSE event delivery: ~10ms
- Throughput: 10+ requests/sec

## Related Documentation

- See `docs/` for comprehensive documentation
- See `docs/api/` for API reference
- See `docs/architecture/` for system design
- See `docs/components/` for component details

---

**Last Updated:** December 4, 2025
**Status:** Production Ready ✅
