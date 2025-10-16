#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VERITAS IMMI Map Widget - Native Tkinter Canvas Map Integration
Verwendet tkintermapview für interaktive OpenStreetMap-Darstellung
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
import requests
import threading
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

try:
    from tkintermapview import TkinterMapView
    MAPVIEW_AVAILABLE = True
except ImportError:
    MAPVIEW_AVAILABLE = False

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# Logger
logger = logging.getLogger(__name__)


class MarkerCluster:
    """Grid-basiertes Marker-Clustering für Performance-Optimierung"""
    
    def __init__(self, grid_size: float = 0.05):
        """
        Args:
            grid_size: Grid-Größe in Grad (~5km bei 0.05)
        """
        self.grid_size = grid_size
        self.clusters: Dict[Tuple[float, float], List[Dict]] = {}
    
    def add_marker(self, lat: float, lon: float, data: Dict):
        """Fügt Marker zu Cluster hinzu"""
        grid_key = (
            round(lat / self.grid_size) * self.grid_size,
            round(lon / self.grid_size) * self.grid_size
        )
        if grid_key not in self.clusters:
            self.clusters[grid_key] = []
        self.clusters[grid_key].append(data)
    
    def get_clusters(self, min_zoom: int = 10) -> List[Dict]:
        """
        Gibt Cluster oder Einzelmarker zurück
        
        Returns:
            Liste mit {'lat', 'lon', 'count', 'markers'} oder einzelne Marker
        """
        result = []
        for (lat, lon), markers in self.clusters.items():
            if len(markers) > 1:
                # Cluster
                result.append({
                    'lat': lat,
                    'lon': lon,
                    'count': len(markers),
                    'markers': markers,
                    'is_cluster': True
                })
            else:
                # Einzelner Marker
                marker = markers[0]
                marker['is_cluster'] = False
                result.append(marker)
        return result
    
    def clear(self):
        """Löscht alle Cluster"""
        self.clusters.clear()


