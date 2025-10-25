# Immissionsschutz Test-Server

## Übersicht

**Eigenständige FastAPI-Instanz** für Immissionsschutz-Datenbanken mit vollständiger relationaler Struktur für Agenten-Tests.

### Technische Details

- **Port**: 5001 (getrennt vom VERITAS Backend auf Port 5000)
- **Technologie**: FastAPI + SQLite
- **Dokumentation**: http://localhost:5001/docs
- **Health**: http://localhost:5001/health

## Datenbanken

### 1. BImSchG (Referenzdatenbank)
- **Quelle**: `data/bimschg/BImSchG.sqlite`
- **Datensätze**: 4.062 genehmigte Anlagen
- **Zweck**: Bundesimmissionsschutzgesetz-Anlagen (Referenz)

### 2. WKA (Referenzdatenbank)
- **Quelle**: `data/wka/wka.sqlite`
- **Datensätze**: 5.457 Windkraftanlagen
- **Zweck**: Windkraftanlagen-Register (Referenz)

### 3. Immissionsschutz Test DB (Haupt-Datenbank)
- **Quelle**: `data/test_databases/immissionsschutz_test.sqlite`
- **Größe**: ~1.6 MB
- **Zweck**: Vollständige Simulation mit relationalen Daten

#### Tabellen:

| Tabelle | Datensätze | Beschreibung |
|---------|------------|--------------|
| `genehmigungsverfahren` | 800 | Genehmigungsverfahren nach § 4/16/19 BImSchG |
| `bescheide` | ~400 | Genehmigungsbescheide |
| `auflagen` | ~3.600 | Nebenbestimmungen und Auflagen |
| `ueberwachung` | 1.200 | Inspektionen und Überwachungsmaßnahmen |
| `messungen` | 3.000 | Lärm- und Emissionsmessungen |
| `maengel` | ~460 | Festgestellte Mängel und Verstöße |

## Server-Management

### PowerShell Script

```powershell
# Starten
.\scripts\manage_test_server.ps1 -Action start

# Stoppen
.\scripts\manage_test_server.ps1 -Action stop

# Status
.\scripts\manage_test_server.ps1 -Action status

# Neustart
.\scripts\manage_test_server.ps1 -Action restart

# Tests
.\scripts\manage_test_server.ps1 -Action test
```

### Python (Direkt)

```bash
# Starten
python data/test_databases/immissionsschutz_test_server.py

# Mit uvicorn
uvicorn immissionsschutz_test_server:app --host 0.0.0.0 --port 5001
```

## API Endpoints

### Root & Health

```http
GET / 
# Service-Info

GET /health
# Health check + Datenbank-Status

GET /databases
# Liste aller verfügbaren Datenbanken
```

### Anlagen (BImSchG & WKA)

```http
GET /anlagen/search?db={bimschg|wka}&bst_nr={nr}&anl_nr={nr}&ort={ort}
# Anlagen suchen

GET /anlagen/{db}/{bst_nr}/{anl_nr}
# Einzelne Anlage abrufen
```

**Beispiel**:
```bash
curl "http://localhost:5001/anlagen/search?db=bimschg&ort=Gransee&limit=10"
```

### Genehmigungsverfahren

```http
GET /verfahren/search?bst_nr={nr}&status={status}&von_datum={date}&bis_datum={date}
# Verfahren suchen

GET /verfahren/{verfahren_id}
# Verfahren mit Bescheiden und Auflagen
```

**Beispiel**:
```bash
# Alle genehmigten Verfahren
curl "http://localhost:5001/verfahren/search?status=genehmigt&limit=20"

# Einzelnes Verfahren mit allen Details
curl "http://localhost:5001/verfahren/V-000001"
```

**Response** (Verfahren-Details):
```json
{
  "verfahren": {
    "verfahren_id": "V-000001",
    "bst_nr": "10650100000",
    "anl_nr": "0001",
    "verfahrensart": "Erstgenehmigung nach § 4 BImSchG",
    "status": "genehmigt",
    "behoerde": "Landesamt für Umwelt Brandenburg"
  },
  "bescheide": [
    {
      "bescheid_id": "B-000001",
      "bescheidtyp": "Genehmigung",
      "auflagen_anzahl": 12
    }
  ],
  "auflagen": [...]
}
```

### Messungen

```http
GET /messungen/search?bst_nr={nr}&messart={art}&ueberschreitung={true|false}
# Messungen suchen
```

