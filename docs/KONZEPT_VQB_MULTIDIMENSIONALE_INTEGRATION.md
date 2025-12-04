# VQB - Multidimensionale Datenintegration

## Der VQB als Integrations- und Vermittlungsschicht
**Version**: 1.0  
**Datum**: 19. November 2025

---

## 1. Kernkonzept: Datenquellenintegration

### 1.1 Vision

Der **Visual Query Builder (VQB)** ist eine **Integrations- und Vermittlungsschicht**, die heterogene Datenquellen aus dem VCC-Veritas-Ökosystem zusammenführt und über **multiple Dimensionen** verschneidet.

```
┌─────────────────────────────────────────────────────────────────┐
│                 VQB - Integrations-Layer                         │
│                                                                   │
│  Vereint und verschneidet Daten aus verschiedenen Quellen        │
│  über Zeit, Raum, Recht, Organisation                           │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
    ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
    │ VPB         │  │ Neo4j       │  │ PostgreSQL  │
    │ (Prozesse)  │  │ (Graph)     │  │ (Relational)│
    └─────────────┘  └─────────────┘  └─────────────┘
              ▼               ▼               ▼
    ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
    │ ChromaDB    │  │ Filesystem  │  │ External    │
    │ (Vector)    │  │ (Files)     │  │ APIs        │
    └─────────────┘  └─────────────┘  └─────────────┘
```

**Ziel**: Einheitliche Sicht auf verteilte Daten durch multidimensionale Verknüpfung.

---

## 2. Die Dimensionen

### 2.1 Zeitliche Dimension (Temporal)

**Zweck**: Entwicklung über Zeit nachvollziehen

**Datenquellen**:
- VPB: Prozess-Zeiträume, Meilensteine
- Neo4j: Historische Rechtsnorm-Versionen
- PostgreSQL: Änderungshistorien, Zeitstempel
- Files: Versionierte Dokumente

**Visualisierung**:
```
Timeline (horizontal):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━→ Zeit
2020        2021        2022        2023        2024        2025

Prozess-Ebene (VPB):
  ████████████ Genehmigungsverfahren
              ████████████████████████████████ Betriebsphase

Rechtliche Ebene (Neo4j):
     │                │                    │
     │ BImSchG §4     │ 13.BImSchV neu     │ BImSchG §5 geändert
     │ (Initial)      │ (Novellierung)     │ (Amendment)

Geo-Ebene (PostgreSQL):
  [Bund]──────────────────────────────────────────────────────
     └─[Land Brandenburg]─────────────────────────────────────
           └─[Kommune Potsdam]───────────────────────────────

Dokument-Ebene (Files + Vector):
  📄──────📄──────────📄───────────────📄──────────────────📄
  v1.0    v1.1        v2.0             v2.1              v3.0
```

**Operationen**:
- **Zeitreise**: Zustand zu beliebigem Zeitpunkt anzeigen
- **Änderungsverfolgung**: Was hat sich wann geändert?
- **Projektion**: Zukünftige Entwicklungen prognostizieren

### 2.2 Rechtliche Dimension (Legal)

**Zweck**: Rechtliche Grundlagen und Zusammenhänge

**Datenquellen**:
- Neo4j: Rechtsnormen, Chunks, Rechtsbereiche
- PostgreSQL: Norm-Metadaten, Gültigkeitsbereiche
- ChromaDB: Semantische Ähnlichkeit von Rechtsnormen
- Files: Volltext-Dokumente (Gesetze, Verordnungen)

**Visualisierung**:
```
Rechtshierarchie (vertikal):

Gesetz (oberste Ebene)
├── BImSchG
│   ├── § 4 Genehmigungspflicht ───┐
│   ├── § 5 Betreiberpflichten     │
│   └── § 15 Anzeigepflicht        │
│                                   │
Verordnung (untergeordnet)          │ Implementiert durch
├── 4. BImSchV ◄───────────────────┘
│   ├── Anhang 1 (Anlagentypen)
│   └── § 6 (Verfahren)
│
└── 13. BImSchV
    ├── § 3 (Grenzwerte)
    └── Anhang (Messpflichten)

Rechtsbereiche (horizontal):
[Umweltrecht] ←→ [Baurecht] ←→ [Verwaltungsrecht]
      ↑                              ↑
      └──────────[Überschneidung]────┘
```

