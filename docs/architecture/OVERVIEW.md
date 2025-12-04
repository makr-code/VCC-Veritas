# Systemübersicht

**Status:** In Arbeit
**Zielgruppe:** Alle Rollen
**Ziel:** High-level Verständnis von VERITAS

---

## 🎯 Was ist VERITAS?

VERITAS ist ein **AI-gestütztes Dokumentations- und Recherche-System**, das:

- **Intelligente Suche:** Versteht komplexe juristische Anfragen
- **Kontextuelle Antworten:** Antwortet mit relevanten Quellen und Zitaten
- **Multi-Channel Integration:** Word Add-In, Web API, Desktop App
- **Real-time Streaming:** Live-Responses mit Zwischenschritten

---

## 🏗️ Kern-Komponenten

### 1. **Hybrid Search Engine**
- **Vector Search:** Semantische Suche mit ChromaDB
- **Keyword Search:** BM25 Full-Text-Suche
- **Graph Search:** Neo4j Relationships
- **Ranking:** Cross-Encoder Re-ranking

### 2. **Multi-Agent RAG System**
- **Query Understanding:** Intent-Klassifizierung und Expansion
- **Context Retrieval:** Dokumentensuche und -anreicherung
- **Response Generation:** LLM-basierte Antwort-Synthese
- **Hypothesis Generation:** Generierung von Hypothesen und Followup-Questions

### 3. **Office Integration**
- **Word Add-In:** Recherche direkt in Word
- **Real-time Streaming:** Live-Daten im Chat
- **Citation Management:** Automatische Quellenverweise
- **Export:** PDF-Export mit Formatierung

### 4. **Administration & Monitoring**
- **Dashboard:** System-Health und Metriken
- **Logging:** Strukturierte Logs aller Operationen
- **Configuration:** Umgebungsvariablen und Config-Files
- **Observability:** Prometheus-Metriken und Traces

---

## 📊 Datenfluss

```
User Query (Word Add-In)
        ↓
[Query Preprocessing]
  - Intent Classification
  - Query Expansion
  - Normalization
        ↓
[Hybrid Search]
  - Vector Search (ChromaDB)
  - Keyword Search (BM25)
  - Graph Search (Neo4j)
        ↓
[Re-ranking & Context Building]
  - Cross-Encoder Ranking
  - Token Budget Management
  - Source Deduplication
        ↓
[LLM Response Generation]
  - Prompt Engineering
  - Context Window Optimization
  - Streaming Response
        ↓
[Post-processing]
  - Citation Management
  - Format Optimization
  - Analytics Logging
        ↓
Response to User (Word Add-In / Web)
```

---

## 🔗 Integrations

| System | Rolle | Status |
|--------|-------|--------|
| **UDS3** | Dokumenten-Repository | ✅ Active |
| **ThemisDB** | Multi-Model DB | ✅ Active |
| **Ollama** | LLM Provider | ✅ Active |
| **Neo4j** | Graph Database | ✅ Active |
| **PostgreSQL** | Relational DB | ✅ Active |
| **Office** | Word Add-In | ✅ Active |
| **MCP** | Model Context Protocol | 📋 Planned |

---

## 🚀 Deployment-Topologie

```
┌─────────────────────────────────────┐
│        Word Add-In (Frontend)        │
└────────────┬────────────────────────┘
             │ REST / WebSocket
             ↓
┌─────────────────────────────────────┐
│   VERITAS Backend (FastAPI)          │
│  ├─ Query Router                     │
│  ├─ Agent Orchestrator              │
│  ├─ RAG Service                     │
│  └─ Stream Manager                  │
└──┬──┬──┬──┬──┬──────────────────────┘
   │  │  │  │  │
   ↓  ↓  ↓  ↓  ↓
┌──┬──┬──┬──┬──┐
│  │  │  │  │  │
│ChromaDB │ │ Neo4j │ PostgreSQL │
│        │ │       │
└────────┴─┴───────┘
```

---

## 📋 Architektur-Layer

| Layer | Komponenten | Zweck |
|-------|------------|--------|
| **Frontend** | Word Add-In, Web UI | User Interface |
| **API Gateway** | FastAPI Router | Request Handling |
| **Services** | RAG, Search, Chat | Business Logic |
| **Agents** | Multi-Agent System | Query Processing |
| **Storage** | ChromaDB, Neo4j, PostgreSQL | Data Persistence |
| **Infrastructure** | Docker, K8S, Monitoring | Deployment & Operations |

---

## 🎯 Workflows

### Workflow 1: Simple Query
```
User: "Was wird in §15 BImSchG geregelt?"
  ↓
[Query Understanding] → Intent: research
  ↓
[Hybrid Search] → 4 Dokumente gefunden
  ↓
[Re-ranking] → Sortiert nach Relevanz
  ↓
[LLM Generation] → Antwortet mit Quellen
  ↓
Response: "§15 regelt... (Quelle: BImSchG §15, S.34)"
```

### Workflow 2: Complex Research
```
User: "Vergleiche Regelungen in BImSchG vs. TA Luft"
  ↓
[Query Expansion] → 3 Such-Varianten
  ↓
[Batch Search] → 20+ Dokumente
  ↓
[Hypothesis Generation] → 5 Hypothesen
  ↓
[Agent Processing] → Analyse & Struktur
  ↓
Response: Strukturierte Vergleich-Tabelle
```

---

## 📈 Performance-Charakteristiken

| Metrik | Wert | Ziel |
|--------|------|------|
| Query Response Time | <3 Sekunden | <5 Sekunden |
| Search Recall | 92% | >90% |
| Citation Accuracy | 98% | >95% |
| System Uptime | 99.8% | >99% |
| Token Efficiency | 2.1x | <2.5x |

---

## 🔐 Security & Compliance

- **Authentication:** JWT Token-basiert
- **Encryption:** TLS 1.3 für Transit
- **Audit Logging:** Alle Queries geloggt
- **Data Privacy:** DSGVO-konform
- **Access Control:** Role-Based Access (RBAC)

---

## 📚 Weiterführende Dokumentation

- **[Backend-Architektur](BACKEND_ARCHITECTURE.md)** - Backend im Detail
- **[RAG-Pipeline](RAG_PIPELINE.md)** - RAG System
- **[Agent-Framework](AGENTS.md)** - Multi-Agent Orchestration
- **[API-Referenz](../api/API_REFERENCE.md)** - API Endpoints

---

**Fertig gelesen?** → Wähle einen der Weiterleitungs-Links oben.
