# VERITAS Agent Template System 🤖

**Template-basiertes System für die schnelle Entwicklung neuer VERITAS Agent-Worker**

## 📋 Übersicht

Das VERITAS Agent Template System ermöglicht die schnelle und standardisierte Entwicklung neuer Agent-Worker für verschiedene Domänen. Es bietet eine einheitliche Architektur, automatische Code-Generierung und integrierte Best Practices.

### 🏗️ **Architektur-Komponenten**

```
backend/agents/
├── veritas_agent_template.py           # 🎯 Basis-Template für alle Agents
├── agent_generator.py                  # 🔧 Automatischer Agent-Generator
├── veritas_api_agent_environmental.py  # 📋 Beispiel-Agent (generiert)
├── tests/
│   └── test_environmental_agent.py     # 🧪 Auto-generierte Tests
└── docs/
    └── environmental_agent_README.md   # 📚 Auto-generierte Dokumentation
```

---

## 🚀 **Schnellstart**

### 1. Neuen Agent generieren

```bash
cd y:\veritas\backend\agents

# Basic Agent
python agent_generator.py --domain financial

# Agent mit spezifischen Capabilities
python agent_generator.py --domain legal --capabilities DOCUMENT_RETRIEVAL,LLM_INTEGRATION

# Agent mit Custom Config
python agent_generator.py --domain medical --config '{"api_endpoint":"https://api.medical.com","model":"medical-llm"}'
```

### 2. Agent implementieren

```python
# In der generierten Datei: veritas_api_agent_[domain].py

def process_query(self, request: DomainQueryRequest) -> DomainQueryResponse:
    """Implementiere deine Domain-spezifische Logic hier"""
    
    # 1. Query analysieren
    query_text = request.query_text
    
    # 2. Domain-spezifische Verarbeitung
    results = self._process_domain_logic(query_text)
    
    # 3. Ergebnisse formatieren
    return DomainQueryResponse(
        query_id=request.query_id,
        results=results,
        confidence_score=0.95,
        success=True
    )
```

### 3. Agent testen

```bash
# Unit Tests
python -m unittest backend.agents.tests.test_[domain]_agent

# Integration Test
python backend/agents/veritas_api_agent_[domain].py
```

---

## 🎯 **Template-Features**

### ✅ **Standard-Funktionalität (Ready-to-Use)**

- **Query Processing Pipeline** - Vollständiger Request/Response-Flow
- **Input Validation** - Automatische Parameter-Validierung
- **Error Handling** - Standardisierte Fehlerbehandlung
- **Performance Monitoring** - Built-in Metriken und Logging
- **Agent Registration** - Automatische Registry-Integration
- **Async Support** - Sync/Async Query Processing
- **Status Management** - Agent-Lifecycle und Health-Checks

### 🔧 **Anpassbare Komponenten**

- **process_query()** - Kern-Verarbeitungslogik (MUSS implementiert werden)
- **validate_input()** - Domain-spezifische Validierung
- **preprocess_query()** - Optional: Query-Preprocessing
- **postprocess_results()** - Optional: Result-Postprocessing
- **handle_error()** - Optional: Custom Error Handling

### 📊 **Integrierte Monitoring**

```python
# Automatische Performance-Metriken
agent.get_status()
# {
#   "processed_queries": 42,
#   "avg_processing_time_ms": 150,
#   "success_rate": 0.95,
#   "error_count": 2
# }
```

---

## 🏷️ **Verfügbare Domains**

| Domain | Beschreibung | Beispiel Use Cases |
|--------|--------------|-------------------|
| `environmental` | Umweltdaten & Monitoring | Wetterdaten, Sensoren, Klima |
| `financial` | Finanzanalysen & -daten | Märkte, Transaktionen, Berichte |
| `legal` | Rechtsdokumente & Compliance | Verträge, Gesetze, Vorschriften |
| `medical` | Medizinische Datenanalyse | Diagnosen, Studien, Therapien |
| `educational` | Bildungsinhalte | Kurse, Materialien, Bewertungen |
| `construction` | Bauwesen & Architektur | Pläne, Materialien, Vorschriften |
| `traffic` | Verkehr & Logistik | Routen, Staus, Optimierung |
| `social` | Social Media & Community | Posts, Trends, Sentiment |
| `security` | Sicherheit & Überwachung | Threats, Monitoring, Compliance |
| `quality` | Qualitätsmanagement | Prozesse, Standards, Audits |

