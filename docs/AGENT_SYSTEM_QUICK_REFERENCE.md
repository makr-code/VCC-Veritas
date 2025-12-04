# VERITAS Agent System - Quick Reference

**Stand:** 4. Dezember 2025
**Status:** 🔴 Architektur-Fragmentierung identifiziert

## 📊 Auf einen Blick

| Kategorie | Anzahl | BaseAgent | Registry | Status |
|-----------|--------|-----------|----------|--------|
| **Framework** | 17 | ✅ 100% | ✅ Ja | 🟢 Production |
| **Registry** | 4 | ✅ 100% | ✅ Ja | 🟢 Production |
| **Orchestrator** | 3 | ✅ 100% | ✅ Ja | 🟢 Production |
| **Specialized** | 1 | ✅ 100% | ✅ Ja | 🟢 Production |
| **Domain** | 38 | ❌ 2.6% | ❌ Nein | 🔴 Legacy |
| **ThemisDB** | 8 | ✅ 100% | ✅ Ja | 🟢 Production |
| **Root Utils** | 9 | 🟡 50% | 🟡 Teilweise | 🟡 Mixed |

**Gesamt:** 80 Agenten (76 aktiv + 4 __init__.py)

## 🔴 Kritische Probleme

### 1. **97% der Domain Agents ohne Framework**
- Nur 1 von 38 Domain Agents nutzt BaseAgent
- Registry leer (Domain Agents nicht registriert)
- Orchestration unmöglich

### 2. **69 Backup-Dateien (.bak)**
- Mehr Backups als aktive Dateien
- Unklar welche Version produktiv ist

### 3. **Duplikate**
- **5 Wetter-Agenten** (dwd_weather × 2, dwd_simple, dwd_opendata, brightsky)
- **2 Environmental Agenten** (domain/ + specialized/)
- **2 Immissionsschutz-Versionen** (alt + current)

## 🗂️ Domain Agent Struktur

```
backend/agents/domain/
├── chemical/          ← 2 Agenten (Chemikalien-DB)
├── construction/      ← 3 Agenten (Baugenehmigung)
├── database/          ← 2 Agenten (DB-Zugriff)
├── environmental/     ← 5 Agenten (Umwelt, Boden, Wasser)
├── financial/         ← 2 Agenten (Finanzielle Bewertung)
├── immissionsschutz/  ← 5 Agenten (BImSchG) 🟡 Duplikate
├── social/            ← 6 Agenten (Verwaltung, Recht)
├── standards/         ← 2 Agenten (DIN, VDI, ISO)
├── traffic/           ← 2 Agenten (Verkehrsrecht)
├── weather/           ← 6 Agenten (DWD Wetter) 🔴 5 Versionen!
├── wikipedia/         ← 2 Agenten (Wikipedia-Recherche)
└── database_agent.py  ← 1 Root-Agent
```

## 🎯 Empfohlene Sofort-Aktionen

### ✅ Cleanup (2-3 Tage)

```powershell
# 1. Backup-Dateien archivieren
$timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
New-Item -ItemType Directory -Path "archive/agents_backup_$timestamp"
Get-ChildItem -Recurse -Filter "*.bak" | Move-Item -Destination "archive/agents_backup_$timestamp"

# 2. Weather-Duplikate entfernen (nur V2 + BrightSky behalten)
Remove-Item backend/agents/domain/weather/dwd_weather_agent.py
Remove-Item backend/agents/domain/weather/dwd_simple.py
Remove-Item backend/agents/domain/weather/dwd_opendata_agent.py

# 3. Immissionsschutz Legacy entfernen
Remove-Item backend/agents/domain/immissionsschutz/immissionschutz_alt.py

# 4. Environmental Agent klären: Domain vs Specialized
# → Manuelle Prüfung welcher aktiv genutzt wird
```

### 🔧 Migration zu BaseAgent (2-3 Wochen)

**Phase 1 - Top 5 Agents:**
1. `weather/dwd_weather_agent_v2.py`
2. `construction/genehmigung_agent.py`
3. `environmental/environmental_agent.py`
4. `social/verwaltungsrecht_agent.py`
5. `immissionsschutz/immissionsschutz_agent.py`

**Template:**
```python
from backend.agents.framework.base_agent import BaseAgent
from backend.agents.registry.api_agent_registry import AgentCapability

class MigratedDomainAgent(BaseAgent):
    def get_agent_type(self) -> str:
        return "agent_name"

    def get_capabilities(self) -> List[AgentCapability]:
        return [AgentCapability.DOMAIN_SPECIFIC]

    async def process_query(self, query: str) -> Dict:
        # Legacy query() Logik hier integrieren
        return self._legacy_query(query)
```

## 📋 Detaillierte Dokumentation

Siehe:
- **Architektur-Übersicht:** `AGENT_SYSTEM_ANALYSIS.md`
- **Domain Agent Details:** `DOMAIN_AGENTS_DETAILED.md`
- **Kritische Bewertung:** `AGENT_SYSTEM_CRITICAL_ASSESSMENT.md`

## 🎨 Agent-Architektur (Sollzustand)

```
┌─────────────────────────────────────────────┐
│          Agent Registry (Singleton)         │
│  • Agent Discovery by Capability            │
│  • Lifecycle Management                     │
│  • Instance Pooling                         │
└─────────────────────────────────────────────┘
                    ▲
                    │ register_agent()
                    │
    ┌───────────────┴───────────────┬─────────────┐
    │                               │             │
┌───▼────┐                   ┌──────▼─────┐ ┌────▼─────┐
│Framework│                   │  Domain    │ │Specialized│
│ Agents │                   │  Agents    │ │  Agents  │
│(17)    │                   │   (38)     │ │   (1)    │
└────────┘                   └────────────┘ └──────────┘
    │                               │             │
    └───────────────┬───────────────┴─────────────┘
                    │ extends
                    ▼
         ┌──────────────────────┐
         │  BaseAgent (ABC)     │
         │  • get_agent_type()  │
         │  • get_capabilities()│
         │  • process_query()   │
         └──────────────────────┘
```

**Problem:** 97% der Domain Agents (rot markiert) implementieren NICHT BaseAgent!

## 📞 Kontakt

**Verantwortlich für Agent-System:** [Team Name]
**Kritikalität:** 🔴 HOCH
**Nächste Review:** [Datum nach Entscheidung]

---

**Letzte Aktualisierung:** 4. Dezember 2025