**Operationen**:
- **Norm-Lookup**: Welche Normen gelten für Entität X?
- **Änderungs-Impact**: Welche Prozesse sind von Gesetzesänderung betroffen?
- **Rechtsbereichs-Filter**: Nur Umweltrecht anzeigen

### 2.3 Geo-basierte Dimension (Spatial/Federal)

**Zweck**: Räumliche und föderale Zuständigkeiten

**Datenquellen**:
- PostgreSQL: Föderale Ebenen, Zuständigkeitsbereiche
- Neo4j: Standort-Beziehungen, Hierarchien
- External APIs: Geodaten, Kataster

**Visualisierung**:
```
Föderale Hierarchie:

           ┌─────────────┐
           │    BUND     │ (Bundesebene)
           └──────┬──────┘
                  │
      ┌───────────┼───────────┐
      ▼           ▼           ▼
  ┌───────┐  ┌───────┐   ┌────────┐
  │ B-W   │  │  BB   │   │ Berlin │ (Länder)
  └───┬───┘  └───┬───┘   └────────┘
      │          │
  ┌───▼───┐  ┌───▼───┐
  │ Komm. │  │Potsdam│ (Kommunen)
  └───────┘  └───────┘

Geo-Karte (optional):
   ┌─────────────────────────────┐
   │         ╔═══╗               │
   │         ║ BB║               │
   │    ╔════╝   ╚════╗          │
   │    ║   ● Potsdam ║          │
   │    ║             ║          │
   │    ╚═════════════╝          │
   └─────────────────────────────┘
   
Standort-Marker:
● = Anlage/Einrichtung
■ = Behörde
▲ = Bauvorhaben
```

**Operationen**:
- **Zuständigkeits-Filter**: Nur Brandenburg-relevante Daten
- **Geo-Aggregation**: Alle Anlagen in Region X
- **Hierarchie-Navigation**: Von Kommune → Land → Bund

### 2.4 Organisatorische Dimension (Organizational)

**Zweck**: Verantwortlichkeiten und Zuständigkeiten

**Datenquellen**:
- PostgreSQL: Behörden, Organisationsstrukturen
- Neo4j: Organisationsbeziehungen
- VPB: Prozessverantwortliche

**Visualisierung**:
```
Organisationshierarchie:

        ┌──────────────────────┐
        │   Umweltministerium  │
        │   (BMUV)             │
        └──────────┬───────────┘
                   │
     ┌─────────────┼─────────────┐
     ▼             ▼             ▼
┌─────────┐  ┌─────────┐  ┌─────────┐
│Abteilung│  │Abteilung│  │Abteilung│
│   IG    │  │   WA    │  │   N     │
└─────────┘  └─────────┘  └─────────┘
     │
     ├─[Referat IG I 2] → Zuständig für: Anlagengenehmigung
     └─[Referat IG I 3] → Zuständig für: Überwachung

Verantwortlichkeiten:
Prozess: "Genehmigungsverfahren 2024-001"
├─ Federführung: Referat IG I 2
├─ Beteiligung: Referat N (Naturschutz)
└─ Anhörung: Gemeinde Potsdam
```

**Operationen**:
- **Verantwortungs-Filter**: Alle Vorgänge von Referat X
- **Beteiligungs-Analyse**: Wer ist in Prozess Y involviert?
- **Zuständigkeits-Lookup**: Welche Behörde ist zuständig?

### 2.5 Fachliche Dimension (Domain)

**Zweck**: Fachliche Kategorisierung

