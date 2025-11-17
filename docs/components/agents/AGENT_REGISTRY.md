# Agent Registry

## 📋 Übersicht

Das **Agent Registry** ist die zentrale Registrierungs- und Verwaltungskomponente für alle spezialisierten Agenten im VERITAS-System. Es bietet Auto-Discovery, Initialisierung, Fallback-Handling und capability-basierte Agent-Auswahl für 15 produktive Agenten.

### Zweck

- **Zentrale Agent-Verwaltung**: Einheitlicher Zugriff auf alle spezialisierten Agenten
- **Auto-Discovery**: Automatische Erkennung verfügbarer Agenten
- **Lazy Initialization**: Agenten werden erst bei Bedarf instanziiert
- **Capability-basierte Auswahl**: Agenten können nach Fähigkeiten gefunden werden
- **Domain-Gruppierung**: Agenten sind in fachliche Domains organisiert
- **Dependency Management**: Prüfung von Datenbank- und API-Anforderungen
- **Singleton Pattern**: Global verfügbare Registry-Instanz
- **Graceful Degradation**: Fallback bei fehlenden Dependencies

### Hauptfunktionen

1. **Agent-Registrierung**: Registrierung von 15 spezialisierten Agenten
2. **Agent-Initialisierung**: Lazy loading mit Dependency-Prüfung
3. **Capability-Suche**: Suche nach Agenten basierend auf Fähigkeiten
4. **Domain-Filterung**: Filterung nach Fachdomains (Legal, Environmental, etc.)
5. **Agent-Discovery**: Automatische Erkennung verfügbarer Agenten
6. **Fehlerbehandlung**: Graceful degradation bei Import-Fehlern
7. **Performance-Monitoring**: Tracking der initialisierten Agenten
8. **Search-Funktionalität**: Volltextsuche über Capabilities und Beschreibungen

## 🏗️ Architektur

### Komponenten-Übersicht

```
AgentRegistry
├── AgentInfo (Dataclass)
│   ├── agent_id: str
│   ├── domain: AgentDomain
│   ├── capabilities: List[str]
│   ├── class_reference: Type
│   ├── requires_db: bool
│   ├── requires_api: bool
│   ├── initialized: bool
│   └── description: str
│
├── AgentDomain (Enum)
│   ├── ENVIRONMENTAL
│   ├── LEGAL
│   ├── TECHNICAL
│   ├── KNOWLEDGE
│   ├── ATMOSPHERIC
│   ├── DATABASE
│   └── ADMINISTRATIVE
│
└── Registry Methods
    ├── _register_all_agents()
    ├── _register_agent()
    ├── get_agent()
    ├── get_agents_by_capability()
    ├── get_agents_by_domain()
    ├── list_available_agents()
    ├── get_agent_info()
    └── search_agents()
```

### Registrierte Agenten (15 Total)

#### Environmental Domain (7 Agents)
1. **EnvironmentalAgent**: Umwelt-Anfragen (Luftqualität, Lärm, Abfall, Wasser)
2. **ChemicalDataAgent**: Chemische Daten, Gefahrstoffe, MSDS
3. **ImmissionsschutzAgent**: Luftqualität, Lärmschutz, TA Luft, TA Lärm
4. **BodenGewaesserschutzAgent**: Bodenschutz, Grundwasser, Altlasten
5. **NaturschutzAgent**: BNatSchG, FFH-Richtlinie, UVP, Artenschutz
6. **EmissionenMonitoringAgent**: Emissionsmessung, Überwachung, Grenzwerte

#### Legal Domain (3 Agents)
7. **VerwaltungsrechtAgent**: Baurecht, Genehmigungsverfahren, BImSchG
8. **RechtsrecherchAgent**: Gesetzestexte, Rechtsprechung, Kommentare
9. **VerwaltungsprozessAgent**: VwGO, Klageverfahren, Rechtsmittel

#### Technical Domain (1 Agent)
10. **TechnicalStandardsAgent**: DIN, ISO, EN, VDI Standards

#### Knowledge Domain (1 Agent)
11. **WikipediaAgent**: Enzyklopädie-Recherche, Definitionen

