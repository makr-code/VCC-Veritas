# TODO: SQLite-Datenbanken als FastAPI Test-Instanz für Agenten

**Datum**: 18. Oktober 2025
**Priorität**: ⭐⭐⭐ HOCH
**Ziel**: BImSchG und WKA SQLite-Datenbanken als Test-Datenquellen für Agenten über FastAPI bereitstellen

---

## 📋 Übersicht

### Vorhandene Datenbanken

| Datei | Pfad | Beschreibung |
|-------|------|--------------|
| `BImSchG.sqlite` | `data/bimschg/` | Bundesimmissionsschutzgesetz-Daten |
| `wka.sqlite` | `data/wka/` | Windkraftanlagen-Daten |

### Zusätzliche Dateien

- Shapefile-Daten (`.shp`, `.shx`, `.dbf`, `.prj`, `.cpg`)
- Dokumentations-Ordner (`dok/`)

---

## 🎯 Ziele

1. **FastAPI-Endpoints** für Datenbankzugriff erstellen
2. **Agent-Integration** ermöglichen
3. **Test-Queries** für Agenten bereitstellen
4. **API v3** erweitern mit Datenbank-Endpoints
5. **Dokumentation** erstellen

---

## ✅ Aufgaben

### Phase 1: Datenbank-Analyse (30 min)

- [ ] **BImSchG.sqlite analysieren**
  - Schema auslesen (Tabellen, Spalten, Indizes)
  - Beispiel-Daten prüfen
  - Datentypen identifizieren
  - Foreign Keys dokumentieren

- [ ] **wka.sqlite analysieren**
  - Schema auslesen
  - Beispiel-Daten prüfen
  - Räumliche Daten identifizieren (GIS)
  - Relationen zu Shapefile prüfen

- [ ] **Dokumentation lesen**
  - `data/bimschg/dok/` prüfen
  - `data/wka/dok/` prüfen
  - Datenmodell verstehen

**Script erstellen**:
```python
# scripts/analyze_sqlite_databases.py
import sqlite3
from pathlib import Path

def analyze_database(db_path: Path):
    """Analysiert SQLite-Datenbank und gibt Schema aus"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Tabellen auflisten
    tables = cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()

    for table in tables:
        print(f"Table: {table[0]}")
        # Spalten auflisten
        columns = cursor.execute(f"PRAGMA table_info({table[0]})").fetchall()
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
```

---

### Phase 2: FastAPI-Endpoints erstellen (1-2 Stunden)

- [ ] **Neuer Router erstellen**
  - Datei: `backend/api/v3/database_router.py`
  - Endpoints für BImSchG und WKA
  - Pydantic Models für Responses

- [ ] **BImSchG-Endpoints**
  - `GET /api/v3/database/bimschg/tables` - Liste aller Tabellen
  - `GET /api/v3/database/bimschg/schema/{table}` - Schema einer Tabelle
  - `POST /api/v3/database/bimschg/query` - SQL-Query ausführen
  - `GET /api/v3/database/bimschg/records/{table}` - Datensätze einer Tabelle (paginiert)
  - `GET /api/v3/database/bimschg/search` - Volltextsuche

- [ ] **WKA-Endpoints**
  - `GET /api/v3/database/wka/tables`
  - `GET /api/v3/database/wka/schema/{table}`
  - `POST /api/v3/database/wka/query`
  - `GET /api/v3/database/wka/records/{table}`
  - `GET /api/v3/database/wka/locations` - Geo-Daten (Windkraftanlagen-Standorte)
  - `GET /api/v3/database/wka/statistics` - Statistiken

- [ ] **Gemeinsame Endpoints**
  - `GET /api/v3/database/list` - Alle verfügbaren Datenbanken
  - `GET /api/v3/database/status` - Datenbank-Status und Verbindungen

