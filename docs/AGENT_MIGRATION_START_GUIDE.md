# 🚀 VERITAS Agent Framework Migration - Start Guide

**Status:** Phase 1 In Progress (2/38 Agents)
**Datum:** 4. Dezember 2025
**Ziel:** 100% Framework-Integration aller Domain Agents

## 📋 Was wurde heute erreicht?

### ✅ Kern-Infrastruktur
- **BaseAgent Migration Template** - Vorlage für alle Agenten-Migrationen
- **Registry-System** - Zentrale Agent-Registrierung & Discovery
- **Migration Tools** - Automatisierte Cleanup & Bulk-Migration
- **Dokumentation** - Umfassende Migrations-Guides

### ✅ Agents Migriert (2/38 = 5.3%)
| Agent | Status | Datei |
|-------|--------|-------|
| **GenehmigungAgent** | ✅ BaseAgent v2.0 | `construction/genehmigung_agent.py` |
| **DwdWeatherAgent** | ✅ BaseAgent v3_framework | `weather/dwd_weather_agent_v3_framework.py` |

### ✅ Cleanup Abgeschlossen
- 21 Merge-Konflikte automatisch aufgelöst
- 4 Wetter-Agent Duplikate archiviert
- 1 Immissionsschutz Legacy-Version archiviert
- Alle .bak Dateien archiviert (keine im Code)

---

## 🎯 Migration Roadmap

```
Phase 1 (diese Woche) ━━━━━━━━━━━━━━━━━━━━━━━━ [40% done]
  ✅ GenehmigungAgent
  ✅ DwdWeatherAgent
  🚀 ConstructionAgent (nächst)
  🚀 EnvironmentalAgent (nächst)
  🟡 VerwaltungsrechtWorker (teils kompatibel)

Phase 2 (Woche 2) ━━━━━━━━━━━━━━━━━━━━━━━━━━━ [15 Agents]
  🏢 Weather, Environmental, Immissionsschutz
  ⚖️ Legal & Social Agents
  🔧 Technical & Standards

Phase 3 (Woche 3) ━━━━━━━━━━━━━━━━━━━━━━━━━━━ [Finalize + Features]
  📊 Framework Extensions (Caching, Monitoring, etc.)
  🧪 Full Test Coverage
  🚀 Production Ready
```

---

## 🛠️ Verwendung für nächste Agents

### Schnelle Migration eines Agents (z.B. ConstructionAgent)

```bash
# 1. Template kopieren
cp backend/agents/templates/baseagent_migration_template.py \
   backend/agents/domain/construction/construction_agent_v2.py

# 2. Manuelle Migration (einfach):
# - Öffne Datei
# - Ersetze [DOMAIN_NAME] durch "construction"
# - Integriere Original-Logik aus construction_agent.py
# - Test & Registriere

# 3. Oder: Auto-Migration via Accelerator (komplexer)
python backend/agents/migration/migration_accelerator.py \
  --mode=migrate \
  --agents=construction
```

### Registry Integration

```python
# Neue Agent automatisch registriert via:
from backend.agents.registry.domain_agent_registration import register_phase1_agents

register_phase1_agents()

# Oder manuell in domain_agent_registration.py registrieren:
registry.register_agent(
    agent_type="construction",
    agent_class=ConstructionAgent,
    capabilities=[AgentCapability.LEGAL_FRAMEWORK],
    lifecycle_type=AgentLifecycleType.ON_DEMAND,
    max_concurrent_instances=2
)
```

---

## 📁 Projekt-Struktur

