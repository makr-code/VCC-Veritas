# VERITAS Agent-System Übersicht

**Stand:** 4. Dezember 2025
**Framework:** BaseAgent v2.0
**Status:** ✅ 20 Agents aktiv, 22 Capabilities

---

## 📊 Agent-Übersicht

### Phase 1: Core Weather Agents (2)

Wetterdaten von DWD und BrightSky API.

| Agent ID | Quelle | Capabilities | Framework |
|----------|--------|--------------|-----------|
| `weather_dwd` | DWD Wetterdienst | WEATHER_DATA, REAL_TIME_DATA, EXTERNAL_API | BaseAgent v2.0 |
| `brightsky_weather` | BrightSky API | WEATHER_DATA, REAL_TIME_DATA, EXTERNAL_API, QUERY_PROCESSING | BaseAgent v2.0 |

**Code:** `backend/agents/environmental/weather/`
**Tests:** 14 Benchmarks

### Phase 2: Environmental Agents (4)

Umweltdaten und Compliance-Prüfung.

| Agent ID | Domain | Capabilities | Framework |
|----------|--------|--------------|-----------|
| `naturschutz` | Naturschutz | ENVIRONMENTAL_DATA, LEGAL_FRAMEWORK, COMPLIANCE | BaseAgent v2.0 |
| `boden_gewaesserschutz` | Boden & Gewässer | ENVIRONMENTAL_DATA, LEGAL_FRAMEWORK, COMPLIANCE | BaseAgent v2.0 |
| `emissionen_monitoring` | Emissionen | ENVIRONMENTAL_DATA, REAL_TIME_PROCESSING, COMPLIANCE | BaseAgent v2.0 |
| `immissionsschutz` | Immissionsschutz | ENVIRONMENTAL_DATA, LEGAL_FRAMEWORK, COMPLIANCE | BaseAgent v2.0 |

**Code:** `backend/agents/environmental/`
**Tests:** 28 Benchmarks

### Phase 3: Domain Agents v2.0 (10)

Spezialisierte Domain-Agents mit BaseAgent v2.0 Framework.

| Agent ID | Domain | LOC | Tests | Capabilities |
|----------|--------|-----|-------|--------------|
| `social` | Soziales | 450 | 7 | SOCIAL_SERVICES, LEGAL_FRAMEWORK, QUERY_PROCESSING, DATA_ANALYSIS |
| `verwaltungsrecht` | Verwaltung | 420 | 7 | LEGAL_FRAMEWORK, PROCESS_GUIDANCE, COMPLIANCE |
| `rechtsrecherche` | Recht | 480 | 7 | LEGAL_FRAMEWORK, DOCUMENT_RETRIEVAL, KNOWLEDGE_SYNTHESIS |
| `verwaltungsprozess` | Prozess | 510 | 7 | PROCESS_GUIDANCE, LEGAL_FRAMEWORK, DOCUMENT_RETRIEVAL |
| `financial` | Finanzen | 490 | 7 | TAXATION, FINANCIAL_IMPACT, DATA_ANALYSIS, QUERY_PROCESSING |
| `technical_standards` | Standards | 380 | 7 | LEGAL_FRAMEWORK, DOCUMENT_RETRIEVAL, COMPLIANCE |
| `chemical_data` | Chemie | 340 | 7 | ENVIRONMENTAL_DATA, EXTERNAL_API, QUERY_PROCESSING |
| `wikipedia` | Wissen | 290 | 7 | KNOWLEDGE_SYNTHESIS, EXTERNAL_API, QUERY_PROCESSING |
| `traffic` | Verkehr | 320 | 7 | TRANSPORT_DATA, REAL_TIME_PROCESSING, EXTERNAL_API |
| `database` | Datenbank | 580 | 7 | DATA_ANALYSIS, QUERY_PROCESSING, DOCUMENT_RETRIEVAL |

**Code:** `backend/agents/domain/`
**Tests:** 70 Tests (7 pro Agent)
**Total LOC:** ~4,260

### Phase 4: Visualization & Generation Agents (4)

Multi-modale Output-Generierung.

| Agent ID | Engine | LOC | Tests | Capabilities |
|----------|--------|-----|-------|--------------|
| `chart_engine` | Plotly, Matplotlib | 380 | 36 | CHART_GENERATION, DATA_ANALYSIS |
| `presentation_canvas` | VDL, python-pptx | 628 | - | PRESENTATION_CREATION, VISUAL_DESIGN, CHART_GENERATION |
| `image_generation` | SwarmUI, Stable Diffusion | 650 | 37 | IMAGE_GENERATION, VISUAL_DESIGN |
| `geo_map` | OSM, pyproj | 582 | 36 | MAP_GENERATION, GEO_DATA_PROCESSING, DATA_ANALYSIS |

**Code:** `backend/agents/visualization/`, `backend/agents/geo/`
**Tests:** 109 Tests
**Total LOC:** ~2,240

---

## 🎯 Capabilities (22)

### Core (5)

- `QUERY_PROCESSING` - 15 Agents
- `DATA_ANALYSIS` - 4 Agents
- `LEGAL_FRAMEWORK_ANALYSIS` - 7 Agents
- `COMPLIANCE_CHECKING` - 1 Agent
- `PROCESS_GUIDANCE` - 3 Agents

### Visualization (6)

- `CHART_GENERATION` - 2 Agents (chart_engine, presentation_canvas)
- `PRESENTATION_CREATION` - 1 Agent (presentation_canvas)
- `IMAGE_GENERATION` - 1 Agent (image_generation)
- `MAP_GENERATION` - 1 Agent (geo_map)
- `VISUAL_DESIGN` - 2 Agents (presentation_canvas, image_generation)
- `GEO_DATA_PROCESSING` - 1 Agent (geo_map)

