# External - Third-Party Dependencies & Libraries

## Overview

The `external/` directory contains vendored third-party libraries, external dependencies, and integration code for external services used by VERITAS.

## Directory Structure

```
external/
├── vcpkg/                    # C++ package manager
│   ├── vcpkg-configuration.json
│   └── ports/
│
├── llama-cpp/                # LLaMA C++ inference
│   ├── include/
│   └── lib/
│
├── hnswlib/                  # Vector similarity search
│   ├── include/
│   └── python/
│
├── folly/                    # Facebook's utility library
│   └── include/
│
├── openssl/                  # Cryptography library
│   └── lib/
│
├── zlib/                     # Compression library
│   └── lib/
│
├── python-deps/              # Python package dependencies
│   ├── requirements.txt
│   └── vendored/
│
└── README.md                 # This file
```

## C++ Dependencies

### VCPkg Package Manager

**Configuration:** `vcpkg-configuration.json`

Lists all C++ dependencies:
```json
{
  "dependencies": [
    {
      "name": "llama",
      "version": "latest"
    },
    {
      "name": "hnswlib",
      "version": "0.8"
    },
    {
      "name": "openssl",
      "version": "3.0"
    },
    {
      "name": "zlib",
      "version": "1.2.13"
    }
  ]
}
```

**Installation:**
```bash
# Install all dependencies
vcpkg install

# Install specific package
vcpkg install llama:x64-windows

# Update packages
vcpkg update
```

### LLaMA C++ (llama-cpp)

**Purpose:** High-performance C++ inference engine

**Files:**
- `include/` - Header files
- `lib/` - Compiled libraries
- `CMakeLists.txt` - Build configuration

**Features:**
- Fast LLaMA model inference
- Optimized for CPU
- SIMD support
- Quantization support

**Usage in C++:**
```cpp
#include <llama-cpp/llama.h>

llama_context * ctx = llama_new_context_with_model(model, params);
llama_eval(ctx, tokens.data(), tokens.size(), 0, 8);
```

### HNSWLIB

**Purpose:** Hierarchical Navigable Small World - Vector similarity search

**Files:**
- `include/hnswlib/` - Headers
- `python/` - Python bindings

**Features:**
- Fast approximate nearest neighbor search
- Memory efficient
- Python and C++ support
- Configurable parameters

**Usage in Python:**
```python
import hnswlib

space = 'cosine'
dim = 1024
max_elements = 100000

index = hnswlib.Index(space=space, dim=dim)
index.init_index(max_elements=max_elements, ef_construction=200, M=16)
index.add_items(data, ids)
labels, distances = index.knn_query(query, k=5)
```

### Folly

**Purpose:** Facebook's collection of reusable C++ components

**Features:**
- String manipulation
- Hash tables
- Concurrent data structures
- Futures and promises
- Memory management utilities

**Use Cases:**
- Efficient string operations
- Lock-free data structures
- Concurrent task execution

### OpenSSL

**Purpose:** Cryptography and SSL/TLS

**Version:** 3.0

**Features:**
- Encryption/decryption
- Digital signatures
- Certificate handling
- TLS protocol

**Usage:**
```cpp
#include <openssl/rand.h>

unsigned char *buf = new unsigned char[32];
RAND_bytes(buf, 32);
```

### Zlib

**Purpose:** Data compression/decompression

**Version:** 1.2.13

**Features:**
- Deflate compression
- Stream compression
- Fast compression
- Memory efficient

**Usage:**
```cpp
#include <zlib.h>

z_stream stream = {};
deflateInit2(&stream, Z_DEFAULT_COMPRESSION, Z_DEFLATED, ...);
```

## Python Dependencies

### Requirements File

**Location:** `external/python-deps/requirements.txt`

Contains all Python package dependencies:
```
# AI/ML Framework
torch==2.0.1
transformers==4.30.0
numpy==1.24.3
scipy==1.11.1

# Data Processing
pandas==2.0.2
polars==0.18.0

# Web Framework
fastapi==0.100.0
pydantic==2.0.0
uvicorn==0.23.1

# Database
sqlalchemy==2.0.19
alembic==1.11.0
psycopg2-binary==2.9.6

# Vector DB
pinecone-client==2.2.2
hnswlib==0.7.0

# LLM Integration
langchain==0.0.240
ollama==0.0.1

# Testing
pytest==7.4.0
pytest-cov==4.1.0
pytest-asyncio==0.21.0

# Utilities
python-dotenv==1.0.0
pyyaml==6.0
requests==2.31.0
aiohttp==3.8.5
```

### Installation

```bash
# Install all dependencies
pip install -r external/python-deps/requirements.txt

# Install with dev dependencies
pip install -r external/python-deps/requirements-dev.txt

# Upgrade all packages
pip install -U -r external/python-deps/requirements.txt
```

### Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r external/python-deps/requirements.txt