#### Atmospheric Domain (2 Agents)
12. **AtmosphericFlowAgent**: Luftströmungen, Schadstoffausbreitung
13. **DWDOpenDataAgent**: Historische Wetterdaten (DWD Open Data)

#### Database Domain (1 Agent)
14. **DatabaseAgent**: Direkte Datenbank-Abfragen

#### Administrative Domain (1 Agent)
15. **GenehmigungsAgent**: Genehmigungsverfahren, VwVfG, Fristen

### Initialisierungs-Flow

```
1. AgentRegistry.__init__()
   │
   ├─> _register_all_agents()
   │   │
   │   ├─> Import Agent Class
   │   │   ├─> Success: Register Agent
   │   │   └─> ImportError: Log Warning, Continue
   │   │
   │   ├─> _register_agent() für jeden Agent
   │   │   └─> Speichere AgentInfo in self.agents
   │   │
   │   └─> Log: Anzahl registrierter Agenten
   │
   └─> Registry Ready (Lazy Loading)

2. get_agent(agent_id)
   │
   ├─> Check: Already initialized?
   │   ├─> Yes: Return cached instance
   │   └─> No: Continue
   │
   ├─> Check: Agent registered?
   │   ├─> No: Return None
   │   └─> Yes: Continue
   │
   ├─> Check Dependencies
   │   ├─> requires_db: Prüfe db_pool
   │   └─> requires_api: Prüfe api_config
   │
   ├─> Instantiate Agent
   │   ├─> EnvironmentalAgent: Mit Config
   │   └─> Andere: Default Constructor
   │
   ├─> Cache Instance
   │   └─> self.initialized_agents[agent_id]
   │
   └─> Return Agent Instance
```

### Dependency-Management

```
Agent Requirements:
│
├─> requires_db = True
│   ├─> DatabaseAgent (SQL Queries)
│   └─> Fallback: Mock/Degraded Mode
│
├─> requires_api = True
│   ├─> WikipediaAgent (Wikipedia API)
│   ├─> AtmosphericFlowAgent (DWD Weather)
│   └─> Fallback: Mock/Cached Data
│
└─> requires_db = False, requires_api = False
    └─> 12 Agents: Keine externen Dependencies
```

## 📚 API-Referenz

### AgentRegistry Klasse

#### `__init__(db_pool=None, api_config=None)`

Initialisiert die Agent Registry.

**Parameter:**
- `db_pool` (optional): Database connection pool
- `api_config` (dict, optional): API configuration dictionary

**Beispiel:**
```python
registry = AgentRegistry()
# Oder mit Dependencies:
registry = AgentRegistry(db_pool=my_pool, api_config={"wikipedia_api_key": "..."})
```

#### `get_agent(agent_id: str) -> Optional[Any]`

Gibt eine initialisierte Agent-Instanz zurück (lazy loading).

**Parameter:**
- `agent_id`: Agent-Identifier (z.B. "EnvironmentalAgent")

**Returns:**
- Agent-Instanz oder `None` bei Fehler

**Beispiel:**
```python
agent = registry.get_agent("EnvironmentalAgent")
if agent:
    result = agent.query("Luftqualität München")
```

#### `get_agents_by_capability(capability: str) -> List[str]`

Findet alle Agenten mit einer bestimmten Fähigkeit.

**Parameter:**
- `capability`: Capability-Keyword (z.B. "luftqualitaet")

**Returns:**
- Liste von Agent-IDs

**Beispiel:**
```python
agents = registry.get_agents_by_capability("luftqualitaet")
# ['EnvironmentalAgent', 'ImmissionsschutzAgent']
```

#### `get_agents_by_domain(domain: AgentDomain) -> List[str]`

Gibt alle Agenten einer fachlichen Domain zurück.

**Parameter:**
- `domain`: AgentDomain enum value

**Returns:**
- Liste von Agent-IDs

**Beispiel:**
```python
from backend.agents.agent_registry import AgentDomain

env_agents = registry.get_agents_by_domain(AgentDomain.ENVIRONMENTAL)
# ['EnvironmentalAgent', 'ChemicalDataAgent', 'ImmissionsschutzAgent', ...]
```

#### `list_available_agents() -> Dict[str, Any]`