**Datenquellen**:
- Neo4j: Rechtsbereiche, Fachgebiete
- PostgreSQL: Kategorien, Tags
- ChromaDB: Thematische Cluster

**Visualisierung**:
```
Fachgebiete (Tagcloud):

  ╔══════════════════════════════════════════╗
  ║                                          ║
  ║  UMWELT          Bau                     ║
  ║         recht            SOZIAL          ║
  ║                                          ║
  ║    Immissions-     Verwaltungs           ║
  ║      schutz          recht               ║
  ║                                          ║
  ║         Personal      ARBEITS            ║
  ║                         schutz           ║
  ╚══════════════════════════════════════════╝

Größe = Anzahl Dokumente/Prozesse

Fachliche Cluster (ChromaDB Vector):
     [Cluster 1: Genehmigungen]
           ◉ ◉
         ◉   ◉ ◉
           ◉
     
     [Cluster 2: Überwachung]
         ◉ ◉ ◉
           ◉
```

**Operationen**:
- **Fachbereichs-Filter**: Nur Umweltrecht
- **Themen-Clustering**: Ähnliche Vorgänge finden
- **Cross-Domain-Suche**: Überschneidungen zwischen Fachgebieten

### 2.6 Semantische Dimension (Semantic/Vector)

**Zweck**: Bedeutungsbasierte Verknüpfung

**Datenquellen**:
- ChromaDB: Vektor-Embeddings von Texten
- Neo4j: Semantische Graph-Relationen
- External: LLM-basierte Ähnlichkeit

**Visualisierung**:
```
Vektor-Raum (2D-Projektion):

  Semantische Ähnlichkeit
    │
    │    ● Genehmigung
    │   ●  ●
    │  ● Erlaubnis
    │     ● Bewilligung
────┼────────────────────
    │
    │ ● Überwachung
    │  ● Kontrolle
    │   ●
    │    ● Inspektion
```

**Operationen**:
- **Ähnlichkeits-Suche**: Finde semantisch ähnliche Dokumente
- **Konzept-Expansion**: "Genehmigung" → ["Erlaubnis", "Bewilligung", ...]
- **Empfehlungen**: "Nutzer die X lasen, lasen auch Y"

---

## 3. Multidimensionale Verknüpfung

### 3.1 Beispiel: Verschneidung aller Dimensionen

**Szenario**: "Zeige alle Genehmigungsverfahren für Großfeuerungsanlagen in Brandenburg, die von der Novellierung der 13. BImSchV 2023 betroffen sind"

```python
# Multidimensionale Query
query = MultiDimensionalQuery()

# Zeitliche Dimension
query.add_filter(TemporalFilter(
    start_date=datetime(2020, 1, 1),
    end_date=datetime(2024, 12, 31)
))

# Rechtliche Dimension
query.add_filter(LegalFilter(
    rechtsnormen=["urn:vcc:legal:norm:13bimschv:year:2023"],
    auswirkung=[AuswirkungsArt.DIREKT, AuswirkungsArt.INDIREKT]
))

# Geo-Dimension
query.add_filter(GeoFilter(
    foederale_ebene="urn:vcc:fed:land:brandenburg"
))

# Fachliche Dimension
query.add_filter(DomainFilter(
    rechtsbereiche=["umweltrecht"],
    anlagen_typ=["feuerungsanlage"]
))

# Organisatorische Dimension
query.add_filter(OrganizationalFilter(
    zustaendige_behoerde="urn:vcc:org:authority:mluk-bb"
))

# Ausführen
results = vqb.execute_query(query)
```

**Ergebnis**: Liste von Entitäten (Prozesse, Dokumente, etc.), die ALLE Kriterien erfüllen.

### 3.2 Visualisierung: Multidimensionale Matrix

