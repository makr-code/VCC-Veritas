# VERITAS Demo-Prompts - Agent & UDS3 Capabilities Showcase

**Datum:** 18. November 2025  
**System:** VERITAS + UDS3 Polyglot Database  
**Agenten:** 23 spezialisierte Domain-Experten

---

## 🎯 Schnellstart - Grundfunktionen

### 1. Einfache Frage (ASK Mode)
```
Was ist das Bundes-Immissionsschutzgesetz (BImSchG)?
```
**Zeigt:** RAG-Pipeline, Semantic Search, IEEE Citations

### 2. Multi-Source Retrieval
```
Welche Grenzwerte gelten für Luftschadstoffe nach TA Luft?
```
**Zeigt:** Hybrid Search (Vector + BM25), Document Retrieval

---

## 🏗️ Bau & Genehmigung

### 3. Genehmigungsverfahren
```
Welche Unterlagen brauche ich für eine BImSchG-Genehmigung einer Lackieranlage?
```
**Agent:** GenehmigungsAgent  
**Zeigt:** Prozess-Workflows, Compliance-Checks

### 4. Baurecht
```
Sind bei einem Wohnhaus mit 8 Stockwerken barrierefreie Zugänge nach DIN 18040 Pflicht?
```
**Agent:** ConstructionAgent, TechnicalStandardsAgent  
**Zeigt:** Multi-Agent-Koordination, Normrecherche

---

## 🌍 Umwelt & Naturschutz

### 5. Umweltrecht
```
Wie sind FFH-Gebiete rechtlich geschützt und welche Eingriffe sind verboten?
```
**Agent:** EnvironmentalAgent, NaturschutzAgent  
**Zeigt:** Graph-Traversal (Knowledge Graph), Relationship Mapping

### 6. Bodenschutz
```
Welche Grenzwerte gelten für Schwermetalle im Boden nach BBodSchV?
```
**Agent:** BodenGewaesserschutzAgent  
**Zeigt:** Relational DB Queries, Tabular Data

### 7. Immissionsschutz
```
Wie berechne ich die Schornsteinhöhe einer Feuerungsanlage nach TA Luft?
```
**Agent:** ImmissionsschutzAgent, AtmosphericFlowAgent  
**Zeigt:** Technische Berechnungen, API Integration

### 8. Emissionsmonitoring
```
Welche Messverfahren sind für NOx-Emissionen zugelassen?
```
**Agent:** EmissionenMonitoringAgent  
**Zeigt:** Real-time Data, External API

---

## 🧪 Chemie & Gefahrstoffe

### 9. Chemikalienrecht
```
Welche REACH-Anforderungen gelten für Chromtrioxid in der EU?
```
**Agent:** ChemicalDataAgent  
**Zeigt:** External API (PubChem/ChemSpider), Structured Data

### 10. Gefahrstofflagerung
```
Wie müssen brennbare Flüssigkeiten der Gefahrenklasse 3 gelagert werden?
```
**Agent:** TechnicalStandardsAgent  
**Zeigt:** Multi-Standard-Lookup (DIN, VDE, TRGS)

---

## 🌦️ Wetter & Klima

### 11. Wetterdaten
```
Wie ist die Wettervorhersage für München in den nächsten 3 Tagen?
```
**Agent:** DWDWeatherAgent (v1/v2), BrightskyWeatherAgent  
**Zeigt:** Live Weather API Integration (DWD, Brightsky)

### 12. Klimadaten
```
Welche durchschnittliche Niederschlagsmenge hatte Berlin im Oktober 2024?
```
**Agent:** DWDOpenDataAgent  
**Zeigt:** Historical Weather Data, Time-Series Analysis

---

## 🚗 Verkehr & Mobilität

### 13. Verkehrsrecht
```
Welche Lärmschutzanforderungen gelten für Straßen nach der 16. BImSchV?
```
**Agent:** TrafficAgent  
**Zeigt:** Cross-Domain Query (Verkehr + Immissionsschutz)

### 14. Straßenplanung
```
Welche Mindestbreiten gelten für Radwege nach den RASt 06?
```
**Agent:** TechnicalStandardsAgent, TrafficAgent  
**Zeigt:** Technical Standards Retrieval

---

## 💰 Finanzen & Soziales

### 15. Fördermittel
```
Welche KfW-Programme fördern energetische Sanierung von Wohngebäuden?
```
**Agent:** FinancialAgent  
**Zeigt:** Financial Data Retrieval, Subsidy Information

### 16. Sozialrecht
```
Welche Voraussetzungen gelten für Wohngeld nach dem WoGG?
```
**Agent:** SocialAgent  
**Zeigt:** Legal Framework Analysis, Eligibility Checks

---

## 📚 Verwaltung & Recht

### 17. Verwaltungsrecht
```
Wie läuft ein Widerspruchsverfahren nach VwGO ab?
```
**Agent:** VerwaltungsrechtAgent, VerwaltungsprozessAgent  
**Zeigt:** Process Modeling, Legal Workflows

### 18. Rechtsrecherche
```
Welche Urteile gibt es zur Auslegung von § 35 BauGB Außenbereich?
```
**Agent:** RechtsrechercheAgent  
**Zeigt:** Case Law Retrieval, Citation Networks

---

## 🔍 Wissensmanagement & Recherche

