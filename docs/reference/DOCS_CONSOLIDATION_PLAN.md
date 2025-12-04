# Documentation Consolidation Plan

**Date:** December 4, 2025
**Goal:** Consolidate all markdown files into `docs/` directory structure
**Total Files to Process:** ~293 files (outside docs/)

---

## Strategy

### Keep in Root (Do Not Move)
- `README.md` - Main project README
- `CONTRIBUTING.md` - Contribution guidelines
- `license.md` - License file

### Move to docs/

#### 1. Root Level Files → docs/
```
MARKDOWN_FILES_OVERVIEW.md → docs/reference/MARKDOWN_FILES_OVERVIEW.md
PHASE14_COMPLETION_REPORT.md → docs/phases/PHASE14_COMPLETION_REPORT.md
```

#### 2. Archive Directories → docs/archive/
```
.archive/ → docs/archive/legacy/
  - concepts/ → docs/archive/concepts/
  - deployment-logs/ → docs/archive/deployment-logs/
  - obsolete-guides/ → docs/archive/obsolete-guides/
  - old-versions/ → docs/archive/old-versions/
  - phase-reports/ → docs/archive/phase-reports/
  - session-summaries/ → docs/archive/session-summaries/
```

#### 3. Reports → docs/reports/
```
reports/ → docs/reports/
  - All 19 .md files from reports/
```

#### 4. Backend Documentation → docs/backend/
```
backend/README.md → Keep (directory README)
backend/ENV_VARS.md → docs/backend/ENV_VARS.md
backend/agents/*.md → docs/backend/agents/
backend/api/v3/README.md → docs/api/v3/README.md
backend/evaluation/README.md → docs/backend/evaluation/
```

#### 5. Frontend Documentation → docs/frontend/
```
frontend/README.md → Keep (directory README)
frontend/ui/README_UI_MODULES.md → docs/frontend/ui/README_UI_MODULES.md
```

#### 6. Testing Documentation → docs/testing/
```
tests/README.md → Keep (directory README)
tests/SCIENTIFIC_PIPELINE_TESTS.md → docs/testing/SCIENTIFIC_PIPELINE_TESTS.md
tests/TEST_HAMBURGER_EXPORT.md → docs/testing/TEST_HAMBURGER_EXPORT.md
tests/TESTING_README.md → docs/testing/TESTING_README.md
tests/agents/README.md → docs/testing/agents/README.md
tests/reports/TEST_GENERATION_REPORT.md → docs/testing/reports/TEST_GENERATION_REPORT.md
```

#### 7. Scripts Documentation → docs/scripts/
```
scripts/README.md → Keep (directory README)
scripts/README_BACKEND_V4.md → docs/scripts/README_BACKEND_V4.md
scripts/README_SERVICE_MANAGEMENT.md → docs/scripts/README_SERVICE_MANAGEMENT.md
scripts/README_BACKEND_MANAGEMENT.md → docs/scripts/README_BACKEND_MANAGEMENT.md
scripts/QUICK_REFERENCE.md → docs/scripts/QUICK_REFERENCE.md
scripts/UPDATE_SUMMARY.md → docs/scripts/UPDATE_SUMMARY.md
```

#### 8. Configuration Documentation → docs/config/
```
config/README.md → Keep (directory README)
config/README_HYBRID_CONFIG.md → docs/config/README_HYBRID_CONFIG.md
```

#### 9. Other Directories
```
benchmarks/README.md → Keep (directory README)
data/README.md → Keep (directory README)
docker/README.md → Keep (directory README)
external/README.md → Keep (directory README)
helm/veritas/README.md → docs/deployment/helm/README.md
tools/pgbouncer/README.md → docs/tools/pgbouncer/README.md
vqb_frontend/README.md → docs/frontend/vqb/README.md
.github/COPILOT_INSTRUCTIONS.md → docs/development/COPILOT_INSTRUCTIONS.md
themisdb/docs/aql/aql_prompt_engineering.md → docs/integration/themisdb/aql_prompt_engineering.md
```

---

## Implementation Steps