**Router-Struktur**:
```python
# backend/api/v3/database_router.py
from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import sqlite3
from pathlib import Path

router = APIRouter(prefix="/database", tags=["Database"])

# Pydantic Models
class TableInfo(BaseModel):
    name: str
    columns: List[Dict[str, str]]
    row_count: int

class QueryRequest(BaseModel):
    sql: str
    limit: int = 100

class QueryResponse(BaseModel):
    success: bool
    columns: List[str]
    rows: List[Dict[str, Any]]
    row_count: int

# Database Connections
DATABASES = {
    "bimschg": Path("data/bimschg/BImSchG.sqlite"),
    "wka": Path("data/wka/wka.sqlite")
}

@router.get("/list")
async def list_databases():
    """Liste aller verfügbaren Datenbanken"""
    # ...

@router.get("/{db_name}/tables")
async def get_tables(db_name: str):
    """Liste aller Tabellen einer Datenbank"""
    # ...

@router.post("/{db_name}/query")
async def execute_query(db_name: str, query: QueryRequest):
    """SQL-Query ausführen"""
    # ...
```

---

### Phase 3: Agent-Integration (1 Stunde)

- [ ] **DatabaseAgent erweitern**
  - Datei: `backend/agents/veritas_api_agent_database.py`
  - Methoden für BImSchG und WKA hinzufügen
  - Query-Builder für strukturierte Abfragen

- [ ] **Neue Agent-Methoden**
  - `query_bimschg(query: str)` - BImSchG-Daten abfragen
  - `query_wka(query: str)` - WKA-Daten abfragen
  - `search_regulations(keyword: str)` - Vorschriften suchen
  - `find_wind_turbines(location: str)` - WKA nach Standort finden

- [ ] **ImmissionsschutzAgent erweitern**
  - Integration mit BImSchG-Datenbank
  - Vorschriften-Lookup
  - Grenzwerte abfragen

- [ ] **EnvironmentalAgent erweitern**
  - Integration mit WKA-Datenbank
  - Windkraftanlagen-Daten
  - Umweltauswirkungen

**Agent-Code-Beispiel**:
```python
# backend/agents/veritas_api_agent_database.py (Erweiterung)

class DatabaseAgent:
    def __init__(self):
        self.bimschg_db = "data/bimschg/BImSchG.sqlite"
        self.wka_db = "data/wka/wka.sqlite"

    async def query_bimschg(self, query_text: str) -> Dict[str, Any]:
        """Fragt BImSchG-Datenbank ab"""
        # NLP → SQL-Query konvertieren
        sql = self._convert_to_sql(query_text, "bimschg")

        # Query ausführen
        results = self._execute_query(self.bimschg_db, sql)

        return {
            "source": "BImSchG Database",
            "results": results,
            "sql_query": sql
        }

    async def query_wka(self, location: str = None) -> Dict[str, Any]:
        """Fragt WKA-Datenbank ab"""
        # ...
```

---

### Phase 4: Testing (30 min)

- [ ] **Unit-Tests erstellen**
  - Datei: `tests/test_database_router.py`
  - Tests für alle Endpoints
  - Mock-Datenbank für Tests

- [ ] **Integration-Tests**
  - Agent-Queries mit echten Datenbanken
  - End-to-End-Tests

- [ ] **Manuelles Testing**
  - Queries über OpenAPI Docs (`/docs`)
  - Agent-Execution testen

**Test-Beispiele**:
```python
# tests/test_database_router.py
import pytest
from fastapi.testclient import TestClient

def test_list_databases(client: TestClient):
    response = client.get("/api/v3/database/list")
    assert response.status_code == 200
    data = response.json()
    assert "bimschg" in data["databases"]
    assert "wka" in data["databases"]

def test_query_bimschg(client: TestClient):
    query = {
        "sql": "SELECT * FROM regulations LIMIT 10",
        "limit": 10
    }
    response = client.post("/api/v3/database/bimschg/query", json=query)
    assert response.status_code == 200
    assert response.json()["success"] == True
```

---

### Phase 5: Dokumentation (30 min)

- [ ] **API-Dokumentation erweitern**
  - `docs/API_V3_COMPLETE.md` aktualisieren
  - Neue Database-Endpoints dokumentieren
  - Beispiel-Queries hinzufügen