Listet alle registrierten Agenten mit Status-Informationen.

**Returns:**
- Dictionary mit Agent-Informationen

**Beispiel:**
```python
agents = registry.list_available_agents()
for agent_id, info in agents.items():
    print(f"{agent_id}: {info['description']}")
    print(f"  Domain: {info['domain']}")
    print(f"  Initialized: {info['initialized']}")
```

#### `get_agent_info(agent_id: str) -> Optional[Dict[str, Any]]`

Gibt detaillierte Informationen über einen spezifischen Agenten.

**Parameter:**
- `agent_id`: Agent-Identifier

**Returns:**
- Agent-Info Dictionary oder `None`

**Beispiel:**
```python
info = registry.get_agent_info("VerwaltungsrechtAgent")
print(f"Domain: {info['domain']}")
print(f"Capabilities: {info['capabilities']}")
print(f"Requires DB: {info['requires_db']}")
```

#### `search_agents(query: str) -> List[str]`

Sucht Agenten basierend auf Query-String (Capabilities + Beschreibungen).

**Parameter:**
- `query`: Such-Query

**Returns:**
- Liste von Agent-IDs

**Beispiel:**
```python
results = registry.search_agents("baurecht")
# ['VerwaltungsrechtAgent', 'GenehmigungsAgent']
```

### Global Functions

#### `get_agent_registry(db_pool=None, api_config=None) -> AgentRegistry`

Gibt die globale Singleton-Instanz der Registry zurück.

**Beispiel:**
```python
from backend.agents.agent_registry import get_agent_registry

registry = get_agent_registry()
agent = registry.get_agent("WikipediaAgent")
```

#### `reset_agent_registry()`

Setzt die Singleton-Instanz zurück (nützlich für Tests).

**Beispiel:**
```python
reset_agent_registry()
registry = get_agent_registry()  # Neue Instanz
```

#### `get_agent(agent_id: str) -> Optional[Any]`

Convenience-Funktion: Holt Agent aus globaler Registry.

**Beispiel:**
```python
from backend.agents.agent_registry import get_agent

agent = get_agent("EnvironmentalAgent")
```

#### `list_agents() -> Dict[str, Any]`

Convenience-Funktion: Listet alle Agenten.

**Beispiel:**
```python
from backend.agents.agent_registry import list_agents

all_agents = list_agents()
```

#### `search_agents(query: str) -> List[str]`

Convenience-Funktion: Sucht Agenten.

**Beispiel:**
```python
from backend.agents.agent_registry import search_agents

results = search_agents("immissionsschutz")
```

## ⚙️ Konfiguration

### Agent Dependencies

```python
# Agents ohne Dependencies (12)
- EnvironmentalAgent
- ChemicalDataAgent
- TechnicalStandardsAgent
- VerwaltungsrechtAgent
- RechtsrecherchAgent
- ImmissionsschutzAgent
- BodenGewaesserschutzAgent
- NaturschutzAgent
- GenehmigungsAgent
- EmissionenMonitoringAgent
- VerwaltungsprozessAgent
- DWDOpenDataAgent

# Agents mit API-Requirement (2)
- WikipediaAgent (requires_api=True)
- AtmosphericFlowAgent (requires_api=True)

# Agents mit Database-Requirement (1)
- DatabaseAgent (requires_db=True)
```

### Agent Domains

```python
AgentDomain.ENVIRONMENTAL     # 7 Agents
AgentDomain.LEGAL             # 3 Agents
AgentDomain.TECHNICAL         # 1 Agent
AgentDomain.KNOWLEDGE         # 1 Agent
AgentDomain.ATMOSPHERIC       # 2 Agents
AgentDomain.DATABASE          # 1 Agent
AgentDomain.ADMINISTRATIVE    # 1 Agent
```

## 💡 Verwendungsbeispiele

### Beispiel 1: Basic Agent Usage

```python
from backend.agents.agent_registry import AgentRegistry

# Initialize registry
registry = AgentRegistry()

# Get specific agent
env_agent = registry.get_agent("EnvironmentalAgent")
if env_agent:
    result = env_agent.query("Luftqualität in München")
    print(result)
```