```
3D-Würfel (Zeit × Geo × Recht):

        Recht
         ↑
         │     ╱╲
         │    ╱  ╲ BImSchG
         │   ╱    ╲
         │  ╱______╲
         │ ╱  VwVfG ╲
         │╱__________╲
         └────────────→ Zeit
        ╱
       ╱ Geo (Bund/Land/Kommune)
      ↙

Jeder Punkt im Würfel = Datenpunkt
Farbe = Fachgebiet
Größe = Anzahl verknüpfter Dokumente
```

---

## 4. Datenquellen-Integration

### 4.1 Architektur

```
┌─────────────────────────────────────────────────────────────┐
│                VQB Integration Layer                         │
│                                                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ Temporal    │  │   Legal     │  │    Geo      │         │
│  │ Aggregator  │  │ Aggregator  │  │ Aggregator  │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
│         │                │                │                 │
│         └────────────────┼────────────────┘                 │
│                          │                                   │
│                   ┌──────▼──────┐                           │
│                   │   Query     │                           │
│                   │  Executor   │                           │
│                   └──────┬──────┘                           │
└──────────────────────────┼──────────────────────────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
    ┌────▼────┐       ┌────▼────┐      ┌────▼────┐
    │  VPB    │       │ Neo4j   │      │ Postgres│
    │ Adapter │       │ Adapter │      │ Adapter │
    └────┬────┘       └────┬────┘      └────┬────┘
         │                 │                 │
    ┌────▼────┐       ┌────▼────┐      ┌────▼────┐
    │   VPB   │       │  Neo4j  │      │Postgres │
    │ Backend │       │  Graph  │      │   DB    │
    └─────────┘       └─────────┘      └─────────┘
```

### 4.2 Adapter-Pattern

```python
from abc import ABC, abstractmethod
from typing import List, Any

class DataSourceAdapter(ABC):
    """Abstrakte Basis für Datenquellen-Adapter"""
    
    @abstractmethod
    async def query(self, filters: Dict[str, Any]) -> List[Any]:
        """Query mit Filtern"""
        pass
    
    @abstractmethod
    def supports_dimension(self, dimension: str) -> bool:
        """Prüfe ob Dimension unterstützt wird"""
        pass

class VPBAdapter(DataSourceAdapter):
    """Adapter für VPB-Backend"""
    
    def supports_dimension(self, dimension: str) -> bool:
        return dimension in ["temporal", "organizational", "process"]
    
    async def query(self, filters):
        # Temporal Filter
        if "temporal" in filters:
            start = filters["temporal"]["start"]
            end = filters["temporal"]["end"]
            # Query VPB processes in timerange
        
        # Organizational Filter
        if "organizational" in filters:
            authority = filters["organizational"]["authority"]
            # Query processes by authority

class Neo4jAdapter(DataSourceAdapter):
    """Adapter für Neo4j Graph"""
    
    def supports_dimension(self, dimension: str) -> bool:
        return dimension in ["legal", "geo", "semantic"]
    
    async def query(self, filters):
        cypher = "MATCH (c:Chunk)"
        
        # Legal Filter
        if "legal" in filters:
            cypher += "-[:BELONGS_TO]->(d:LegalDomain {name: $domain})"
        
        # Geo Filter
        if "geo" in filters:
            cypher += "-[:GOVERNED_BY]->(f:FederalLevel {urn: $federal_urn})"
        
        cypher += " RETURN c"
        
        return await self.neo4j.run(cypher, **filters)

class PostgreSQLAdapter(DataSourceAdapter):
    """Adapter für PostgreSQL"""
    
    def supports_dimension(self, dimension: str) -> bool:
        return dimension in ["temporal", "geo", "organizational", "metadata"]
    
    async def query(self, filters):
        sql = "SELECT * FROM entities WHERE 1=1"
        params = []
        
        # Temporal
        if "temporal" in filters:
            sql += " AND created_at BETWEEN %s AND %s"
            params.extend([filters["temporal"]["start"], filters["temporal"]["end"]])
        
        # Geo
        if "geo" in filters:
            sql += " AND federal_level = %s"
            params.append(filters["geo"]["level"])
        
        return await self.db.fetch(sql, *params)

class ChromaDBAdapter(DataSourceAdapter):
    """Adapter für ChromaDB (Vector)"""
    
    def supports_dimension(self, dimension: str) -> bool:
        return dimension in ["semantic", "domain"]
    
    async def query(self, filters):
        # Semantic similarity search
        if "semantic" in filters:
            query_text = filters["semantic"]["text"]
            return self.collection.query(
                query_texts=[query_text],
                n_results=filters.get("limit", 10)
            )
```