---

## 🛠️ **Agent Capabilities**

### Standard Capabilities
```python
AgentCapability.QUERY_PROCESSING        # Basic Query-Verarbeitung
AgentCapability.DATA_ANALYSIS           # Datenanalyse-Features
AgentCapability.DOCUMENT_RETRIEVAL      # Dokument-Suche und -Abruf
```

### Advanced Capabilities
```python
AgentCapability.LLM_INTEGRATION         # LLM/AI-Model Integration
AgentCapability.EXTERNAL_API_INTEGRATION # Externe API-Calls
AgentCapability.REAL_TIME_PROCESSING    # Real-time Stream Processing
AgentCapability.BATCH_PROCESSING        # Batch-Verarbeitung
```

---

## 📝 **Template-Struktur**

### 1. **Konfiguration**
```python
@dataclass
class DomainAgentConfig:
    processing_mode: ProcessingMode = ProcessingMode.SYNC
    max_concurrent_tasks: int = 5
    timeout_seconds: int = 30
    # Domain-spezifische Parameter
    api_endpoint: Optional[str] = None
    model_name: Optional[str] = None
```

### 2. **Request/Response Models**
```python
@dataclass
class DomainQueryRequest:
    query_id: str
    query_text: str
    context: Dict[str, Any] = field(default_factory=dict)
    # Domain-spezifische Felder hier hinzufügen

@dataclass 
class DomainQueryResponse:
    query_id: str
    results: List[Dict[str, Any]]
    confidence_score: float
    success: bool
```

### 3. **Agent Implementation**
```python
class DomainAgent(BaseTemplateAgent):
    def process_query(self, request: DomainQueryRequest) -> DomainQueryResponse:
        # Implementiere Domain-Logic
        pass
    
    def validate_input(self, request: DomainQueryRequest) -> bool:
        # Implementiere Validierung
        pass
```

---

## 🔗 **Integration mit VERITAS-System**

### Agent Registry Integration
```python
# Automatische Registrierung beim Initialisierung
registry = get_agent_registry()
registry.register_agent(
    agent_id=self.agent_id,
    capabilities=AGENT_CAPABILITIES,
    metadata={"domain": AGENT_DOMAIN}
)
```

### Orchestrator Integration
```python
# Agent wird automatisch vom Orchestrator erkannt
orchestrator = get_agent_orchestrator()
response = orchestrator.process_query_with_agents(
    query="Environmental data for Berlin",
    preferred_agents=["environmental_agent"]
)
```

### Backend API Integration
```python
# FastAPI Endpoint Integration
@app.post("/agents/{domain}/query")
async def domain_agent_query(domain: str, request: QueryRequest):
    agent = get_domain_agent(domain)
    return await agent.execute_query_async(request)
```

---

## 🧪 **Testing Framework**

### Automatisch generierte Tests
```python
class TestDomainAgent(unittest.TestCase):
    def test_agent_initialization(self):
        # Test Agent Setup
        
    def test_basic_query_processing(self):
        # Test Standard Query Flow
        
    def test_input_validation(self):
        # Test Validation Logic
        
    def test_error_handling(self):
        # Test Error Scenarios
```

### Manual Testing
```python
# Direct Agent Testing
agent = create_domain_agent()
request = DomainQueryRequest(query_id="test", query_text="test query")
response = agent.execute_query(request)
```

---

## 📈 **Performance & Monitoring**