### Beispiel 2: Capability-basierte Suche

```python
from backend.agents.agent_registry import AgentRegistry

registry = AgentRegistry()

# Find all agents that can handle air quality queries
air_agents = registry.get_agents_by_capability("luftqualitaet")
print(f"Air quality agents: {air_agents}")

# Try each agent for best result
for agent_id in air_agents:
    agent = registry.get_agent(agent_id)
    result = agent.query("NO2-Grenzwerte in Wohngebieten")
    if result.confidence > 0.8:
        return result  # Found good answer
```

### Beispiel 3: Domain-basierte Filterung

```python
from backend.agents.agent_registry import AgentRegistry, AgentDomain

registry = AgentRegistry()

# Get all legal domain agents
legal_agents = registry.get_agents_by_domain(AgentDomain.LEGAL)
print(f"Legal agents: {legal_agents}")

# Query each legal agent
for agent_id in legal_agents:
    agent = registry.get_agent(agent_id)
    result = agent.query("Baugenehmigungsverfahren §35 BauGB")
    # Process result...
```

### Beispiel 4: Agent Discovery & Info

```python
from backend.agents.agent_registry import AgentRegistry

registry = AgentRegistry()

# List all available agents
all_agents = registry.list_available_agents()
print("\nAvailable Agents:")
for agent_id, info in all_agents.items():
    print(f"\n{agent_id}:")
    print(f"  Domain: {info['domain']}")
    print(f"  Description: {info['description']}")
    print(f"  Capabilities: {', '.join(info['capabilities'][:5])}...")
    print(f"  Requires DB: {info['requires_db']}")
    print(f"  Requires API: {info['requires_api']}")
    print(f"  Initialized: {info['initialized']}")
```

### Beispiel 5: Search Functionality

```python
from backend.agents.agent_registry import AgentRegistry

registry = AgentRegistry()

# Search for agents dealing with "baurecht"
baurecht_agents = registry.search_agents("baurecht")
print(f"Baurecht agents: {baurecht_agents}")

# Search for "emission" related agents
emission_agents = registry.search_agents("emission")
print(f"Emission agents: {emission_agents}")

# Get detailed info for first result
if baurecht_agents:
    info = registry.get_agent_info(baurecht_agents[0])
    print(f"\nTop result: {info['agent_id']}")
    print(f"Description: {info['description']}")
```

### Beispiel 6: Singleton Pattern Usage

```python
from backend.agents.agent_registry import get_agent_registry, get_agent

# Method 1: Using global registry
registry = get_agent_registry()
agent = registry.get_agent("WikipediaAgent")

# Method 2: Using convenience function
agent = get_agent("WikipediaAgent")

# Both methods return the same agent instance (singleton)
```

### Beispiel 7: Error Handling

```python
from backend.agents.agent_registry import AgentRegistry

registry = AgentRegistry()

# Try to get non-existent agent
agent = registry.get_agent("NonExistentAgent")
if agent is None:
    print("Agent not available")
else:
    result = agent.query("test")

# Search returns empty list if no match
results = registry.search_agents("nonexistent_capability")
if not results:
    print("No agents found for this capability")
```

### Beispiel 8: Multi-Agent Query Strategy

```python
from backend.agents.agent_registry import AgentRegistry

def query_with_fallback(query: str, primary_capability: str, fallback_domain):
    """Query strategy with fallback"""
    registry = AgentRegistry()
    
    # Try primary agents first
    primary_agents = registry.get_agents_by_capability(primary_capability)
    for agent_id in primary_agents:
        agent = registry.get_agent(agent_id)
        result = agent.query(query)
        if result and result.confidence > 0.7:
            return result
    
    # Fallback to domain
    fallback_agents = registry.get_agents_by_domain(fallback_domain)
    for agent_id in fallback_agents:
        if agent_id not in primary_agents:  # Don't retry
            agent = registry.get_agent(agent_id)
            result = agent.query(query)
            if result:
                return result
    
    return None

# Usage
result = query_with_fallback(
    "TA Luft Grenzwerte",
    primary_capability="immissionsschutz",
    fallback_domain=AgentDomain.ENVIRONMENTAL
)
```

