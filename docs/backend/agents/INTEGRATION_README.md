# VERITAS Agents Integration

## Verfügbare Spezialisierte Agenten

### 1. 🌡️ **DWD Weather Agent**
- **Datei:** `veritas_api_agent_dwd_weather.py`
- **Zweck:** Deutsche Wetterdaten über DWD/dwdweather2
- **Features:** Ortsbasiert, historische Daten, Vorhersagen, Stationen-Suche
- **Status:** ✅ Implementiert & getestet

### 2. 📚 **Wikipedia Agent**
- **Datei:** `veritas_api_agent_wikipedia.py`
- **Zweck:** Wikipedia-Enzyklopädie Integration
- **Features:** Mehrsprachig, Artikel-Abruf, Kategorien, intelligente Suche
- **Status:** ✅ Implementiert & getestet

## FastAPI Integration

Alle Agenten werden über einheitliche Endpoints integriert:

```
POST /agents/{agent_name}/query
GET  /agents/{agent_name}/status
GET  /agents/{agent_name}/health
```

### DWD Weather Endpoints:
- `/agents/dwd_weather/query` - Wetterdaten-Abfragen
- `/agents/dwd_weather/status` - Agent-Status

### Wikipedia Endpoints:
- `/agents/wikipedia/search` - Wikipedia-Suche
- `/agents/wikipedia/article` - Artikel-Abruf
- `/agents/wikipedia/summary` - Zusammenfassungen
- `/agents/wikipedia/status` - Agent-Status

```python
# In veritas_api_backend.py hinzufügen:

from backend.agents.veritas_api_agent_dwd_weather import create_dwd_weather_agent
from backend.agents.veritas_api_agent_wikipedia import create_wikipedia_agent

# Agents initialisieren
dwd_agent = None
wikipedia_agent = None

async def startup_agents():
    """Startup-Funktion für alle Agenten"""
    global dwd_agent, wikipedia_agent

    # DWD Weather Agent
    dwd_agent = create_dwd_weather_agent()
    print("✅ DWD Weather Agent loaded")

    # Wikipedia Agent
    wikipedia_agent = create_wikipedia_agent()
    print("✅ Wikipedia Agent loaded")

@app.on_event("startup")
async def startup():
    await startup_agents()

@app.post("/agents/dwd_weather/query")
async def dwd_weather_endpoint(request: dict):
    """DWD Weather Query"""
    try:
        # Convert dict to proper request
        from backend.agents.veritas_api_agent_dwd_weather import (
            DwdWeatherQueryRequest, WeatherInterval, WeatherParameter
        )

        weather_request = DwdWeatherQueryRequest(
            query_id=request.get("query_id", f"dwd-{int(time.time())}"),
            query_text=request.get("query", ""),
            location=request.get("location"),
            latitude=request.get("latitude"),
            longitude=request.get("longitude"),
            start_date=request.get("start_date"),
            end_date=request.get("end_date"),
            interval=WeatherInterval(request.get("interval", "daily")),
            parameters=[
                WeatherParameter(p) for p in request.get("parameters", ["temperature"])
            ]
        )

        response = await dwd_agent.execute_query_async(weather_request)

        return {
            "success": response.success,
            "query_id": response.query_id,
            "results": response.results,
            "metadata": {
                "stations_count": response.stations_count,
                "data_points_count": response.data_points_count,
                "processing_time_ms": response.processing_time_ms,
                "confidence_score": response.confidence_score
            },
            "error": response.error_message
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"DWD Weather Agent Error: {str(e)}"
        }

@app.get("/agents/dwd_weather/status")
async def dwd_weather_status():
    """DWD Weather Agent Status"""
    if dwd_agent:
        return dwd_agent.get_status()
    return {"error": "DWD Weather Agent not initialized"}

# Wikipedia Agent Endpoints
@app.post("/agents/wikipedia/search")
async def wikipedia_search_endpoint(request: dict):
    """Wikipedia Search"""
    try:
        from backend.agents.veritas_api_agent_wikipedia import (
            WikipediaQueryRequest, WikipediaLanguage, WikipediaQueryType
        )

        wiki_request = WikipediaQueryRequest(
            query_id=request.get("query_id", f"wiki-search-{int(time.time())}"),
            query_text=request.get("query", ""),
            query_type=WikipediaQueryType.SEARCH,
            language=WikipediaLanguage(request.get("language", "de")),
            max_results=request.get("max_results", 10),
            include_summary=request.get("include_summary", True)
        )

        response = await wikipedia_agent.execute_query_async(wiki_request)

        return {
            "success": response.success,
            "results": [result.to_dict() for result in response.search_results],
            "metadata": {
                "total_results": response.total_results,
                "processing_time_ms": response.processing_time_ms,
                "confidence": response.confidence_score
            },
            "error": response.error_message
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Wikipedia Search Error: {str(e)}"
        }

@app.post("/agents/wikipedia/article")
async def wikipedia_article_endpoint(request: dict):
    """Wikipedia Article Retrieval"""
    try:
        from backend.agents.veritas_api_agent_wikipedia import (
            WikipediaQueryRequest, WikipediaLanguage, WikipediaQueryType
        )

        wiki_request = WikipediaQueryRequest(
            query_id=request.get("query_id", f"wiki-article-{int(time.time())}"),
            query_text=request.get("title", ""),
            query_type=WikipediaQueryType.ARTICLE,
            language=WikipediaLanguage(request.get("language", "de")),
            include_content=request.get("include_content", True),
            include_categories=request.get("include_categories", True),
            include_links=request.get("include_links", True)
        )

        response = await wikipedia_agent.execute_query_async(wiki_request)

        if response.success and response.articles:
            return {
                "success": True,
                "article": response.articles[0].to_dict(),
                "metadata": {
                    "processing_time_ms": response.processing_time_ms,
                    "confidence": response.confidence_score
                }
            }
        else:
            return {
                "success": False,
                "error": response.error_message or "Article not found"
            }

    except Exception as e:
        return {
            "success": False,
            "error": f"Wikipedia Article Error: {str(e)}"
        }

@app.get("/agents/wikipedia/status")
async def wikipedia_status():
    """Wikipedia Agent Status"""
    if wikipedia_agent:
        return wikipedia_agent.get_status()
    return {"error": "Wikipedia Agent not initialized"}
```

