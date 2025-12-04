# Legacy Code Inventory - VERITAS Agent System

**Datum:** 4. Dezember 2025
**Zweck:** Identifikation von Legacy-Code zur Entfernung nach Phase 2

---

## 📋 Agent Inventory

### ✅ Phase 1 - Migriert (BaseAgent v2.0)
| Agent | Status | Legacy Version | Action |
|-------|--------|----------------|--------|
| **GenehmigungAgent** | ✅ v2.0 | - | Keep |
| **DwdWeatherAgent** | ✅ v3.0 | - | Keep |
| **ConstructionAgent** | ✅ v2.0 Framework | construction_agent.py | Delete Legacy |
| **EnvironmentalAgent** | ✅ v2.0 Framework | environmental_agent.py | Delete Legacy |

### 🔄 Phase 2 - Zu Migrieren (5 Agents)

#### Environmental Domain (3 Agents)
| Agent | File | Status | Priority |
|-------|------|--------|----------|
| **NaturschutzAgent** | naturschutz_agent.py | Legacy | HIGH |
| **BodenGewaesserschutzAgent** | boden_gewaesserschutz_agent.py | Legacy | HIGH |
| **EmissionenMonitoringAgent** | emissionen_monitoring_agent.py | Legacy | HIGH |

#### Immissionsschutz Domain (1 Agent)
| Agent | File | Status | Priority |
|-------|------|--------|----------|
| **ImmissionsschutzAgent** | immissionsschutz_agent.py | Legacy | HIGH |

#### Weather Domain (1 Agent)
| Agent | File | Status | Priority |
|-------|------|--------|----------|
| **BrightSkyWeatherAgent** | brightsky_weather_agent.py | Legacy | MEDIUM |

### 📦 Phase 3+ - Backlog (10+ Agents)

#### Social/Legal Domain (4 Agents)
- VerwaltungsrechtAgent (verwaltungsrecht_agent.py)
- VerwaltungsprozessAgent (verwaltungsprozess_agent.py)
- SocialAgent (social_agent.py)
- RechtsrechercheAgent (rechtsrecherche_agent.py)

#### Technical/Infrastructure (3 Agents)
- DatabaseAgent (database_agent.py)
- TechnicalStandardsAgent (technical_standards_agent.py)
- FinancialAgent (financial_agent.py)

#### Other Domains (3 Agents)
- TrafficAgent (traffic_agent.py)
- WikipediaAgent (wikipedia_agent.py)
- ChemicalDataAgent (chemical_data_agent.py)

---

## 🗑️ Legacy Files - Removal Plan

### 1. Duplicate Agent Files (DELETE AFTER MIGRATION)

#### Construction Domain
```
backend/agents/domain/construction/
  ✅ construction_agent_v2_framework.py    [KEEP - Production v2.0]
  ❌ construction_agent.py                  [DELETE - Legacy duplicate]
```

#### Environmental Domain
```
backend/agents/domain/environmental/
  ✅ environmental_agent_v2_framework.py   [KEEP - Production v2.0]
  ❌ environmental_agent.py                 [DELETE - Legacy duplicate]
  🔄 naturschutz_agent.py                   [MIGRATE → DELETE]
  🔄 boden_gewaesserschutz_agent.py         [MIGRATE → DELETE]
  🔄 emissionen_monitoring_agent.py         [MIGRATE → DELETE]
```

#### Weather Domain
```
backend/agents/domain/weather/
  ✅ dwd_weather_agent_v3_framework.py     [KEEP - Production v3.0]
  🔄 brightsky_weather_agent.py             [MIGRATE → DELETE]
```

### 2. Legacy Wrapper Files (REVIEW & DELETE)

**Locations to check:**
```
backend/agents/*.py                        # Root-level agent wrappers
backend/agents/domain/*/orchestrator.py    # Domain orchestrators
backend/adapters/*/legacy_*.py             # Legacy adapters
shared/legacy/                             # Legacy utilities
```

### 3. Backup Files (ALREADY CLEANED)
```
✅ 69 .bak files archived to backups/
✅ 5 weather agent duplicates consolidated
✅ 21 merge conflicts resolved
```

---

## 🔍 Dependency Analysis

### Critical Dependencies zu prüfen:

#### 1. Legacy Agent Imports
```bash
# Finde alle Importe von Legacy-Agents
grep -r "from.*construction_agent import" backend/
grep -r "from.*environmental_agent import" backend/
grep -r "import.*construction_agent" backend/
```

#### 2. Registry Registrationen
```python
# Prüfe domain_agent_registration.py
backend/agents/registry/domain_agent_registration.py
- Welche Agents sind registriert?
- Welche nutzen Legacy-Klassen?
```

#### 3. API Endpoints
```python
# Prüfe API-Router
backend/api/v3/*_router.py
backend/api/veritas_api_*.py
- Welche Endpoints nutzen Agents?
- Direct imports vs Registry lookup?
```