**Messarten**:
- `Lärm_Tag` / `Lärm_Nacht` (dB(A))
- `PM10` / `PM2.5` (µg/m³)
- `NOx` / `SO2` / `CO` (mg/m³)
- `Ammoniak` (mg/m³)

**Beispiel**:
```bash
# Alle Lärmüberschreitungen
curl "http://localhost:5001/messungen/search?messart=Lärm&ueberschreitung=true"

# Messungen für bestimmte Anlage
curl "http://localhost:5001/messungen/search?bst_nr=10650200000&anl_nr=4001"
```

### Überwachung

```http
GET /ueberwachung/search?bst_nr={nr}&status={status}
# Überwachungen suchen
```

**Status-Werte**:
- `geplant` - Noch nicht durchgeführt
- `durchgeführt` - Abgeschlossen
- `verschoben` - Terminverschiebung
- `abgesagt` - Abgesagt

**Beispiel**:
```bash
# Geplante Inspektionen
curl "http://localhost:5001/ueberwachung/search?status=geplant"
```

### Mängel

```http
GET /maengel/search?status={status}&schweregrad={grad}
# Mängel suchen
```

**Schweregrade**:
- `gering` - Kleinere Mängel
- `mittel` - Mittelschwere Mängel
- `schwer` - Schwerwiegende Mängel
- `kritisch` - Kritische Verstöße

**Beispiel**:
```bash
# Offene kritische Mängel
curl "http://localhost:5001/maengel/search?status=offen&schweregrad=kritisch"
```

### Cross-Database Query (WICHTIG für Agenten!)

```http
GET /anlage-complete/{bst_nr}/{anl_nr}?include_messungen={true|false}&include_verfahren={true|false}
# Vollständige Anlagen-Daten über alle Datenbanken hinweg
```

**Beispiel**:
```bash
curl "http://localhost:5001/anlage-complete/10650200000/4001?include_messungen=true&include_verfahren=true"
```

**Response**:
```json
{
  "anlage": {
    "bst_nr": "10650200000",
    "bst_name": "WENTOWSEE Agrar- und Tierzucht GmbH",
    "anl_nr": "4001",
    "anl_bez": "Sauenanlage",
    "ort": "Gransee",
    "ostwert": 379448.0,
    "nordwert": 5877545.0
  },
  "verfahren": [...],
  "bescheide": [...],
  "messungen": [...],
  "ueberwachungen": [...],
  "maengel": [...],
  "statistik": {
    "verfahren_count": 2,
    "messungen_count": 45,
    "messungen_ueberschreitungen": 3,
    "maengel_count": 2,
    "maengel_offen": 1
  }
}
```

### Statistik

```http
GET /statistik/overview
# Gesamtstatistik
```

**Response**:
```json
{
  "timestamp": "2025-10-18T12:00:00",
  "statistics": {
    "verfahren": {
      "total": 800,
      "genehmigt": 412,
      "in_bearbeitung": 150
    },
    "messungen": {
      "total": 3000,
      "ueberschreitungen": 450
    },
    "ueberwachung": {
      "total": 1200,
      "geplant": 250,
      "mit_maengeln": 180
    },
    "maengel": {
      "total": 463,
      "offen": 120,
      "kritisch": 15
    }
  }
}
```

## Test-Szenarien für Agenten

### Szenario 1: Compliance-Prüfung

**Aufgabe**: Prüfe ob eine Anlage alle Auflagen erfüllt

```python
# 1. Anlage abrufen
anlage = get("/anlage-complete/10650200000/4001")

# 2. Prüfe Bescheide
for bescheid in anlage['bescheide']:
    # 3. Prüfe Auflagen
    for auflage in bescheid['auflagen']:
        if auflage['status'] == 'überfällig':
            # WARNUNG: Auflage nicht erfüllt!
            
# 4. Prüfe Messungen auf Überschreitungen
ueberschreitungen = [m for m in anlage['messungen'] if m['ueberschreitung']]

# 5. Prüfe offene Mängel
offene_maengel = [m for m in anlage['maengel'] if m['status'] == 'offen']
```

**Agent-Prompt**:
```
"Prüfe die Compliance-Status der Anlage 10650200000/4001. 
Berücksichtige:
- Überfällige Auflagen
- Grenzwertüberschreitungen in Messungen
- Offene Mängel mit hohem Schweregrad"
```

### Szenario 2: Emissionsanalyse

**Aufgabe**: Analysiere Emissionstrends einer Anlage

