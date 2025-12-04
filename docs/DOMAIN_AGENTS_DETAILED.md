# VERITAS Domain Agents - Detaillierte Übersicht

**Analysiert am:** 4. Dezember 2025
**Ort:** `backend/agents/domain/`
**Struktur:** Hierarchisch organisiert in 8 Fachbereichen

## 📊 Übersicht

| Bereich | Unterordner | Agenten | Status |
|---------|-------------|---------|--------|
| **Datenbank** | `database/` | 2 | ✅ Aktiv |
| **Chemie** | `chemical/` | 2 | ✅ Aktiv |
| **Bau/Genehmigung** | `construction/` | 3 | ✅ Aktiv |
| **Umwelt** | `environmental/` | 5 | ✅ Aktiv |
| **Finanzen** | `financial/` | 2 | ✅ Aktiv |
| **Immissionsschutz** | `immissionsschutz/` | 5 | 🟡 Duplikate |
| **Verwaltung/Recht** | `social/` | 6 | ✅ Aktiv |
| **Standards** | `standards/` | 2 | ✅ Aktiv |
| **Verkehr** | `traffic/` | 2 | ✅ Aktiv |
| **Wetter** | `weather/` | 6 | 🟡 Duplikate |
| **Wikipedia** | `wikipedia/` | 2 | ✅ Aktiv |
| **Root** | - | 1 | ✅ Aktiv |

**Gesamt:** 38 Python-Dateien (ohne .bak)

## 🗂️ Detaillierte Agent-Liste

### 1️⃣ Database Agents

#### 📁 `database/`

| Agent | Datei | Zweck | Status |
|-------|-------|-------|--------|
| TestServerExtension | `testserver_extension.py` | DB-Testserver Integration | ✅ |
| __init__ | `__init__.py` | Package Init | ✅ |

#### 📄 Root-Level

| Agent | Datei | Zweck | Status |
|-------|-------|-------|--------|
| DatabaseAgent | `database_agent.py` | Haupt-DB-Agent | ✅ |

**Funktionen:**
- Datenbank-Queries
- Schema-Verwaltung
- Test-Datenbank-Integration

---

### 2️⃣ Chemical Agents

#### 📁 `chemical/`

| Agent | Datei | Zweck | Status |
|-------|-------|-------|--------|
| ChemicalDataAgent | `chemical_data_agent.py` | Chemikalien-Datenbank | ✅ |
| __init__ | `__init__.py` | Package Init | ✅ |

**Funktionen:**
- Chemikalien-Informationen
- Sicherheitsdatenblätter
- Stoffdatenbank-Zugriff

---

### 3️⃣ Construction Agents

#### 📁 `construction/`

| Agent | Datei | Zweck | Status |
|-------|-------|-------|--------|
| ConstructionAgent | `construction_agent.py` | Allgemeine Bauvorhaben | ✅ |
| GenehmigungAgent | `genehmigung_agent.py` | Baugenehmigungsverfahren | ✅ |
| __init__ | `__init__.py` | Package Init | ✅ |

**Funktionen:**
- Baugenehmigungsverfahren
- Baurecht-Recherche
- Genehmigungspflicht-Prüfung
- Zuständigkeiten

---

### 4️⃣ Environmental Agents

#### 📁 `environmental/`

| Agent | Datei | Zweck | Status |
|-------|-------|-------|--------|
| BodenGewaesserschutzAgent | `boden_gewaesserschutz_agent.py` | Boden- & Gewässerschutz | ✅ |
| EmissionenMonitoringAgent | `emissionen_monitoring_agent.py` | Emissionsüberwachung | ✅ |
| EnvironmentalAgent | `environmental_agent.py` | Allgemeiner Umwelt-Agent | ✅ |
| NaturschutzAgent | `naturschutz_agent.py` | Naturschutzrecht | ✅ |
| __init__ | `__init__.py` | Package Init | ✅ |

**Funktionen:**
- Umweltschutzrecht
- Bodenschutz & Gewässerschutz
- Naturschutz & FFH-Gebiete
- Emissionsüberwachung
- Umweltverträglichkeitsprüfung (UVP)