- [ ] **Agent-Dokumentation**
  - Agent-Capabilities dokumentieren
  - Use-Cases beschreiben

- [ ] **README erstellen**
  - `docs/DATABASE_INTEGRATION.md`
  - Schema-Dokumentation
  - Query-Beispiele

**Dokumentations-Struktur**:
```markdown
# Database Integration - BImSchG & WKA

## Datenbanken

### BImSchG (Bundesimmissionsschutzgesetz)
- **Pfad**: `data/bimschg/BImSchG.sqlite`
- **Tabellen**: regulations, limits, procedures
- **Use-Case**: Vorschriften-Lookup, Grenzwerte

### WKA (Windkraftanlagen)
- **Pfad**: `data/wka/wka.sqlite`
- **Tabellen**: turbines, locations, specifications
- **Use-Case**: Standort-Daten, Technische Spezifikationen

## Endpoints

### GET /api/v3/database/list
Liste aller verfügbaren Datenbanken

### POST /api/v3/database/{db_name}/query
SQL-Query ausführen

**Request**:
```json
{
  "sql": "SELECT * FROM regulations WHERE category = 'emission'",
  "limit": 50
}
```

**Response**:
```json
{
  "success": true,
  "columns": ["id", "title", "description"],
  "rows": [...],
  "row_count": 42
}
```
```

---

## 📂 Dateien zu erstellen

| Datei | Beschreibung | LOC (geschätzt) |
|-------|--------------|-----------------|
| `scripts/analyze_sqlite_databases.py` | Datenbank-Analyse-Script | ~150 |
| `backend/api/v3/database_router.py` | FastAPI Router für DBs | ~500 |
| `backend/api/v3/models.py` | Neue Pydantic Models | ~100 |
| `backend/agents/veritas_api_agent_database.py` | Agent-Erweiterungen | ~200 |
| `tests/test_database_router.py` | Unit-Tests | ~200 |
| `docs/DATABASE_INTEGRATION.md` | Dokumentation | ~30 Seiten |

---

## 🔧 Technische Details

### Sicherheit

- [ ] **SQL-Injection-Schutz**
  - Parameterized Queries verwenden
  - Whitelist für Tabellennamen
  - Query-Limits erzwingen

- [ ] **Read-Only-Zugriff**
  - Nur SELECT-Queries erlauben
  - Keine INSERT/UPDATE/DELETE

- [ ] **Rate-Limiting**
  - Max. 100 Queries/Minute pro Nutzer

### Performance

- [ ] **Connection-Pooling**
  - SQLite Connection Pool
  - Max. 10 Connections

- [ ] **Caching**
  - Schema-Informationen cachen
  - Häufige Queries cachen (5 min TTL)

- [ ] **Pagination**
  - Default: 50 Zeilen
  - Max: 1000 Zeilen

### Konfiguration

```python
# backend/api/v3/database_router.py

class DatabaseConfig:
    MAX_QUERY_RESULTS = 1000
    DEFAULT_PAGE_SIZE = 50
    QUERY_TIMEOUT = 30  # Sekunden
    CACHE_TTL = 300  # 5 Minuten

    ALLOWED_OPERATIONS = ["SELECT"]  # Nur Lese-Zugriff
```

---

## 🎯 Use-Cases

### 1. Agent-gestützte Vorschriften-Suche

**Scenario**: User fragt "Welche Grenzwerte gelten für Lärm bei Windkraftanlagen?"

**Flow**:
1. ImmissionsschutzAgent wird aktiviert
2. Agent fragt BImSchG-Datenbank ab: `query_bimschg("Lärmgrenzwerte Windkraft")`
3. Query wird in SQL übersetzt
4. Ergebnisse werden zurückgegeben
5. Agent formuliert Antwort mit Quellenangaben

### 2. Windkraftanlagen-Standortanalyse

**Scenario**: User fragt "Wie viele Windkraftanlagen gibt es in Baden-Württemberg?"

**Flow**:
1. EnvironmentalAgent wird aktiviert
2. Agent fragt WKA-Datenbank ab: `query_wka("Baden-Württemberg")`
3. Statistiken werden generiert
4. Geo-Daten werden visualisiert (optional)

