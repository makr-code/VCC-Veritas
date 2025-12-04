# VERITAS Agent Framework Migration - Vollständiger Umsetzungsplan

**Status:** 🚀 In Ausführung
**Datum:** 4. Dezember 2025
**Fortschritt:** Phase 1 (2/5 Agents) + Cleanup ✅ + Test Suite ✅

## 🎯 Executive Summary

Vollständige Migration aller 38 Domain Agents vom Legacy-System zum modernen BaseAgent Framework.

**Erreicht (heute):**
- ✅ BaseAgent Migration Template erstellt
- ✅ GenehmigungAgent → BaseAgent v2.0 (migriert + getestet)
- ✅ DwdWeatherAgent → BaseAgent v2.0 (neu erstellt + getestet)
- ✅ 21 Merge-Konflikte automatisch aufgelöst
- ✅ 5 Wetter-Duplikate konsolidiert
- ✅ Registry-System aufgebaut (domain_agent_registration.py)
- ✅ **Unit Test Suite für beide Agents** (26+ & 28+ tests)
- ✅ **Benchmark Suite** (Performance Validation)
- ✅ **Phase 1 Status Report** (detailliertes Tracking)

**Zu erreichen (Woche 2-3):**
- 🚀 Phase 2: 15 weitere Agents migrieren
- 🚀 Phase 3: Restliche Agents + Framework-Erweiterungen
- 🚀 Vollständige Test-Coverage
- 🚀 Performance-Optimierung & Monitoring

---

## 📋 Phase-by-Phase Plan

### Phase 1: Critical Agents (diese Woche) ✅

**Status:** 40% abgeschlossen (2/5)

| Agent | Priorität | Status | Datei | Ziel |
|-------|-----------|--------|-------|------|
| 1️⃣ GenehmigungAgent | ⭐⭐⭐ | ✅ Migriert | construction/genehmigung_agent.py | BaseAgent + Registry |
| 2️⃣ DwdWeatherAgent | ⭐⭐⭐ | ✅ Neu erstellt | weather/dwd_weather_agent_v3_framework.py | BaseAgent + Registry |
| 3️⃣ ConstructionAgent | ⭐⭐⭐ | 🚀 Nächst | construction/construction_agent.py | Merge-Konflikt lösen + BaseAgent |
| 4️⃣ EnvironmentalAgent | ⭐⭐⭐ | 🚀 Nächst | environmental/environmental_agent.py | Merge-Konflikt lösen + BaseAgent |
| 5️⃣ VerwaltungsrechtWorker | ⭐⭐⭐ | 🟡 Hybrid | social/verwaltungsrecht_worker.py | Bereits teils kompatibel |

**Migrations-Tempo:** ~2 Agents pro Tag × 1 Entwickler = Phase 1 in 2-3 Tagen ✅

---

### Phase 2: Main Domain Agents (Woche 2)

**Geplant:** 15 Agents
**Erwartete Dauer:** 5-7 Arbeitstage

#### Weather & Environmental (6 Agents)
| Agent | Kategorie | Aufwand | Notes |
|-------|-----------|--------|-------|
| BrightSkyWeatherAgent | Weather | Mittel | Externe API-Integration, ähnlich zu DWD |
| ImmissionsschutzAgent | Environmental | Hoch | Spezialisierter Legal-Agent, komplexe Logik |
| BodenGewaesserschutzAgent | Environmental | Mittel | Ähnlich Immissionsschutz |
| NaturschutzAgent | Environmental | Mittel | Knowledge-Base Agent |
| EmissionenMonitoringAgent | Environmental | Hoch | Real-time Monitoring Integration |
| TrafficAgent | Technical | Niedrig | Simple Knowledge-Base |

#### Legal & Social (5 Agents)
| Agent | Kategorie | Aufwand | Notes |
|-------|-----------|--------|-------|
| RechtsrechercheAgent | Legal | Mittel | Knowledge-Base + Search |
| SocialAgent | Social | Niedrig | Simple Classification |
| VerwaltungsprozessAgent | Legal | Hoch | Process Workflow |
| FinancialAgent | Technical | Mittel | Calculation Engine |
| TechnicalStandardsAgent | Technical | Niedrig | Knowledge-Base (DIN, VDI, ISO) |

#### Spezialisiert (4 Agents)
| Agent | Kategorie | Aufwand | Notes |
|-------|-----------|--------|-------|
| DatabaseAgent | Technical | Hoch | Multi-DB Support |
| ChemicalDataAgent | Technical | Mittel | External DB Integration |
| WikipediaAgent | Knowledge | Niedrig | External API |
| VerwaltungsrechtWorker | Legal | Mittel | Worker Pattern |

