# Technische Implementierungsoptionen: Interaktive Karte in Tkinter

**Datum:** 10. Oktober 2025
**Kontext:** IMMI API Map-Visualisierung ohne Browser-Komponenten

---

## 🎯 Anforderung

Interaktive Kartendarstellung von 9,160 Geodaten-Punkten (BImSchG + WKA) direkt in Tkinter Canvas ohne HTML/JavaScript-Abhängigkeiten.

---

## 🛠️ Technische Optionen

### Option 1: **Tkintermapview** (EMPFOHLUNG ✅)

**Library:** `tkintermapview` (Pure Python, aktiv entwickelt)

```bash
pip install tkintermapview
```

**Vorteile:**
- ✅ **Native Tkinter-Integration** (kein Browser-Widget)
- ✅ **OpenStreetMap Tiles** automatisch geladen
- ✅ **Marker-Support** mit Custom Icons
- ✅ **Polygone & Polylinien** für Regionen
- ✅ **Click-Events** auf Marker
- ✅ **Zoom & Pan** mit Maus/Touchpad
- ✅ **Offline-Caching** von Map-Tiles
- ✅ **Leichtgewichtig** (~50 KB)
- ✅ **Aktiv maintained** (letztes Update: 2024)

**Nachteile:**
- ⚠️ Performance bei >1000 Markern (wird langsam)
- ⚠️ Kein Marker-Clustering eingebaut
- ⚠️ Keine Heatmap-Unterstützung

**Code-Beispiel:**

```python
import tkinter as tk
from tkintermapview import TkinterMapView

class IMMIMapWidget(tk.Frame):
    def __init__(self, parent, backend_url="http://localhost:5000"):
        super().__init__(parent)
        self.backend_url = backend_url

        # Map Widget erstellen
        self.map_widget = TkinterMapView(self, width=800, height=600)
        self.map_widget.pack(fill="both", expand=True)

        # Brandenburg-Zentrum setzen
        self.map_widget.set_position(52.45, 13.37)  # Lat, Lon
        self.map_widget.set_zoom(8)

        # Marker laden
        self.load_markers()

    def load_markers(self):
        """Lädt BImSchG + WKA Marker von IMMI API"""
        import requests

        # BImSchG-Anlagen laden
        response = requests.get(f"{self.backend_url}/api/immi/markers/bimschg?limit=1000")
        if response.status_code == 200:
            markers = response.json()
            for marker in markers:
                self.add_marker(
                    marker['lat'],
                    marker['lon'],
                    text=marker['name'],
                    marker_color='red' if 'Feuerung' in marker['category'] else 'blue'
                )

    def add_marker(self, lat, lon, text, marker_color='red'):
        """Fügt Marker zur Karte hinzu"""
        marker = self.map_widget.set_marker(
            lat, lon,
            text=text,
            marker_color_circle=marker_color,
            marker_color_outside=marker_color
        )
        marker.command = lambda: self.on_marker_click(text)
        return marker

    def on_marker_click(self, name):
        """Marker wurde geklickt"""
        print(f"Marker clicked: {name}")
        # Hier: Info-Dialog öffnen
```

**Performance-Optimierung:**

```python
def load_markers_smart(self):
    """Lädt nur sichtbare Marker (Viewport-basiert)"""
    # Aktuelle Map-Bounds ermitteln
    bounds = self.map_widget.get_bounds()
    # bounds = (north, south, east, west)

    # API-Request mit Bounds-Filter
    url = f"{self.backend_url}/api/immi/markers/bimschg"
    params = {
        'bounds': f"{bounds[1]},{bounds[3]},{bounds[0]},{bounds[2]}",
        'limit': 1000
    }
    response = requests.get(url, params=params)

    # Marker hinzufügen
    for marker in response.json():
        self.add_marker(marker['lat'], marker['lon'], marker['name'])
```

**Clustering-Lösung (manuell):**