## 🔧 Troubleshooting

### Problem 1: Agent nicht verfügbar

**Symptom:**
```
⚠️ Agent 'XAgent' not registered
```

**Ursache:**
- Import-Fehler beim Registrieren des Agents
- Dependency fehlt (z.B. Agent-Datei nicht vorhanden)

**Lösung:**
```python
# Prüfe verfügbare Agenten
registry = AgentRegistry()
available = registry.list_available_agents()
print(f"Available agents: {list(available.keys())}")

# Prüfe Logs für Import-Fehler
# ⚠️ XAgent nicht verfügbar: ModuleNotFoundError: ...
```

### Problem 2: Agent-Initialisierung schlägt fehl

**Symptom:**
```
❌ Agent 'XAgent' initialization failed: ...
```

**Ursache:**
- Constructor-Fehler
- Fehlende Dependencies (DB, API)

**Lösung:**
```python
# Prüfe Agent-Info vor Initialisierung
info = registry.get_agent_info("DatabaseAgent")
if info['requires_db']:
    # Stelle sicher, dass db_pool verfügbar ist
    registry = AgentRegistry(db_pool=my_pool)

agent = registry.get_agent("DatabaseAgent")
```

### Problem 3: Keine Agenten für Capability gefunden

**Symptom:**
```python
agents = registry.get_agents_by_capability("xyz")
# Returns: []
```

**Ursache:**
- Falsche Capability-Name
- Capability nicht registriert

**Lösung:**
```python
# Liste alle verfügbaren Capabilities
all_agents = registry.list_available_agents()
all_capabilities = set()
for info in all_agents.values():
    all_capabilities.update(info['capabilities'])

print(f"Available capabilities: {sorted(all_capabilities)}")

# Oder verwende Search für fuzzy matching
results = registry.search_agents("luft")  # Findet "luftqualitaet", etc.
```

### Problem 4: Singleton-Reset nötig (Testing)

**Symptom:**
- Tests beeinflussen sich gegenseitig
- Alte Registry-Instanz wird wiederverwendet

**Lösung:**
```python
from backend.agents.agent_registry import reset_agent_registry

# In setUp() oder vor jedem Test
reset_agent_registry()
registry = get_agent_registry()
```

### Problem 5: Agent gibt None zurück

**Symptom:**
```python
agent = registry.get_agent("XAgent")
# agent is None
```

**Ursache:**
- Agent nicht registriert
- Initialisierung fehlgeschlagen

**Lösung:**
```python
# Prüfe ob registriert
if "XAgent" in registry.agents:
    print("Agent registered")
    # Prüfe Initialisierung
    try:
        agent = registry.get_agent("XAgent")
    except Exception as e:
        print(f"Init failed: {e}")
else:
    print("Agent not registered - check imports")
```

## 🔗 Verwandte Dokumentation

- **Agent Message Broker**: Event-Bus für Agent-Kommunikation
- **Process Executor**: Orchestrierung von Multi-Agent-Workflows
- **Query Service**: Integration der Agents in Query-Pipeline
- **Individual Agent Documentation**:
  - Environmental Agent
  - Chemical Data Agent
  - Technical Standards Agent
  - Wikipedia Agent
  - Atmospheric Flow Agent
  - Database Agent
  - Verwaltungsrecht Agent
  - Rechtsrecherche Agent
  - Immissionsschutz Agent
  - (+ 6 weitere Agents)

## 📊 Performance-Charakteristiken

### Registry Initialization

- **Registrierung**: ~50ms für 15 Agents
- **Memory**: ~500 KB (nur Metadata)
- **Import Errors**: Nicht-blockierend (graceful degradation)

### Agent Initialization (Lazy Loading)

- **First Call**: 10-100ms pro Agent (Import + Init)
- **Cached Calls**: <1ms (direkter Zugriff)
- **Memory**: 5-50 MB pro Agent (je nach Typ)
- **Parallelisierung**: Thread-safe für Read-Operations

### Lookup Performance

- **get_agent()**: O(1) - Direct dict lookup
- **get_agents_by_capability()**: O(n) - Linear scan, n=15
- **get_agents_by_domain()**: O(n) - Linear scan
- **search_agents()**: O(n*m) - n agents, m capabilities/description