### 3. Cross-Database-Queries

**Scenario**: User fragt "Welche WKA verstoßen gegen Lärmschutz-Vorschriften?"

**Flow**:
1. Multi-Agent-Coordination
2. ImmissionsschutzAgent holt Grenzwerte (BImSchG)
3. EnvironmentalAgent holt WKA-Daten (WKA)
4. Supervisor-Agent kombiniert Ergebnisse

---

## 📈 Erfolgs-Metriken

| Metrik | Ziel | Messung |
|--------|------|---------|
| API-Response-Zeit | <200ms | Durchschnitt aller DB-Queries |
| Query-Erfolgsrate | >95% | Erfolgreiche vs. fehlgeschlagene Queries |
| Agent-Integration | 100% | DatabaseAgent nutzt beide DBs |
| Test-Coverage | >80% | Code-Coverage der Router |
| Dokumentation | 100% | Alle Endpoints dokumentiert |

---

## 🔄 Integration in bestehendes System

### 1. Backend v3 erweitern

```python
# backend/api/veritas_api_backend_v3.py

from backend.api.v3.database_router import router as database_router

# Router hinzufügen
api_v3_router.include_router(database_router)
```

### 2. Agent-Registry erweitern

```python
# backend/agents/agent_registry.py

# DatabaseAgent mit neuen Capabilities registrieren
registry.register_agent(
    DatabaseAgent,
    capabilities=["bimschg_query", "wka_query", "sql_execution"]
)
```

### 3. System-Capabilities erweitern

```python
# backend/api/v3/system_router.py

@router.get("/capabilities")
async def get_capabilities():
    return {
        # ... existing capabilities
        "databases": {
            "bimschg": "available",
            "wka": "available"
        }
    }
```

---

## ⏱️ Zeitplan

| Phase | Aufwand | Dauer |
|-------|---------|-------|
| Phase 1: Datenbank-Analyse | 30 min | 0.5h |
| Phase 2: FastAPI-Endpoints | 1-2 Stunden | 2h |
| Phase 3: Agent-Integration | 1 Stunde | 1h |
| Phase 4: Testing | 30 min | 0.5h |
| Phase 5: Dokumentation | 30 min | 0.5h |
| **TOTAL** | **4-5 Stunden** | **~4.5h** |

---

## 🚀 Quick-Start (wenn TODO abgeschlossen)

```powershell
# 1. Backend starten
.\scripts\manage_backend_v3.ps1 -Action start

# 2. Datenbanken testen
Invoke-RestMethod -Uri "http://localhost:5000/api/v3/database/list"

# 3. BImSchG-Tabellen anzeigen
Invoke-RestMethod -Uri "http://localhost:5000/api/v3/database/bimschg/tables"

# 4. Query ausführen
$body = @{
    sql = "SELECT * FROM regulations LIMIT 10"
    limit = 10
} | ConvertTo-Json

Invoke-RestMethod -Method POST `
    -Uri "http://localhost:5000/api/v3/database/bimschg/query" `
    -Body $body -ContentType "application/json"

# 5. Agent-Query testen
$body = @{
    query_text = "Welche Lärmgrenzwerte gelten für Windkraftanlagen?"
    mode = "veritas"
    use_database = $true
} | ConvertTo-Json

Invoke-RestMethod -Method POST `
    -Uri "http://localhost:5000/api/v3/query/execute" `
    -Body $body -ContentType "application/json"
```

---

## 📝 Notizen

- SQLite-Datenbanken sind bereits vorhanden ✅
- Shapefile-Daten können später für Geo-Visualisierung genutzt werden
- GIS-Integration (z.B. mit GeoPandas) ist optional
- Connection-Pooling wichtig für Performance
- Read-Only-Modus für Sicherheit

---

**Erstellt**: 18. Oktober 2025
**Status**: ⏳ TODO
**Priorität**: ⭐⭐⭐ HOCH
**Nächster Schritt**: Phase 1 - Datenbank-Analyse starten