```python
def cluster_markers(self, markers, zoom_level):
    """Manuelle Marker-Gruppierung bei niedriger Zoom-Stufe"""
    if zoom_level < 10:
        # Grid-basiertes Clustering
        grid_size = 0.1  # ~10km
        clusters = {}

        for marker in markers:
            grid_key = (
                round(marker['lat'] / grid_size) * grid_size,
                round(marker['lon'] / grid_size) * grid_size
            )
            if grid_key not in clusters:
                clusters[grid_key] = []
            clusters[grid_key].append(marker)

        # Cluster-Marker erstellen
        for (lat, lon), group in clusters.items():
            count = len(group)
            if count > 1:
                self.add_cluster_marker(lat, lon, count)
            else:
                self.add_marker(lat, lon, group[0]['name'])
    else:
        # Einzelne Marker bei hoher Zoom-Stufe
        for marker in markers:
            self.add_marker(marker['lat'], marker['lon'], marker['name'])

def add_cluster_marker(self, lat, lon, count):
    """Fügt Cluster-Marker hinzu (Anzahl anzeigen)"""
    marker = self.map_widget.set_marker(
        lat, lon,
        text=f"🗺️ {count} Anlagen",
        marker_color_circle="purple",
        marker_color_outside="purple"
    )
    return marker
```

---

### Option 2: **Matplotlib + Basemap/Cartopy** (Statisch)

**Libraries:** `matplotlib`, `cartopy`

**Vorteile:**
- ✅ **Wissenschaftliche Karten** (GIS-Features)
- ✅ **Heatmaps** direkt unterstützt
- ✅ **Viele Projektionen** (UTM, Lambert, etc.)
- ✅ **Offline-fähig**

**Nachteile:**
- ❌ **Nicht interaktiv** (keine Zoom/Pan wie Google Maps)
- ❌ **Langsames Rendering** bei vielen Punkten
- ❌ **Keine Map-Tiles** (muss manuell gezeichnet werden)

**Code-Beispiel:**

```python
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import cartopy.crs as ccrs
import cartopy.feature as cfeature

class StaticMapWidget(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        # Matplotlib Figure erstellen
        self.fig, self.ax = plt.subplots(
            subplot_kw={'projection': ccrs.PlateCarree()},
            figsize=(10, 8)
        )

        # Karte zeichnen
        self.ax.set_extent([11.5, 15.0, 51.0, 53.5], crs=ccrs.PlateCarree())
        self.ax.add_feature(cfeature.COASTLINE)
        self.ax.add_feature(cfeature.BORDERS, linestyle=':')
        self.ax.add_feature(cfeature.LAND, color='lightgray')

        # Canvas in Tkinter einbetten
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def add_markers(self, lats, lons, colors):
        """Fügt Marker hinzu"""
        self.ax.scatter(lons, lats, c=colors, s=50, alpha=0.6,
                       transform=ccrs.PlateCarree())
        self.canvas.draw()
```

**Bewertung:** ❌ Nicht empfohlen (zu statisch, keine echte Interaktivität)

---

### Option 3: **Folium + WebView** (Hybrid)

**Libraries:** `folium`, `tkinterweb`

**Vorteile:**
- ✅ **Leaflet.js Power** (Clustering, Heatmap)
- ✅ **Python-seitige Konfiguration**
- ✅ **Alle Features aus TODO verfügbar**

**Nachteile:**
- ⚠️ **Abhängigkeit von Browser-Widget**
- ⚠️ **HTML-Kommunikation über Dateien**

**Code-Beispiel:**

```python
import folium
from tkinterweb import HtmlFrame

class FoliumMapWidget(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        # Folium-Karte erstellen
        self.map = folium.Map(
            location=[52.45, 13.37],
            zoom_start=8,
            tiles='OpenStreetMap'
        )

        # Marker hinzufügen
        folium.Marker([52.5, 13.4], popup="Test").add_to(self.map)

        # Als HTML speichern
        self.map.save("temp_map.html")

        # In HtmlFrame laden
        self.html_frame = HtmlFrame(self, horizontal_scrollbar="auto")
        self.html_frame.load_file("temp_map.html")
        self.html_frame.pack(fill="both", expand=True)
```

