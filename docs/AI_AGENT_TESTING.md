# AI Agent Test Suite Documentation

Comprehensive testing and benchmarking for all 4 AI agents in the VERITAS system.

## Overview

This test suite provides complete coverage for:
1. **Vector Chart Agent** - Chart generation and export
2. **Presentation Canvas Agent** - VDL and presentation rendering
3. **Geo Sub-Agent** - Coordinate transformation and map generation
4. **AI Image Generator** - Image generation and analysis

## Test Structure

```
tests/
├── agents/                         # Unit tests for each agent
│   ├── test_vector_chart_agent.py
│   ├── test_presentation_canvas_agent.py
│   ├── test_geo_sub_agent.py
│   └── test_ai_image_generator.py
├── integration/                    # Integration tests for APIs
│   └── test_api_endpoints.py
└── benchmarks/                     # Performance benchmarks
    └── test_agent_benchmarks.py
```

## Running Tests

### Quick Start

```bash
# Run all tests
python run_ai_agent_tests.py

# Run specific test suite
pytest tests/agents/test_vector_chart_agent.py -v

# Run with coverage
pytest tests/agents/ --cov=backend/agents --cov-report=html
```

### Test Categories

Tests are marked with pytest markers:

```bash
# Unit tests only (fast, no external dependencies)
pytest -v -m unit

# Integration tests (require running backend)
pytest -v -m integration

# Performance benchmarks
pytest -v -m benchmark

# All tests
pytest -v
```

## Test Coverage

### Vector Chart Agent (test_vector_chart_agent.py)

**Unit Tests:**
- ✅ Agent initialization
- ✅ Template listing (4 templates)
- ✅ Bar chart generation
- ✅ Pie chart generation
- ✅ Line chart generation
- ✅ Scatter chart generation
- ✅ Fallback without LLM
- ✅ Invalid template handling
- ✅ Export formats (PNG, SVG, PDF, PPTX)
- ✅ Concurrent generation

**Total: 10 test cases**

### Presentation Canvas Agent (test_presentation_canvas_agent.py)

**Unit Tests:**
- ✅ Agent initialization
- ✅ VDL creation
- ✅ VDL validation
- ✅ Invalid VDL detection
- ✅ Complete presentation generation
- ✅ Text element rendering
- ✅ Shape element rendering
- ✅ PowerPoint export
- ✅ Multiple layouts (6 types)
- ✅ AI image placeholder

**Total: 10 test cases**

### Geo Sub-Agent (test_geo_sub_agent.py)

**Unit Tests (CoordinateTransformer):**
- ✅ Transformer initialization
- ✅ UTM to WGS84 conversion
- ✅ WGS84 to UTM conversion
- ✅ Round-trip conversion accuracy
- ✅ Brandenburg validation

**Unit Tests (GeoSubAgent):**
- ✅ Agent initialization
- ✅ BImSchG data retrieval
- ✅ WKA data retrieval
- ✅ Category filtering
- ✅ Bounding box filtering
- ✅ Map generation
- ✅ Custom marker styles
- ✅ Brandenburg bounds
- ✅ Empty features handling

**Total: 14 test cases**

### AI Image Generator (test_ai_image_generator.py)

**Unit Tests:**
- ✅ Agent initialization
- ✅ Supported generators (4 types)
- ✅ Image generation with fallback
- ✅ Custom parameters
- ✅ Image analysis (caption)
- ✅ OCR task
- ✅ VQA task
- ✅ Object detection task
- ✅ Batch image generation
- ✅ Batch image analysis
- ✅ Capabilities listing
- ✅ Invalid task handling
- ✅ Nonexistent image handling
- ✅ Cross-platform file naming
- ✅ Different generators

**Total: 15 test cases**

## Benchmarks

### Performance Metrics

Each benchmark measures:
- **Duration** - Total execution time in seconds
- **Duration per iteration** - Average time per operation in milliseconds
- **Throughput** - Operations per second
- **Memory usage** - Memory delta in MB
- **Memory before/after** - Total memory usage

### Vector Chart Agent Benchmarks

1. **Single Chart Generation**
   - Expected: < 5 seconds
   - Measures: PNG/SVG/PDF/PPTX export

2. **Multiple Charts (10x)**
   - Expected: > 0.5 charts/second
   - Tests: Sequential generation

3. **Concurrent Generation (5x)**
   - Expected: < 10 seconds total
   - Tests: Parallel execution

