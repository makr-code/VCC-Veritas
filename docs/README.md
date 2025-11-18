# VERITAS Documentation Index

**Last Updated:** 14. Oktober 2025
**Version:** 3.25.0
**Status:** ✅ Production Ready

---

## 📚 **Current Documentation (Active)**

### 🎯 **Getting Started**

| Document | Description | Status |
|----------|-------------|--------|
| [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) | Project organization and file structure | ✅ Current |
| [STATUS_REPORT.md](STATUS_REPORT.md) | Overall project status and metrics | ✅ Current |
| [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) | Production deployment instructions | ✅ Current |
| [TESTING.md](TESTING.md) | Testing guidelines and procedures | ✅ Current |

---

### 🚀 **Phase 4 & 5: RAG & Hypothesis Generation (Latest)**

**Priority: HIGH - Current Implementation**

| Document | Description | Lines | Status |
|----------|-------------|-------|--------|
| [PHASE5_HYPOTHESIS_GENERATION.md](PHASE5_HYPOTHESIS_GENERATION.md) | **Complete Phase 5 Documentation** | 1,050+ | ✅ **NEW** |
| [PHASE4_RAG_INTEGRATION.md](PHASE4_RAG_INTEGRATION.md) | RAG Integration + Enhanced RAG Features | 2,000+ | ✅ Enhanced |
| [PHASE5_START_HERE.md](PHASE5_START_HERE.md) | Quick start guide for Phase 5 | 200+ | ✅ Current |

**Phase 5 Features:**
- ✅ **Hypothesis Generation** - LLM-based query analysis (8 question types, 4 confidence levels)
- ✅ **Batch Search** - Parallel query processing (10x-13x speedup)
- ✅ **Query Expansion** - 30+ German synonym categories (+40-60% recall)
- ✅ **LLM Re-ranking** - Contextual relevance scoring (+15-25% precision)

**Phase 4 Features:**
- ✅ **Multi-Source Search** - ChromaDB (vector), Neo4j (graph), PostgreSQL (relational)
- ✅ **Hybrid Ranking** - 3 strategies (RRF, Weighted, Borda)
- ✅ **Source Citations** - Page numbers, sections, timestamps
- ✅ **Context Building** - Token-limited LLM context

**Quick Start:**
```bash
# See comprehensive documentation
docs/PHASE5_HYPOTHESIS_GENERATION.md

# Quick start guide
docs/PHASE5_START_HERE.md
```

---

### 📊 **Implementation Reports**

| Document | Description | Status |
|----------|-------------|--------|
| [PHASE5_FINAL_COMPLETE_SUMMARY.md](PHASE5_FINAL_COMPLETE_SUMMARY.md) | Phase 5 completion report | ✅ Complete |
| [PHASE4_COMPLETION_REPORT.md](PHASE4_COMPLETION_REPORT.md) | Phase 4 completion report | ✅ Complete |
| [PHASE4_EXECUTIVE_SUMMARY.md](PHASE4_EXECUTIVE_SUMMARY.md) | Phase 4 executive summary | ✅ Complete |

---

### 🏗️ **Architecture & Design**

| Document | Description | Status |
|----------|-------------|--------|
| [UDS3_INTEGRATION_GUIDE.md](UDS3_INTEGRATION_GUIDE.md) | UDS3 database integration | ✅ Current |
| [UDS3_QUICK_START.md](UDS3_QUICK_START.md) | UDS3 quick start guide | ✅ Current |
| [PROCESS_TREE_ARCHITECTURE.md](PROCESS_TREE_ARCHITECTURE.md) | Process tree design | ✅ Current |
| [SERVER_SIDE_PROCESSING_ARCHITECTURE.md](SERVER_SIDE_PROCESSING_ARCHITECTURE.md) | Server-side architecture | ✅ Current |

---

### 🔧 **API & Integration**