**Bewertung:** ⚠️ Funktioniert, aber nicht "native Canvas"

---

### Option 4: **Custom Canvas Drawing** (Pure Tkinter)

**Vorteile:**
- ✅ **100% Kontrolle**
- ✅ **Keine externen Dependencies**
- ✅ **Schnell** (direktes Canvas-Drawing)

**Nachteile:**
- ❌ **Sehr aufwändig** (Map-Tiles, Projektionen, Zoom selbst implementieren)
- ❌ **Keine Map-Tiles** (nur eigene Grafiken)
- ❌ **Schlechte Kartendarstellung**

**Code-Beispiel:**

```python
class CustomCanvasMap(tk.Canvas):
    def __init__(self, parent, width=800, height=600):
        super().__init__(parent, width=width, height=height, bg='lightblue')

        self.center_lat = 52.45
        self.center_lon = 13.37
        self.zoom = 8

        # Background (vereinfachte Karte)
        self.create_rectangle(0, 0, width, height, fill='lightblue', outline='')

        # Land (Brandenburg - grob)
        self.create_polygon(
            100, 100, 700, 100, 700, 500, 100, 500,
            fill='lightgreen', outline='black'
        )

    def lat_lon_to_pixel(self, lat, lon):
        """Konvertiert Lat/Lon zu Canvas-Koordinaten"""
        # Mercator-Projektion (vereinfacht)
        x = (lon - self.center_lon) * 50 * (2 ** self.zoom) + 400
        y = 300 - (lat - self.center_lat) * 50 * (2 ** self.zoom)
        return x, y

    def add_marker(self, lat, lon, color='red'):
        """Fügt Marker hinzu"""
        x, y = self.lat_lon_to_pixel(lat, lon)
        self.create_oval(x-5, y-5, x+5, y+5, fill=color, outline='black')
```

**Bewertung:** ❌ Viel zu aufwändig für professionelle Kartendarstellung

---

### Option 5: **PyQt + Leaflet WebEngine** (Alternative GUI)

**Libraries:** `PyQt5`, `QtWebEngineWidgets`

**Vorteile:**
- ✅ **Vollständiges Leaflet.js**
- ✅ **Native Integration** (kein separates Fenster)
- ✅ **JavaScript-Python Bridge**

**Nachteile:**
- ❌ **Wechsel von Tkinter zu PyQt** (großer Aufwand)
- ❌ **Schwere Dependencies** (QtWebEngine ~50 MB)

**Bewertung:** ❌ Nicht praktikabel (gesamtes Frontend umschreiben)

---

## 📊 Vergleichstabelle

| Option | Interaktiv | Performance | Map-Tiles | Clustering | Heatmap | Aufwand | Empfehlung |
|--------|-----------|-------------|-----------|-----------|---------|---------|------------|
| **tkintermapview** | ✅ | ⭐⭐⭐ | ✅ | 🔧 Manual | ❌ | LOW | ✅ **BESTE WAHL** |
| Matplotlib/Cartopy | ❌ | ⭐⭐ | ❌ | ❌ | ✅ | MEDIUM | ❌ |
| Folium + WebView | ✅ | ⭐⭐⭐⭐ | ✅ | ✅ | ✅ | LOW | ⚠️ Hybrid |
| Custom Canvas | ✅ | ⭐⭐⭐⭐⭐ | ❌ | 🔧 Manual | 🔧 Manual | VERY HIGH | ❌ |
| PyQt + Leaflet | ✅ | ⭐⭐⭐⭐ | ✅ | ✅ | ✅ | VERY HIGH | ❌ |

---