**⚠️ Hinweis:**
- Spezialisierter `EnvironmentalAgent` auch in `backend/agents/specialized/`
- Möglicherweise Duplikate oder unterschiedliche Zwecke

---

### 5️⃣ Financial Agents

#### 📁 `financial/`

| Agent | Datei | Zweck | Status |
|-------|-------|-------|--------|
| FinancialAgent | `financial_agent.py` | Finanzielle Aspekte | ✅ |
| __init__ | `__init__.py` | Package Init | ✅ |

**Funktionen:**
- Gebührenberechnung
- Kostenabschätzung
- Finanzielle Bewertung von Vorhaben

---

### 6️⃣ Immissionsschutz Agents

#### 📁 `immissionsschutz/`

| Agent | Datei | Zweck | Status |
|-------|-------|-------|--------|
| ImmissionsschutzAlt | `immissionschutz_alt.py` | Legacy-Version | 🟡 |
| ImmissionsschutzAgent | `immissionsschutz_agent.py` | Aktueller Agent | ✅ |
| Orchestrator | `orchestrator.py` | Immissionsschutz-Orchestrator | ✅ |
| TestServerExtension | `testserver_extension.py` | Test-Integration | ✅ |
| __init__ | `__init__.py` | Package Init | ✅ |

**Funktionen:**
- BImSchG-Genehmigungen (Bundesimmissionsschutzgesetz)
- 4. und 13. BImSchV
- Emissionsgrenzwerte
- Genehmigungspflichtige Anlagen

**🔴 Problem:**
- **Zwei Versionen:** `immissionschutz_alt.py` und `immissionsschutz_agent.py`
- **Empfehlung:** Legacy-Version (`alt`) entfernen oder archivieren
- **Orchestrator:** Eigener Orchestrator nur für Immissionsschutz? Redundant?

---

### 7️⃣ Social/Legal/Administrative Agents

#### 📁 `social/`

| Agent | Datei | Zweck | Status |
|-------|-------|-------|--------|
| RechtsrechercheAgent | `rechtsrecherche_agent.py` | Rechtsrecherche | ✅ |
| SocialAgent | `social_agent.py` | Soziale Aspekte | ✅ |
| VerwaltungsprozessAgent | `verwaltungsprozess_agent.py` | Verwaltungsverfahren | ✅ |
| VerwaltungsrechtAgent | `verwaltungsrecht_agent.py` | Verwaltungsrecht | ✅ |
| VerwaltungsrechtWorker | `verwaltungsrecht_worker.py` | Verwaltungsrecht Worker | ✅ |
| __init__ | `__init__.py` | Package Init | ✅ |

**Funktionen:**
- Rechtsrecherche (Gesetze, Verordnungen)
- Verwaltungsverfahren
- Verwaltungsrecht (VwVfG)
- Soziale Auswirkungen
- Beteiligungsverfahren

**🟡 Hinweis:**
- **VerwaltungsrechtAgent + Worker:** Worker-Pattern implementiert
- Möglicherweise parallele Verarbeitung

---

### 8️⃣ Technical Standards Agents

#### 📁 `standards/`

| Agent | Datei | Zweck | Status |
|-------|-------|-------|--------|
| TechnicalStandardsAgent | `technical_standards_agent.py` | Technische Normen | ✅ |
| __init__ | `__init__.py` | Package Init | ✅ |

**Funktionen:**
- DIN-Normen
- VDI-Richtlinien
- ISO-Standards
- Technische Regelwerke

---

### 9️⃣ Traffic Agents

#### 📁 `traffic/`

| Agent | Datei | Zweck | Status |
|-------|-------|-------|--------|
| TrafficAgent | `traffic_agent.py` | Verkehrsrecht | ✅ |
| __init__ | `__init__.py` | Package Init | ✅ |

**Funktionen:**
- Verkehrsrecht
- Straßenverkehrsordnung
- Verkehrsgenehmigungen

---

### 🔟 Weather Agents

#### 📁 `weather/`

