# IMMI-Karte - Benutzerhandbuch

**Version:** 1.0  
**Datum:** 10. Oktober 2025  
**Integration:** VERITAS App + tkintermapview

---

## 📋 Übersicht

Die **IMMI-Karte** (Immissionsschutz-Karte) visualisiert Geodaten von:
- **🏭 BImSchG-Anlagen:** 4,062 Umweltgenehmigungen nach Bundesimmissionsschutzgesetz
- **🌬️ Windkraftanlagen (WKA):** 5,457 Windenergieanlagen

**Koordinatensystem:** ETRS89 UTM Zone 33N → WGS84 (automatische Transformation)  
**Abdeckung:** Brandenburg (51.37°-53.52°N, 12.01°-14.73°E)  
**Performance:** Native Tkinter Canvas (kein Browser-Widget)

---

## 🚀 Zugriff auf die Karte

### Option 1: Über VERITAS App (Empfohlen)

1. **VERITAS App starten:**
   ```bash
   python frontend/veritas_app.py
   ```

2. **Hamburger-Menü öffnen** (☰-Button oben links)

3. **"🗺️ IMMI-Karte öffnen" klicken**

4. **Neues Fenster öffnet sich** mit interaktiver Karte

### Option 2: Standalone-Modus

```bash
cd frontend/ui
python veritas_ui_map_widget.py
```

---

## 🎛️ Bedienelemente

### Sidebar (Links)

#### 🗂️ Datenquellen
- **☑️ BImSchG-Anlagen** - Toggle für Umweltgenehmigungen
- **☑️ Windkraftanlagen** - Toggle für WKA-Marker
- **☑️ Marker-Clustering** - Gruppierung bei niedriger Zoom-Stufe

#### 📊 Marker-Limit
- **Slider:** 100 - 5000 Marker
- **Empfohlen:** 500-1000 für beste Performance
- **Änderung:** Automatisches Neu-Laden beim Anpassen

#### 🔘 Aktionen
- **🔄 Neu laden** - Marker von IMMI API neu laden
- **📍 Brandenburg zentrieren** - Karte zurücksetzen (52.45°N, 13.37°E, Zoom 8)
- **🔍 Suchen...** - Volltext-Suche nach Anlagen

#### 🎨 Legende BImSchG
- **🔴 Feuerung** - Verbrennungsanlagen (Kraftwerke, Heizwerke)
- **🟢 Tierhaltung** - Landwirtschaftliche Anlagen
- **🟠 Chemie** - Chemische Produktionsanlagen
- **🟤 Abfall** - Abfallbehandlung, Recycling
- **🔵 Lagerung** - Zeitweilige Lagerung (Gefahrstoffe)
- **⚫ Sonstige** - Nicht kategorisiert

#### 🎨 Legende WKA
- **🟢 In Betrieb** - Aktive Windkraftanlagen
- **🟡 Vor Inbetriebnahme** - Geplante WKA
- **⚫ Im Genehmigungsverfahren** - Noch nicht genehmigt

---

## 🗺️ Karten-Interaktion

### Zoom & Navigation
- **Mausrad** - Zoom In/Out
- **Linke Maustaste halten + Ziehen** - Karte verschieben (Pan)
- **Doppelklick** - Zoom auf Position
- **Rechtsklick** - Koordinaten anzeigen (Statusbar)

### Marker-Klick
- **Linksklick auf Marker** - Info-Dialog öffnen
- **Info-Dialog Inhalt:**
  - BImSchG: Name, Kategorie, Betreiber, 4. BImSchV-Nr., Genehmigung
  - WKA: Anlage, Leistung, Nabenhöhe, Rotordurchmesser, Status
  - Koordinaten: Lat/Lon (WGS84) + UTM (ETRS89)

### Cluster-Marker
- **Lila Marker mit Anzahl** (z.B. "📍 15 Anlagen")
- **Klick öffnet Liste** aller Anlagen an diesem Standort
- **Doppelklick auf Liste** öffnet Detail-Dialog
- **Automatisches Clustering** bei Zoom < 10

---

## 🔍 Suchfunktion

### Suche öffnen
1. **Klick auf "🔍 Suchen..." Button**
2. **Oder:** Sidebar → Suchen-Feld

### Such-Query
- **Orte:** "Schwedt", "Potsdam", "Cottbus"
- **Betreiber:** "50Hertz", "Vattenfall", "LEAG"
- **Anlagen:** "PCK Raffinerie", "Kraftwerk Jänschwalde"
- **Teilwort-Suche:** "Wind", "Bio", "Chemie"