**Migrations-Strategie Phase 2:**
1. Grouping nach Complexity
2. Parallele Migration (3 Entwickler)
3. Tägliche Integration Tests
4. Kontinuierliche Registry-Updates

---

### Phase 3: Finalization & Framework Extensions (Woche 3)

**Geplant:** Restliche Agents + Framework-Erweiterungen

#### Remaining Agents (wenn Phase 2 Kapazität überschreitet)
- Spezialisierte one-off Agents
- Teste-Helper Agenten
- Legacy Compatibility Wrapper

#### Framework-Erweiterungen
| Feature | Priorität | Aufwand | Benefit |
|---------|-----------|---------|---------|
| **Caching Layer** | ⭐⭐⭐ | 2-3 Tage | 30-50% Performance ↑ |
| **Advanced Monitoring Dashboard** | ⭐⭐ | 2-3 Tage | Real-time Insights |
| **Async Pooling Optimization** | ⭐⭐⭐ | 2-3 Tage | Memory Efficiency ↑ |
| **Health Check System** | ⭐⭐⭐ | 1-2 Tage | Reliability ↑ |
| **Metrics Export (Prometheus)** | ⭐⭐ | 1-2 Tage | Observability ↑ |
| **LLM Integration Layer** | ⭐ | 3-5 Tage | Future AI Features |

---

## 🛠️ Implementierungs-Details

### Template-basierte Migration

**Migration Template:** `backend/agents/templates/baseagent_migration_template.py`

**Verwendung für jeden Agent:**

```python
# 1. Kopiere Template
cp backend/agents/templates/baseagent_migration_template.py \
   backend/agents/domain/[domain]/[agent_name]_agent.py

# 2. Ersetze Platzhalter
sed -i 's/\[DOMAIN_NAME\]/[agent_name]/g' [agent_name]_agent.py

# 3. Integriere Legacy-Logik
# Ersetze _legacy_query() mit originalem Code

# 4. Definiere Capabilities
# Füge agent-spezifische AgentCapability hinzu

# 5. Registriere in domain_agent_registration.py
```

### Registry-Integration

**Automatische Auto-Registration:**

```python
# backend/agents/registry/domain_agent_registration.py
def register_all_domain_agents(phase: str = "all"):
    """Register Domain Agents by Phase"""

    if phase in ("all", "1"):
        register_phase1_agents()      # 5 Agents

    if phase in ("all", "2"):
        register_phase2_agents()      # 15 Agents

    if phase in ("all", "3"):
        register_phase3_agents()      # Remaining
```

**Startup Auto-Registration:**

```python
# backend/__init__.py oder main.py
from backend.agents.registry.domain_agent_registration import auto_register_on_startup

auto_register_on_startup()  # Registriere Phase 1 Agents beim Start
```

### Cleanup & Preprocessing

**Migration Accelerator:** `backend/agents/migration/migration_accelerator.py`

**Features:**
- ✅ Automatisches .bak Archivieren
- ✅ Duplikat-Erkennung
- ✅ Merge-Konflikt Auflösung
- ✅ Test-Generierung

**Verwendung:**

```bash
# Phase 0: Cleanup (bereits ausgeführt)
python backend/agents/migration/cleanup_script.py

# Phase 0b: Migration Prep
python backend/agents/migration/migration_accelerator.py --mode=resolve --agents=weather,construction

# Phase 1-3: Batch Migration
python backend/agents/migration/migration_accelerator.py --mode=migrate --agents=weather,construction,environmental
```

---

## 📊 Metriken & Erfolgs-Kriterien

### Aktueller Status

| Metrik | Ist | Soll | Status |
|--------|-----|------|--------|
| Domain Agents (BaseAgent) | 2/38 | 38/38 | 5% |
| Registrierte Agents | 2 | 38+ | 5% |
| Merge-Konflikte | ✅ 0 | 0 | ✅ |
| Backup-Dateien | 0 | 0 | ✅ |
| Duplikate | ✅ 0 | 0 | ✅ |
| Test Coverage | 10% | 80%+ | 10% |

### Ziel-Status (Ende nächste Woche)