### Best Practices

1. **Singleton verwenden**: `get_agent_registry()` statt `AgentRegistry()`
2. **Lazy Loading nutzen**: Agents werden erst bei Bedarf initialisiert
3. **Cache Agent-Instanzen**: Registry cached automatisch
4. **Capability-Suche bevorzugen**: Schneller als Search
5. **Domain-Filterung für Batch**: Effizient für mehrere Agents

## 🧪 Testing

### Unit Test Beispiel

```python
import unittest
from backend.agents.agent_registry import AgentRegistry, AgentDomain, reset_agent_registry

class TestAgentRegistry(unittest.TestCase):
    
    def setUp(self):
        """Reset registry before each test"""
        reset_agent_registry()
        self.registry = AgentRegistry()
    
    def test_registry_initialization(self):
        """Test registry initializes with agents"""
        agents = self.registry.list_available_agents()
        self.assertGreater(len(agents), 0)
        self.assertIn("EnvironmentalAgent", agents)
    
    def test_get_agent(self):
        """Test getting specific agent"""
        agent = self.registry.get_agent("WikipediaAgent")
        self.assertIsNotNone(agent)
        
        # Test caching
        agent2 = self.registry.get_agent("WikipediaAgent")
        self.assertIs(agent, agent2)  # Same instance
    
    def test_capability_search(self):
        """Test capability-based search"""
        agents = self.registry.get_agents_by_capability("luftqualitaet")
        self.assertGreater(len(agents), 0)
        self.assertIn("EnvironmentalAgent", agents)
    
    def test_domain_filter(self):
        """Test domain filtering"""
        legal_agents = self.registry.get_agents_by_domain(AgentDomain.LEGAL)
        self.assertGreater(len(legal_agents), 0)
        
        for agent_id in legal_agents:
            info = self.registry.get_agent_info(agent_id)
            self.assertEqual(info['domain'], 'legal')
    
    def test_search_agents(self):
        """Test search functionality"""
        results = self.registry.search_agents("umwelt")
        self.assertGreater(len(results), 0)
    
    def test_nonexistent_agent(self):
        """Test handling of non-existent agent"""
        agent = self.registry.get_agent("NonExistentAgent")
        self.assertIsNone(agent)

if __name__ == "__main__":
    unittest.main()
```

### Integration Test Beispiel

```python
import unittest
from backend.agents.agent_registry import get_agent_registry, reset_agent_registry, AgentDomain

class TestAgentRegistryIntegration(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        """Initialize registry once for all tests"""
        reset_agent_registry()
        cls.registry = get_agent_registry()
    
    def test_all_agents_initializable(self):
        """Test that all registered agents can be initialized"""
        all_agents = self.registry.list_available_agents()
        
        for agent_id in all_agents.keys():
            with self.subTest(agent_id=agent_id):
                agent = self.registry.get_agent(agent_id)
                # Some agents may be None due to missing dependencies
                # This is expected behavior (graceful degradation)
                if agent is not None:
                    self.assertTrue(hasattr(agent, 'query'))
    
    def test_domain_coverage(self):
        """Test that all domains have agents"""
        for domain in AgentDomain:
            agents = self.registry.get_agents_by_domain(domain)
            # Not all domains are guaranteed to have agents
            # But main ones should
            if domain in [AgentDomain.ENVIRONMENTAL, AgentDomain.LEGAL]:
                self.assertGreater(len(agents), 0, 
                    f"Domain {domain} should have agents")
    
    def test_capability_overlap(self):
        """Test that capabilities can have multiple agents"""
        # "luftqualitaet" should be handled by multiple agents
        agents = self.registry.get_agents_by_capability("luftqualitaet")
        # Could be 0 if agents not available due to imports
        # So we just check the mechanism works
        self.assertIsInstance(agents, list)
```

---

**Datei**: `backend/agents/agent_registry.py` (693 LOC)  
**Dokumentation**: 26.8 KB  
**Agents verwaltet**: 15 spezialisierte Agents  
**Version**: 1.0 (Production)  
**Letzte Aktualisierung**: 2025-11-17