### Ergebnis-Handling
- **Liste mit Treffern** (max. 50)
- **Format:** `[Typ] Name (Ort/Betreiber)`
- **Doppelklick** → Karte springt zu Position + Zoom auf Marker
- **Automatischer Zoom:** Level 13 (Detail-Ansicht)

**Beispiel:**
```
🔍 Suche: "Schwedt"

Ergebnisse (5):
1. [BImSchG] 50Hertz Transmission (Schwedt/Oder)
2. [BImSchG] MC Schwedt im ADAC (Schwedt/Oder)
3. [BImSchG] MILGETA Agrargesellschaft (Schwedt/Oder)
4. [BImSchG] PCK Raffinerie (Schwedt/Oder)
5. [WKA] Windpark Schwedt-West (ENERTRAG)
```

---

## 📊 Statusbar (Unten)

### Links: Status-Meldungen
- **"Bereit | 0 Marker geladen"** - Idle
- **"Lade Marker von IMMI API..."** - Loading
- **"148 Marker angezeigt | 1000 gesamt"** - Erfolgreich
- **"Fehler: Connection refused"** - API nicht erreichbar

### Rechts: Koordinaten
- **"Position: --"** - Keine Koordinaten
- **"Position: 52.45°N, 13.37°E"** - Nach Rechtsklick auf Karte

---

## 🎨 Marker-Kategorisierung

### BImSchG-Kategorien (Automatische Erkennung)

| 4. BImSchV | Kategorie | Farbe | Beispiele |
|-----------|-----------|-------|-----------|
| 1.x | **Feuerung** | 🔴 Rot | Kraftwerke, Heizwerke, Verbrennungsmotoren |
| 7.x | **Tierhaltung** | 🟢 Grün | Schweinezucht, Geflügelhaltung, Biogasanlagen |
| 4.x, 9.x | **Chemie** | 🟠 Orange | Chemische Fabriken, Raffinerien |
| 8.11.x | **Abfall** | 🟤 Braun | Müllverbrennungsanlagen, Recycling |
| 8.12.x | **Lagerung** | 🔵 Blau | Gefahrstofflager, Tanklager |
| Sonstige | **Sonstige** | ⚫ Grau | Nicht kategorisiert |

### WKA-Status (Aus Datenbank)

| Status | Farbe | Bedeutung |
|--------|-------|-----------|
| **in Betrieb** | 🟢 Grün | Aktive Stromerzeugung |
| **vor Inbetriebnahme** | 🟡 Gelb | Genehmigt, noch nicht aktiv |
| **im Genehmigungsverfahren** | ⚫ Grau | Antrag gestellt |

---

## ⚡ Performance-Optimierung

### Marker-Clustering

**Warum?**
- 9,160 Marker gleichzeitig → Langsames Rendering
- Clustering gruppiert nahe Marker

**Wie funktioniert's?**
- **Grid-basiert:** 0.05° Grid (~5km)
- **Automatisch bei Zoom < 10**
- **Cluster-Marker:** Lila mit Anzahl
- **Auflösung:** Zoom > 10 zeigt Einzelmarker

**Beispiel:**
```
Zoom 7 (Brandenburg-Übersicht):
  → 150 Cluster-Marker (10-50 Anlagen/Cluster)

Zoom 13 (Stadt-Detail):
  → 500 Einzelmarker (1 Anlage/Marker)
```

### Marker-Limit

**Standard:** 500 Marker  
**Maximum:** 5000 Marker  
**Empfehlung:**
- **Übersicht (Zoom 7-9):** 500 Marker
- **Detail (Zoom 10-13):** 1000 Marker
- **High-End PC:** 2000+ Marker

**Anpassung:**
Sidebar → Marker-Limit Slider → Automatisches Neu-Laden

### Viewport-basiertes Laden (Geplant)

**Aktuell:** Alle Marker werden geladen  
**Geplant:** Nur sichtbare Marker (bounds-Filter)

**Vorteile:**
- Schnelleres Initial-Laden
- Dynamisches Nachladen beim Panning
- Unbegrenzte Marker-Anzahl möglich

---

## 🔧 Technische Details

### Architektur