class IMMIMapWidget(tk.Frame):
    """
    Interaktive Karte für BImSchG und WKA Geodaten
    Verwendet tkintermapview (native Canvas) statt Browser-Widget
    """
    
    # Marker-Farben nach Kategorie
    BIMSCHG_COLORS = {
        'Feuerung': '#FF4444',        # Rot
        'Tierhaltung': '#44FF44',     # Grün
        'Chemie': '#FF8800',          # Orange
        'Abfall': '#8B4513',          # Braun
        'Lagerung': '#4444FF',        # Blau
        'Sonstige': '#888888'         # Grau
    }
    
    WKA_COLORS = {
        'in Betrieb': '#00CC00',      # Grün
        'vor Inbetriebnahme': '#FFAA00',  # Gelb
        'im Genehmigungsverfahren': '#888888',  # Grau
        'default': '#888888'
    }
    
    def __init__(self, parent, backend_url: str = "http://localhost:5000"):
        """
        Args:
            parent: Tkinter Parent-Widget
            backend_url: IMMI API Backend URL
        """
        super().__init__(parent)
        
        if not MAPVIEW_AVAILABLE:
            self._show_error("tkintermapview nicht installiert!\n\n"
                           "Bitte installieren: pip install tkintermapview")
            return
        
        self.backend_url = backend_url
        self.markers: Dict[str, Any] = {}  # marker_id -> tkintermapview.Marker
        self.current_data: List[Dict] = []
        self.clusterer = MarkerCluster(grid_size=0.05)
        self.clustering_enabled = True
        self.show_bimschg = True
        self.show_wka = True
        
        # UI aufbauen
        self._create_widgets()
        
        # Initial-Daten laden
        self.after(500, self._load_initial_data)
        
        logger.info("✅ IMMIMapWidget initialisiert (tkintermapview)")
    
    def _create_widgets(self):
        """Erstellt UI-Elemente"""
        # Hauptcontainer
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        # Sidebar (Filter + Controls)
        self._create_sidebar()
        
        # Map Container
        self._create_map()
        
        # Statusbar
        self._create_statusbar()
    
    def _create_sidebar(self):
        """Erstellt Filter-Sidebar"""
        sidebar = ttk.Frame(self, width=250)
        sidebar.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        sidebar.grid_propagate(False)
        
        # Header
        header = ttk.Label(
            sidebar,
            text="🗺️ IMMI Karte",
            font=("Segoe UI", 14, "bold")
        )
        header.pack(pady=10)
        
        # Filter-Section
        filter_frame = ttk.LabelFrame(sidebar, text="Datenquellen", padding=10)
        filter_frame.pack(fill="x", padx=10, pady=5)
        
        # BImSchG Toggle
        self.bimschg_var = tk.BooleanVar(value=True)
        bimschg_check = ttk.Checkbutton(
            filter_frame,
            text="🏭 BImSchG-Anlagen",
            variable=self.bimschg_var,
            command=self._on_filter_change
        )
        bimschg_check.pack(anchor="w", pady=2)
        
        # WKA Toggle
        self.wka_var = tk.BooleanVar(value=True)
        wka_check = ttk.Checkbutton(
            filter_frame,
            text="🌬️ Windkraftanlagen",
            variable=self.wka_var,
            command=self._on_filter_change
        )
        wka_check.pack(anchor="w", pady=2)
        
        # Clustering Toggle
        self.cluster_var = tk.BooleanVar(value=True)
        cluster_check = ttk.Checkbutton(
            filter_frame,
            text="📍 Marker-Clustering",
            variable=self.cluster_var,
            command=self._on_clustering_change
        )
        cluster_check.pack(anchor="w", pady=2)
        
        # Limit-Slider
        limit_frame = ttk.LabelFrame(sidebar, text="Marker-Limit", padding=10)
        limit_frame.pack(fill="x", padx=10, pady=5)
        
        self.limit_var = tk.IntVar(value=500)
        limit_slider = ttk.Scale(
            limit_frame,
            from_=100,
            to=5000,
            variable=self.limit_var,
            orient="horizontal",
            command=lambda _: self._on_limit_change()
        )
        limit_slider.pack(fill="x")
        
        self.limit_label = ttk.Label(limit_frame, text="500 Marker")
        self.limit_label.pack()
        
        # Action-Buttons
        action_frame = ttk.Frame(sidebar)
        action_frame.pack(fill="x", padx=10, pady=10)
        
        reload_btn = ttk.Button(
            action_frame,
            text="🔄 Neu laden",
            command=self._reload_markers
        )
        reload_btn.pack(fill="x", pady=2)
        
        center_btn = ttk.Button(
            action_frame,
            text="📍 Brandenburg zentrieren",
            command=self._center_brandenburg
        )
        center_btn.pack(fill="x", pady=2)
        
        search_btn = ttk.Button(
            action_frame,
            text="🔍 Suchen...",
            command=self._show_search_dialog
        )
        search_btn.pack(fill="x", pady=2)
        
        # Legende
        legend_frame = ttk.LabelFrame(sidebar, text="Legende BImSchG", padding=10)
        legend_frame.pack(fill="x", padx=10, pady=5)
        
        for category, color in self.BIMSCHG_COLORS.items():
            item = ttk.Label(
                legend_frame,
                text=f"● {category}",
                foreground=color,
                font=("Segoe UI", 9)
            )
            item.pack(anchor="w", pady=1)
        
        # WKA Legende
        wka_legend = ttk.LabelFrame(sidebar, text="Legende WKA", padding=10)
        wka_legend.pack(fill="x", padx=10, pady=5)
        
        for status, color in self.WKA_COLORS.items():
            if status != 'default':
                item = ttk.Label(
                    wka_legend,
                    text=f"● {status}",
                    foreground=color,
                    font=("Segoe UI", 9)
                )
                item.pack(anchor="w", pady=1)
    
    def _create_map(self):
        """Erstellt Map-Widget"""
        map_container = ttk.Frame(self)
        map_container.grid(row=0, column=1, sticky="nsew")
        
        # tkintermapview Map erstellen
        self.map_widget = TkinterMapView(
            map_container,
            width=800,
            height=600,
            corner_radius=0
        )
        self.map_widget.pack(fill="both", expand=True)
        
        # Brandenburg-Zentrum setzen
        self.map_widget.set_position(52.45, 13.37)  # Lat, Lon
        self.map_widget.set_zoom(8)
        
        # Event-Handler
        self.map_widget.add_right_click_menu_command(
            label="🔍 Details anzeigen",
            command=self._on_map_right_click,
            pass_coords=True
        )
        
        logger.info("✅ Map-Widget erstellt: Brandenburg 52.45°N, 13.37°E, Zoom 8")
    
    def _create_statusbar(self):
        """Erstellt Statusbar"""
        statusbar = ttk.Frame(self, relief="sunken")
        statusbar.grid(row=1, column=0, columnspan=2, sticky="ew")
        
        self.status_label = ttk.Label(
            statusbar,
            text="Bereit | 0 Marker geladen",
            font=("Segoe UI", 9)
        )
        self.status_label.pack(side="left", padx=5)
        
        self.coord_label = ttk.Label(
            statusbar,
            text="Position: --",
            font=("Segoe UI", 9)
        )
        self.coord_label.pack(side="right", padx=5)
    
    def _load_initial_data(self):
        """Lädt initiale Marker-Daten"""
        self._update_status("Lade Marker von IMMI API...")
        threading.Thread(target=self._load_markers_thread, daemon=True).start()
    
    def _load_markers_thread(self):
        """Thread-sicheres Marker-Laden"""
        try:
            markers = []
            
            # BImSchG laden
            if self.show_bimschg:
                url = f"{self.backend_url}/api/immi/markers/bimschg"
                params = {'limit': self.limit_var.get()}
                response = requests.get(url, params=params, timeout=10)
                
                if response.status_code == 200:
                    bimschg_data = response.json()
                    markers.extend(bimschg_data)
                    logger.info(f"✅ {len(bimschg_data)} BImSchG-Marker geladen")
            
            # WKA laden
            if self.show_wka:
                url = f"{self.backend_url}/api/immi/markers/wka"
                params = {'limit': self.limit_var.get()}
                response = requests.get(url, params=params, timeout=10)
                
                if response.status_code == 200:
                    wka_data = response.json()
                    markers.extend(wka_data)
                    logger.info(f"✅ {len(wka_data)} WKA-Marker geladen")
            
            # Marker anzeigen (in Main-Thread)
            self.after(0, lambda: self._display_markers(markers))
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Fehler beim Laden der Marker: {e}")
            self.after(0, lambda: self._update_status(f"Fehler: {e}"))
        except Exception as e:
            logger.error(f"❌ Unerwarteter Fehler: {e}")
            self.after(0, lambda: self._update_status(f"Fehler: {e}"))
    
    def _display_markers(self, markers: List[Dict]):
        """Zeigt Marker auf der Karte an"""
        # Alte Marker löschen
        self._clear_markers()
        
        if not markers:
            self._update_status("Keine Marker gefunden")
            return
        
        self.current_data = markers
        
        # Clustering anwenden wenn aktiviert
        if self.clustering_enabled and self.map_widget.zoom < 10:
            markers_to_show = self._apply_clustering(markers)
        else:
            markers_to_show = markers
        
        # Marker hinzufügen
        for i, marker_data in enumerate(markers_to_show):
            if i >= self.limit_var.get():
                break
            
            try:
                self._add_marker(marker_data)
            except Exception as e:
                logger.warning(f"⚠️ Fehler beim Hinzufügen von Marker: {e}")
        
        count = len(self.markers)
        self._update_status(f"{count} Marker angezeigt | {len(markers)} gesamt")
        logger.info(f"✅ {count} Marker auf Karte angezeigt")
    
    def _apply_clustering(self, markers: List[Dict]) -> List[Dict]:
        """Wendet Grid-Clustering an"""
        self.clusterer.clear()
        
        for marker in markers:
            self.clusterer.add_marker(
                marker['lat'],
                marker['lon'],
                marker
            )
        
        return self.clusterer.get_clusters()
    
    def _add_marker(self, marker_data: Dict):
        """Fügt einzelnen Marker zur Karte hinzu"""
        lat = marker_data.get('lat')
        lon = marker_data.get('lon')
        
        if lat is None or lon is None:
            return
        
        # Marker-Farbe bestimmen
        if marker_data.get('is_cluster'):
            color = "purple"
            text = f"📍 {marker_data['count']} Anlagen"
        elif marker_data.get('type') == 'bimschg':
            category = marker_data.get('category', 'Sonstige')
            # Kategorie extrahieren (vor Klammer)
            cat_short = category.split('(')[0].strip()
            color = self._get_bimschg_color(cat_short)
            text = marker_data.get('name', 'Unbekannt')
        else:  # WKA
            status = marker_data.get('status', 'default')
            color = self.WKA_COLORS.get(status, self.WKA_COLORS['default'])
            text = marker_data.get('name', 'WKA')
        
        # Marker erstellen
        marker = self.map_widget.set_marker(
            lat, lon,
            text=text,
            marker_color_circle=color,
            marker_color_outside=color,
            data=marker_data  # Daten für Click-Event speichern
        )
        
        # Click-Handler
        marker.command = lambda m=marker_data: self._on_marker_click(m)
        
        # Marker speichern
        marker_id = f"{lat}_{lon}_{len(self.markers)}"
        self.markers[marker_id] = marker
    
    def _get_bimschg_color(self, category: str) -> str:
        """Ermittelt Farbe für BImSchG-Kategorie"""
        for key, color in self.BIMSCHG_COLORS.items():
            if key.lower() in category.lower():
                return color
        return self.BIMSCHG_COLORS['Sonstige']
    
    def _clear_markers(self):
        """Löscht alle Marker von der Karte"""
        for marker in self.markers.values():
            try:
                marker.delete()
            except:
                pass
        self.markers.clear()
        logger.debug("🗑️ Alle Marker gelöscht")
    
    def _on_marker_click(self, marker_data: Dict):
        """Marker wurde geklickt"""
        logger.info(f"🖱️ Marker geklickt: {marker_data.get('name', 'Unbekannt')}")
        
        # Info-Dialog anzeigen
        if marker_data.get('is_cluster'):
            self._show_cluster_info(marker_data)
        else:
            self._show_marker_info(marker_data)
    
    def _show_marker_info(self, marker_data: Dict):
        """Zeigt Marker-Details in Dialog"""
        info_window = tk.Toplevel(self)
        info_window.title("Marker-Details")
        info_window.geometry("500x400")
        
        # Scrollable Text
        text_widget = tk.Text(info_window, wrap="word", padx=10, pady=10)
        text_widget.pack(fill="both", expand=True)
        
        # Formatierte Infos
        if marker_data.get('type') == 'bimschg':
            info_text = f"""🏭 BImSchG-Anlage

Name: {marker_data.get('name', 'Unbekannt')}
Kategorie: {marker_data.get('category', '--')}
Ort: {marker_data.get('ort', '--')}
Betreiber: {marker_data.get('betreiber', '--')}
4. BImSchV: {marker_data.get('nr_4bv', '--')}

📍 Position:
  Latitude: {marker_data.get('lat', '--')}°N
  Longitude: {marker_data.get('lon', '--')}°E
  
  UTM (ETRS89 Zone 33N):
  Ostwert: {marker_data.get('ostwert', '--')} m
  Nordwert: {marker_data.get('nordwert', '--')} m

Genehmigung: {marker_data.get('genehmigung', '--')}
Stand: {marker_data.get('aktualisiert', '--')}
"""
        else:  # WKA
            info_text = f"""🌬️ Windkraftanlage

Anlage: {marker_data.get('name', 'Unbekannt')}
Status: {marker_data.get('status', '--')}
Betreiber: {marker_data.get('betreiber', '--')}

🔧 Technische Daten:
  Leistung: {marker_data.get('leistung', '--')} MW
  Nabenhöhe: {marker_data.get('nabenhoehe', '--')} m
  Rotordurchmesser: {marker_data.get('rotordurchmesser', '--')} m
  Gesamthöhe: {marker_data.get('gesamthoehe', '--')} m

📍 Position:
  Latitude: {marker_data.get('lat', '--')}°N
  Longitude: {marker_data.get('lon', '--')}°E
  
  UTM (ETRS89 Zone 33N):
  Ostwert: {marker_data.get('ostwert', '--')} m
  Nordwert: {marker_data.get('nordwert', '--')} m

Inbetriebnahme: {marker_data.get('inbetriebnahme', '--')}
"""
        
        text_widget.insert("1.0", info_text)
        text_widget.config(state="disabled")
        
        # Close-Button
        close_btn = ttk.Button(
            info_window,
            text="Schließen",
            command=info_window.destroy
        )
        close_btn.pack(pady=5)
    
    def _show_cluster_info(self, cluster_data: Dict):
        """Zeigt Cluster-Details"""
        count = cluster_data['count']
        markers = cluster_data.get('markers', [])
        
        info_window = tk.Toplevel(self)
        info_window.title(f"Cluster: {count} Anlagen")
        info_window.geometry("600x500")
        
        # Header
        header = ttk.Label(
            info_window,
            text=f"📍 {count} Anlagen an diesem Standort",
            font=("Segoe UI", 12, "bold")
        )
        header.pack(pady=10)
        
        # Listbox mit Anlagen
        list_frame = ttk.Frame(info_window)
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        
        listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
        listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=listbox.yview)
        
        # Anlagen-Liste füllen
        for i, marker in enumerate(markers[:100], 1):  # Max 100 anzeigen
            name = marker.get('name', 'Unbekannt')
            category = marker.get('category', marker.get('status', ''))
            listbox.insert("end", f"{i}. {name} ({category})")
        
        if len(markers) > 100:
            listbox.insert("end", f"... und {len(markers) - 100} weitere")
        
        # Double-Click zum Öffnen
        def on_double_click(event):
            selection = listbox.curselection()
            if selection:
                idx = selection[0]
                if idx < len(markers):
                    self._show_marker_info(markers[idx])
        
        listbox.bind("<Double-Button-1>", on_double_click)
        
        # Close-Button
        close_btn = ttk.Button(
            info_window,
            text="Schließen",
            command=info_window.destroy
        )
        close_btn.pack(pady=5)
    
    def _on_filter_change(self):
        """Filter wurde geändert"""
        self.show_bimschg = self.bimschg_var.get()
        self.show_wka = self.wka_var.get()
        
        logger.info(f"🔧 Filter geändert: BImSchG={self.show_bimschg}, WKA={self.show_wka}")
        self._reload_markers()
    
    def _on_clustering_change(self):
        """Clustering wurde geändert"""
        self.clustering_enabled = self.cluster_var.get()
        logger.info(f"🔧 Clustering: {self.clustering_enabled}")
        
        # Marker neu anzeigen (mit/ohne Clustering)
        if self.current_data:
            self._display_markers(self.current_data)
    
    def _on_limit_change(self):
        """Marker-Limit wurde geändert"""
        limit = self.limit_var.get()
        self.limit_label.config(text=f"{limit} Marker")
    
    def _reload_markers(self):
        """Lädt Marker neu"""
        self._update_status("🔄 Lade Marker neu...")
        threading.Thread(target=self._load_markers_thread, daemon=True).start()
    
    def _center_brandenburg(self):
        """Zentriert Karte auf Brandenburg"""
        self.map_widget.set_position(52.45, 13.37)
        self.map_widget.set_zoom(8)
        logger.info("📍 Karte auf Brandenburg zentriert")
    
    def _show_search_dialog(self):
        """Zeigt Such-Dialog"""
        search_window = tk.Toplevel(self)
        search_window.title("Suche")
        search_window.geometry("400x150")
        
        ttk.Label(search_window, text="Suche nach Ort, Anlage oder Betreiber:").pack(pady=10)
        
        search_var = tk.StringVar()
        search_entry = ttk.Entry(search_window, textvariable=search_var, width=40)
        search_entry.pack(pady=5)
        search_entry.focus()
        
        def do_search():
            query = search_var.get().strip()
            if not query:
                return
            
            search_window.destroy()
            self._execute_search(query)
        
        search_entry.bind("<Return>", lambda e: do_search())
        
        ttk.Button(search_window, text="🔍 Suchen", command=do_search).pack(pady=10)
    
    def _execute_search(self, query: str):
        """Führt Suche aus"""
        self._update_status(f"🔍 Suche nach '{query}'...")
        
        def search_thread():
            try:
                url = f"{self.backend_url}/api/immi/search"
                params = {'query': query, 'limit': 50}
                response = requests.get(url, params=params, timeout=10)
                
                if response.status_code == 200:
                    results = response.json()
                    self.after(0, lambda: self._show_search_results(query, results))
                else:
                    self.after(0, lambda: self._update_status(f"Fehler bei Suche: {response.status_code}"))
            except Exception as e:
                logger.error(f"❌ Such-Fehler: {e}")
                self.after(0, lambda: self._update_status(f"Such-Fehler: {e}"))
        
        threading.Thread(target=search_thread, daemon=True).start()
    
    def _show_search_results(self, query: str, results: List[Dict]):
        """Zeigt Such-Ergebnisse"""
        if not results:
            messagebox.showinfo("Suche", f"Keine Ergebnisse für '{query}' gefunden.")
            self._update_status("Keine Ergebnisse")
            return
        
        # Ergebnis-Fenster
        result_window = tk.Toplevel(self)
        result_window.title(f"Suchergebnisse: {query}")
        result_window.geometry("600x400")
        
        ttk.Label(
            result_window,
            text=f"🔍 {len(results)} Ergebnisse für '{query}'",
            font=("Segoe UI", 11, "bold")
        ).pack(pady=10)
        
        # Listbox
        list_frame = ttk.Frame(result_window)
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        
        listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
        listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=listbox.yview)
        
        # Ergebnisse füllen
        for i, result in enumerate(results, 1):
            name = result.get('name', 'Unbekannt')
            typ = "BImSchG" if result.get('type') == 'bimschg' else "WKA"
            ort = result.get('ort', result.get('betreiber', ''))
            listbox.insert("end", f"{i}. [{typ}] {name} ({ort})")
        
        # Zur Position springen
        def on_select(event):
            selection = listbox.curselection()
            if selection:
                idx = selection[0]
                result = results[idx]
                lat = result.get('lat')
                lon = result.get('lon')
                if lat and lon:
                    self.map_widget.set_position(lat, lon)
                    self.map_widget.set_zoom(13)
                    result_window.destroy()
        
        listbox.bind("<Double-Button-1>", on_select)
        
        ttk.Button(
            result_window,
            text="Schließen",
            command=result_window.destroy
        ).pack(pady=5)
        
        self._update_status(f"{len(results)} Ergebnisse gefunden")
    
    def _on_map_right_click(self, coords):
        """Rechtsklick auf Karte"""
        lat, lon = coords
        self.coord_label.config(text=f"Position: {lat:.5f}°N, {lon:.5f}°E")
        logger.debug(f"🖱️ Rechtsklick: {lat:.5f}°N, {lon:.5f}°E")
    
    def _update_status(self, message: str):
        """Aktualisiert Statusbar"""
        self.status_label.config(text=message)
        logger.debug(f"📊 Status: {message}")
    
    def _show_error(self, message: str):
        """Zeigt Fehler-Meldung"""
        error_label = ttk.Label(
            self,
            text=f"❌ {message}",
            font=("Segoe UI", 12),
            foreground="red",
            justify="center"
        )
        error_label.pack(expand=True)


# Test-Anwendung
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    root = tk.Tk()
    root.title("IMMI Map Widget - Test")
    root.geometry("1200x700")
    
    map_widget = IMMIMapWidget(root)
    map_widget.pack(fill="both", expand=True)
    
    root.mainloop()