#### 4. Test Files
```python
# Prüfe Test-Importe
tests/agents/test_*.py
tests/integration/test_*.py
- Welche Tests nutzen Legacy-Agents?
- Migration zu neuen Agents erforderlich?
```

---

## 📊 Legacy Code Metrics

### Geschätzte Legacy Code-Menge

| Kategorie | Files | LOC | Action |
|-----------|-------|-----|--------|
| **Duplicate Agents** | 2 | ~800 | DELETE |
| **Legacy Agents (Phase 2)** | 5 | ~2,000 | MIGRATE → DELETE |
| **Legacy Agents (Phase 3+)** | 10+ | ~5,000+ | MIGRATE → DELETE |
| **Legacy Wrappers** | TBD | TBD | REVIEW |
| **Backup Files** | 0 | 0 | ✅ DONE |

**Total zu entfernen (nach Migration):** ~7,800+ LOC

---

## 🛠️ Legacy Removal Workflow

### Phase 2 Workflow pro Agent:

```
1. ✅ Legacy Agent analysieren
2. ✅ BaseAgent v2.0 Implementation erstellen
3. ✅ Tests migrieren/erweitern
4. ✅ Benchmarks erstellen
5. ✅ Registry Registration
6. ✅ Dependency Check (wer nutzt Legacy?)
7. ✅ Dependencies migrieren
8. ✅ Tests ausführen (100% PASS)
9. ✅ Legacy File löschen
10. ✅ Documentation Update
```

### Safety Checklist vor Löschung:

- [ ] Neuer Agent komplett getestet
- [ ] Alle Dependencies migriert
- [ ] Keine Importe des Legacy-Agents gefunden
- [ ] Registry verwendet neue Version
- [ ] API Endpoints verwenden Registry
- [ ] Integration Tests PASS
- [ ] Backup erstellt (git branch)
- [ ] Code Review approved

---

## 📈 Phase 2 Progress Tracking

### Week 1: Migration (5 Agents)
- [ ] NaturschutzAgent → v2.0
- [ ] BodenGewaesserschutzAgent → v2.0
- [ ] EmissionenMonitoringAgent → v2.0
- [ ] ImmissionsschutzAgent → v2.0
- [ ] BrightSkyWeatherAgent → v2.0

### Week 2: Testing & Validation
- [ ] 50+ Unit Tests für Phase 2
- [ ] 10+ Benchmarks
- [ ] Integration Tests
- [ ] Performance Validation

### Week 3: Cleanup & Consolidation
- [ ] Legacy Dependencies migrieren
- [ ] Duplicate Files löschen
- [ ] Wrapper eliminieren
- [ ] Code Consolidation

### Week 4: Documentation & Deployment
- [ ] Phase 2 Documentation
- [ ] Migration Guide Update
- [ ] Production Deployment
- [ ] Legacy Code Archive

---

## 🎯 Success Criteria

### Phase 2 Complete wenn:
- [x] 5 neue Agents in BaseAgent v2.0
- [x] 100% Test Coverage für neue Agents
- [x] Alle Benchmarks PASS
- [x] Legacy Dependencies eliminiert
- [x] Duplicate Files gelöscht
- [x] Code-Reduktion: -2,000+ LOC

### Legacy Removal Complete wenn:
- [ ] Alle Agents migriert (Phase 1-3)
- [ ] Zero Legacy-Importe
- [ ] Zero Duplicate Files
- [ ] Wrapper konsolidiert
- [ ] Code-Reduktion: -7,800+ LOC
- [ ] Codebase < 30,000 LOC (vs. aktuell ~35,000)

---

## 🚨 Risks & Mitigation

### Risk 1: Breaking Dependencies
**Mitigation:** Comprehensive dependency scan vor jeder Löschung

### Risk 2: Lost Functionality
**Mitigation:** Feature parity check zwischen Legacy & v2.0

### Risk 3: Test Coverage Gaps
**Mitigation:** Minimum 80% Coverage vor Legacy Removal

### Risk 4: Performance Regression
**Mitigation:** Benchmark comparison Legacy vs v2.0

---

## 📝 Next Actions

### Immediate (Diese Session):
1. ✅ Inventory erstellt
2. 🔄 Dependency Analysis starten
3. 🔄 Phase 2 Agent Migration beginnen
4. 🔄 Tests für erste 2 Agents

### Short-term (Diese Woche):
1. Alle 5 Phase 2 Agents migrieren
2. Legacy Dependencies identifizieren
3. Duplicate Files vorbereiten für Löschung
4. Test Suite erweitern

### Mid-term (Nächste 2 Wochen):
1. Phase 2 Complete
2. Legacy Code Cleanup Start
3. Code Consolidation
4. Documentation Update

---

**Status:** Phase 2 STARTED
**Target:** 5 Agents migriert, Legacy Code entfernt
**Timeline:** 2-3 Wochen
**Risk Level:** LOW (mit Safety Checklist)