```
┌─────────────────────────────────────────┐
│       VERITAS App (veritas_app.py)      │
│              (Tkinter Main)             │
└─────────────────┬───────────────────────┘
                  │
                  │ open_immi_map()
                  │
                  ▼
┌─────────────────────────────────────────┐
│   IMMIMapWidget (veritas_ui_map_widget) │
│         (Tkinter Toplevel Window)       │
├─────────────────────────────────────────┤
│  • Sidebar (Filter, Controls)          │
│  • TkinterMapView (Native Canvas)      │
│    └─ OpenStreetMap Tiles              │
│  • Statusbar                            │
└─────────────────┬───────────────────────┘
                  │
                  │ HTTP GET Requests
                  │
                  ▼
┌─────────────────────────────────────────┐
│    IMMI API (veritas_api_backend.py)   │
│           (FastAPI @ :5000)             │
├─────────────────────────────────────────┤
│  • /api/immi/markers/bimschg            │
│  • /api/immi/markers/wka                │
│  • /api/immi/search                     │
│  • /api/immi/filters                    │
│  • /api/immi/heatmap/bimschg            │
│  • /api/immi/statistics/region          │
└─────────────────┬───────────────────────┘
                  │
                  │ SQLite Queries
                  │
                  ▼
┌─────────────────────────────────────────┐
│        SQLite Databases                 │
├─────────────────────────────────────────┤
│  • BImSchG.sqlite (4,062 Anlagen)       │
│  • wka.sqlite (5,457 WKA)               │
│                                         │
│  Koordinaten: ETRS89 UTM Zone 33N       │
└─────────────────────────────────────────┘
```

### Dependencies

**Python Libraries:**
- `tkintermapview==1.29` - Native Tkinter Map (kein Browser!)
- `Pillow==11.3.0` - Image Processing (für Custom Icons)
- `requests==2.32.5` - HTTP Client (IMMI API)
- `pyproj` - Koordinaten-Transformation (ETRS89 → WGS84)

**Installation:**
```bash
pip install tkintermapview pillow requests pyproj
```

### Koordinaten-Transformation

**Problem:** Datenbank speichert ETRS89 UTM, Karte benötigt WGS84

**Lösung:**
```python
from pyproj import Transformer

transformer = Transformer.from_crs(
    "EPSG:25833",  # ETRS89 UTM Zone 33N
    "EPSG:4326",   # WGS84 (lat/lon)
    always_xy=True
)

lat, lon = transformer.transform(ostwert, nordwert)
```

**Validierung:** 96.2% Erfolgsquote (9,160/9,519 Koordinaten)

**Brandenburg Bounds:**
- **Nord:** 53.52°N (Prignitz)
- **Süd:** 51.37°N (Niederlausitz)
- **Ost:** 14.73°E (Oder)
- **West:** 12.01°E (Elbe)

---

## 🐛 Troubleshooting

### Problem: "IMMI-Karte konnte nicht geladen werden"

**Ursache:** tkintermapview nicht installiert

**Lösung:**
```bash
pip install tkintermapview pillow
```

### Problem: "Keine Marker sichtbar"

**Ursache:** Backend nicht erreichbar

**Checks:**
1. Backend läuft? `python backend/api/veritas_api_backend.py`
2. URL korrekt? `http://localhost:5000`
3. API erreichbar? `curl http://localhost:5000/api/immi/markers/bimschg?limit=3`

**Statusbar:** Zeigt Fehler-Meldung

### Problem: "Karte sehr langsam"

**Ursachen:**
- Zu viele Marker (>2000)
- Clustering deaktiviert
- Langsame Internet-Verbindung (Map-Tiles)

**Lösungen:**
1. **Marker-Limit reduzieren:** Sidebar → Slider auf 500
2. **Clustering aktivieren:** Sidebar → ☑️ Marker-Clustering
3. **Map-Tiles cachen:** tkintermapview cached automatisch nach 1. Laden

### Problem: "Koordinaten außerhalb Brandenburg"

**Ursache:** Ungültige Transformation (3.8% der Daten)

**Erkennung:** API filtert automatisch (nur Brandenburg-Bounds)

**Beispiel:**
```
UTM: 999999m Ost, 999999m Nord
→ Ungültige Koordinaten
→ Marker wird nicht angezeigt
```

### Problem: "Cluster-Marker zeigt zu viele Anlagen"

**Erklärung:** Mehrere Anlagen an exakt gleicher Position

**Beispiel:**
```
📍 11 Anlagen
→ Industriegebiet mit mehreren Betrieben
→ Alle haben gleiche Koordinaten (Grundstück)
```

**Lösung:** Zoom > 10 für Einzelmarker (falls unterscheidbar)

---

## 📊 Statistiken

### Datenbestand (Stand: 10. Oktober 2025)