### Phase 1: Create Target Directory Structure
```powershell
New-Item -ItemType Directory -Force -Path docs/reference
New-Item -ItemType Directory -Force -Path docs/reports
New-Item -ItemType Directory -Force -Path docs/backend/agents
New-Item -ItemType Directory -Force -Path docs/backend/evaluation
New-Item -ItemType Directory -Force -Path docs/frontend/ui
New-Item -ItemType Directory -Force -Path docs/frontend/vqb
New-Item -ItemType Directory -Force -Path docs/scripts
New-Item -ItemType Directory -Force -Path docs/config
New-Item -ItemType Directory -Force -Path docs/deployment/helm
New-Item -ItemType Directory -Force -Path docs/tools/pgbouncer
New-Item -ItemType Directory -Force -Path docs/archive/legacy
New-Item -ItemType Directory -Force -Path docs/archive/concepts
New-Item -ItemType Directory -Force -Path docs/archive/deployment-logs
New-Item -ItemType Directory -Force -Path docs/archive/obsolete-guides
New-Item -ItemType Directory -Force -Path docs/archive/old-versions
New-Item -ItemType Directory -Force -Path docs/integration/themisdb
```

### Phase 2: Move Root Level Files
```powershell
Move-Item MARKDOWN_FILES_OVERVIEW.md docs/reference/
Move-Item PHASE14_COMPLETION_REPORT.md docs/phases/
```

### Phase 3: Move Archive Directories
```powershell
Move-Item .archive/concepts/* docs/archive/concepts/
Move-Item .archive/deployment-logs/* docs/archive/deployment-logs/
Move-Item .archive/obsolete-guides/* docs/archive/obsolete-guides/
Move-Item .archive/old-versions/* docs/archive/old-versions/
Move-Item .archive/phase-reports/* docs/archive/phase-reports/
Move-Item .archive/session-summaries/* docs/archive/session-summaries/
Move-Item .archive/*.md docs/archive/legacy/
```

### Phase 4: Move Reports
```powershell
Move-Item reports/*.md docs/reports/
```

### Phase 5: Move Backend Documentation
```powershell
Move-Item backend/ENV_VARS.md docs/backend/
Move-Item backend/agents/*.md docs/backend/agents/
Move-Item backend/api/v3/README.md docs/api/v3/
Move-Item backend/evaluation/README.md docs/backend/evaluation/
```

### Phase 6: Move Frontend Documentation
```powershell
Move-Item frontend/ui/README_UI_MODULES.md docs/frontend/ui/
```

### Phase 7: Move Testing Documentation
```powershell
Move-Item tests/SCIENTIFIC_PIPELINE_TESTS.md docs/testing/
Move-Item tests/TEST_HAMBURGER_EXPORT.md docs/testing/
Move-Item tests/TESTING_README.md docs/testing/
Move-Item tests/agents/README.md docs/testing/agents/
Move-Item tests/reports/TEST_GENERATION_REPORT.md docs/testing/reports/
```

### Phase 8: Move Scripts Documentation
```powershell
Move-Item scripts/README_BACKEND_V4.md docs/scripts/
Move-Item scripts/README_SERVICE_MANAGEMENT.md docs/scripts/
Move-Item scripts/README_BACKEND_MANAGEMENT.md docs/scripts/
Move-Item scripts/QUICK_REFERENCE.md docs/scripts/
Move-Item scripts/UPDATE_SUMMARY.md docs/scripts/
```

### Phase 9: Move Configuration Documentation
```powershell
Move-Item config/README_HYBRID_CONFIG.md docs/config/
```

### Phase 10: Move Other Documentation
```powershell
Move-Item helm/veritas/README.md docs/deployment/helm/
Move-Item tools/pgbouncer/README.md docs/tools/pgbouncer/
Move-Item vqb_frontend/README.md docs/frontend/vqb/
Move-Item .github/COPILOT_INSTRUCTIONS.md docs/development/
Move-Item themisdb/docs/aql/aql_prompt_engineering.md docs/integration/themisdb/
```

---

## Expected Result

### Directory Structure After Consolidation