| Agent | Datei | Zweck | Status |
|-------|-------|-------|--------|
| BrightSkyWeatherAgent | `brightsky_weather_agent.py` | BrightSky API | ✅ |
| DwdOpenDataAgent | `dwd_opendata_agent.py` | DWD Open Data | ✅ |
| DwdSimple | `dwd_simple.py` | DWD Simple | ✅ |
| DwdWeatherAgent | `dwd_weather_agent.py` | DWD Weather v1 | ✅ |
| DwdWeatherAgentV2 | `dwd_weather_agent_v2.py` | DWD Weather v2 | ✅ |
| __init__ | `__init__.py` | Package Init | ✅ |

**Funktionen:**
- Wetterdaten (Deutscher Wetterdienst)
- BrightSky API Integration
- DWD Open Data API
- Wettervorhersagen
- Historische Wetterdaten

**🔴 Problem:**
- **Fünf verschiedene Wetter-Agenten!**
  - `brightsky_weather_agent.py`
  - `dwd_opendata_agent.py`
  - `dwd_simple.py`
  - `dwd_weather_agent.py`
  - `dwd_weather_agent_v2.py`

**Empfehlung:**
1. Welcher Agent ist der aktuelle?
2. Legacy-Agenten archivieren
3. Ein einheitlicher Wetter-Agent mit verschiedenen Backends

---

### 1️⃣1️⃣ Wikipedia Agents

#### 📁 `wikipedia/`

| Agent | Datei | Zweck | Status |
|-------|-------|-------|--------|
| WikipediaAgent | `wikipedia_agent.py` | Wikipedia-Recherche | ✅ |
| __init__ | `__init__.py` | Package Init | ✅ |

**Funktionen:**
- Wikipedia-Artikel-Recherche
- Hintergrundinformationen
- Begriffsklärung

---

## 🔍 Analyse & Findings

### ✅ Positive Aspekte

1. **Klare Organisation:**
   - Agenten in Fachbereiche gruppiert
   - Hierarchische Struktur logisch
   - `__init__.py` für jedes Package

2. **Breite Abdeckung:**
   - Umweltrecht ✅
   - Baurecht ✅
   - Verwaltungsrecht ✅
   - Immissionsschutz ✅
   - Technische Daten (Wetter, Chemie) ✅

3. **Spezialisierung:**
   - Jeder Agent hat klaren Fokus
   - Domain-spezifisches Wissen

### 🔴 Probleme

#### 1. **Duplikate & Versionen**

**Wetter-Agenten (5 Versionen!):**
```
weather/
├── brightsky_weather_agent.py
├── dwd_opendata_agent.py
├── dwd_simple.py
├── dwd_weather_agent.py
└── dwd_weather_agent_v2.py
```
**Frage:** Welcher ist aktiv? Warum 5 Versionen?

**Immissionsschutz (2 Versionen):**
```
immissionsschutz/
├── immissionschutz_alt.py  ← Legacy
└── immissionsschutz_agent.py  ← Aktiv?
```

**Environmental (2 Versionen):**
```
domain/environmental/environmental_agent.py
specialized/environmental_agent.py
```

#### 2. **69 Backup-Dateien (.bak)**
- **Problem:** 69 .bak Dateien im agents/ Verzeichnis
- **Risiko:** Verwirrung über aktive Version
- **Empfehlung:** Alle .bak in Archiv verschieben

#### 3. **Fehlende Standardisierung**
- Nicht klar ob alle Agenten BaseAgent implementieren
- Capabilities nicht dokumentiert
- Registry-Integration unklar

#### 4. **Test-Dateien im Production Code**
```
immissionsschutz/testserver_extension.py
database/testserver_extension.py
```
**Frage:** Sind das Production-Extensions oder Tests?

### 🟡 Verbesserungspotenzial

#### 1. **Konsolidierung nötig:**
- **Wetter:** 5 Agenten → 1 Agent mit verschiedenen Backends
- **Immissionsschutz:** 2 Versionen → 1 aktive Version
- **Environmental:** 2 Versionen → Klären welcher wofür