**BImSchG-Anlagen:**
- **Gesamt:** 4,062 Genehmigungen
- **Mit Koordinaten:** 3,905 (96.1%)
- **Kategorien:** 183 verschiedene 4. BImSchV-Nummern
- **TOP 3:**
  1. Zeitweilige Lagerung (8.12.2V) - 458 Anlagen
  2. Sonstige Behandlung (8.11.2.4V) - 416 Anlagen
  3. Verbrennungsmotoren (1.2.2.2V) - 332 Anlagen

**Windkraftanlagen:**
- **Gesamt:** 5,457 WKA
- **Mit Koordinaten:** 5,255 (96.3%)
- **Status:**
  - In Betrieb: ~4,500 (82%)
  - Vor Inbetriebnahme: ~500 (9%)
  - Im Genehmigungsverfahren: ~450 (8%)
- **Leistung:** 0.06 - 8.0 MW
- **Nabenhöhe:** 30 - 200 m

**Geodaten:**
- **Validierte Koordinaten:** 9,160 (96.2%)
- **Ungültige Koordinaten:** 359 (3.8%)
- **Abdeckung:** Ganz Brandenburg
- **Zentrum:** 52.45°N, 13.37°E (Potsdam-Nähe)

### Performance-Benchmarks

**Hardware:** Standard-PC (Intel i5, 16 GB RAM)

| Aktion | Zeit | Marker |
|--------|------|--------|
| Initial-Laden (BImSchG) | ~200ms | 500 |
| Initial-Laden (WKA) | ~150ms | 500 |
| Map-Rendering | ~300ms | 1000 |
| Clustering (Zoom < 10) | ~50ms | 9160 → 150 |
| Marker-Click | <10ms | 1 |
| Suche "Schwedt" | ~100ms | 5 Ergebnisse |

**Netzwerk:**
- Map-Tiles (OpenStreetMap): 10-50 KB/Tile
- API-Response (500 Marker): ~150 KB
- Heatmap-Data: ~235 KB (3232 Punkte)

---

## 🔮 Geplante Features

### Phase 2: Erweiterte Visualisierung (2-3h)

- [ ] **Heatmap-Layer** für Anlagen-Dichte
  - Matplotlib-Overlay über tkintermapview
  - Toggle in Sidebar
- [ ] **Custom Marker-Icons**
  - SVG-Icons für alle Kategorien (BImSchG + WKA)
  - Größere Icons bei Zoom > 12
- [ ] **Info-Window statt Dialog**
  - Popup direkt über Marker
  - Weniger Klicks für schnelle Info

### Phase 3: Performance-Boost (1-2h)

- [ ] **Viewport-basiertes Laden**
  - IMMI API bounds-Parameter nutzen
  - Nur sichtbare Marker laden
  - Dynamisches Nachladen beim Pan/Zoom
- [ ] **Server-Side Clustering**
  - Backend berechnet Cluster
  - Reduzierte Datenmenge
  - Schnelleres Rendering

### Phase 4: Analyse-Tools (3-4h)

- [ ] **Regions-Statistiken**
  - Overlay mit Anzahl Anlagen pro Kreis
  - Diagramme (Kategorie-Verteilung)
- [ ] **Export-Funktionen**
  - CSV-Export sichtbarer Marker
  - PNG-Screenshot der Karte
  - PDF-Report mit Statistiken

### Phase 5: Mobile & Responsive (2-3h)

- [ ] **Touch-Support**
  - Pinch-to-Zoom
  - Swipe-to-Pan
- [ ] **Responsive Layout**
  - Sidebar ausblendbar
  - Fullscreen-Modus

---

## 📞 Support & Feedback

**Dokumentation:**
- API-Referenz: `docs/IMMI_API_DOCUMENTATION.md`
- Test-Report: `docs/IMMI_API_INTEGRATION_TEST_REPORT.md`
- Implementation Options: `docs/MAP_IMPLEMENTATION_OPTIONS.md`

**Logs:**
- Frontend: Konsolen-Output
- Backend: `data/veritas_auto_server.log`
- Map-Widget: `logger.info(...)` Ausgaben

**Bekannte Einschränkungen:**
- Keine Heatmap-Unterstützung (noch)
- Kein Auto-Clustering (manuell implementiert)
- Kein Viewport-Loading (lädt alle Marker)
- Performance-Limit bei >2000 Markern

**Feature-Requests:**
Bitte in `TODO_MAP_INTEGRATION.md` dokumentieren

---

**Version:** 1.0  
**Erstellt:** 10. Oktober 2025  
**Autor:** VERITAS Agent System  
**Lizenz:** Projektintern