```python
# 1. Messungen abrufen (zeitlich gefiltert)
messungen = get("/messungen/search", params={
    "bst_nr": "10650200000",
    "anl_nr": "4001",
    "messart": "PM10",
    "von_datum": "2023-01-01",
    "bis_datum": "2025-12-31"
})

# 2. Trend analysieren
for messung in messungen:
    if messung['ueberschreitung']:
        # Grenzwertüberschreitung!
        
# 3. Mit Grenzwert vergleichen
durchschnitt = mean([m['messwert'] for m in messungen])
```

**Agent-Prompt**:
```
"Analysiere die PM10-Emissionen der Anlage 10650200000/4001 über die letzten 2 Jahre.
Identifiziere Trends und Grenzwertüberschreitungen."
```

### Szenario 3: Verfahrens-Tracking

**Aufgabe**: Überwache Status aller laufenden Verfahren

```python
# 1. Laufende Verfahren
verfahren = get("/verfahren/search", params={"status": "in_bearbeitung"})

# 2. Überfällige Verfahren identifizieren
from datetime import datetime, timedelta
heute = datetime.now()

for v in verfahren:
    antrag_datum = datetime.fromisoformat(v['antragsdatum'])
    dauer = (heute - antrag_datum).days
    
    if dauer > 365:  # Länger als 1 Jahr
        # WARNUNG: Überlange Bearbeitungszeit!
```

**Agent-Prompt**:
```
"Identifiziere alle Genehmigungsverfahren, die seit mehr als einem Jahr in Bearbeitung sind.
Liste Aktenzeichen und Behörden."
```

### Szenario 4: Überwachungsplanung

**Aufgabe**: Erstelle Überwachungsplan basierend auf Risikobewertung

```python
# 1. Anlagen mit Mängeln
anlagen_mit_maengeln = get("/maengel/search", params={
    "status": "offen",
    "schweregrad": "schwer"
})

# 2. Für jede Anlage: Letzte Überwachung prüfen
for mangel in anlagen_mit_maengeln:
    ueberwachungen = get("/ueberwachung/search", params={
        "bst_nr": mangel['bst_nr'],
        "anl_nr": mangel['anl_nr']
    })
    
    letzte_ueberwachung = max(ueberwachungen, key=lambda u: u['durchgefuehrt_datum'])
    
    # Wenn länger als 6 Monate her: Priorität hoch!
```

**Agent-Prompt**:
```
"Erstelle einen Überwachungsplan für die nächsten 3 Monate.
Priorisiere Anlagen mit:
1. Offenen schweren Mängeln
2. Langer Zeit seit letzter Überwachung
3. Häufigen Grenzwertüberschreitungen"
```

### Szenario 5: Multi-Anlage Vergleich

**Aufgabe**: Vergleiche Performance mehrerer Anlagen

```python
# 1. Anlagen in Region
anlagen = get("/anlagen/search", params={"db": "bimschg", "ort": "Gransee"})

# 2. Für jede Anlage: Statistik
for anlage in anlagen['results']:
    complete = get(f"/anlage-complete/{anlage['bst_nr']}/{anlage['anl_nr']}")
    
    # Vergleiche:
    # - Anzahl Grenzwertüberschreitungen
    # - Offene Mängel
    # - Compliance-Rate
```

**Agent-Prompt**:
```
"Vergleiche alle Anlagen in Gransee hinsichtlich Compliance und Emissionen.
Identifiziere Best-Practice und Problemfälle."
```

## Datenmodell - Relationen

```
┌──────────────┐
│   BImSchG    │◄────┐
│     WKA      │     │
└──────────────┘     │
                     │ bst_nr, anl_nr
                     │
    ┌────────────────┼────────────────┬───────────────┐
    │                │                │               │
    ▼                ▼                ▼               ▼
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│Verfahren │   │Überwachg.│   │ Messungen│   │  Mängel  │
└────┬─────┘   └──────────┘   └──────────┘   └──────────┘
     │
     │ verfahren_id
     ▼
┌──────────┐
│Bescheide │
└────┬─────┘
     │
     │ bescheid_id
     ▼
┌──────────┐
│ Auflagen │
└──────────┘
```

## Performance-Hinweise

### Pagination
- Default Limits: 50-200 Datensätze
- Maximum Limits: 500-2000 Datensätze
- Verwende `limit` Parameter um Performance zu optimieren

### Caching
- Schema-Informationen werden gecached
- Connection-Pooling aktiv
- Statistiken: Cache-TTL 5 Minuten

### Best Practices