### 19. Wikipedia-Integration
```
Erkläre den Unterschied zwischen Kyoto-Protokoll und Pariser Abkommen
```
**Agent:** WikipediaAgent  
**Zeigt:** External Knowledge Base, Semantic Linking

### 20. Datenbank-Abfrage
```
Zeige alle Dokumente zum Thema "Lärmschutz" aus den letzten 2 Jahren
```
**Agent:** DatabaseAgent  
**Zeigt:** Direct DB Query, Metadata Filtering, Time-Range Queries

---

## 🚀 Advanced Use Cases - Multi-Agent Orchestration

### 21. Komplexe Genehmigung
```
Ich plane eine Biogasanlage mit 500 kW. Welche Genehmigungen brauche ich, 
welche Umweltauflagen gelten, und wie hoch sind die Fördermittel?
```
**Agents:** GenehmigungsAgent, EnvironmentalAgent, ImmissionsschutzAgent, FinancialAgent  
**Zeigt:** Multi-Agent-Workflow, Parallel Execution, Cross-Domain Integration

### 22. Städtebauliches Projekt
```
Wir bauen eine Schule mit 800 Schülern. Analysiere: Baurecht, Lärmschutz, 
Barrierefreiheit, Brandschutz, Verkehrsanbindung und Fördermöglichkeiten.
```
**Agents:** ConstructionAgent, TrafficAgent, TechnicalStandardsAgent, FinancialAgent, ImmissionsschutzAgent  
**Zeigt:** Supervisor-Agent, Parallel Queries, Consolidated Response

### 23. Umweltgutachten
```
Erstelle eine Übersicht zu Umweltauswirkungen eines Gewerbegebiets: 
Naturschutz, Bodenschutz, Luftqualität, Lärmimmissionen, Gewässerschutz.
```
**Agents:** EnvironmentalAgent, NaturschutzAgent, BodenGewaesserschutzAgent, ImmissionsschutzAgent, AtmosphericFlowAgent  
**Zeigt:** Environmental Impact Assessment, Multi-Source Data Fusion

---

## 🎓 System-Capabilities Showcase

### 24. Hybrid Search Demo
```
Finde alle relevanten Dokumente zu "Emissionsgrenzwerte Biogas BImSchG TA Luft"
```
**Zeigt:** 
- Dense Retrieval (Semantic Embeddings)
- Sparse Retrieval (BM25 Keyword Matching)
- Reciprocal Rank Fusion (RRF)
- Cross-Encoder Re-Ranking

### 25. Knowledge Graph Navigation
```
Zeige mir die Zusammenhänge zwischen BImSchG, TA Luft, 4. BImSchV und TEHG
```
**Zeigt:**
- Neo4j Graph Traversal
- Relationship Mapping
- Citation Networks
- Legal Hierarchy

### 26. Multi-Database Query
```
Welche Genehmigungen wurden 2024 in Bayern für Windkraftanlagen erteilt?
```
**Zeigt:**
- PostgreSQL (Structured Metadata)
- ChromaDB (Semantic Search)
- Neo4j (Relationships)
- Document Retrieval (CouchDB/FileStore)

---

## 📊 UDS3 Polyglot Database Features

### Vector Search (ChromaDB)
- Semantic Document Retrieval
- Embedding-based Similarity
- Multi-Query Expansion

### Graph Traversal (Neo4j)
- Legal Citation Networks
- Process Dependencies
- Knowledge Graph Exploration

### Relational Queries (PostgreSQL)
- Metadata Filtering
- Time-Range Queries
- Structured Data Joins

### Document Storage (CouchDB - Optional)
- Original File Access
- Version History
- Attachment Handling

---

## 🔧 Technical Highlights

**Pipeline Features:**
- Intelligent Query Classification (Intent Detection)
- Token Budget Management (Dynamic Context Window)
- Query Expansion (Synonyms, Context, Technical Terms)
- Multi-Agent Coordination (Parallel + Sequential Execution)
- Progress Tracking (Real-time Updates via SSE)
- Streaming Responses (Chunked Output)

**Quality Features:**
- IEEE-Standard Citations (35+ Metadata Fields)
- Confidence Scoring (LLM + Retrieval)
- Source Diversity (Multiple Data Sources)
- Cross-Validation (Multi-Agent Consensus)
- Quality Metrics (Relevance, Completeness, Accuracy)

**Integration:**
- Office Add-ins (Word, Excel, PowerPoint)
- REST API (FastAPI)
- WebSocket (Real-time)
- SSE (Server-Sent Events)
- MCP Protocol (Model Context Protocol)

---

## 💡 Best Practices für Demo

1. **Starte einfach:** Beginne mit Prompt 1-3 (Grundfunktionen)
2. **Zeige Breite:** Wechsle zwischen Domänen (Umwelt → Bau → Verkehr)
3. **Demonstriere Tiefe:** Nutze Prompt 21-23 (Multi-Agent)
4. **Erkläre Technik:** Nutze Prompt 24-26 (System-Features)
5. **Live-Daten:** Nutze Wetter-Prompts (11-12) für Echtzeit-Demo
6. **Office-Integration:** Teste im Word Add-in für Business-Context

---

**Hinweis:** Alle Prompts funktionieren im:
- Office Add-in (Word/Excel/PowerPoint)
- REST API (`POST /api/office/query`)
- WebUI (falls vorhanden)
- CLI/Testing-Tools

**Status:** ✅ Backend läuft, Agenten registriert, UDS3 verfügbar
