# VERITAS Documentation Quick Reference

**Version:** 3.25.0  
**Last Updated:** 14. Oktober 2025

---

## 🚀 Quick Start (New Developers)

```bash
# 1. Read project structure
docs/PROJECT_STRUCTURE.md

# 2. Setup deployment
docs/DEPLOYMENT_GUIDE.md

# 3. Learn Phase 5 features (latest)
docs/PHASE5_HYPOTHESIS_GENERATION.md
docs/PHASE5_START_HERE.md

# 4. API reference
docs/API_REFERENCE.md
```

---

## 📚 Documentation Map

### Core Documentation (Start Here)

| Priority | Document | Purpose |
|----------|----------|---------|
| 🔥 **HIGH** | [PHASE5_HYPOTHESIS_GENERATION.md](PHASE5_HYPOTHESIS_GENERATION.md) | Latest features (v5.0) |
| 🔥 **HIGH** | [PHASE4_RAG_INTEGRATION.md](PHASE4_RAG_INTEGRATION.md) | RAG + Enhanced features |
| ⚡ **MEDIUM** | [API_REFERENCE.md](API_REFERENCE.md) | Complete API docs |
| ⚡ **MEDIUM** | [STATUS_REPORT.md](STATUS_REPORT.md) | Project status |
| 📖 **INFO** | [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) | File organization |

---

## 🎯 Common Tasks

### Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run Phase 5 tests only
python -m pytest tests/test_hypothesis_service.py -v
python -m pytest tests/test_batch_search.py -v
python -m pytest tests/test_reranker_service.py -v

# See: docs/TESTING.md
```

### Deployment

```bash
# Start backend
python start_backend.py

# Start frontend
python start_frontend.py

# See: docs/DEPLOYMENT_GUIDE.md
```

### Using Phase 5 Features

```python
# Hypothesis Generation
from backend.services.hypothesis_service import HypothesisService
hypothesis_service = HypothesisService()
hypothesis = hypothesis_service.generate_hypothesis("your query")

# Batch Search
from backend.services.rag_service import RAGService
import asyncio
rag = RAGService()
results = asyncio.run(rag.batch_search(["query1", "query2"]))

# Query Expansion
expansions = rag.expand_query("Bauantrag", max_expansions=3)

# LLM Re-ranking
from backend.services.reranker_service import RerankerService
reranker = RerankerService()
reranked = reranker.rerank(query, documents, top_k=5)

# See: docs/PHASE5_HYPOTHESIS_GENERATION.md
```

---

## 📁 Documentation Structure

```
docs/
├── README.md                           # Main index (YOU ARE HERE)
├── QUICK_REFERENCE.md                  # This file
│
├── 🔥 CURRENT PHASE (4-5)
│   ├── PHASE5_HYPOTHESIS_GENERATION.md # v5.0 features
│   ├── PHASE4_RAG_INTEGRATION.md       # RAG + enhancements
│   └── PHASE5_START_HERE.md            # Quick start
│
├── 🏗️ ARCHITECTURE
│   ├── PROCESS_TREE_ARCHITECTURE.md
│   ├── SERVER_SIDE_PROCESSING_ARCHITECTURE.md
│   └── UDS3_INTEGRATION_GUIDE.md
│
├── 🔧 API & INTEGRATION
│   ├── API_REFERENCE.md
│   ├── VERITAS_API_BACKEND_DOCUMENTATION.md
│   └── WEBSOCKET_PROTOCOL.md
│
├── 📊 REPORTS & STATUS
│   ├── STATUS_REPORT.md
│   ├── PHASE5_FINAL_COMPLETE_SUMMARY.md
│   └── PHASE4_COMPLETION_REPORT.md
│
└── 📦 archive/                         # Historical docs
    ├── README.md                       # Archive index
    ├── phase1-3/                       # 32 files
    ├── old-implementations/            # 42 files
    └── deprecated-features/            # 13 files