### Built-in Metriken
- **Processing Time** - Query-Verarbeitungszeit
- **Success Rate** - Erfolgsquote der Queries
- **Error Count** - Anzahl der Fehler
- **Throughput** - Queries pro Sekunde

### Logging Integration
```python
# Automatisches Logging für alle Operations
logger.info(f"✅ Query processed: {query_id} ({processing_time}ms)")
logger.error(f"❌ Query failed: {query_id} - {error}")
```

### Health Checks
```python
# Agent Status abfragen
status = agent.get_status()
# Verwendung in FastAPI Health Endpoints
```

---

## 🔄 **Development Workflow**

### 1. **Planning Phase**
- Domain-Anforderungen definieren
- Capabilities festlegen
- API-Schnittstellen planen

### 2. **Generation Phase**
```bash
python agent_generator.py --domain [domain] --capabilities [caps]
```

### 3. **Implementation Phase**
- `process_query()` implementieren
- Domain-spezifische Logik entwickeln
- Externe APIs/Services integrieren

### 4. **Testing Phase**
```bash
python -m unittest tests.test_[domain]_agent
python veritas_api_agent_[domain].py  # Manual test
```

### 5. **Integration Phase**
- Agent im System registrieren
- FastAPI Endpoints konfigurieren
- Orchestrator-Integration testen

### 6. **Deployment Phase**
- Performance optimieren
- Monitoring konfigurieren
- Production-Deployment

---

## 🎯 **Best Practices**

### ✅ **DO's**
- Implementiere immer `process_query()` und `validate_input()`
- Verwende standardisierte Request/Response-Models
- Integriere angemessenes Error Handling
- Dokumentiere Domain-spezifische Parameter
- Implementiere Unit Tests
- Verwende Performance Monitoring

### ❌ **DON'Ts**
- Modifiziere nicht die Base-Template-Struktur
- Verwende keine blocking I/O in sync methods
- Ignoriere keine Input-Validierung
- Vergesse nicht das Agent Registry
- Verwende keine hardcoded Konfiguration
- Ignoriere keine Error Handling

---

## 📚 **Beispiele**

### Environmental Agent
```python
def process_query(self, request: EnvironmentalQueryRequest) -> EnvironmentalQueryResponse:
    # Weather API Integration
    weather_data = self.weather_api.get_current_weather(request.location)
    
    # Air Quality Data
    air_quality = self.air_quality_api.get_measurements(request.location)
    
    # Combine Results
    results = [{
        "location": request.location,
        "temperature": weather_data.temperature,
        "air_quality_index": air_quality.aqi,
        "timestamp": datetime.now().isoformat()
    }]
    
    return EnvironmentalQueryResponse(
        query_id=request.query_id,
        results=results,
        confidence_score=0.95,
        success=True
    )
```

### Financial Agent
```python
def process_query(self, request: FinancialQueryRequest) -> FinancialQueryResponse:
    # Stock Market Data
    stock_data = self.finance_api.get_stock_info(request.symbol)
    
    # Financial Analysis
    analysis = self.analyze_financial_trends(stock_data)
    
    results = [{
        "symbol": request.symbol,
        "current_price": stock_data.price,
        "trend": analysis.trend,
        "recommendation": analysis.recommendation
    }]
    
    return FinancialQueryResponse(
        query_id=request.query_id,
        results=results,
        confidence_score=analysis.confidence,
        success=True
    )
```

---

## 🚀 **Fazit**

Das VERITAS Agent Template System bietet:

- ✅ **Schnelle Entwicklung** neuer Domain-Agents
- ✅ **Standardisierte Architektur** für Konsistenz
- ✅ **Automatische Code-Generierung** für Effizienz  
- ✅ **Integrierte Best Practices** für Qualität
- ✅ **Complete Testing Framework** für Zuverlässigkeit
- ✅ **Seamless VERITAS Integration** für Kompatibilität

**Ready für Production-Deployment! 🎯**

---

*Dokumentation erstellt am: 28. September 2025*  
*VERITAS Agent Template System v1.0*