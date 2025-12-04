# Data - Datasets, Examples & Sample Data

## Overview

The `data/` directory contains sample datasets, examples, and test data used for testing, demonstration, and development purposes.

## Directory Structure

```
data/
├── samples/                  # Sample data for testing
│   ├── queries.json         # Example queries
│   ├── results.json         # Example results
│   └── conversations.json   # Multi-turn conversation samples
│
├── bimschg/                 # BImSchG-related test data
│   ├── regulations.json     # Regulation samples
│   ├── procedures.json      # Procedure examples
│   └── cases.json           # Case law examples
│
├── admin-law/               # Administrative law datasets
│   ├── statutes.json        # Legal statutes
│   ├── decisions.json       # Court decisions
│   └── references.json      # Legal references
│
├── rag-sources/             # RAG source data
│   ├── documents.json       # Document corpus
│   ├── embeddings.json      # Pre-computed embeddings
│   └── index.json           # Vector index data
│
├── benchmarks/              # Benchmark test data
│   ├── performance-tests.json
│   ├── quality-metrics.json
│   └── golden-datasets.json
│
└── README.md                # This file
```

## Sample Data

### Sample Queries

**File:** `samples/queries.json`

```json
{
  "queries": [
    {
      "id": "q001",
      "text": "What are the requirements for environmental impact assessment?",
      "domain": "admin_law",
      "complexity": "medium"
    },
    {
      "id": "q002",
      "text": "How do I file an objection to a BImSchG decision?",
      "domain": "bimschg",
      "complexity": "high"
    }
  ]
}
```

### Sample Results

**File:** `samples/results.json`

```json
{
  "results": [
    {
      "query_id": "q001",
      "response": "Environmental impact assessments are required...",
      "citations": [
        {
          "source": "BImSchG § 1",
          "confidence": 0.98
        }
      ],
      "quality_metrics": {
        "citation_accuracy": 0.98,
        "relevance": 0.96,
        "completeness": 0.95
      }
    }
  ]
}
```

### Sample Conversations

**File:** `samples/conversations.json`

```json
{
  "conversations": [
    {
      "id": "conv001",
      "turns": [
        {
          "user": "What is BImSchG?",
          "assistant": "BImSchG is the Federal Immission Control Act..."
        },
        {
          "user": "Who enforces it?",
          "assistant": "Environmental agencies at federal and state level..."
        }
      ]
    }
  ]
}
```

## BImSchG Test Data

### Regulations

**File:** `bimschg/regulations.json`

Contains sample regulations from the BImSchG (Bundes-Immissions Schutz Gesetz):
- Federal Immission Control Act
- Air Quality Regulations
- Noise Control Regulations
- Hazardous Substance Regulations

### Procedures

**File:** `bimschg/procedures.json`

Sample procedures for:
- Environmental impact assessment
- Licensing procedures
- Objection filing
- Administrative appeals

### Case Law

**File:** `bimschg/cases.json`

Examples of relevant court decisions:
- Bundesverwaltungsgericht (Federal Administrative Court)
- State administrative courts
- Key precedents
- Legal interpretations

## Administrative Law Datasets

### Statutes

**File:** `admin-law/statutes.json`

Legal statutes covering:
- Administrative Procedure Act (VwVfG)
- General Administrative Law Principles
- Statutory Authority and Delegation
- Legal Norms and Regulations

### Decisions

**File:** `admin-law/decisions.json`

Court decisions including:
- Landmark cases
- Regulatory interpretations
- Procedural rulings
- Administrative law principles

### References

**File:** `admin-law/references.json`

Cross-references and citations:
- Statute sections
- Case citations
- Legal commentaries
- Related regulations

## RAG Source Data

### Documents

**File:** `rag-sources/documents.json`

Document corpus for RAG system:
- Legal documents
- Regulations
- Administrative guidance
- Case summaries

### Embeddings

**File:** `rag-sources/embeddings.json`

Pre-computed embeddings:
- Vector representations
- Dimension: 1024 (multilingual-e5-large)
- Document IDs mapped to vectors
- Similarity scores

### Vector Index

**File:** `rag-sources/index.json`

Vector index metadata:
- Index structure
- Document-to-ID mappings
- Metadata
- Version information

## Benchmark Datasets

### Performance Tests

**File:** `benchmarks/performance-tests.json`

Test cases for performance benchmarking:
- Retrieval latency tests
- Inference performance tests
- Streaming tests
- Load tests