### Presentation Canvas Agent Benchmarks

1. **Single Presentation (2 slides)**
   - Expected: < 10 seconds
   - Tests: VDL → rendering → PPTX

2. **VDL Rendering (10x)**
   - Expected: > 1 render/second
   - Tests: Canvas rendering speed

### Geo Sub-Agent Benchmarks

1. **Coordinate Transformation (1000x)**
   - Expected: > 1000 transforms/second
   - Tests: UTM ↔ WGS84 speed

2. **Geo Data Retrieval (100 features)**
   - Expected: < 2 seconds
   - Tests: Database query + transformation

3. **Map Generation**
   - Expected: < 5 seconds
   - Tests: Matplotlib rendering

### AI Image Generator Benchmarks

1. **Image Generation**
   - Expected: < 3 seconds (placeholder)
   - Note: Real AI generation is slower

2. **Image Analysis**
   - Expected: < 2 seconds (metadata)
   - Note: Real vision model is slower

3. **Batch Generation (5x)**
   - Tests: Concurrent placeholder generation

## Integration Tests

### API Endpoints

Tests all REST API endpoints with httpx:

**Chart API** (3 endpoints)
- POST /api/charts/generate
- GET /api/charts/templates
- GET /api/charts/download/{filename}

**Presentation API** (4 endpoints)
- POST /api/presentations/generate
- POST /api/presentations/validate_vdl
- GET /api/presentations/vdl_example
- GET /api/presentations/download/{filename}

**Geo API** (4 endpoints)
- POST /api/geo/query
- POST /api/geo/map
- POST /api/geo/transform
- GET /api/geo/bbox/brandenburg

**Image API** (8 endpoints)
- POST /api/images/generate
- POST /api/images/analyze
- POST /api/images/analyze/upload
- POST /api/images/analyze/batch
- GET /api/images/capabilities
- GET /api/images/generators
- POST /api/images/batch
- GET /api/images/download/{filename}

**Total: 19 API endpoints tested**

## Requirements

### Test Dependencies

```bash
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
httpx>=0.24.0
psutil>=5.9.0
```

Install with:
```bash
pip install pytest pytest-asyncio pytest-cov httpx psutil
```

## Running Benchmarks

```bash
# Run all benchmarks
pytest tests/benchmarks/ -v -m benchmark

# Save results
pytest tests/benchmarks/ -v -m benchmark > benchmark_results.txt

# With JSON output
pytest tests/benchmarks/ -v -m benchmark --json-report
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: AI Agent Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov httpx psutil
      - name: Run unit tests
        run: pytest tests/agents/ -v -m unit --cov=backend/agents
      - name: Run benchmarks
        run: pytest tests/benchmarks/ -v -m benchmark
```

## Test Results

Results are saved to:
- `test_results.json` - Overall test summary
- `htmlcov/index.html` - Coverage report
- `benchmark_results.json` - Performance metrics
- `pytest-report.xml` - JUnit XML format

## Expected Coverage

- **Vector Chart Agent**: > 90%
- **Presentation Canvas Agent**: > 85%
- **Geo Sub-Agent**: > 90%
- **AI Image Generator**: > 80%

**Overall Target: > 85% code coverage**

## Troubleshooting

### Tests Fail Due to Missing Dependencies

```bash
# Install all test dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Integration Tests Fail

Integration tests require the backend to be running:

```bash
# Start backend
python start_backend.py

# Run integration tests
pytest tests/integration/ -v -m integration
```

### Benchmarks Show Poor Performance

Benchmarks are sensitive to system load. For accurate results:
- Close other applications
- Run on dedicated hardware
- Use consistent test data

## Contributing

When adding new features:

1. **Write unit tests** - Test individual components
2. **Add integration tests** - Test API endpoints
3. **Include benchmarks** - Measure performance impact
4. **Update documentation** - Document new test cases

## Summary

**Total Test Coverage:**
- Unit Tests: 49 test cases
- Integration Tests: 19 API endpoints
- Benchmarks: 11 performance tests
- **Total: 79 automated tests**

**Test Execution:**
- Unit tests: ~30 seconds
- Integration tests: ~60 seconds (with backend)
- Benchmarks: ~120 seconds
- **Total: ~3-4 minutes**

All tests are designed to run in CI/CD pipelines with automatic failure detection and performance regression monitoring.