## ✅ Empfehlung: **tkintermapview** mit Custom Clustering

### Warum?

1. ✅ **Native Tkinter** - passt perfekt zur bestehenden App
2. ✅ **Einfache Installation** - `pip install tkintermapview`
3. ✅ **OpenStreetMap** - kostenlose, hochwertige Karten
4. ✅ **Zoom/Pan** - wie Google Maps
5. ✅ **Marker-Support** - mit Click-Events
6. ✅ **Offline-Caching** - Tiles werden gespeichert
7. ✅ **Leichtgewichtig** - keine Browser-Engine
8. ✅ **Gut dokumentiert** - aktive Community

### Limitierungen & Lösungen:

**Problem 1: Keine Heatmap**
- **Lösung:** Matplotlib-Overlay für Heatmap-Layer
- Oder: Dichte-Marker (größere Kreise bei vielen Anlagen)

**Problem 2: Kein Auto-Clustering**
- **Lösung:** Manuelles Grid-Clustering (siehe Code oben)
- Bei Zoom < 10: Gruppen von Markern zusammenfassen
- Bei Zoom ≥ 10: Einzelne Marker anzeigen

**Problem 3: Performance bei >1000 Markern**
- **Lösung:** Viewport-basiertes Laden (nur sichtbare Marker)
- IMMI API unterstützt `bounds` Parameter
- Dynamisches Nachladen beim Zoomen/Panning

---

## 🚀 Implementierungsplan

### Phase 1: Basic Map (2h)
```python
# frontend/ui/veritas_ui_map_widget.py
import tkinter as tk
from tkintermapview import TkinterMapView
import requests

class IMMIMapWidget(tk.Frame):
    def __init__(self, parent, backend_url="http://localhost:5000"):
        super().__init__(parent)

        # Map erstellen
        self.map = TkinterMapView(self, width=800, height=600)
        self.map.pack(fill="both", expand=True)
        self.map.set_position(52.45, 13.37)
        self.map.set_zoom(8)

        # Marker laden
        self.load_markers()

    def load_markers(self):
        # Von IMMI API laden
        pass
```

### Phase 2: Marker & Clustering (3h)
- Custom Icons für BImSchG/WKA
- Grid-basiertes Clustering
- Click-Events für Info-Dialogs

### Phase 3: Filter-UI (2h)
- Sidebar mit Filter-Optionen
- API-Integration für Filter-Queries
- Dynamisches Marker-Update

### Phase 4: Optimierung (1h)
- Viewport-basiertes Laden
- Caching von Marker-Daten
- Smooth Zoom-Transitions

**Gesamtaufwand:** 8 Stunden (statt 16h mit Leaflet.js)

---

## 📦 Installation

```bash
# tkintermapview installieren
pip install tkintermapview

# Optional: Pillow für Custom Icons
pip install Pillow
```

**Dependencies:**
- `tkintermapview` (~50 KB)
- `requests` (bereits vorhanden)
- `Pillow` (optional, für Icons)

**Keine Browser-Engine, kein JavaScript, kein HTML!** 🎉

---

## 🎯 Fazit

**Native Tkinter Canvas-Lösung:** ✅ **MÖGLICH & EMPFOHLEN**

Mit `tkintermapview` bekommen Sie:
- ✅ Interaktive Karte (Zoom, Pan, Click)
- ✅ OpenStreetMap Tiles (kostenlos)
- ✅ Native Tkinter-Integration
- ✅ Marker mit Custom Icons
- ✅ Performance (mit Viewport-Loading)
- ✅ Offline-Caching

**Ohne:**
- ❌ Browser-Widget
- ❌ HTML/JavaScript
- ❌ Schwere Dependencies
- ❌ Komplexe Integration

**Zeit bis zur funktionierenden Karte:** ~2 Stunden! ⚡

---

**Nächster Schritt:** `pip install tkintermapview` und los geht's! 🚀