### 4.3 Query Executor

```python
class MultiDimensionalQueryExecutor:
    """Führt Queries über multiple Datenquellen und Dimensionen aus"""
    
    def __init__(self):
        self.adapters = {
            "vpb": VPBAdapter(),
            "neo4j": Neo4jAdapter(),
            "postgres": PostgreSQLAdapter(),
            "chromadb": ChromaDBAdapter()
        }
    
    async def execute(self, query: MultiDimensionalQuery) -> List[Entity]:
        """
        Führe Query aus und verschneide Ergebnisse
        
        Strategie:
        1. Bestimme welche Adapter für welche Dimensionen zuständig
        2. Führe Teil-Queries parallel aus
        3. Verschneide Ergebnisse über URNs
        4. Aggregiere und sortiere
        """
        # 1. Filter nach Adaptern gruppieren
        adapter_queries = self._group_by_adapter(query)
        
        # 2. Parallel ausführen
        results = await asyncio.gather(*[
            adapter.query(filters) 
            for adapter, filters in adapter_queries.items()
        ])
        
        # 3. Verschneiden über URNs
        merged = self._merge_results(results)
        
        # 4. Post-Processing (Sortierung, Ranking)
        final = self._post_process(merged, query.ranking)
        
        return final
    
    def _merge_results(self, results: List[List[Any]]) -> List[Entity]:
        """
        Verschneide Ergebnisse über URNs
        
        Nur Entitäten, die in ALLEN Ergebnislisten vorkommen,
        werden zurückgegeben (AND-Verknüpfung).
        """
        # Konvertiere zu URN-Sets
        urn_sets = [
            {self._extract_urn(item) for item in result}
            for result in results
        ]
        
        # Schnittmenge bilden
        common_urns = set.intersection(*urn_sets)
        
        # Entitäten laden
        entities = []
        for urn in common_urns:
            entity = self._load_entity_by_urn(urn)
            entities.append(entity)
        
        return entities
```

---

## 5. UI-Komponenten für Multidimensionale Navigation

### 5.1 Dimension Selector

```python
class DimensionSelector(tk.Frame):
    """
    UI-Komponente zur Auswahl aktiver Dimensionen
    
    Ermöglicht Nutzer:
    - Dimensionen ein/ausschalten
    - Filter pro Dimension setzen
    - Verschneidungs-Modus wählen (AND/OR)
    """
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.active_dimensions = {}
        
        # Checkboxes für Dimensionen
        dimensions = [
            ("📅 Zeit", "temporal"),
            ("⚖️ Recht", "legal"),
            ("🌍 Geo", "geo"),
            ("🏢 Organisation", "organizational"),
            ("📚 Fachgebiet", "domain"),
            ("🔍 Semantik", "semantic")
        ]
        
        for label, dim_id in dimensions:
            var = tk.BooleanVar()
            self.active_dimensions[dim_id] = var
            
            cb = tk.Checkbutton(self, text=label, variable=var,
                              command=lambda d=dim_id: self._toggle_dimension(d))
            cb.pack(anchor="w")
    
    def _toggle_dimension(self, dimension_id):
        """Dimension aktivieren/deaktivieren"""
        if self.active_dimensions[dimension_id].get():
            # Zeige Filteroptionen für diese Dimension
            self._show_filter_panel(dimension_id)
        else:
            # Verstecke Filteroptionen
            self._hide_filter_panel(dimension_id)
```