| Document | Description | Status |
|----------|-------------|--------|
| [API_REFERENCE.md](API_REFERENCE.md) | Complete API reference | ✅ Current |
| [VERITAS_API_BACKEND_DOCUMENTATION.md](VERITAS_API_BACKEND_DOCUMENTATION.md) | Backend API docs | ✅ Current |
| [WEBSOCKET_PROTOCOL.md](WEBSOCKET_PROTOCOL.md) | WebSocket streaming protocol | ✅ Current |

---

### 📈 **Evaluation & Quality**

| Document | Description | Status |
|----------|-------------|--------|
| [BASELINE_EVALUATION_INTEGRATION_COMPLETE.md](BASELINE_EVALUATION_INTEGRATION_COMPLETE.md) | Baseline evaluation system | ✅ Complete |
| [GOLDEN_DATASET_SYSTEM.md](GOLDEN_DATASET_SYSTEM.md) | Golden dataset for testing | ✅ Complete |
| [RERANKING_EVALUATION_IMPLEMENTATION.md](RERANKING_EVALUATION_IMPLEMENTATION.md) | Re-ranking evaluation | ✅ Complete |

---

### 🔐 **Security & Authentication**

| Document | Description | Status |
|----------|-------------|--------|
| [AUTHENTICATION.md](AUTHENTICATION.md) | Authentication system | ✅ Current |
| [MTLS_QUICK_START.md](MTLS_QUICK_START.md) | mTLS setup guide | ✅ Complete |
| [PKI_FINAL_STATUS.md](PKI_FINAL_STATUS.md) | PKI implementation status | ✅ Complete |

---

### 🎨 **UI & Frontend**

| Document | Description | Status |
|----------|-------------|--------|
| [UI_INTEGRATION_COMPLETE.md](UI_INTEGRATION_COMPLETE.md) | UI integration report | ✅ Complete |
| [STRUCTURED_RESPONSE_ARCHITECTURE.md](STRUCTURED_RESPONSE_ARCHITECTURE.md) | Structured responses | ✅ Current |
| [RICH_MEDIA_JSON_SYSTEM.md](RICH_MEDIA_JSON_SYSTEM.md) | Rich media support | ✅ Current |

---

### 🗄️ **Database & Storage**

| Document | Description | Status |
|----------|-------------|--------|
| [UDS3_POLYGLOT_QUERY_API.md](UDS3_POLYGLOT_QUERY_API.md) | Polyglot query API | ✅ Current |
| [UDS3_HYBRID_SEARCH_FINAL_REPORT.md](UDS3_HYBRID_SEARCH_FINAL_REPORT.md) | Hybrid search implementation | ✅ Complete |
| [POSTGRES_COUCHDB_INTEGRATION.md](POSTGRES_COUCHDB_INTEGRATION.md) | PostgreSQL + CouchDB integration | ✅ Complete |
| [CHROMADB_V2_COMPLETE_SUMMARY.md](CHROMADB_V2_COMPLETE_SUMMARY.md) | ChromaDB v2 integration | ✅ Complete |

---

### 📝 **Prompts & LLM**

| Document | Description | Status |
|----------|-------------|--------|
| [DUAL_PROMPT_SYSTEM.md](DUAL_PROMPT_SYSTEM.md) | Dual prompt architecture | ✅ Current |
| [PROMPT_IMPROVEMENT_SYSTEM.md](PROMPT_IMPROVEMENT_SYSTEM.md) | Prompt optimization | ✅ Current |
| [LLM_PARAMETERS.md](LLM_PARAMETERS.md) | LLM configuration | ✅ Current |

---

## 📦 **Archived Documentation**

Older documentation has been moved to organized archive folders:

### Archive Structure