```
backend/agents/
├── framework/               ← Framework Core (17 Komponenten)
│   ├── base_agent.py       ← BaseAgent ABC (alle Agents erben)
│   ├── agent_monitoring.py ← Monitoring & Metriken
│   ├── quality_gate.py     ← Qualitätsprüfung
│   └── retry_handler.py    ← Fehlerbehandlung
│
├── registry/               ← Agent Registry (Zentrale Discovery)
│   ├── agent_registry.py
│   ├── api_agent_registry.py
│   └── domain_agent_registration.py ← Alle Agents hier registriert!
│
├── domain/                 ← Domain Agents (38 Agenten)
│   ├── construction/
│   │   ├── genehmigung_agent.py       ✅ Migriert
│   │   └── construction_agent.py      🚀 Nächst
│   ├── weather/
│   │   ├── dwd_weather_agent_v3_framework.py ✅ Neu/Migriert
│   │   └── brightsky_weather_agent.py 🚀 Phase 2
│   ├── environmental/
│   │   └── environmental_agent.py     🚀 Nächst
│   └── ... weitere Domains
│
├── templates/              ← Migration Vorlagen
│   └── baseagent_migration_template.py ← Kopiere für neue Agents
│
├── migration/              ← Migration Tools
│   ├── migration_accelerator.py ← Batch Migration Tool
│   └── cleanup_script.py   ← Cleanup & Archivierung
│
└── orchestrator/           ← Agent Orchestration
    ├── agent_orchestrator.py
    └── pipeline_manager.py
```

---

## 📚 Dokumentation

| Dokument | Inhalt | Wann lesen |
|----------|--------|-----------|
| **AGENT_MIGRATION_STRATEGY.md** | Vollständiger Migrations-Plan | Start der Migration |
| **baseagent_migration_template.py** | Template für neue Agents | Vor Agent-Migration |
| **AGENT_SYSTEM_ANALYSIS.md** | Architektur-Details | Verständnis aufbauen |
| **DOMAIN_AGENTS_DETAILED.md** | Agent-Übersicht | Bei Agent-Recherche |
| **AGENT_SYSTEM_CRITICAL_ASSESSMENT.md** | Problem-Analyse | Kontext verstehen |
| **AGENT_SYSTEM_QUICK_REFERENCE.md** | Quick Start | Schnelle Übersicht |

---

## 🚀 Quick Start für Entwickler

### Agent migrieren (5 Schritte)

```python
# 1. BaseAgent importieren
from backend.agents.framework.base_agent import BaseAgent
from backend.agents.registry.api_agent_registry import AgentCapability, AgentLifecycleType

# 2. Klasse erstellen und erben
class MyAgent(BaseAgent):
    AGENT_TYPE = "my_agent"

    def get_agent_type(self) -> str:
        return self.AGENT_TYPE

    def get_capabilities(self) -> List[AgentCapability]:
        return [AgentCapability.QUERY_PROCESSING]

    async def process_query(self, query: str) -> Dict:
        # Ursprüngliche Logik hier
        return {"success": True, "results": []}

# 3. Registrieren
from backend.agents.registry.api_agent_registry import get_agent_registry
registry = get_agent_registry()
registry.register_agent(
    agent_type="my_agent",
    agent_class=MyAgent,
    capabilities=[AgentCapability.QUERY_PROCESSING],
    lifecycle_type=AgentLifecycleType.ON_DEMAND
)

# 4. Verwenden
agent = registry.get_agent_for_capability(AgentCapability.QUERY_PROCESSING)
result = await agent.process_query("test")

# 5. Testen
pytest tests/test_my_agent.py
```

---

## ⚡ Performance & Features

### Neue Framework-Features

✅ **Lifecycle Management**
- ON_DEMAND: Erstelle auf Request
- POOLED: Wiederverwendbare Instanzen
- PERSISTENT: Immer im Speicher

✅ **Monitoring & Metrics**
- Query Count, Response Time, Error Rate
- Performance Dashboard (Prometheus-export ready)

✅ **Quality Gates**
- Confidence Scoring
- Result Validation
- Auto-Retry Logik

✅ **Async/Await Support**
- Non-blocking Query Processing
- Concurrent Agent Execution
- Streaming Support

---

## 🔍 Registry Discovery Beispiele