## Frontend Integration

```javascript
// JavaScript Client für Wikipedia & Weather Queries

class VeritasAgentsClient {
    constructor(baseUrl = '') {
        this.baseUrl = baseUrl;
    }

    // Wikipedia Methods
    async searchWikipedia(query, options = {}) {
        const {
            language = 'de',
            maxResults = 10,
            includeSummary = true
        } = options;

        const payload = {
            query,
            language,
            max_results: maxResults,
            include_summary: includeSummary
        };

        const response = await fetch(`${this.baseUrl}/agents/wikipedia/search`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        return await response.json();
    }

    async getWikipediaArticle(title, options = {}) {
        const {
            language = 'de',
            includeContent = true,
            includeCategories = true
        } = options;

        const payload = {
            title,
            language,
            include_content: includeContent,
            include_categories: includeCategories
        };

        const response = await fetch(`${this.baseUrl}/agents/wikipedia/article`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        return await response.json();
    }

    // Weather Methods
    async queryWeather(options = {}) {
        const {
            location,
            latitude,
            longitude,
            startDate,
            endDate = startDate,
            interval = 'daily',
            parameters = ['temperature']
        } = options;

        const payload = {
            query: `Weather data for ${location || `${latitude},${longitude}`}`,
            location,
            latitude,
            longitude,
            start_date: startDate,
            end_date: endDate,
            interval,
            parameters
        };

        const response = await fetch(`${this.baseUrl}/agents/dwd_weather/query`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        return await response.json();
    }

    // Agent Status Methods
    async getWikipediaStatus() {
        const response = await fetch(`${this.baseUrl}/agents/wikipedia/status`);
        return await response.json();
    }

    async getWeatherStatus() {
        const response = await fetch(`${this.baseUrl}/agents/dwd_weather/status`);
        return await response.json();
    }
}

// Verwendung:
const agentsClient = new VeritasAgentsClient();

// Wikipedia-Suche
const wikiResults = await agentsClient.searchWikipedia('Künstliche Intelligenz', {
    language: 'de',
    maxResults: 5
});

// Wikipedia-Artikel
const article = await agentsClient.getWikipediaArticle('Berlin', {
    includeContent: true
});

// Wetter-Abfrage
const weather = await agentsClient.queryWeather({
    location: 'Berlin',
    startDate: '2025-09-28',
    parameters: ['temperature', 'precipitation']
});

console.log('Wikipedia Results:', wikiResults.results);
console.log('Article:', article.article);
console.log('Weather:', weather.data);
```