### 5.2 Multidimensionales Dashboard

```
┌─────────────────────────────────────────────────────────────┐
│  VQB - Multidimensionales Dashboard                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Aktive Dimensionen:  [x] Zeit  [x] Recht  [ ] Geo          │
│                       [x] Organisation  [ ] Semantik         │
│                                                               │
├─────────────┬───────────────────────────────────────────────┤
│             │                                                 │
│ Dimension-  │         Hauptansicht                          │
│ Filter      │                                                 │
│             │  ┌──────────────────────────────────────┐     │
│ 📅 Zeit     │  │  Timeline View                        │     │
│  2020-2024  │  │  (zeigt gefilterte Prozesse)         │     │
│             │  └──────────────────────────────────────┘     │
│ ⚖️ Recht    │                                                 │
│  BImSchG    │  ┌──────────────────────────────────────┐     │
│  13.BImSchV │  │  Graph View                           │     │
│             │  │  (zeigt rechtliche Verknüpfungen)     │     │
│ 🏢 Org      │  └──────────────────────────────────────┘     │
│  MLUK-BB    │                                                 │
│             │  ┌──────────────────────────────────────┐     │
│             │  │  Ergebnisliste (42 Treffer)          │     │
│             │  │  ✓ Genehmigung XYZ                   │     │
│             │  │  ✓ Überwachung ABC                   │     │
│             │  └──────────────────────────────────────┘     │
└─────────────┴───────────────────────────────────────────────┘
```

---

## 6. Use Cases

### Use Case 1: Rechtliche Änderungsanalyse

**Frage**: "Welche laufenden Verfahren in Brandenburg sind von der Novellierung der 13. BImSchV betroffen?"

```python
query = MultiDimensionalQuery()
query.add_filter(LegalFilter(rechtsnorm="urn:vcc:legal:norm:13bimschv:year:2023"))
query.add_filter(GeoFilter(land="brandenburg"))
query.add_filter(TemporalFilter(status="laufend"))

results = await executor.execute(query)
# → 15 Verfahren gefunden
```

### Use Case 2: Geo-basierte Compliance-Prüfung

**Frage**: "Alle Anlagen in Potsdam, die in den nächsten 6 Monaten eine Überwachung benötigen"

```python
query = MultiDimensionalQuery()
query.add_filter(GeoFilter(kommune="potsdam"))
query.add_filter(TemporalFilter(
    event_type="überwachung",
    next_n_months=6
))

results = await executor.execute(query)
```

### Use Case 3: Semantische Dokumentensuche über Zeit

**Frage**: "Dokumente ähnlich zu 'Immissionsschutz', erstellt seit 2022"

```python
query = MultiDimensionalQuery()
query.add_filter(SemanticFilter(text="Immissionsschutz", similarity=0.8))
query.add_filter(TemporalFilter(start=datetime(2022, 1, 1)))

results = await executor.execute(query)
```

---

## 7. Zusammenfassung

Der VQB ist eine **Integrations- und Vermittlungsschicht**, die:

✅ **Heterogene Datenquellen** vereint (VPB, Neo4j, PostgreSQL, ChromaDB, Files)  
✅ **Multiple Dimensionen** unterstützt (Zeit, Recht, Geo, Organisation, Fachgebiet, Semantik)  
✅ **Flexible Verschneidung** ermöglicht (AND/OR, gewichtete Kombinationen)  
✅ **Einheitliche Sicht** bietet (über VCC-URNs verknüpft)  
✅ **Interaktive Exploration** erlaubt (Drill-down über Dimensionen)

**Kernwert**: Komplexe Zusammenhänge über Systemgrenzen hinweg sichtbar machen.

---

**Version**: 1.0  
**Status**: Konzept für multidimensionale Integration  
**Nächste Schritte**: Implementierung Adapter-Layer und Query Executor