```

---

## 🔍 Finding Information

### By Topic

| Topic | Document |
|-------|----------|
| **Hypothesis Generation** | PHASE5_HYPOTHESIS_GENERATION.md |
| **RAG Search** | PHASE4_RAG_INTEGRATION.md |
| **Batch Processing** | PHASE4_RAG_INTEGRATION.md (Enhanced RAG) |
| **Query Expansion** | PHASE4_RAG_INTEGRATION.md (Enhanced RAG) |
| **LLM Re-ranking** | PHASE4_RAG_INTEGRATION.md (Enhanced RAG) |
| **API Endpoints** | API_REFERENCE.md |
| **UDS3 Databases** | UDS3_INTEGRATION_GUIDE.md |
| **Deployment** | DEPLOYMENT_GUIDE.md |
| **Testing** | TESTING.md |

### By Use Case

| Use Case | Solution |
|----------|----------|
| "I need to understand user queries" | → PHASE5_HYPOTHESIS_GENERATION.md |
| "I want faster search" | → PHASE4_RAG_INTEGRATION.md (Batch Search) |
| "I need better recall" | → PHASE4_RAG_INTEGRATION.md (Query Expansion) |
| "I want more relevant results" | → PHASE4_RAG_INTEGRATION.md (LLM Re-ranking) |
| "How do I deploy?" | → DEPLOYMENT_GUIDE.md |
| "What's the project status?" | → STATUS_REPORT.md |

---

## 🎯 Feature Quick Reference

### Phase 5 Features (Latest)

| Feature | Code | Docs |
|---------|------|------|
| **Hypothesis** | `backend/services/hypothesis_service.py` | PHASE5_HYPOTHESIS_GENERATION.md §3 |
| **Batch Search** | `backend/services/rag_service.py` | PHASE4_RAG_INTEGRATION.md §4.1 |
| **Query Expansion** | `backend/services/rag_service.py` | PHASE4_RAG_INTEGRATION.md §4.2 |
| **LLM Re-ranking** | `backend/services/reranker_service.py` | PHASE4_RAG_INTEGRATION.md §4.3 |

### Phase 4 Features

| Feature | Code | Docs |
|---------|------|------|
| **Vector Search** | `backend/services/rag_service.py` | PHASE4_RAG_INTEGRATION.md §3 |
| **Hybrid Ranking** | `backend/services/rag_service.py` | PHASE4_RAG_INTEGRATION.md §3 |
| **Citations** | `backend/models/document_source.py` | PHASE4_RAG_INTEGRATION.md §5 |

---

## 💡 Tips

### For New Developers

1. **Start with:** PROJECT_STRUCTURE.md
2. **Then read:** PHASE5_START_HERE.md
3. **Reference:** API_REFERENCE.md
4. **Test with:** Examples in `examples/` folder

### For Existing Developers

1. **Latest features:** PHASE5_FINAL_COMPLETE_SUMMARY.md
2. **Enhanced RAG:** PHASE4_RAG_INTEGRATION.md (Section 4)
3. **Migration guide:** (N/A - backward compatible)

### For Deployment

1. **Production:** DEPLOYMENT_GUIDE.md
2. **Quick start:** DEPLOYMENT_QUICKSTART.md
3. **Testing:** TESTING.md

---

## 📊 Statistics

| Metric | Value |
|--------|-------|
| **Active Docs** | 151 files |
| **Archived Docs** | 87 files |
| **Current Phase** | 5.0 (Hypothesis & Enhanced RAG) |
| **Total Lines** | 30,000+ |
| **Last Update** | 14. Oktober 2025 |

---

## 🔗 External Links

- **Main README:** `../README.md`
- **TODO List:** `../TODO.md`
- **Tests:** `../tests/`
- **Examples:** `../examples/`

---

## ⚠️ Important Notes

### Documentation Updates

- **Phase 1-3** documentation → **ARCHIVED** (superseded)
- **Current focus:** Phase 4-5 features
- **Active versions:** v3.25.0+
- **Archive location:** `docs/archive/`

### Using Archived Docs

- ❌ Don't use as implementation guide
- ✅ Use for historical context only
- ✅ Always check current docs first
- ✅ See `docs/archive/README.md` for details

---

## 📞 Need Help?

1. **Check:** [docs/README.md](README.md) (main index)
2. **Search:** Use file listings above
3. **Status:** [STATUS_REPORT.md](STATUS_REPORT.md)
4. **API:** [API_REFERENCE.md](API_REFERENCE.md)

---

**Quick Reference Version:** 1.0  
**Last Updated:** 14. Oktober 2025  
**Status:** ✅ Current