#### 2. **Capability Mapping fehlt:**
Für jeden Agent dokumentieren:
```python
class WetterAgent(BaseAgent):
    def get_capabilities(self) -> List[str]:
        return [
            AgentCapability.WEATHER_DATA,
            AgentCapability.EXTERNAL_API,
            AgentCapability.HISTORICAL_DATA
        ]
```

#### 3. **Registry-Integration prüfen:**
Sind alle Agenten registriert?
```python
# In backend/agents/registry/agent_registry.py
def _register_all_agents():
    # Alle domain agents hier?
    registry.register_agent("weather", DwdWeatherAgentV2, ...)
    registry.register_agent("construction", GenehmigungAgent, ...)
    # etc.
```

## 📋 Empfohlene Aktionen

### 🔴 Kritisch (Sofort)

1. **Backup-Dateien entfernen:**
   ```powershell
   # Alle .bak in Archiv
   $timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
   New-Item -ItemType Directory -Path "c:\VCC\veritas\archive\agents_backup_$timestamp"
   Get-ChildItem -Path "c:\VCC\veritas\backend\agents" -Recurse -Filter "*.bak" |
       Move-Item -Destination "c:\VCC\veritas\archive\agents_backup_$timestamp"
   ```

2. **Legacy-Agenten identifizieren:**
   - `immissionschutz_alt.py` → Archivieren oder löschen
   - Wetter-Agenten: Welcher ist aktiv?
     - Empfehlung: Nur `dwd_weather_agent_v2.py` behalten
     - Andere als `_legacy.py` markieren

### 🟡 Wichtig (diese Woche)

3. **Capability Audit:**
   - Für jeden Agent prüfen:
     - Implementiert BaseAgent? ✅/❌
     - get_capabilities() vorhanden? ✅/❌
     - get_agent_type() vorhanden? ✅/❌

4. **Registry-Integration prüfen:**
   ```python
   # Script erstellen: check_agent_registration.py
   from backend.agents.registry import get_agent_registry

   registry = get_agent_registry()
   registered = registry.list_all_agents()

   # Vergleichen mit tatsächlichen Agenten
   ```

5. **Dokumentation erstellen:**
   - `AGENT_CAPABILITIES_MATRIX.md`
   - Welcher Agent für welchen Use Case?
   - API-Beispiele

### 🟢 Optimierung (nächster Sprint)

6. **Konsolidierung:**
   - Wetter-Agenten vereinheitlichen
   - Environmental-Agenten klären
   - Test-Extensions in tests/ verschieben

7. **Performance Testing:**
   - Load-Tests für häufig genutzte Agenten
   - Response-Time Tracking

8. **Integration Tests:**
   - E2E-Tests für alle Domain-Agenten
   - Registry-Integration testen

## 📊 Statistik

### Agent-Kategorien

| Kategorie | Anzahl | % |
|-----------|--------|---|
| Wetter | 6 | 15.8% |
| Verwaltung/Recht | 6 | 15.8% |
| Umwelt | 5 | 13.2% |
| Immissionsschutz | 5 | 13.2% |
| Bau | 3 | 7.9% |
| Datenbank | 2 | 5.3% |
| Chemie | 2 | 5.3% |
| Finanzen | 2 | 5.3% |
| Wikipedia | 2 | 5.3% |
| Standards | 2 | 5.3% |
| Verkehr | 2 | 5.3% |
| **Gesamt** | **38** | **100%** |

### Duplikate & Versionen

| Bereich | Versionen | Problem |
|---------|-----------|---------|
| Wetter | 5 | 🔴 Zu viele |
| Immissionsschutz | 2 | 🟡 Legacy vorhanden |
| Environmental | 2 | 🟡 Ort unklar |

### Backup-Dateien

- **.bak Dateien:** 69
- **Ratio:** 69 Backups zu 38 aktiven Dateien = 1.8:1
- **Problem:** Mehr Backups als aktive Dateien!

---

**Nächster Schritt:** Agent Capability Mapping (`AGENT_CAPABILITIES_MATRIX.md`)