### Data Sources (5)

- `ENVIRONMENTAL_DATA` - 4 Agents
- `WEATHER_DATA` - 2 Agents
- `TRANSPORT_DATA` - 1 Agent
- `EXTERNAL_API` - 3 Agents
- `REAL_TIME_DATA` - 1 Agent

### Knowledge & Documents (2)

- `DOCUMENT_RETRIEVAL` - 3 Agents
- `KNOWLEDGE_SYNTHESIS` - 3 Agents

### Specialized (4)

- `SOCIAL_SERVICES` - 1 Agent
- `TAXATION` - 1 Agent
- `FINANCIAL_IMPACT` - 1 Agent
- `REAL_TIME_PROCESSING` - 3 Agents

---

## 🔧 Agent-Framework

### BaseAgent v2.0

**Features:**
- Unified interface für alle Agents
- Built-in Context Management
- Standardisierte Query Processing
- Capability-based Registration
- Error Handling & Logging
- Async/Await Support

**Core Methods:**
```python
class BaseAgent:
    async def process_query(query: str, context: dict) -> dict
    async def validate_input(query: str) -> bool
    def get_capabilities() -> List[AgentCapability]
    def get_metadata() -> dict
```

**Migration Status:**
- Phase 1: ✅ 2/2 Agents migrated
- Phase 2: ✅ 4/4 Agents migrated
- Phase 3: ✅ 10/10 Agents migrated
- Phase 4: ✅ 4/4 Agents implemented

**Total:** 20/20 Agents using BaseAgent v2.0

---

## 📦 Agent Registry

### Registrierung

**Datei:** `backend/agents/registry/domain_agent_registration.py`

**Funktionen:**
- `register_phase1_agents()` - Weather Agents
- `register_phase2_agents()` - Environmental Agents
- `register_phase3_agents()` - Domain v2.0 Agents
- `register_visualization_agents()` - Phase 4 Visualization Agents
- `register_all_domain_agents()` - Alle Phasen

**Registrierungs-Status:**
- ✅ 20/24 Agents erfolgreich
- ❌ 4/24 Agents fehlgeschlagen (Legacy/Deprecated)

### Capability-Based Selection

```python
from backend.agents.registry.api_agent_registry import get_agent_registry, AgentCapability

registry = get_agent_registry()

# Get agents by capability
chart_agents = registry.get_agents_for_capability(AgentCapability.CHART_GENERATION)
# Returns: [chart_engine, presentation_canvas]

map_agents = registry.get_agents_for_capability(AgentCapability.MAP_GENERATION)
# Returns: [geo_map]
```

---

## 🚀 Orchestrator-Integration

### Task Blueprints

**Datei:** `backend/agents/orchestrator/agent_orchestrator.py` (Lines 183-208)

| Blueprint | Stage | Priority | Parallel | Dependencies |
|-----------|-------|----------|----------|--------------|
| `chart_generation` | response_generation | 0.7 | ✅ | data_analysis, database |
| `presentation_creation` | response_enhancement | 0.75 | ❌ | content_synthesis, chart_generation |
| `image_generation` | response_enhancement | 0.65 | ✅ | - |
| `map_generation` | response_generation | 0.7 | ✅ | data_analysis |

### Dispatcher

**Datei:** `backend/agents/orchestrator/visualization_dispatcher.py` (360 LOC)

**Funktionen:**
- `dispatch_chart_generation()` - Chart via ChartManager
- `dispatch_presentation_creation()` - VDL Presentations
- `dispatch_image_generation()` - AI Images via SwarmUI
- `dispatch_map_generation()` - OSM Maps with Coord Transform
- `dispatch_visualization_agent()` - Unified Dispatcher (Capability-Based)
- `dispatch_visualization_batch()` - Parallel Batch Processing

**Pipeline-Beispiel:**
```
User Query
    ↓
Query Analysis (hypothesis_agent)
    ↓
Data Retrieval (database_agent)
    ↓
    ├─→ chart_generation (parallel) ─→ chart_engine
    ├─→ map_generation (parallel) ───→ geo_map
    └─→ image_generation (parallel) ─→ image_generation
    ↓
presentation_creation (sequential) → presentation_canvas
    ↓
Final Response
```

---

## 📊 Code-Metrics

### Agent Code

| Phase | Agents | LOC | Tests | Status |
|-------|--------|-----|-------|--------|
| Phase 1 | 2 | ~800 | 14 | ✅ |
| Phase 2 | 4 | ~1,600 | 28 | ✅ |
| Phase 3 | 10 | ~4,260 | 70 | ✅ |
| Phase 4 | 4 | ~2,240 | 109 | ✅ |
| **Total** | **20** | **~8,900** | **221** | **✅** |

---

## 🧪 Testing

**Total:** 221 Tests (alle PASSED)

```
tests/
├── benchmarks/
│   ├── test_phase1_agent_benchmarks.py    # 14 tests
│   ├── test_phase2_agent_benchmarks.py    # 28 tests
│   └── test_phase3_agent_benchmarks.py    # 70 tests
├── test_chart_engine.py                   # 36 tests
├── test_image_generation.py               # 37 tests
├── test_geo_sub_agent.py                  # 36 tests
└── test_visualization_orchestrator.py     # 6 integration tests
```

---

## Quick Links

- [Back to Documentation](../README.md)
- [System Status](../CURRENT_STATUS.md)
- [Getting Started](../getting-started/QUICK_START.md)
