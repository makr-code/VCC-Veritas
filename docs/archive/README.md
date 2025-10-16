# Documentation Archive Index

**Archive Created:** 14. Oktober 2025  
**Reason:** Superseded by Phase 4-5 implementation

---

## 📦 Archive Structure

### Phase 1-3 (Superseded)

**Location:** `docs/archive/phase1-3/`

**Status:** ✅ Complete but superseded by Phase 4-5

**Contents:**
- Phase 1: Process Tree & NLP Foundation
- Phase 2: Agent Integration  
- Phase 3: Streaming Progress

**Why Archived:**
These phases established the foundation but have been significantly enhanced and superseded by:
- Phase 4: RAG Integration (multi-source search, hybrid ranking)
- Phase 5: Hypothesis Generation & Enhanced RAG (intelligent query analysis, batch processing)

**Historical Value:**
- Shows development progression
- Documents original design decisions
- Reference for architectural evolution

---

### Old Implementations

**Location:** `docs/archive/old-implementations/`

**Status:** Superseded by current implementations

**Major Items:**

1. **Chat Persistence System** (`CHAT_PERSISTENCE_*.md`)
   - Old chat storage implementation
   - Superseded by: Current session management

2. **LLM Parameter Controls** (`LLM_PARAMETER_*.md`)
   - Early LLM configuration UI
   - Superseded by: Integrated parameter management

3. **Supervisor Integration** (`SUPERVISOR_*.md`)
   - Original supervisor agent design
   - Superseded by: Process executor with hypothesis

4. **V7 API** (`V7_*.md`)
   - Version 7 API documentation
   - Superseded by: Current API (v3.25.0)

5. **Session Reports** (`SESSION_*.md`)
   - Historical session summaries
   - Archived after: Implementation completion

**Why Archived:**
- Features reimplemented with better architecture
- Implementation approaches changed
- Documentation no longer matches current code

---

### Deprecated Features

**Location:** `docs/archive/deprecated-features/`

**Status:** Removed, fixed, or no longer applicable

**Major Items:**

1. **Bug Fixes** (Various `*_FIX_*.md`, `*_BUGFIX_*.md`)
   - CHROMADB_DEPENDENCY_REMOVAL.md
   - CRITICAL_BUGFIX_RAG_MOCK_DATA.md
   - RAG_INTEGRATION_FIX_UPDATE.md
   - STREAMING_FIX_COMPLETE.md
   - BACKEND_PORT_FIX.md
   - **Status:** Bugs fixed and deployed

2. **Warning/Issue Reports** (`WARNING_*.md`, `WARNUNGEN_*.md`)
   - FRONTEND_WARNINGS_FIX.md
   - BACKEND_WARNINGS_EXPLAINED.md
   - WARNING_OPTIMIZATION_REPORT.md
   - **Status:** Issues resolved

3. **Old Versions** (`*_old.md`)
   - PRODUCTION_DEPLOYMENT_GUIDE_v1.0_old.md
   - STATUS_REPORT_old.md
   - **Status:** Superseded by current versions

**Why Archived:**
- Bugs have been fixed
- Warnings resolved
- Documentation outdated
- No longer relevant to current codebase

---

## 🔍 Finding Archived Documentation

### By Phase

```bash
# Phase 1 documentation
ls docs/archive/phase1-3/PHASE1_*.md

# Phase 2 documentation
ls docs/archive/phase1-3/PHASE2_*.md

# Phase 3 documentation
ls docs/archive/phase1-3/PHASE3_*.md
```

### By Feature

```bash
# Chat persistence
ls docs/archive/old-implementations/CHAT_PERSISTENCE_*.md

# LLM parameters
ls docs/archive/old-implementations/LLM_PARAMETER_*.md

# Supervisor integration
ls docs/archive/old-implementations/SUPERVISOR_*.md
```

### By Type

```bash
# Bug fixes
ls docs/archive/deprecated-features/*FIX*.md

# Warning reports
ls docs/archive/deprecated-features/WARNING_*.md

# Old versions
ls docs/archive/deprecated-features/*_old.md

### Legacy Files

The following legacy file was moved to the archive on 14.10.2025:

- `docs/archive/legacy/TODO_PKI_INTEGRATION_LEGACY.md` — PKI legacy integration notes
```

---

## ⚠️ **Important Notes**

### Using Archived Documentation

**DO:**
- ✅ Reference for historical context
- ✅ Understand design evolution
- ✅ Learn from past decisions

**DON'T:**
- ❌ Use as implementation guide
- ❌ Copy code examples (may be outdated)
- ❌ Assume features still exist
- ❌ Follow deprecated patterns

### Current Documentation

For up-to-date information, always refer to:

1. **Active Documentation:** `docs/README.md`
2. **Current Phase:** `docs/PHASE5_HYPOTHESIS_GENERATION.md`
3. **Enhanced RAG:** `docs/PHASE4_RAG_INTEGRATION.md`
4. **Project Status:** `docs/STATUS_REPORT.md`

---

## 📊 Archive Statistics

| Category | Files | Estimated Lines |
|----------|-------|----------------|
| Phase 1-3 | ~15 | ~8,000 |
| Old Implementations | ~30 | ~15,000 |
| Deprecated Features | ~15 | ~5,000 |
| **Total** | **~60** | **~28,000** |

---

## 🔄 Archive Maintenance

### When to Add to Archive

Documentation should be moved to archive when:
- Implementation superseded by newer version
- Feature deprecated or removed
- Bug fixed and deployed
- Session/report completed
- Major version upgrade (e.g., v3.x → v4.x)

### Archive Organization

```
docs/archive/
├── phase1-3/              # Superseded phases
├── old-implementations/   # Reimplemented features
├── deprecated-features/   # Removed/fixed features
└── [future categories]    # As needed
```

### Cleanup Schedule

- **Quarterly Review:** Check for outdated documentation
- **Major Releases:** Archive superseded versions
- **Feature Deprecation:** Immediate archival

---

## 📞 Questions?

If you need information from archived documentation:

1. **Check current docs first:** Most features have been enhanced, not removed
2. **Search archive:** Use file listings above
3. **Ask maintainers:** We can help find historical context
4. **Check git history:** See when features changed

---

**Archive Created:** 14. Oktober 2025  
**Archive Maintainer:** VERITAS Team  
**Status:** ✅ Organized & Indexed