### Quality Metrics

**File:** `benchmarks/quality-metrics.json`

Pre-computed quality metrics:
- Citation accuracy scores
- Content relevance scores
- Legal accuracy metrics
- Aspect coverage scores

### Golden Datasets

**File:** `benchmarks/golden-datasets.json`

Curated golden datasets:
- Expert-validated answers
- Reference citations
- Expected quality metrics
- Baseline comparisons

## Using Test Data

### Loading Sample Queries

```python
import json

with open('data/samples/queries.json') as f:
    samples = json.load(f)

for query in samples['queries']:
    print(f"Query: {query['text']}")
```

### Loading RAG Documents

```python
from backend.rag import RAGSystem

rag = RAGSystem()
documents = rag.load_documents('data/rag-sources/documents.json')
```

### Loading Benchmark Data

```python
from benchmarks.benchmark_suite import BenchmarkRunner

runner = BenchmarkRunner()
runner.load_golden_dataset('data/benchmarks/golden-datasets.json')
```

## Creating New Test Data

### Guidelines

1. **Relevance** - Data should be relevant to real use cases
2. **Accuracy** - Factual correctness, especially for legal data
3. **Diversity** - Cover various scenarios and domains
4. **Validation** - Expert review before adding
5. **Documentation** - Clear descriptions and metadata

### Adding New Samples

1. Create new JSON file in appropriate subdirectory
2. Follow existing structure and naming conventions
3. Include metadata (date, source, validation status)
4. Add documentation in this README
5. Commit with descriptive message

### Naming Conventions

```
data/<category>/<type>-<date>.json

Examples:
data/samples/queries-2025-01-15.json
data/bimschg/regulations-v2.json
data/benchmarks/golden-dataset-phase13.json
```

## Data Quality

### Validation Checklist

- [ ] Data is syntactically valid JSON
- [ ] All required fields present
- [ ] Data types are correct
- [ ] No sensitive information included
- [ ] Metadata is accurate
- [ ] Source is documented
- [ ] Data is representative

### Updating Data

```bash
# Validate JSON syntax
python -m json.tool data/samples/queries.json

# Check for required fields
python scripts/validate_data.py data/

# Generate statistics
python scripts/data_statistics.py data/
```

## Legal Data Accuracy

### BImSchG & Admin Law Data

All legal data should be:
- ✅ Current (updated with latest amendments)
- ✅ Accurate (verified against official sources)
- ✅ Complete (including all relevant references)
- ✅ Properly cited (with source attribution)

### Reference Sources

- **Gesetze im Internet** - https://www.gesetze-im-internet.de/
- **BundesAnzeiger** - Official Federal Gazette
- **Court Decisions** - Available from court websites
- **Commentaries** - Legal expert commentaries

## Data Retention & Cleanup

### Retention Policy

- **Sample Data:** Keep indefinitely
- **Benchmark Data:** Keep last 10 versions
- **Test Data:** Can be regenerated, not retained
- **Performance Data:** Archive older than 1 year

### Cleanup

```bash
# Archive old benchmark data
find data/benchmarks -name "*.json" -mtime +365 | xargs gzip

# Remove test artifacts
rm data/tmp/*.json

# Regenerate embeddings if needed
python scripts/regenerate_embeddings.py
```

## Privacy & Security

### Sensitive Data

⚠️ **Never include:**
- Personal identifying information
- Confidential business data
- Private communications
- Credentials or secrets
- Unreleased court decisions

### Anonymization

If using real data:
1. Remove identifying details
2. Generalize locations
3. Anonymize names and dates
4. Obscure specific references
5. Get appropriate permissions

## Integration with Tests

### Test Fixtures

```python
from tests.fixtures import load_sample_queries, load_golden_dataset

def test_retrieval():
    queries = load_sample_queries()
    results = system.retrieve(queries[0])
    assert len(results) > 0
```

### Pytest Fixtures

```python
@pytest.fixture
def sample_query():
    return load_sample_queries()[0]

def test_with_sample(sample_query):
    result = process(sample_query)
    assert result is not None
```

## Related Documentation

- See `tests/README.md` for test data requirements
- See `benchmarks/README.md` for benchmark data
- See `backend/README.md` for RAG data handling
- See `config/README.md` for data directory configuration

---

**Last Updated:** December 4, 2025
**Status:** Production Ready ✅
**Data Files:** 15+
**Total Size:** ~500 MB
**Last Validation:** December 4, 2025