| Metrik | Ziel | Status |
|--------|------|--------|
| Domain Agents (BaseAgent) | 38/38 | 100% ✅ |
| Registrierte Agents | 38 | 100% ✅ |
| Registry-Integration | 100% | ✅ |
| Orchestration Test | Erfolgreich | ✅ |
| Test Coverage | 80%+ | ✅ |
| Performance (vs Legacy) | ±10% | ✅ |

---

## 🚀 Nächste Konkrete Schritte

### Heute (4. Dezember)

- ✅ **Phase 1-2 Agents Cleanup** (Backups, Duplikate, Konflikte)
- ✅ GenehmigungAgent v2.0 erstellt
- ✅ DwdWeatherAgent v3_framework erstellt
- ✅ Registry-System aufgebaut
- **Nächste:** ConstructionAgent migrieren

### Morgen (5. Dezember)

- 🔧 **ConstructionAgent → BaseAgent**
  ```bash
  # Merge-Konflikt auflösen
  python backend/agents/migration/migration_accelerator.py --mode=resolve --agents=construction

  # Migrieren
  # → Benutze Template & originale Logik
  # → Register in domain_agent_registration.py
  ```

- 🔧 **EnvironmentalAgent (domain/) → BaseAgent**
  - Merge-Konflikt auflösen
  - Migrieren
  - Registry-Integration

- 📋 **Start Phase 2 Planning**
  - Weather Agents gruppieren (für parallele Migration)
  - Environmental Agents gruppieren
  - Assign zu Entwickler-Teams (wenn vorhanden)

### Woche 2 (9-13. Dezember)

- 🚀 **Phase 2: 15 Agents parallel migrieren**
  - 3 Developer Teams à 5 Agents
  - Tägliche Integration
  - Kontinuierliche Registry-Updates

- 🧪 **Test-Coverage aufbauen**
  - Unit Tests für Phase 2 Agents
  - Integration Tests mit Registry
  - E2E Tests für Orchestrator

### Woche 3 (16-20. Dezember)

- 🎯 **Phase 3: Finalization**
  - Restliche Agents
  - Framework-Erweiterungen (Caching, Monitoring, etc.)
  - Performance-Optimierung
  - Final Integration Tests

---

## 📚 Ressourcen & Tools

### Templates & Skripte
- ✅ `backend/agents/templates/baseagent_migration_template.py` - Migration Template
- ✅ `backend/agents/migration/migration_accelerator.py` - Batch Migration Tool
- ✅ `backend/agents/migration/cleanup_script.py` - Cleanup Utility
- ✅ `backend/agents/registry/domain_agent_registration.py` - Registry Population

### Framework-Komponenten
- ✅ `backend/agents/framework/base_agent.py` - Abstract Base Class
- ✅ `backend/agents/framework/agent_monitoring.py` - Monitoring & Metrics
- ✅ `backend/agents/framework/quality_gate.py` - Quality Validation
- ✅ `backend/agents/framework/retry_handler.py` - Error Handling
- ✅ `backend/agents/framework/streaming_manager.py` - Streaming Support

### Documentation
- ✅ `AGENT_SYSTEM_ANALYSIS.md` - Architektur-Übersicht
- ✅ `AGENT_SYSTEM_CRITICAL_ASSESSMENT.md` - Problem-Analyse
- ✅ `AGENT_SYSTEM_QUICK_REFERENCE.md` - Quick Start
- ✅ `AGENT_MIGRATION_STRATEGY.md` - Dieses Dokument

---

## ⚠️ Risiken & Mitigations-Strategien

| Risiko | Wahrscheinlichkeit | Impact | Mitigation |
|--------|-------------------|--------|-----------|
| **Backward Compatibility Break** | Mittel | Hoch | Legacy Wrapper Methods, Extensive Testing |
| **Performance Degradation** | Niedrig | Hoch | Benchmark vor/nach, Caching Layer |
| **Registry Conflicts** | Niedrig | Mittel | Unique Agent Types, Validation |
| **Deployment Issues** | Mittel | Hoch | Gradual Rollout (Phase by Phase) |
| **Legacy Code Complexity** | Hoch | Mittel | Template-basierte Vereinfachung |

---

## 📞 Kontakt & Support

**Migration Owner:** VERITAS Development Team
**Questions/Issues:** Siehe GitHub Issues oder Contact Development Lead

**Notfall-Fallback:** Alle .bak Dateien archiviert in `archive/agents_cleanup_*/` mit Restore-Möglich keit

---

**Letzte Aktualisierung:** 4. Dezember 2025
**Nächste Review:** 5. Dezember 2025
**Zielabschluss:** 20. Dezember 2025