# Freeze dependencies
pip freeze > external/python-deps/requirements-frozen.txt
```

### Vendored Packages

**Location:** `external/python-deps/vendored/`

Some packages are vendored (included in repository):
- Critical infrastructure packages
- Packages with complex dependencies
- Custom-patched packages
- Legacy compatibility packages

**Usage:**
```python
import sys
sys.path.insert(0, 'external/python-deps/vendored')
from vendored_package import module
```

## Integration Services

### Ollama Integration

**Purpose:** Local LLM backend integration

**Configuration:**
```yaml
ollama:
  host: localhost
  port: 11434
  models:
    - neural-9b-german
    - mistral
    - llama2
```

**External Reference:**
- GitHub: https://github.com/ollama/ollama
- Models: https://ollama.ai/library

### Pinecone Integration

**Purpose:** Vector database for RAG

**Configuration:**
```yaml
pinecone:
  api_key: ${PINECONE_API_KEY}
  environment: us-west1
  index: veritas-prod
```

**External Reference:**
- Website: https://www.pinecone.io/
- Docs: https://docs.pinecone.io/

### PostgreSQL Integration

**Purpose:** Primary relational database

**Version:** 15+

**Extensions Used:**
- pgvector (Vector operations)
- uuid-ossp (UUID generation)
- pg_trgm (Text search)
- ltree (Hierarchical data)

**External Reference:**
- Website: https://www.postgresql.org/
- Docs: https://www.postgresql.org/docs/

## Build & Compilation

### C++ Build

```bash
# Install dependencies
vcpkg install

# Create build directory
mkdir build
cd build

# Configure with CMake
cmake -DCMAKE_TOOLCHAIN_FILE=../vcpkg/scripts/buildsystems/vcpkg.cmake ..

# Build
cmake --build . --config Release
```

### Python Build

```bash
# Create distribution
python setup.py sdist bdist_wheel

# Install in development mode
pip install -e .
```

## Version Management

### Update Checklist

Before updating dependencies:

1. **Check compatibility**
   - Run test suite
   - Check breaking changes
   - Review deprecation warnings

2. **Update incrementally**
   - Update one package at a time
   - Test after each update
   - Commit with message

3. **Test thoroughly**
   - Unit tests
   - Integration tests
   - Performance tests
   - Deployment testing

4. **Document changes**
   - Update CHANGELOG
   - Note breaking changes
   - Update requirements files

### Security Updates

```bash
# Check for vulnerabilities
pip-audit

# Safety check
safety check

# Update vulnerable packages
pip install -U package-name
```

## Performance & Optimization

### Binary Distribution

Pre-compiled binaries available for:
- HNSWLIB (faster than pip version)
- LLaMA-cpp (optimized SIMD)
- Cryptography libraries

### Wheel Support

```bash
# Build wheels
pip wheel -r external/python-deps/requirements.txt

# Install from wheels
pip install --no-index --find-links=/path/to/wheels package
```

### Memory Optimization

- Use production-optimized versions
- Enable compression for storage
- Consider quantization for ML models
- Profile memory usage

## Troubleshooting

### Missing Dependencies

```bash
# Find missing dependency
python -c "import missing_module"

# Install missing package
pip install missing_package

# Check installed versions
pip show package-name
```

### Compilation Errors

```bash
# Clean build
rm -rf build/
cmake --build . --clean-first

# Verbose output
cmake --build . -- VERBOSE=1

# Check compiler
gcc --version
```

### Version Conflicts

```bash
# Check conflicts
pip check

# Show dependency tree
pipdeptree

# Use compatible versions
pip install package-name==specific-version
```

## Documentation & References

### Official Documentation
- [VCPkg Docs](https://vcpkg.io/)
- [CMake Docs](https://cmake.org/cmake/help/documentation.html)
- [PyPI.org](https://pypi.org/)
- [LLaMA-cpp Docs](https://github.com/ggerganov/llama.cpp)

### Security
- [CVE Database](https://cve.mitre.org/)
- [Safety](https://safety.readthedocs.io/)
- [Pip-audit](https://github.com/pypa/pip-audit)

### Performance
- [Benchmarking Tools](https://perf.wiki.kernel.org/)
- [Profiling](https://docs.python.org/3/library/profile.html)

## License Compliance

All included external libraries maintain their original licenses:

- **OpenSSL** - Apache 2.0
- **Zlib** - Zlib License
- **LLaMA-cpp** - MIT
- **HNSWLIB** - Apache 2.0
- **Folly** - Apache 2.0
- **Python packages** - Various (see each package)

**Note:** Always verify licenses when using external code in production.

## Contributing

### Adding New External Dependency

1. **Evaluate necessity** - Is this really needed?
2. **Check alternatives** - Are there better options?
3. **Verify license** - Is license compatible?
4. **Add to requirements** - Update requirements.txt or vcpkg-configuration.json
5. **Document** - Add entry to this README
6. **Test** - Verify integration and performance
7. **Commit** - With clear message about why

---

**Last Updated:** December 4, 2025
**Status:** Production Ready ✅
**C++ Packages:** 5+
**Python Packages:** 50+
**Security Scans:** Regular (weekly)