```
docs/archive/
├── phase1-3/              # Phase 1-3 documentation (superseded by Phase 4-5)
│   ├── PHASE1_*.md       # Process tree & NLP foundation
│   ├── PHASE2_*.md       # Agent integration
│   └── PHASE3_*.md       # Streaming progress
│
├── old-implementations/   # Superseded implementations
│   ├── CHAT_PERSISTENCE_*.md
│   ├── LLM_PARAMETER_*.md
│   ├── SUPERVISOR_*.md
│   ├── V7_*.md
│   └── SESSION_*.md
│
└── deprecated-features/   # Deprecated/removed features
    ├── CHROMADB_DEPENDENCY_REMOVAL.md
    ├── *_FIX_*.md        # Old bugfix docs
    └── *_old.md          # Old versions

### Recently archived

The following legacy file was moved to the archive on 14.10.2025:

- `docs/archive/legacy/TODO_PKI_INTEGRATION_LEGACY.md` — legacy PKI integration notes
```

**Note:** Archive documentation is preserved for historical reference but may not reflect current implementation.

---

## 🎯 **Quick Navigation**

### For New Developers

1. **Start Here:** [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)
2. **Setup:** [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
3. **Current Features:** [PHASE5_HYPOTHESIS_GENERATION.md](PHASE5_HYPOTHESIS_GENERATION.md)
4. **API Reference:** [API_REFERENCE.md](API_REFERENCE.md)

### For Existing Developers

1. **Latest Updates:** [PHASE5_FINAL_COMPLETE_SUMMARY.md](PHASE5_FINAL_COMPLETE_SUMMARY.md)
2. **Enhanced RAG:** [PHASE4_RAG_INTEGRATION.md](PHASE4_RAG_INTEGRATION.md) (Section: Enhanced RAG Features)
3. **Status:** [STATUS_REPORT.md](STATUS_REPORT.md)

### For Deployment

1. **Production Guide:** [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
2. **Quick Start:** [DEPLOYMENT_QUICKSTART.md](DEPLOYMENT_QUICKSTART.md)
3. **Testing:** [TESTING.md](TESTING.md)

---

## 📊 **Documentation Statistics**

| Category | Active Docs | Archive Docs | Total Lines |
|----------|-------------|--------------|-------------|
| Phase 4-5 (Current) | 3 | - | 3,000+ |
| Architecture | 8 | - | 6,000+ |
| Implementation Reports | 12 | 30+ | 10,000+ |
| API & Integration | 5 | - | 4,000+ |
| Total | ~50 | ~50 | 30,000+ |

---

## 🔄 **Documentation Updates**

**Latest Changes (14.10.2025):**
- ✅ Created comprehensive Phase 5 documentation (1,050+ lines)
- ✅ Enhanced Phase 4 RAG documentation (+300 lines)
- ✅ Archived Phase 1-3 documentation (superseded)
- ✅ Archived old implementation reports
- ✅ Archived deprecated/fixed issues
- ✅ Created organized archive structure

**Next Updates:**
- Continuous updates to Phase 5 based on production feedback
- Performance optimization documentation
- Advanced usage patterns and recipes

---

## 💡 **Documentation Guidelines**

### When to Archive

Documentation should be archived when:
- ✅ Superseded by newer implementation (e.g., Phase 1-3 → Phase 4-5)
- ✅ Feature deprecated or removed
- ✅ Bugfix documentation after fix deployed
- ✅ Session reports after completion
- ✅ Old version documentation after version upgrade

### Active Documentation Standards

Active documentation should:
- ✅ Reflect current implementation (v3.25.0+)
- ✅ Include working code examples
- ✅ Be tested and validated
- ✅ Have clear version and date markers
- ✅ Link to related documentation

---

## 🚀 **Contributing**

When adding new documentation:

1. **Use clear naming:** `FEATURE_NAME_DESCRIPTION.md`
2. **Include metadata:** Version, date, status
3. **Add to this index:** Update the appropriate section
4. **Keep it current:** Archive when superseded

---

## 📞 **Support**

For questions about documentation:
- Check [STATUS_REPORT.md](STATUS_REPORT.md) for current project status
- See [API_REFERENCE.md](API_REFERENCE.md) for API questions
- Refer to [PHASE5_START_HERE.md](PHASE5_START_HERE.md) for quick start

---

**Last Updated:** 14. Oktober 2025, 18:00 Uhr
**Documentation Version:** 3.25.0
**Status:** ✅ Current & Complete