```python
from backend.agents.registry.api_agent_registry import (
    get_agent_registry, AgentCapability
)

registry = get_agent_registry()

# 1. Alle Agents finden mit Capability
weather_agents = registry.get_agents_by_capability(AgentCapability.WEATHER_DATA)

# 2. Beste Agent für Capability auswählen
agent = registry.get_agent_for_capability(AgentCapability.LEGAL_FRAMEWORK)

# 3. Agent by Type suchen
genehmigung = registry.get_agent("genehmigung")

# 4. Alle Agents auflisten
all_agents = registry.list_all_agents()

# 5. Statistics
stats = registry.get_statistics()
print(f"Total agents: {stats['total_agents']}")
print(f"Total queries: {stats['total_queries']}")
print(f"Avg response time: {stats['avg_response_time']}ms")
```

---

## ✅ Checkliste für Migration

### Für jeden Agent:

```
[ ] 1. Merge-Konflikte gelöst (auto oder manual)
[ ] 2. Template kopiert & angepasst
[ ] 3. Original-Logik integriert (_legacy_query)
[ ] 4. Capabilities definiert (get_capabilities)
[ ] 5. In domain_agent_registration.py registriert
[ ] 6. Unit Tests geschrieben (pytest)
[ ] 7. Integration Test mit Registry
[ ] 8. E2E Test mit Orchestrator
[ ] 9. Git Commit & Push
[ ] 10. Code Review & Merge
```

---

## 🎯 Nächste Schritte

### Tag 2 (morgen)
1. **ConstructionAgent** migrieren (ähnlich zu Genehmigung)
2. **EnvironmentalAgent** migrieren (komplexer, aber gutes Template-Beispiel)
3. **Phase 1 Tests** schreiben
4. **Registry Tests** durchführen

### Woche 2
1. **Phase 2 Planning** - 15 Agents in 3er-Teams
2. **Parallel Migration** - 3 Developer Teams
3. **Integration Tests** - Täglich
4. **Performance Baseline** - Benchmark

### Woche 3
1. **Phase 3 Finalization** - Restliche Agents
2. **Framework Extensions** - Caching, Monitoring, etc.
3. **Production Ready** - Full Test Coverage
4. **Deployment** - Schrittweise Rollout

---

## 💡 Tipps für erfolgreiche Migration

### ✅ Best Practices
1. **Template verwenden** - 80% der Arbeit ist gleich
2. **Legacy-Logik bewahren** - Keine Refactorings während Migration
3. **Tests früh schreiben** - TDD für Migrationen
4. **Incremental Commits** - Viele kleine, nachverfolgbare Commits
5. **Registry-Integration testen** - Discovery funktioniert?

### ⚠️ Häufige Fehler
1. ❌ Zu viel Refactoring (nur migrieren!)
2. ❌ Capabilities vergessen (leere Liste)
3. ❌ Registry nicht testen
4. ❌ Async nicht beachten (await missing)
5. ❌ Legacy-Tests nicht portieren

---

## 📞 Support & Fragen

**Wenn stuck:**
1. Siehe `AGENT_MIGRATION_STRATEGY.md` - Vollständiger Plan
2. Siehe `baseagent_migration_template.py` - Template studieren
3. Siehe `GenehmigungAgent` → `DwdWeatherAgent` - Gute Beispiele
4. Siehe `backend/agents/tests/` - Existing Tests als Referenz

**Migration Owner:** VERITAS Development Team

---

## 📊 Progress Tracking

**Aktueller Stand: 2/38 Agents (5.3%)**

```
Phase 1: ████░░░░░░░░░░░░░ 40% (2/5)
Phase 2: ░░░░░░░░░░░░░░░░░░  0% (0/15)
Phase 3: ░░░░░░░░░░░░░░░░░░  0% (0/18+)
─────────────────────────────
TOTAL:  ░░░░░░░░░░░░░░░░░░  5% (2/38)
```

**Ziel: 100% by 20. Dezember 2025** ✅

---

**Viel Erfolg mit der Migration! 🚀**

Für Fragen: Siehe Dokumentation oder GitHub Issues
