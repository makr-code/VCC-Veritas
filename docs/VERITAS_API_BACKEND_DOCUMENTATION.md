# VERITAS API Backend Dokumentation
## Umfangreiche Dokumentation des Agenten-Systems

> Kurz erklärt für Nicht-Techniker: Stellen Sie sich VERITAS wie ein digitales Amt mit vielen Fachabteilungen vor. Ihre Frage kommt am Empfang an, wird an die richtigen Fachleute ("Agenten") verteilt, die parallel recherchieren und Ergebnisse zusammentragen. Währenddessen erhalten Sie Live-Updates, so als würde man Ihnen durch das Fenster der Büros beim Arbeiten zusehen.

### Version: 3.4.0
### Datum: 21. September 2025

---

## 📋 Inhaltsverzeichnis

1. [System-Übersicht](#system-übersicht)
2. [Agenten-Architektur](#agenten-architektur) 
3. [API-Endpoints](#api-endpoints)
4. [Streaming-System](#streaming-system)
5. [Agenten-Typen](#agenten-typen)
6. [RAG-Integration](#rag-integration)
7. [Datenbank-Strategien](#datenbank-strategien)
8. [Externe APIs](#externe-apis)
9. [Quality-Management](#quality-management)
10. [Deployment](#deployment)
11. [Roadmap](#roadmap)
12. [Glossar (Begriffe einfach erklärt)](#glossar)
13. [FAQ – Häufige Fragen in einfach](#faq)

---

## 1. System-Übersicht

### 🏗️ Architektur-Prinzipien

**VERITAS API Backend** ist ein hochmodernes, agent-basiertes Backend-System für die Verarbeitung komplexer Verwaltungsanfragen.

- In einfachen Worten: Mehrere digitale Fachkräfte (Agenten) arbeiten gleichzeitig an Ihrer Frage – jede mit eigener Spezialisierung (z. B. Bauen, Umwelt, Verkehr). 
- Sie bekommen bereits während der Bearbeitung Einblicke in den Fortschritt (Streaming), ohne erst auf das Endergebnis warten zu müssen.

- **🤖 Multi-Agent-Architektur**: Spezialisierte Agenten für verschiedene Domänen
- **🔄 Real-time Streaming**: Live-Updates über Server-Sent Events (SSE)
- **📊 RAG-Integration**: Vector-, Graph- und Relational-Database-Strategien
- **🧠 LLM-Integration**: Ollama-basierte Intelligenz für Response-Generation
- **⚡ Asynchrone Verarbeitung**: Parallel-Execution für optimale Performance

> Analogie: Wie bei einer Krankenhaus-Visite – Kardiologie, Radiologie und Labor arbeiten gleichzeitig. Der Gesamtbefund entsteht aus allen Teilbefunden und Sie sehen live, was schon erledigt ist.

### 🌟 Kern-Features

```python
CORE_FEATURES = {
    "streaming_progress": "Real-time Progress Updates mit SSE",
    "agent_orchestration": "Intelligente Agent-Koordination",
    "rag_pipeline": "Tri-Database RAG-Strategie",
    "quality_assessment": "Automatische Qualitätsbewertung",
    "cancellation_support": "Nutzer-initiierte Abbrüche",
    "external_api_integration": "50+ externe Datenquellen",
    "domain_specialization": "6 Haupt-Domänen abgedeckt"
}
```

> Übersetzt: Sie sehen live, wie weit die Bearbeitung ist; verschiedene Fachmodule arbeiten koordiniert zusammen; Informationen kommen aus mehreren Datenbanken; die Qualität wird automatisch bewertet; auf Wunsch können Sie abbrechen; und viele Ämter-/Fachdatenquellen sind angebunden.

### Kontext zum Code (CORE_FEATURES)

- Zweck: Kompakter Überblick über die Hauptfähigkeiten des Systems.
- Inputs/Outputs: Reine Konfigurationskonstante; wird z. B. in Statusseiten/Docs angezeigt.
- Einsatz: Für Stakeholder-Präsentationen, Feature-Flags oder Health-/Info-Endpoints.
- Hinweise je Schlüssel:
    - streaming_progress: Live-Status über SSE; frühe Einblicke statt „Warten bis fertig“.
    - agent_orchestration: Koordiniert mehrere spezialisierte Agenten effizient.
    - rag_pipeline: Faktenrecherche in Vector-, Graph- und Relationen-Datenbanken.
    - quality_assessment: Bewertet Antworten (Vollständigkeit, Relevanz, Genauigkeit …).
    - cancellation_support: Nutzer kann laufende Vorgänge abbrechen; sicheres Aufräumen.
    - external_api_integration: Abrufe offizieller, verlässlicher Datenquellen.
    - domain_specialization: Abdeckung typischer Verwaltungsthemen über Module.

### 🎯 Anwendungsgebiete

- **Verwaltungsberatung**: Baugenehmigungen, Gewerbeanmeldungen
- **Rechtsinformationen**: Gesetze, Verordnungen, Rechtsprechung
- **Bürgerdienste**: Anträge, Formulare, Verfahren
- **Umweltberatung**: Emissionsschutz, Umweltauflagen
- **Verkehrsplanung**: ÖPNV, Verkehrsrecht, Infrastruktur
- **Sozialberatung**: Leistungen, Ansprüche, Beratungsstellen

---

## 2. Agenten-Architektur

> Warum Agenten? Weil komplexe Fragen selten nur eine Perspektive brauchen. Ein Bauvorhaben berührt Recht, Umwelt, Verkehr und Kosten. Agenten sind wie Fachreferate, die abgestimmt zusammenarbeiten.

### 🔄 Agent-Pipeline

```mermaid
graph TD
    A[User Query] --> B[Query Preprocessor]
    B --> C[Domain Classification]
    C --> D[Agent Selection]
    D --> E[Parallel Agent Execution]
    E --> F1[Core Agents]
    E --> F2[Domain Agents]
    E --> F3[Processing Agents]
    F1 --> G[Result Aggregation]
    F2 --> G
    F3 --> G
    G --> H[LLM Response Generation]
    H --> I[Quality Assessment]
    I --> J[Final Response]
```

### Kontext zum Diagramm (Agenten-Pipeline)

- Preprocessor: Bereinigt/normalisiert die Eingabe, erkennt Absicht (Intent).
- Domain Classification: Ordnet die Frage passenden Themen zu (Bauen, Umwelt, …).
- Agent Selection: Wählt pro Thema die relevanten Worker mit der höchsten Erwartung auf Mehrwert.
- Parallel Agent Execution: Führt ausgewählte Worker parallel aus, um Wartezeiten zu reduzieren.
- Result Aggregation: Vereint Teilergebnisse, löst Widersprüche, dedupliziert Quellen.
- LLM Response: Formuliert eine verständliche Antwort und verknüpft Belege.
- Quality Assessment: Prüft die Qualität und liefert nachvollziehbare Scores.
- Abbruchpunkte: Während paralleler Ausführung werden Cancel-Signale regelmäßig geprüft.

### 🎯 Agent-Kategorien

#### **Core Agents** (Basis-Services)
```python
CORE_AGENTS = {
    "legal_framework": {
        "function": "Rechtlicher Kontext und Gesetzesanalyse",
        "data_sources": ["Gesetze", "Verordnungen", "Rechtsprechung"],
        "processing_time": "1-2s",
        "confidence_threshold": 0.8
    },
    "geo_context": {
        "function": "Geografische und administrative Zuordnung",
        "data_sources": ["OSM", "Verwaltungsgrenzen", "Kataster"],
        "processing_time": "0.5-1s",
        "confidence_threshold": 0.9
    },
    "document_retrieval": {
        "function": "RAG-basierte Dokumentensuche",
        "data_sources": ["Vector DB", "Graph DB", "Metadaten"],
        "processing_time": "1-3s",
        "confidence_threshold": 0.7
    },
    "timeline": {
        "function": "Verfahrensfristen und Zeitplanung",
        "data_sources": ["Verwaltungsverfahren", "Gesetze"],
        "processing_time": "0.5s",
        "confidence_threshold": 0.85
    }
}
```

#### **Domain Agents** (Fachspezifisch)
```python
DOMAIN_AGENTS = {
    "environmental": {
        "workers": [
            "air_quality_worker",           # Luftqualität und Emissionen
            "noise_complaint_worker",       # Lärmbeschwerde und Schallschutz  
            "waste_management_worker",      # Abfallentsorgung und Recycling
            "water_protection_worker",      # Gewässerschutz und Wasserwirtschaft
            "nature_conservation_worker"    # Naturschutz und Biodiversität
        ],
        "rag_focus": ["immissionsschutz", "umweltrecht", "naturschutz"],
        "external_apis": ["umweltbundesamt", "landesumweltämter"],
        "complexity_handling": "environmental_regulations"
    },
    
    "construction": {
        "workers": [
            "building_permit_worker",       # Baugenehmigungen und Baurecht
            "urban_planning_worker",        # Stadtplanung und Flächennutzung
            "heritage_protection_worker",   # Denkmalschutz und historische Gebäude
            "construction_safety_worker",   # Bausicherheit und Vorschriften
            "zoning_analysis_worker"        # Bebauungsplan und Zonierung
        ],
        "rag_focus": ["bauplanungsrecht", "bauordnungsrecht", "denkmalschutz"],
        "external_apis": ["bauaufsicht", "stadtplanung", "denkmalschutz"],
        "complexity_handling": "multi_authority_coordination"
    },
    
    "traffic": {
        "workers": [
            "traffic_management_worker",    # Verkehrsmanagement und -planung
            "public_transport_worker",      # Öffentlicher Nahverkehr
            "parking_management_worker",    # Parkraumbewirtschaftung
            "road_construction_worker",     # Straßenbau und -sanierung
            "traffic_safety_worker"         # Verkehrssicherheit und Unfallprävention
        ],
        "rag_focus": ["straßenverkehrsrecht", "straßenrecht", "öpnv"],
        "external_apis": ["verkehrsbetriebe", "straßenbauamt", "verkehrsüberwachung"],
        "complexity_handling": "multi_modal_transport"
    },
    
    "financial": {
        "workers": [
            "tax_assessment_worker",        # Steuerveranlagung und Steuerbescheide
            "funding_opportunities_worker", # Förderungen und Finanzierungshilfen
            "business_tax_worker",          # Gewerbesteuer-Optimierung
            "municipal_fees_worker",        # Kommunale Gebühren und Abgaben
            "subsidy_analysis_worker"       # Subventions- und Beihilfenanalyse
        ],
        "rag_focus": ["steuerrecht", "förderrichtlinien", "kommunalrecht"],
        "external_apis": ["finanzämter", "förderbanken", "ihk"],
        "complexity_handling": "multi_jurisdiction_tax"
    },
    
    "social": {
        "workers": [
            "social_benefits_worker",       # Sozialleistungen und Anspruchsprüfung
            "citizen_services_worker",      # Allgemeine Bürgerdienste
            "health_insurance_worker",      # Krankenversicherung und Gesundheit
            "family_services_worker",       # Familienhilfen und Kinderbetreuung
            "elderly_care_worker"           # Altenpflege und Seniorendienste
        ],
        "rag_focus": ["sozialrecht", "verwaltungsrecht", "gesundheitsrecht"],
        "external_apis": ["sozialämter", "krankenkassen", "familienberatung"],
        "complexity_handling": "eligibility_assessment"
    }
}
```

#### **Processing Agents** (Verarbeitung)
```python
PROCESSING_AGENTS = {
    "preprocessor": {
        "function": "Query-Normalisierung und Intent-Erkennung",
        "techniques": ["NLP", "Entity Recognition", "Domain Classification"],
        "processing_time": "0.2s"
    },
    "postprocessor": {
        "function": "Result-Aggregation und Conflict-Resolution",
        "techniques": ["Weighted Voting", "Confidence Scoring", "Duplicate Removal"],
        "processing_time": "0.5s"
    },
    "quality_assessor": {
        "function": "Automatische Qualitätsbewertung",
        "metrics": ["Completeness", "Accuracy", "Relevance", "Consistency"],
        "threshold": 0.7
    },
    "aggregator": {
        "function": "Multi-Source-Result-Kombination",
        "strategies": ["Ranking", "Clustering", "Deduplication"],
        "processing_time": "0.3s"
    }
}
```

### 🔗 Agent-Orchestration

```python
class AgentOrchestrator:
    """
    Zentrale Koordination aller Agenten
    """
    
    async def process_query(self, query: str, domain: str) -> AgentResponse:
        # 1. Preprocessor Stage
        preprocessed = await self.preprocessor.analyze(query)
        
        # 2. Agent Selection
        selected_agents = self.select_agents(domain, preprocessed.complexity)
        
        # 3. Parallel Execution
        tasks = [agent.process(query, preprocessed) for agent in selected_agents]
        results = await asyncio.gather(*tasks)
        
        # 4. Aggregation
        aggregated = await self.aggregator.combine(results)
        
        # 5. Quality Assessment  
        quality_score = await self.quality_assessor.evaluate(aggregated)
        
        # 6. Response Generation
        final_response = await self.llm_generator.generate(aggregated)
        
        return AgentResponse(
            content=final_response,
            quality_score=quality_score,
            agent_results=results,
            processing_metadata=preprocessed
        )
```

### Kontext zum Code (AgentOrchestrator)

- Input: query (Nutzerfrage), domain (optional, kann automatisch bestimmt werden).
- Output: AgentResponse mit Endtext, Qualitätswerten, Agenten-Teilresultaten und Metadaten.
- Verhalten: Führt die Pipeline-Schritte aus, startet parallele Tasks und sammelt Ergebnisse ein.
- Fehlerfälle: Timeouts/Fehler einzelner Agenten → werden protokolliert; Aggregation nutzt verfügbare Teilergebnisse; Cancel-Signal beendet laufende Tasks kontrolliert.
- Nebenwirkung: Fortschrittsereignisse werden an den Progress-Manager für die UI gesendet.

---

## 3. API-Endpoints

### 🌐 Core Endpoints

#### **1. Health & Status**
```http
GET /health
Response: {
    "status": "healthy",
    "uptime": 3600,
    "streaming_available": true,
    "agent_count": 25,
    "database_connections": "active"
}
```

#### **2. System Information**
```http
GET /
Response: {
    "service": "Veritas API Backend (Streaming)",
    "version": "3.4.0",
    "features": ["streaming", "agents", "rag", "quality"],
    "documentation": "http://localhost:5000/docs"
}
```

### 🤖 Agent Endpoints

#### **1. Available Agent Types**
```http
GET /agents/types
Response: {
    "agent_types": [
        "legal_framework", "document_retrieval", "geo_context",
        "environmental", "construction", "traffic", 
        "financial", "social", "external_api"
    ],
    "streaming_features": {
        "progress_updates": true,
        "intermediate_results": true, 
        "llm_thinking": true
    }
}
```

#### **2. Agent Query Processing**
```http
POST /v2/agents/query
Content-Type: application/json

{
    "query": "Wie beantrage ich eine Baugenehmigung für ein Einfamilienhaus?",
    "agent_types": ["construction", "legal_framework", "document_retrieval"],
    "complexity": "standard",
    "external_sources": true,
    "quality_level": "high",
    "session_id": "session_20250921_143022"
}

Response: {
    "answer": "Für eine Baugenehmigung...",
    "agent_results": [
        {
            "agent_type": "construction",
            "summary": "Bautechnische Aspekte und Genehmigungsverfahren bewertet",
            "confidence_score": 0.92,
            "sources": ["DIN-Normen", "Bauordnung", "Technische Richtlinien"]
        }
    ],
    "quality_metrics": {
        "completeness": 0.89,
        "accuracy": 0.94,
        "relevance": 0.91
    },
    "session_id": "session_20250921_143022"
}
```

### 🔄 Streaming Endpoints

#### **1. Start Streaming Query**
```http
POST /v2/query/stream
Content-Type: application/json

{
    "query": "Umweltauflagen für Industrieanlage",
    "session_id": "stream_session_001",
    "enable_streaming": true,
    "enable_intermediate_results": true,
    "enable_llm_thinking": true
}

Response: {
    "session_id": "stream_session_001",
    "stream_url": "/progress/stream_session_001",
    "estimated_time": "15-30 seconds",
    "selected_agents": ["environmental", "legal_framework", "external_api"]
}
```

#### **2. Progress Stream (SSE)**
```http
GET /progress/{session_id}
Accept: text/event-stream

Events:
event: stage_update
data: {
    "stage": "agent_processing",
    "progress": 35,
    "message": "Environmental worker analyzing emission requirements"
}

event: intermediate_result  
data: {
    "agent_type": "environmental",
    "result": "BImSchG requirements identified",
    "confidence": 0.88
}

event: llm_thinking
data: {
    "message": "Synthesizing environmental and legal requirements...",
    "thinking_step": "legal_environmental_cross_check"
}

event: stage_complete
data: {
    "stage": "completed",
    "final_result": "Complete environmental compliance analysis"
}
```

#### **3. Cancel Streaming**
```http
POST /cancel/{session_id}
Content-Type: application/json

{
    "reason": "user_cancelled"
}

Response: {
    "success": true,
    "message": "Stream erfolgreich abgebrochen",
    "cancelled_at": "agent_processing_stage"
}
```

### 📊 Quality & Analytics

#### **1. Query Quality Analysis**
```http
POST /quality/analyze
Content-Type: application/json

{
    "content": "Generated response text...",
    "query": "Original user query",
    "metrics": ["completeness", "accuracy", "relevance"]
}

Response: {
    "quality_score": 0.87,
    "metrics": {
        "completeness": 0.89,
        "accuracy": 0.91,
        "relevance": 0.82,
        "consistency": 0.85
    },
    "recommendations": [
        "Add more specific examples",
        "Include relevant legal references"
    ]
}
```

#### **2. System Metrics**
```http
GET /metrics
Response: {
    "daily_queries": 1247,
    "avg_response_time": 4.2,
    "agent_performance": {
        "environmental": {"success_rate": 0.94, "avg_time": 3.1},
        "construction": {"success_rate": 0.91, "avg_time": 3.8}
    },
    "quality_metrics": {
        "avg_quality_score": 0.86,
        "user_satisfaction": 0.91
    }
}
```

---

## 4. Streaming-System

> Was bedeutet „Streaming“ hier? Statt erst am Ende eine Antwort zu sehen, erhalten Sie während der Bearbeitung kleine Statusmeldungen und Zwischenergebnisse – wie ein Paket-Tracking mit Meilensteinen (abgeholt, sortiert, unterwegs, zugestellt).

- „stage_update“ = Der nächste Bearbeitungsschritt läuft (z. B. „Umweltprüfung gestartet“)
- „intermediate_result“ = Ein Fachbereich hat eine Teilauswertung fertig
- „llm_thinking“ = Das System formuliert oder verknüpft Inhalte (Einblick in den Denkprozess)
- „stage_complete“ = Alles abgeschlossen, Ergebnis liegt vor
- „cancelled“ = Vorgang wurde abgebrochen

> Sie können einen laufenden Vorgang abbrechen – so wie einen Online-Kauf, solange er noch nicht versendet ist.

### 🔄 Real-time Progress Updates

Das Streaming-System ermöglicht Live-Updates während der Agent-Verarbeitung:

```python
class VeritasProgressManager:
    """
    Verwaltet Real-time Progress für Streaming-Queries
    """
    
    def __init__(self):
        self.active_sessions = {}
        self.cancelled_sessions = set()
        self.progress_streamer = VeritasProgressStreamer()
    
    async def update_stage(self, session_id: str, stage: ProgressStage):
        """Aktualisiert Verarbeitungsstage"""
        progress_data = {
            "type": "stage_update",
            "stage": stage.value,
            "timestamp": datetime.now().isoformat(),
            "message": f"Stage {stage.value} started"
        }
        await self.progress_streamer.send_update(session_id, progress_data)
    
    async def add_intermediate_result(self, session_id: str, agent_type: str, result: Dict):
        """Fügt Zwischenergebnis hinzu"""
        progress_data = {
            "type": "intermediate_result",
            "agent_type": agent_type,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        await self.progress_streamer.send_update(session_id, progress_data)
```

### Kontext zum Code (VeritasProgressManager)

- Zweck: Zentrale Verwaltung von Fortschritt und Events für Live-Updates.
- Inputs: session_id (eindeutiger Lauf), stage/Resultate (z. B. agent_processing, Zwischenergebnis).
- Outputs: Ereignisse (stage_update, intermediate_result, llm_thinking, stage_complete), die die UI via SSE konsumiert.
- Nutzung: Jede relevante Verarbeitungsphase meldet hier Status; UI und Backend bleiben lose gekoppelt.
- Fehlerfälle: Unbekannte/abgelaufene session_id → keine Events; bei Abbruch wird „cancelled“ gesendet und Session aufgeräumt.

### 📡 Server-Sent Events (SSE) Implementation

```python
async def get_progress_stream(session_id: str):
    """
    SSE Endpoint für Progress Updates
    """
    async def event_generator():
        while session_id in progress_manager.active_sessions:
            # Check for cancellation
            if progress_manager.is_session_cancelled(session_id):
                yield f"event: cancelled\ndata: {{\"message\": \"Session cancelled\"}}\n\n"
                break
            
            # Get latest progress
            progress = await progress_manager.get_latest_progress(session_id)
            if progress:
                yield f"event: {progress['type']}\ndata: {json.dumps(progress)}\n\n"
            
            await asyncio.sleep(0.5)  # 500ms polling
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )
```

### Kontext zum Code (SSE-Endpoint)

- Input: session_id identifiziert den laufenden Auftrag.
- Output: Kontinuierlicher Event-Stream (text/event-stream) für Live-Updates.
- Verhalten: Solange die Session aktiv ist, werden neue Events ausgesendet; danach endet der Stream sauber.
- Hinweis: SSE ist unidirektional (Server → Client). Zum Abbrechen nutzt der Client den Cancel-Endpoint.

### 🛑 Cancellation Support

```python
async def cancel_streaming_session(session_id: str, cancel_request: dict):
    """
    Bricht laufende Streaming-Session ab
    """
    if session_id not in progress_manager.active_sessions:
        raise HTTPException(404, "Session not found")
    
    # Mark as cancelled
    progress_manager.cancel_session(session_id)
    
    # Notify agents to stop processing
    await agent_orchestrator.cancel_session(session_id)
    
    # Send cancellation event
    await progress_manager.send_cancellation_event(session_id)
    
    return {
        "success": True,
        "message": "Session successfully cancelled",
        "cancelled_at": datetime.now().isoformat()
    }
```

### Kontext zum Code (Abbruch/Cancel)

- Zweck: Nutzer-initiierter Abbruch eines laufenden Jobs.
- Ablauf: Session markieren → Agenten stoppen → „cancelled“-Event senden → Ressourcen freigeben.
- Fehlerfälle: Unbekannte Session (404) oder bereits beendeter Job → UI zeigt Abschluss/Info an.
- UX-Hinweis: Die Cancel-Schaltfläche in der App ruft genau diesen Endpoint auf.

---

## 5. Agenten-Typen

### 🎯 Domain-spezifische Agenten

#### **Environmental Domain**
```python
ENVIRONMENTAL_AGENTS = {
    "air_quality_worker": {
        "expertise": "Luftqualitätsmessungen und Grenzwerte",
        "data_sources": ["Umweltbundesamt", "Messstationen", "EU-Richtlinien"],
        "legal_framework": ["BImSchG", "39. BImSchV", "EU-Luftqualitätsrichtlinie"],
        "typical_queries": [
            "Luftqualität in meiner Stadt",
            "Grenzwerte für Stickstoffdioxid", 
            "Emissionsberichte für Industrieanlagen"
        ]
    },
    
    "noise_complaint_worker": {
        "expertise": "Lärmschutz und Schallimmissionen",
        "data_sources": ["Lärmkarten", "Messdaten", "Rechtsprechung"],
        "legal_framework": ["BImSchG", "TA Lärm", "DIN 45680"],
        "typical_queries": [
            "Lärmbelästigung durch Baustelle",
            "Nachtruhe und Lärmschutz",
            "Fluglärm-Entschädigung"
        ]
    }
    // ... weitere Environmental Agents
}
```

#### **Construction Domain**
```python
CONSTRUCTION_AGENTS = {
    "building_permit_worker": {
        "expertise": "Baugenehmigungsverfahren und Baurecht",
        "data_sources": ["Bauordnungen", "Bebauungspläne", "Formulare"],
        "legal_framework": ["BauGB", "LBO", "BauNVO"],
        "process_steps": [
            "Bauvoranfrage", "Bauantrag", "Prüfung", 
            "Genehmigung", "Bauabnahme"
        ],
        "typical_queries": [
            "Baugenehmigung für Einfamilienhaus",
            "Umbau ohne Genehmigung",
            "Bauvoranfrage stellen"
        ]
    },
    
    "urban_planning_worker": {
        "expertise": "Stadtplanung und Flächennutzung",
        "data_sources": ["FNP", "Bebauungspläne", "Landschaftspläne"],
        "legal_framework": ["BauGB", "ROG", "BNatSchG"],
        "typical_queries": [
            "Bebauungsplan einsehen",
            "Flächennutzungsplan Änderung",
            "Baulandausweisung"
        ]
    }
    // ... weitere Construction Agents
}
```

### 🔄 Processing Pipeline

```python
async def process_domain_query(domain: str, query: str) -> DomainResult:
    """
    Domain-spezifische Query-Verarbeitung
    """
    # 1. Domain Agent Selection
    domain_agents = DOMAIN_AGENTS[domain]["workers"]
    selected_agents = await select_relevant_agents(query, domain_agents)
    
    # 2. Parallel Agent Execution
    agent_tasks = []
    for agent_name in selected_agents:
        agent = get_agent_instance(agent_name)
        task = agent.process_query(query)
        agent_tasks.append(task)
    
    # 3. Gather Results
    agent_results = await asyncio.gather(*agent_tasks)
    
    # 4. Domain-specific Aggregation
    aggregated_result = await aggregate_domain_results(
        domain, agent_results
    )
    
    return DomainResult(
        domain=domain,
        agent_results=agent_results,
        aggregated_result=aggregated_result,
        confidence_score=calculate_confidence(agent_results),
        processing_time=time.time() - start_time
    )
```

### Kontext zum Code (process_domain_query)

- Input: domain (z. B. environmental), query (Nutzerfrage).
- Output: DomainResult mit Agenten-Teilergebnissen, Aggregation, Confidence und Laufzeit.
- Ablauf: Relevante Worker wählen → parallel ausführen → Ergebnisse einsammeln → domänenspezifisch zusammenfassen.
- Fehlerfälle: Kein passender Worker/Timeouts; Aggregator nutzt dann Teilmengen und markiert Unsicherheiten.

---

## 6. RAG-Integration

> RAG („Retrieval Augmented Generation“) heißt: Erst recherchieren, dann antworten. 
> Analogie: Bevor ein Gutachten erstellt wird, werden Akten gesichtet (Recherche). Danach wird die Bewertung geschrieben (Antwort). So wird’s fundiert statt geraten.

### 🔍 Tri-Database-Strategie

Das VERITAS System nutzt eine innovative **Tri-Database-RAG-Strategie**:

```python
class TriDatabaseRAGStrategy:
    """
    Vector + Graph + Relational Database Integration
    """
    
    def __init__(self):
        self.vector_db = ChromaDB()      # Semantic Search
        self.graph_db = Neo4j()          # Relationship Analysis  
        self.relational_db = PostgreSQL() # Metadata & Structure
    
    async def query_rag_pipeline(self, query: str) -> RAGResult:
        # 1. Vector Search - Semantic Similarity
        vector_results = await self.vector_db.similarity_search(
            query, k=50, threshold=0.7
        )
        
        # 2. Graph Traversal - Relationship Analysis
        graph_results = await self.graph_db.traverse_relationships(
            entities=extract_entities(query),
            max_depth=3,
            relationship_types=["CITES", "REFERENCES", "CONTAINS"]
        )
        
        # 3. Relational Filter - Metadata Filtering
        relational_results = await self.relational_db.filter_metadata(
            candidates=vector_results + graph_results,
            filters={
                "document_type": ["law", "regulation", "guideline"],
                "validity": "current",
                "jurisdiction": infer_jurisdiction(query)
            }
        )
        
        # 4. Result Combination & Ranking
        combined_results = await self.combine_and_rank(
            vector_results, graph_results, relational_results
        )
        
        return RAGResult(
            documents=combined_results,
            retrieval_strategy="tri_database",
            confidence_score=calculate_rag_confidence(combined_results)
        )
```

### Kontext zum Code (TriDatabaseRAGStrategy)

- Zweck: Fundierte Faktenbasis durch Kombination aus semantischer Suche, Beziehungsanalyse und Metadaten-Filtern.
- Inputs: query (Fragestellung), implizit abgeleitete Entitäten/Jurisdiktion.
- Output: RAGResult mit priorisierten Dokumenten, Strategiehinweis und Confidence.
- Ablauf: Vector (ähnliche Passagen) → Graph (Zitate/Beziehungen) → Relational (gültig, zuständig, aktuell) → Ranking.
- Fehlerfälle: Leere/inkonsistente Treffer; die Strategie degradiert auf verfügbare Teilmengen und reduziert Confidence.

### 📊 Database-spezifische Strategien

#### **Vector Database (ChromaDB)**
- **Zweck**: Semantische Ähnlichkeitssuche
- **Embeddings**: sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
- **Collections**: document_chunks, document_summaries, legal_articles
- **Performance**: ~200ms für 50 results

#### **Graph Database (Neo4j)**
- **Zweck**: Beziehungsanalyse und Zitationsnetzwerke
- **Nodes**: Document, Law, Regulation, Authority, Concept
- **Relationships**: CITES, REFERENCES, SUPERSEDES, APPLIES_TO
- **Traversal**: Max. 3 Hops für relevante Verbindungen

#### **Relational Database (PostgreSQL)**
- **Zweck**: Metadaten, Strukturierte Daten, Statistiken
- **Tabellen**: documents, authorities, legal_entities, keywords
- **Indizes**: Volltext-Suche, Geo-Indizes, Zeitstempel-Indizes
- **Performance**: Optimiert für komplexe Metadaten-Queries

### 🔗 RAG-Agent-Integration

```python
class RAGIntegratedAgent:
    """
    Agent mit integrierter RAG-Pipeline
    """
    
    def __init__(self, agent_type: str):
        self.agent_type = agent_type
        self.rag_strategy = TriDatabaseRAGStrategy()
        self.domain_focus = DOMAIN_AGENTS[agent_type]["rag_focus"]
    
    async def process_with_rag(self, query: str) -> AgentResult:
        # 1. Domain-focused RAG Query
        rag_context = await self.rag_strategy.query_with_domain_focus(
            query, self.domain_focus
        )
        
        # 2. Agent-specific Processing
        agent_analysis = await self.analyze_with_context(
            query, rag_context
        )
        
        # 3. Confidence Assessment
        confidence = self.calculate_confidence(
            rag_context.confidence_score,
            agent_analysis.certainty
        )
        
        return AgentResult(
            agent_type=self.agent_type,
            analysis=agent_analysis,
            rag_context=rag_context,
            confidence_score=confidence,
            sources=rag_context.sources
        )
```

---

## 7. Datenbank-Strategien

### 🗄️ UDS3 v3.0 Integration

```python
class OptimizedUnifiedDatabaseStrategy:
    """
    Unified Database Strategy v3.0 mit Quality Framework
    """
    
    def __init__(self):
        self.strategies = {
            "vector": VectorDatabaseAPI(),
            "graph": GraphDatabaseAPI(), 
            "relational": RelationalDatabaseAPI(),
            "document": DocumentDatabaseAPI()
        }
        self.quality_manager = QualityManager()
        self.security_manager = SecurityManager()
    
    async def unified_query(self, query: str, strategy_weights: Dict[str, float]) -> UnifiedResult:
        """
        Parallelisierte Multi-Database-Query mit Quality Assessment
        """
        # 1. Security Check
        security_level = await self.security_manager.assess_query_security(query)
        
        # 2. Parallel Database Queries
        tasks = {}
        for strategy_name, weight in strategy_weights.items():
            if weight > 0:
                strategy = self.strategies[strategy_name]
                tasks[strategy_name] = strategy.query(query)
        
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        
        # 3. Quality Assessment per Strategy
        quality_scores = {}
        for strategy_name, result in zip(tasks.keys(), results):
            if not isinstance(result, Exception):
                quality_scores[strategy_name] = await self.quality_manager.assess_result_quality(
                    result, strategy_name
                )
        
        # 4. Weighted Result Combination
        unified_result = await self.combine_weighted_results(
            dict(zip(tasks.keys(), results)),
            strategy_weights,
            quality_scores
        )
        
        return UnifiedResult(
            content=unified_result,
            strategy_contributions=quality_scores,
            security_level=security_level,
            overall_quality=calculate_overall_quality(quality_scores)
        )
```

### 📈 Performance-Optimierung

```python
DATABASE_PERFORMANCE_CONFIG = {
    "connection_pooling": {
        "vector_db": {"pool_size": 20, "max_overflow": 10},
        "graph_db": {"pool_size": 15, "max_overflow": 5},
        "relational_db": {"pool_size": 25, "max_overflow": 15}
    },
    
    "caching_strategy": {
        "query_cache_ttl": 300,  # 5 minutes
        "result_cache_ttl": 900,  # 15 minutes
        "metadata_cache_ttl": 3600  # 1 hour
    },
    
    "parallel_execution": {
        "max_concurrent_queries": 50,
        "query_timeout": 30,  # seconds
        "circuit_breaker_threshold": 5
    }
}
```

---

## 8. Externe APIs

> Externe Schnittstellen sind digitale Amtsgänge: Statt persönlich zur Behörde zu gehen, fragt das System automatisiert bei verlässlichen Quellen an (z. B. Umweltbundesamt, Statistikamt, Geoportale).

### 🌐 API-Integration-Framework

```python
class ExternalAPIManager:
    """
    Zentrale Verwaltung externer API-Integrationen
    """
    
    def __init__(self):
        self.api_registry = {
            # Governmental APIs
            "umweltbundesamt": UmweltbundesamtAPI(),
            "destatis": DestatisAPI(),
            "geoportal": GeoportalAPI(),
            
            # Municipal APIs  
            "kommune_api": KommunaleAPI(),
            "stadtplanung": StadtplanungsAPI(),
            "bauaufsicht": BauaufsichtAPI(),
            
            # Legal APIs
            "gesetze_im_internet": GesetzeImInternetAPI(),
            "rechtsprechung": RechtsprechungsAPI(),
            "verwaltungsportal": VerwaltungsportalAPI(),
            
            # Business APIs
            "unternehmensregister": UnternehmensregisterAPI(),
            "ihk": IHKAPI(),
            "handwerkskammer": HandwerkskammerAPI()
        }
        
        self.rate_limiter = RateLimiter()
        self.circuit_breaker = CircuitBreaker()
    
    async def query_external_sources(self, 
                                   query: str, 
                                   agent_type: str,
                                   max_sources: int = 5) -> List[ExternalResult]:
        """
        Parallelisierte Abfrage externer APIs
        """
        # Select relevant APIs for agent type
        relevant_apis = self.get_relevant_apis(agent_type)
        
        # Rate limiting and circuit breaker checks
        available_apis = []
        for api_name, api_instance in relevant_apis.items():
            if (await self.rate_limiter.can_call(api_name) and 
                self.circuit_breaker.is_available(api_name)):
                available_apis.append((api_name, api_instance))
        
        # Parallel API calls
        tasks = [
            self.call_external_api(api_name, api_instance, query)
            for api_name, api_instance in available_apis[:max_sources]
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter successful results
        successful_results = [
            result for result in results 
            if not isinstance(result, Exception)
        ]
        
        return successful_results
```

### 🏛️ Behörden-APIs

```python
GOVERNMENTAL_APIS = {
    "umweltbundesamt": {
        "base_url": "https://api.umweltbundesamt.de/",
        "endpoints": {
            "air_quality": "/luft/messwerte",
            "emission_data": "/emissionen/anlagen",
            "environmental_reports": "/berichte"
        },
        "rate_limit": "100/hour",
        "authentication": "api_key"
    },
    
    "destatis": {
        "base_url": "https://api.destatis.de/",
        "endpoints": {
            "population": "/bevoelkerung",
            "economics": "/wirtschaft",
            "regional_data": "/regional"
        },
        "rate_limit": "200/hour",
        "authentication": "oauth2"
    },
    
    "geoportal": {
        "base_url": "https://api.geoportal.de/",
        "endpoints": {
            "cadastre": "/liegenschaftskarte",
            "zoning": "/bebauungsplan", 
            "environmental_zones": "/umweltzonen"
        },
        "rate_limit": "300/hour",
        "authentication": "bearer_token"
    }
}
```

### 🔄 API-Resilience

```python
class APIResilienceManager:
    """
    Fehlertoleranz und Fallback-Strategien für externe APIs
    """
    
    def __init__(self):
        self.retry_config = {
            "max_retries": 3,
            "backoff_strategy": "exponential",
            "base_delay": 1.0
        }
        self.fallback_sources = {}
        self.cache_manager = CacheManager()
    
    async def resilient_api_call(self, 
                                api_name: str, 
                                endpoint: str, 
                                params: Dict) -> APIResult:
        """
        Resilient API call with retries and fallbacks
        """
        # Try cached result first
        cache_key = f"{api_name}_{endpoint}_{hash(str(params))}"
        cached_result = await self.cache_manager.get(cache_key)
        if cached_result:
            return cached_result
        
        # Attempt primary API call with retries
        for attempt in range(self.retry_config["max_retries"]):
            try:
                result = await self.make_api_call(api_name, endpoint, params)
                
                # Cache successful result
                await self.cache_manager.set(
                    cache_key, result, ttl=900  # 15 minutes
                )
                
                return result
                
            except APIException as e:
                if attempt < self.retry_config["max_retries"] - 1:
                    delay = self.calculate_backoff_delay(attempt)
                    await asyncio.sleep(delay)
                    continue
                else:
                    # Try fallback sources
                    fallback_result = await self.try_fallback_sources(
                        api_name, endpoint, params
                    )
                    if fallback_result:
                        return fallback_result
                    
                    raise e
```

### Kontext zum Code (APIResilienceManager)

- Zweck: Stabile API-Aufrufe trotz Rate-Limits/Ausfällen.
- Mechanismen: Rate Limiting, Circuit Breaker, Retries (exponentielles Backoff), Caching, Fallback-Quellen.
- Output: Erfolgsresultat aus Primär- oder Fallback-Quelle; ansonsten sauberer Fehler.
- Hinweise: Caching-TTLs beachten; Fallbacks nur für lesende Endpunkte sinnvoll; Fehler werden strukturiert geloggt.

---

## 9. Quality-Management

> Qualität heißt: vollständig, korrekt, relevant, konsistent – und mit seriösen Quellen belegt. 
> Denken Sie an ein Vier-Augen-Prinzip plus Checkliste: Ergebnisse durchlaufen feste Qualitätskriterien.

### 📊 Quality Assessment Framework

```python
class QualityAssessmentFramework:
    """
    Umfassendes Quality Assessment für Agent-Responses
    """
    
    def __init__(self):
        self.metrics = {
            "completeness": CompletenessAssessor(),
            "accuracy": AccuracyAssessor(),
            "relevance": RelevanceAssessor(), 
            "consistency": ConsistencyAssessor(),
            "timeliness": TimelinessAssessor(),
            "authority": AuthorityAssessor()
        }
        
        self.quality_thresholds = {
            "excellent": 0.9,
            "good": 0.8,
            "satisfactory": 0.7,
            "needs_improvement": 0.6
        }
    
    async def assess_response_quality(self, 
                                    response: AgentResponse,
                                    original_query: str) -> QualityReport:
        """
        Comprehensive quality assessment of agent response
        """
        # 1. Individual Metric Assessment
        metric_scores = {}
        for metric_name, assessor in self.metrics.items():
            score = await assessor.assess(response, original_query)
            metric_scores[metric_name] = score
        
        # 2. Weighted Overall Score
        weights = {
            "completeness": 0.25,
            "accuracy": 0.25,  
            "relevance": 0.20,
            "consistency": 0.15,
            "timeliness": 0.10,
            "authority": 0.05
        }
        
        overall_score = sum(
            metric_scores[metric] * weights[metric]
            for metric in metric_scores
        )
        
        # 3. Quality Classification
        quality_level = self.classify_quality(overall_score)
        
        # 4. Improvement Recommendations
        recommendations = await self.generate_recommendations(
            metric_scores, quality_level
        )
        
        return QualityReport(
            overall_score=overall_score,
            metric_scores=metric_scores,
            quality_level=quality_level,
            recommendations=recommendations,
            assessment_timestamp=datetime.now().isoformat()
        )
```

### Kontext zum Code (QualityAssessmentFramework)

- Zweck: Bewertet Antworten entlang mehrerer Qualitätsdimensionen und erzeugt konkrete Empfehlungen.
- Inputs: Response (Inhalt, Quellen), Original-Query.
- Output: QualityReport mit Einzelmetriken, Gesamtwert und Verbesserungsvorschlägen.
- Gewichtung: Standardgewichte sind definiert, können domänenspezifisch angepasst werden.
- Fehlerfälle: Unvollständige/inkonsistente Antworten → niedrigere Teilwerte; die Scores machen die Bewertung transparent.

### 🎯 Quality Metrics Details

```python
QUALITY_METRICS = {
    "completeness": {
        "description": "Vollständigkeit der Antwort bezüglich der Fragestellung",
        "factors": [
            "Alle Aspekte der Frage beantwortet",
            "Relevante Unterthemen abgedeckt",
            "Notwendige Detailinformationen enthalten"
        ],
        "calculation": "ratio_of_addressed_aspects / total_query_aspects"
    },
    
    "accuracy": {
        "description": "Faktische Korrektheit der bereitgestellten Informationen",
        "factors": [
            "Korrekte Rechtslage dargestellt",
            "Aktuelle Gesetze und Verordnungen referenziert",
            "Keine widersprüchlichen Aussagen"
        ],
        "calculation": "verified_facts / total_factual_claims"
    },
    
    "relevance": {
        "description": "Relevanz der Antwort für die spezifische Fragestellung",
        "factors": [
            "Direkte Bezug zur Frage",
            "Kontextspezifische Informationen",
            "Vermeidung unnötiger Informationen"
        ],
        "calculation": "relevant_content_ratio"
    },
    
    "consistency": {
        "description": "Interne Konsistenz und Widerspruchsfreiheit",
        "factors": [
            "Keine internen Widersprüche",
            "Konsistente Terminologie",
            "Logische Argumentationsstruktur"
        ],
        "calculation": "1 - contradiction_penalty"
    },
    
    "authority": {
        "description": "Autorität und Zuverlässigkeit der Quellen",
        "factors": [
            "Offizielle Behördenquellen",
            "Aktuelle Rechtsprechung",
            "Anerkannte Fachpublikationen"
        ],
        "calculation": "weighted_source_authority_score"
    }
}
```

### 🔄 Continuous Quality Improvement

```python
class QualityImprovementLoop:
    """
    Kontinuierliche Qualitätsverbesserung durch Feedback-Integration
    """
    
    def __init__(self):
        self.feedback_collector = FeedbackCollector()
        self.pattern_analyzer = PatternAnalyzer()
        self.model_updater = ModelUpdater()
    
    async def process_quality_feedback(self, 
                                     session_id: str,
                                     quality_feedback: Dict) -> None:
        """
        Verarbeitet Quality-Feedback für kontinuierliche Verbesserung
        """
        # 1. Feedback Storage
        await self.feedback_collector.store_feedback(
            session_id, quality_feedback
        )
        
        # 2. Pattern Analysis
        patterns = await self.pattern_analyzer.analyze_quality_patterns(
            feedback_data=quality_feedback,
            timeframe="last_7_days"
        )
        
        # 3. Agent Performance Updates
        if patterns.significant_changes_detected:
            await self.update_agent_performance_weights(patterns)
        
        # 4. Model Fine-tuning Triggers
        if patterns.quality_drift_detected:
            await self.trigger_model_retraining(patterns)
        
        # 5. Quality Threshold Adjustments
        await self.adjust_quality_thresholds_if_needed(patterns)
```

### Kontext zum Code (QualityImprovementLoop)

- Zweck: Aus Nutzerfeedback und Mustern kontinuierlich lernen.
- Schritte: Feedback speichern → Muster erkennen → Agentengewichte/Modelle anpassen → ggf. Re-Training auslösen.
- Datenschutz: Feedback wird ohne personenbezogene Daten verarbeitet; siehe Security-Abschnitt.

---

## 10. Deployment

### 🚀 Production Deployment

#### **Docker Configuration**
```dockerfile
# Dockerfile für VERITAS API Backend
FROM python:3.11-slim

WORKDIR /app

# System Dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Python Dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application Code
COPY . .

# Environment Configuration
ENV PYTHONPATH=/app
ENV VERITAS_ENV=production
ENV PORT=5000

# Health Check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:$PORT/health || exit 1

# Expose Port
EXPOSE $PORT

# Start Command
CMD ["uvicorn", "veritas_api_backend:app", "--host", "0.0.0.0", "--port", "5000"]
```

### Kontext zum Dockerfile (wichtigste Zeilen)

- Schlankes Basisimage (python:3.11-slim) reduziert Angriffsfläche und Größe.
- Dependencies und Requirements getrennt für besseres Layer-Caching.
- HEALTHCHECK erlaubt automatisches Wiederanstarten bei Störungen.
- EXPOSE/PORT definieren den API-Port (5000) konsistent.
- CMD startet Uvicorn in einer produktionsnahen Konfiguration.

#### **Docker Compose Configuration**
```yaml
# docker-compose.yml
version: '3.8'

services:
  veritas-api:
    build: .
    ports:
      - "5000:5000"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/veritas
      - REDIS_URL=redis://redis:6379/0
      - OLLAMA_URL=http://ollama:11434
    depends_on:
      - postgres
      - redis
      - ollama
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
    
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: veritas
      POSTGRES_USER: veritas_user
      POSTGRES_PASSWORD: secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
      
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
      
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    
  chromadb:
    image: chromadb/chroma:latest
    ports:
      - "8000:8000"
    volumes:
      - chroma_data:/chroma/chroma
      
volumes:
  postgres_data:
  redis_data:
  ollama_data:
  chroma_data:
```

#### **Kubernetes Deployment**
```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: veritas-api
  labels:
    app: veritas-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: veritas-api
  template:
    metadata:
      labels:
        app: veritas-api
    spec:
      containers:
      - name: veritas-api
        image: veritas/api-backend:latest
        ports:
        - containerPort: 5000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: veritas-secrets
              key: database-url
        livenessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
---
apiVersion: v1
kind: Service
metadata:
  name: veritas-api-service
spec:
  selector:
    app: veritas-api
  ports:
    - protocol: TCP
      port: 80
      targetPort: 5000
  type: LoadBalancer
```

### Kontext zur Kubernetes-Konfiguration

- replicas: Mehrere Pods für Ausfallsicherheit und Skalierung.
- Service (LoadBalancer): Exponiert die API nach außen; alternativ Ingress/ClusterIP.
- Probes (/health): Ermöglichen schnelles Erkennen fehlerhafter Pods.
- Ressourcenlimits: Schützen Cluster vor Überlast; Requests für Scheduling.

### 📊 Monitoring & Observability

```python
# monitoring.py
from prometheus_client import Counter, Histogram, Gauge
import structlog

# Metrics
REQUEST_COUNT = Counter('veritas_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('veritas_request_duration_seconds', 'Request duration')
AGENT_PERFORMANCE = Histogram('veritas_agent_duration_seconds', 'Agent performance', ['agent_type'])
ACTIVE_SESSIONS = Gauge('veritas_active_sessions', 'Active streaming sessions')

# Structured Logging
logger = structlog.get_logger()

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    REQUEST_DURATION.observe(duration)
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    logger.info(
        "request_processed",
        method=request.method,
        path=request.url.path,
        duration=duration,
        status_code=response.status_code
    )
    
    return response
```

### Kontext zum Monitoring-Code

- REQUEST_COUNT: Zählt Anfragen (Method/Endpoint/Status) für Durchsatz/Fehlerraten.
- REQUEST_DURATION: Verteilung der Antwortzeiten zur Performanceanalyse.
- AGENT_PERFORMANCE: Dauer pro Agenten-Typ identifiziert langsame Worker.
- ACTIVE_SESSIONS: Anzahl aktiver Streaming-Sessions als Lastindikator.
- Structured Logging (structlog): Maschinell auswertbare Logs für Debugging/Audits.

### 🔐 Security Configuration

```python
# security.py
SECURITY_CONFIG = {
    "cors": {
        "allow_origins": ["https://veritas.app", "https://admin.veritas.app"],
        "allow_methods": ["GET", "POST"],
        "allow_headers": ["*"],
        "allow_credentials": True
    },
    
    "rate_limiting": {
        "requests_per_minute": 60,
        "burst_limit": 10,
        "sliding_window": True
    },
    
    "authentication": {
        "jwt_secret_key": "${JWT_SECRET_KEY}",
        "jwt_algorithm": "HS256",
        "jwt_expiration": 3600  # 1 hour
    },
    
    "input_validation": {
        "max_query_length": 5000,
        "allowed_file_types": [".pdf", ".txt", ".docx"],
        "max_file_size": "10MB"
    }
}
```

---

## 11. Roadmap

> Wohin geht die Reise? Kurz: schneller, klüger, breiter einsetzbar – mit Fokus auf Qualität, Sicherheit und Anwenderfreundlichkeit.

### 🗓️ Entwicklungs-Roadmap 2025-2026

#### **Q4 2025 - Foundation Enhancement**

**🎯 Woche 39-42 (September-Oktober)**
- ✅ **Streaming Integration Completed**
  - Real-time Progress Updates via SSE
  - User Cancellation Support
  - Frontend Integration mit veritas_app.py

- 🔄 **Agent System Optimization**
  - Performance-Tuning für parallele Agent-Execution
  - Memory-optimierte Agent-Pipeline
  - Enhanced Error Recovery

**🎯 Woche 43-46 (Oktober-November)**
- 🆕 **Advanced RAG Pipeline**
  - Multi-modal Document Processing (PDF, Images, Tables)
  - Enhanced Graph Traversal Algorithms
  - Semantic Chunking mit Overlap-Strategien

- 🆕 **Quality Framework v2.0**
  - ML-basierte Quality Assessment
  - Automated Quality Improvement Loops
  - User Feedback Integration

**🎯 Woche 47-52 (November-Dezember)**
- 🆕 **Extended External API Integration**
  - 50+ neue Behörden-APIs
  - Rate Limiting & Circuit Breaker Enhancement
  - API Response Caching Layer

#### **Q1 2026 - Intelligence & Automation**

**🎯 Januar 2026**
- 🆕 **LLM Fine-tuning Pipeline**
  - Domain-spezifische Model Fine-tuning
  - Automated Training Data Generation
  - A/B Testing für Model Performance

**🎯 Februar 2026**
- 🆕 **Agent Learning System**
  - Reinforcement Learning für Agent-Selektion
  - Dynamic Agent Weight Adjustment
  - Continuous Performance Optimization

**🎯 März 2026**
- 🆕 **Predictive Analytics**
  - Query Intent Prediction
  - Proactive Information Retrieval
  - User Behavior Pattern Recognition

#### **Q2 2026 - Scale & Performance**

**🎯 April 2026**
- 🆕 **Distributed Agent Architecture**
  - Microservices-basierte Agent-Deployment
  - Load Balancing für Agent-Pools
  - Cross-Region Agent Distribution

**🎯 Mai 2026**
- 🆕 **Advanced Caching Layer**
  - Intelligent Query Result Caching
  - Distributed Cache mit Redis Cluster
  - Cache Invalidation Strategies

**🎯 Juni 2026**
- 🆕 **Performance Analytics**
  - Real-time Performance Monitoring
  - Bottleneck Detection & Auto-Scaling
  - Cost Optimization durch Usage Analytics

#### **Q3 2026 - Innovation & Integration**

**🎯 Juli 2026**
- 🆕 **Multi-Language Support**
  - Englisch, Französisch, Italienisch
  - Cross-Language Legal Document Processing
  - Language-specific Agent Specialization

**🎯 August 2026**
- 🆕 **Voice Interface Integration**
  - Speech-to-Text für Voice Queries
  - Text-to-Speech für Responses
  - Voice-optimierte Agent Responses

**🎯 September 2026**
- 🆕 **Mobile API Optimization**
  - Mobile-first Response Formatting
  - Bandwidth-optimierte Streaming
  - Offline-Capable Agent Results

#### **Q4 2026 - Enterprise & Advanced Features**

**🎯 Oktober 2026**
- 🆕 **Enterprise Features**
  - Multi-Tenant Architecture
  - Role-based Access Control
  - Audit Logging & Compliance

**🎯 November 2026**
- 🆕 **Advanced Analytics Dashboard**
  - Admin Dashboard für System Monitoring
  - Usage Analytics & Reporting
  - Performance Trend Analysis

**🎯 Dezember 2026**
- 🆕 **AI-Powered Workflows**
  - Automated Workflow Generation
  - Cross-Agent Workflow Orchestration
  - Intelligent Task Delegation

### 📊 Success Metrics & KPIs

```python
ROADMAP_SUCCESS_METRICS = {
    "performance": {
        "avg_response_time": "< 3 seconds",
        "availability": "> 99.9%",
        "concurrent_users": "> 1000"
    },
    
    "quality": {
        "avg_quality_score": "> 0.85",
        "user_satisfaction": "> 90%",
        "accuracy_rate": "> 95%"
    },
    
    "adoption": {
        "daily_active_users": "> 5000",
        "query_volume": "> 10000/day",
        "api_integrations": "> 100"
    },
    
    "innovation": {
        "new_agent_types": "2 per quarter",
        "api_integrations": "10 per quarter", 
        "feature_releases": "1 per month"
    }
}
```

### 🎯 Strategic Priorities

1. **🚀 Performance First**: Sub-3-second response times bei allen Queries
2. **🧠 Intelligence Enhancement**: Kontinuierliche AI/ML-Verbesserungen
3. **🔗 Ecosystem Growth**: Aufbau eines Developer-Ecosystems
4. **🌍 Scale Preparation**: Vorbereitung für bundesweite Nutzung
5. **🔒 Security & Compliance**: Höchste Sicherheitsstandards

---

## 📞 Support & Kontakt

### 🛠️ Technical Support
- **Email**: tech-support@veritas.system
- **Documentation**: https://docs.veritas.system
- **API Status**: https://status.veritas.system

### 🤝 Development Community
- **GitHub**: https://github.com/veritas-system/api-backend
- **Discord**: https://discord.gg/veritas-dev
- **Developer Portal**: https://developers.veritas.system

### 📚 Training & Resources
- **Getting Started Guide**: /docs/getting-started
- **Agent Development Tutorial**: /docs/agent-development
- **API Integration Examples**: /docs/examples

---

*Diese Dokumentation wird kontinuierlich aktualisiert. Letzte Aktualisierung: 21. September 2025*