1. **Spezifische Queries**: Nutze Filter statt alle Daten abzurufen
2. **Cross-DB Queries sparsam**: `/anlage-complete` ist teuer
3. **Zeitfilter**: Nutze `von_datum`/`bis_datum` bei Messungen
4. **Pagination**: Bei großen Resultsets immer `limit` setzen

## Fehlerbehandlung

### HTTP Status Codes

- `200 OK` - Erfolg
- `400 Bad Request` - Ungültige Parameter
- `404 Not Found` - Ressource nicht gefunden
- `500 Internal Server Error` - Server-Fehler

### Beispiel-Fehler

```json
{
  "detail": "Database 'xyz' not found"
}
```

## Entwicklung

### Datenbank neu generieren

```bash
# Lösche alte Datenbank
rm data/test_databases/immissionsschutz_test.sqlite

# Generiere neu
python scripts/create_immissionsschutz_test_db.py
```

### Server im Debug-Modus

```python
# In immissionsschutz_test_server.py:
uvicorn.run(..., reload=True, log_level="debug")
```

### Schema anpassen

1. Editiere `scripts/create_immissionsschutz_test_db.py`
2. Passe `SCHEMAS` Dictionary an
3. Passe Generator-Klassen an
4. Regeneriere Datenbank

## Integration mit VERITAS

### Seperater Port
- VERITAS Backend: Port 5000
- Test-Server: Port 5001
- Kein Konflikt, beide parallel nutzbar

### Agent-Integration

```python
# In VERITAS Agent:
import requests

class ImmissionsschutzAgent:
    TEST_SERVER = "http://localhost:5001"
    
    def query_verfahren(self, bst_nr, anl_nr):
        response = requests.get(
            f"{self.TEST_SERVER}/verfahren/search",
            params={"bst_nr": bst_nr, "anl_nr": anl_nr}
        )
        return response.json()
    
    def check_compliance(self, bst_nr, anl_nr):
        anlage = requests.get(
            f"{self.TEST_SERVER}/anlage-complete/{bst_nr}/{anl_nr}"
        ).json()
        
        # Analyse...
        return compliance_report
```

## Monitoring

### Health-Check

```bash
# Regelmäßig prüfen
curl http://localhost:5001/health

# Erwartete Response:
{
  "status": "healthy",
  "databases": {
    "bimschg": "ok",
    "wka": "ok",
    "immissionsschutz": "ok"
  }
}
```

### Logs

```bash
# Server-Logs (wenn vorhanden)
tail -f data/test_databases/immissionsschutz_server.log
```

## Troubleshooting

### Server startet nicht

```powershell
# Prüfe ob Port belegt
Get-NetTCPConnection -LocalPort 5001

# Prüfe Python-Prozesse
Get-Process python

# Starte neu
.\scripts\manage_test_server.ps1 -Action restart
```

### Datenbank-Fehler

```powershell
# Prüfe Datei-Existenz
Test-Path data/test_databases/immissionsschutz_test.sqlite

# Prüfe Dateigröße
(Get-Item data/test_databases/immissionsschutz_test.sqlite).Length / 1MB
```

### Langsame Queries

1. Reduziere `limit` Parameter
2. Nutze spezifische Filter
3. Vermeide `/anlage-complete` für Listen
4. Prüfe Datenbank-Indizes

## Weiterentwicklung

### Geplante Features

- [ ] WebSocket für Echtzeit-Updates
- [ ] Export-Funktionen (CSV, Excel)
- [ ] Batch-Operations für Agents
- [ ] Erweiterte Geo-Queries (GIS-Integration)
- [ ] Audit-Log für alle Zugriffe
- [ ] Rate-Limiting pro Agent

### Erweiterungsmöglichkeiten

1. **Zusätzliche Datenbanken**:
   - Betreiber-Stammdaten
   - Dokumente-Verwaltung
   - Zeitreihen-Analysen

2. **Erweiterte Queries**:
   - Aggregationen
   - Komplexe Joins
   - Stored Procedures

3. **Machine Learning**:
   - Vorhersage von Grenzwertüberschreitungen
   - Anomalie-Erkennung
   - Risiko-Scoring

## Support & Kontakt

- **Dokumentation**: http://localhost:5001/docs
- **Health-Check**: http://localhost:5001/health
- **Statistik**: http://localhost:5001/statistik/overview

---

**Version**: 1.0.0  
**Erstellt**: 18. Oktober 2025  
**Status**: ✅ Produktiv