```
docs/
├── README.md                           # Main documentation index
├── getting-started/                    # Quick start guides
├── architecture/                       # Architecture docs
├── api/                                # API documentation
│   └── v3/                            # v3 API docs
├── components/                         # Component docs
├── integration/                        # Integration guides
│   └── themisdb/                      # ThemisDB integration
├── deployment/                         # Deployment guides
│   └── helm/                          # Helm charts docs
├── development/                        # Development guides
│   └── COPILOT_INSTRUCTIONS.md       # Copilot setup
├── testing/                            # Testing documentation
│   ├── agents/                        # Agent tests
│   └── reports/                       # Test reports
├── reference/                          # Reference docs
│   └── MARKDOWN_FILES_OVERVIEW.md    # This overview
├── phases/                             # Phase completion reports
│   └── PHASE14_COMPLETION_REPORT.md  # Latest phase
├── benchmarks/                         # Benchmark docs
├── backend/                            # Backend documentation
│   ├── agents/                        # Agent docs
│   └── evaluation/                    # Evaluation docs
├── frontend/                           # Frontend documentation
│   ├── ui/                            # UI modules
│   └── vqb/                           # Visual Query Builder
├── scripts/                            # Script documentation
├── config/                             # Configuration docs
├── tools/                              # Tool documentation
│   └── pgbouncer/                     # PgBouncer docs
├── reports/                            # Project reports
└── archive/                            # Historical documentation
    ├── legacy/                        # Legacy docs
    ├── concepts/                      # Old concepts
    ├── deployment-logs/               # Old deployment logs
    ├── obsolete-guides/               # Obsolete guides
    ├── old-versions/                  # Old version docs
    ├── phase-reports/                 # Historical phases
    ├── session-summaries/             # Historical sessions
    ├── phase1-3/                      # Phase 1-3 docs
    ├── old-implementations/           # Old implementations
    └── deprecated-features/           # Deprecated features
```

### Files Remaining Outside docs/

**Root Directory:**
- README.md (main project)
- CONTRIBUTING.md
- license.md

**Directory READMEs (Keep for GitHub):**
- backend/README.md
- frontend/README.md
- tests/README.md
- scripts/README.md
- benchmarks/README.md
- config/README.md
- data/README.md
- docker/README.md
- external/README.md

---

## Validation Steps

After consolidation:

1. **Verify all files moved:**
   ```powershell
   Get-ChildItem -Path . -Recurse -Filter "*.md" | Where-Object {
     $_.FullName -notlike "*\docs\*" -and
     $_.FullName -notlike "*\node_modules\*"
   }
   ```

2. **Check for broken links:**
   - Run link checker on docs/
   - Update relative paths
   - Fix cross-references

3. **Update main docs/README.md:**
   - Add new sections
   - Update navigation
   - Fix all links

4. **Git commit:**
   ```bash
   git add -A
   git commit -m "docs: Consolidate all markdown files into docs/ directory"
   ```

---

## Benefits

✅ **Single Source of Truth:** All docs in one place
✅ **Better Organization:** Clear hierarchy
✅ **Easier Maintenance:** Centralized updates
✅ **Better Discovery:** Logical grouping
✅ **Clean Repository:** Minimal root clutter
✅ **GitHub-Friendly:** README.md in key directories

---

## Risks & Mitigation

**Risk 1: Broken Links**
- Mitigation: Update all relative links after move
- Tool: Run automated link checker

**Risk 2: Lost Files**
- Mitigation: Git tracks all moves
- Backup: Git history preserves original locations

**Risk 3: Disrupted Workflows**
- Mitigation: Update documentation first
- Communication: Clear migration guide

---

## Timeline

- **Phase 1-2:** 10 minutes (structure + root files)
- **Phase 3:** 15 minutes (archive directories)
- **Phase 4-10:** 20 minutes (individual moves)
- **Validation:** 15 minutes (checks + fixes)
- **Total:** ~60 minutes

---

**Status:** Ready to Execute
**Approval:** Awaiting confirmation
**Next Step:** Execute Phase 1 (create directory structure)