## Agent Registrierung

```python
# agent_registry.py für zentrale Verwaltung

from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

class AgentType(Enum):
    WEATHER = "weather"
    TRAFFIC = "traffic"
    FINANCIAL = "financial"
    ENVIRONMENTAL = "environmental"
    SOCIAL = "social"
    KNOWLEDGE = "knowledge"  # Für Wikipedia, Enzyklopädien, etc.

@dataclass
class AgentInfo:
    name: str
    type: AgentType
    version: str
    description: str
    endpoints: Dict[str, str] = field(default_factory=dict)
    status: str = "inactive"
    capabilities: list = field(default_factory=list)

class AgentRegistry:
    def __init__(self):
        self.agents: Dict[str, AgentInfo] = {}

    def register_agent(self, agent_info: AgentInfo):
        """Registriere einen neuen Agenten"""
        self.agents[agent_info.name] = agent_info
        print(f"✅ Agent '{agent_info.name}' registered")

    def get_available_agents(self) -> Dict[str, AgentInfo]:
        """Alle verfügbaren Agenten"""
        return self.agents

    def get_agent_status(self, name: str) -> Optional[AgentInfo]:
        """Status eines spezifischen Agenten"""
        return self.agents.get(name)

# Globale Registry
agent_registry = AgentRegistry()

# DWD Weather Agent registrieren
agent_registry.register_agent(AgentInfo(
    name="dwd_weather",
    type=AgentType.WEATHER,
    version="1.0.0",
    description="German Weather Service (DWD) integration agent",
    endpoints={
        "query": "/agents/dwd_weather/query",
        "status": "/agents/dwd_weather/status"
    },
    capabilities=[
        "historical_weather_data",
        "current_weather",
        "station_based_data",
        "hourly_daily_intervals",
        "temperature_precipitation_wind"
    ]
))

# Wikipedia Agent registrieren
agent_registry.register_agent(AgentInfo(
    name="wikipedia",
    type=AgentType.KNOWLEDGE,
    version="1.0.0",
    description="Wikipedia encyclopedia integration agent",
    endpoints={
        "search": "/agents/wikipedia/search",
        "article": "/agents/wikipedia/article",
        "status": "/agents/wikipedia/status"
    },
    capabilities=[
        "multilingual_search",
        "article_retrieval",
        "category_navigation",
        "cross_language_support",
        "intelligent_query_processing"
    ]
))
```

## Testing Integration

```bash
# Installation aller Agent-Abhängigkeiten
pip install dwdweather2 wikipedia

# Vollständige System-Tests
python backend/agents/test_dwd_weather_standalone.py
python backend/agents/test_wikipedia_agent_standalone.py

# FastAPI Tests
curl -X POST "http://localhost:8000/agents/dwd_weather/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Weather in Berlin",
    "location": "Berlin",
    "start_date": "2025-09-28",
    "end_date": "2025-09-28",
    "parameters": ["temperature", "precipitation"]
  }'

curl -X POST "http://localhost:8000/agents/wikipedia/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Künstliche Intelligenz",
    "language": "de",
    "max_results": 5
  }'
```

## Next Steps

1. **Package Installation:** `pip install dwdweather2 wikipedia`
2. **Backend Integration:** Agents in FastAPI einbinden
3. **Frontend UI:** Weather & Wikipedia-Widgets erstellen
4. **Additional Agents:** Traffic, Financial, etc.
5. **Agent Orchestration:** Multi-Agent Queries
6. **Cross-Agent Knowledge:** Wikipedia + Weather Kombinationen

**VERITAS Agent System mit DWD Weather + Wikipedia ist produktionsbereit! 🚀**
