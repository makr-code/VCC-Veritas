# VQB - Anlagen-Lebenszyklus-View nach BImSchG

## Konzept-Erweiterung für überwachungsbedürftige Anlagen
**Version**: 1.2  
**Datum**: 19. November 2025

---

## 1. Executive Summary

Der **Anlagen-Lebenszyklus-View** ist eine spezialisierte Ansicht im VQB, die den kompletten Lebenszyklus überwachungsbedürftiger Anlagen nach BImSchG visualisiert. Die Ansicht verbindet:

- **VPB-Prozesse** (Genehmigung, Überwachung, Änderungen, Stilllegung)
- **Rechtliche Grundlagen** (BImSchG, Verordnungen, Änderungen)
- **Zeitliche Entwicklung** (Prozess-Timeline mit rechtlichen Änderungen)
- **Pflichten & Ereignisse** (Anzeigen, Meldungen, Nachweise)

### Visualisierung

```
Timeline (horizontal):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━→ Zeit
   │                    │                                      │
   │                    │                                      │
Genehmigungs-     Betrieb (mit zyklischen              Stilllegung &
verfahren         Überwachungen)                        Beräumung
2020-01          2020-06 ─────────────────────→         2040-12

Ereignisse:
   ⚡ Anlagenänderung (2022-03)
      └─ Anzeigepflicht ✓
      └─ Teil-Genehmigung
   
   ⚡ Neue BImSchV (2023-01)
      └─ Indirekte Auswirkung: Grenzwertanpassung
   
   📋 Überwachung (zyklisch: alle 3 Jahre)
      ├─ 2020-06 ✓
      ├─ 2023-06 ✓
      └─ 2026-06 (geplant)
   
   📄 Meldepflichten (jährlich)
      ├─ Emissionsbericht 2021 ✓
      ├─ Emissionsbericht 2022 ✓
      └─ ...

Rechtliche Grundlagen (vertikal):
├─ BImSchG § 4 (Genehmigungspflicht)
├─ 4. BImSchV (Genehmigungsverfahren)
├─ BImSchG § 15 (Anzeigepflicht)
├─ 13. BImSchV (Großfeuerungsanlagen) [geändert 2023-01]
└─ BImSchG § 5 (Betreiberpflichten)
```

---

## 2. Datenmodell-Erweiterungen

### 2.1 Anlage (Facility)

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from enum import Enum

class AnlagenTyp(Enum):
    """Anlagentypen nach 4. BImSchV Anhang 1"""
    FEUERUNGSANLAGE = "feuerungsanlage"
    ABFALLBEHANDLUNG = "abfallbehandlung"
    STEINE_ERDEN = "steine_erden"
    GLAS_KERAMIK = "glas_keramik"
    STAHL_EISEN = "stahl_eisen"
    # ... weitere Typen aus Anhang 1

class AnlagenStatus(Enum):
    """Status der Anlage"""
    GEPLANT = "geplant"
    GENEHMIGUNGSVERFAHREN = "genehmigungsverfahren"
    IN_BETRIEB = "in_betrieb"
    STILLGELEGT = "stillgelegt"
    BERAEUMT = "beraeumt"

@dataclass
class Anlage:
    """
    Überwachungsbedürftige Anlage nach BImSchG
    
    Attributes:
        urn: VCC-URN der Anlage
        bezeichnung: Anlagenbezeichnung
        typ: Anlagentyp nach 4. BImSchV
        betreiber: Betreiber der Anlage
        standort: Standort (föderale Ebene)
        status: Aktueller Status
        genehmigungsdatum: Datum der Erstgenehmigung
        inbetriebnahme: Datum der Inbetriebnahme
        geplante_stilllegung: Geplantes Stilllegungsdatum
        prozesse: Zugeordnete VPB-Prozesse (URNs)
        rechtliche_grundlagen: Anwendbare Rechtsnormen (URNs)
        ereignisse: Wichtige Ereignisse im Lebenszyklus
    """
    urn: str  # urn:vcc:facility:bimschg:{anlage-id}
    bezeichnung: str
    typ: AnlagenTyp
    betreiber: str
    standort: str  # URN der föderalen Ebene
    status: AnlagenStatus
    genehmigungsdatum: Optional[datetime] = None
    inbetriebnahme: Optional[datetime] = None
    geplante_stilllegung: Optional[datetime] = None
    prozesse: List[str] = field(default_factory=list)  # Process URNs
    rechtliche_grundlagen: List[str] = field(default_factory=list)  # Legal norm URNs
    ereignisse: List['AnlagenEreignis'] = field(default_factory=list)
    
    @property
    def betriebsdauer_jahre(self) -> Optional[float]:
        """Berechne bisherige/geplante Betriebsdauer in Jahren"""
        if not self.inbetriebnahme:
            return None
        
        end_date = self.geplante_stilllegung or datetime.now()
        delta = end_date - self.inbetriebnahme
        return delta.days / 365.25
```

### 2.2 Anlagen-Ereignis

```python
from enum import Enum

class EreignisTyp(Enum):
    """Typen von Anlagen-Ereignissen"""
    # Genehmigungsrelevant
    ERSTGENEHMIGUNG = "erstgenehmigung"
    AENDERUNGSGENEHMIGUNG = "aenderungsgenehmigung"
    TEILGENEHMIGUNG = "teilgenehmigung"
    
    # Anzeigepflichtig
    ANZEIGEPFLICHTIGE_AENDERUNG = "anzeigepflichtige_aenderung"
    BETRIEBSBEGINN_ANZEIGE = "betriebsbeginn_anzeige"
    BETREIBERWECHSEL = "betreiberwechsel"
    
    # Überwachung
    WIEDERKEHRENDE_UEBERWACHUNG = "wiederkehrende_ueberwachung"
    ANLASSBEZOGENE_UEBERWACHUNG = "anlassbezogene_ueberwachung"
    EMISSIONSMESSUNG = "emissionsmessung"
    
    # Meldepflichten
    EMISSIONSBERICHT = "emissionsbericht"
    STOERFALL_MELDUNG = "stoerfall_meldung"
    JAHRESBERICHT = "jahresbericht"
    
    # Nachweispflichten
    IMMISSIONSSCHUTZGUTACHTEN = "immissionsschutzgutachten"
    SICHERHEITSTECHNISCHE_PRUEFUNG = "sicherheitstechnische_pruefung"
    
    # Rechtliche Änderungen
    NEUE_RECHTSVORSCHRIFT = "neue_rechtsvorschrift"
    RECHTSVORSCHRIFT_GEAENDERT = "rechtsvorschrift_geaendert"
    
    # Lebenszyklus-Events
    STILLLEGUNG_ANGEZEIGT = "stilllegung_angezeigt"
    STILLLEGUNG_ABGESCHLOSSEN = "stilllegung_abgeschlossen"
    BERÄUMUNG_ABGESCHLOSSEN = "beräumung_abgeschlossen"

class AuswirkungsArt(Enum):
    """Art der Auswirkung rechtlicher Änderungen"""
    DIREKT = "direkt"           # Unmittelbare Anwendung
    INDIREKT = "indirekt"       # Mittelbare Auswirkung
    GEPLANT = "geplant"         # Zukünftige Anwendung
    NICHT_BETROFFEN = "nicht_betroffen"

@dataclass
class AnlagenEreignis:
    """
    Ereignis im Lebenszyklus einer Anlage
    
    Attributes:
        urn: URN des Ereignisses
        typ: Ereignistyp
        datum: Datum des Ereignisses
        anlage_urn: URN der betroffenen Anlage
        prozess_urn: Optional: Zugeordneter VPB-Prozess
        rechtsnorm_urn: Optional: Betroffene Rechtsnorm
        auswirkung: Bei rechtlichen Änderungen: Art der Auswirkung
        beschreibung: Kurzbeschreibung
        frist: Optional: Frist für Umsetzung/Reaktion
        erledigt: Status (erledigt/offen)
        dokumente: Zugeordnete Dokumente
    """
    urn: str
    typ: EreignisTyp
    datum: datetime
    anlage_urn: str
    prozess_urn: Optional[str] = None
    rechtsnorm_urn: Optional[str] = None
    auswirkung: Optional[AuswirkungsArt] = None
    beschreibung: str = ""
    frist: Optional[datetime] = None
    erledigt: bool = False
    dokumente: List[str] = field(default_factory=list)
    
    @property
    def is_frist_abgelaufen(self) -> bool:
        """Prüfe ob Frist abgelaufen"""
        if not self.frist:
            return False
        return datetime.now() > self.frist and not self.erledigt
    
    @property
    def tage_bis_frist(self) -> Optional[int]:
        """Tage bis zur Frist"""
        if not self.frist or self.erledigt:
            return None
        delta = self.frist - datetime.now()
        return delta.days
```

### 2.3 Rechtliche Änderung

```python
@dataclass
class RechtlicheAenderung:
    """
    Änderung einer Rechtsnorm
    
    Attributes:
        urn: URN der Änderung
        norm_urn: URN der geänderten Norm
        aenderungsdatum: Datum des Inkrafttretens
        aenderungstyp: Art der Änderung
        betroffene_paragraphen: Liste geänderter Paragraphen
        auswirkung_auf_anlagen: Mapping Anlage → Auswirkungsart
        beschreibung: Beschreibung der Änderung
        uebergangsfristen: Optional: Übergangsfristen
    """
    urn: str
    norm_urn: str
    aenderungsdatum: datetime
    aenderungstyp: str  # "novellierung", "neufassung", "aufhebung"
    betroffene_paragraphen: List[str] = field(default_factory=list)
    auswirkung_auf_anlagen: Dict[str, AuswirkungsArt] = field(default_factory=dict)
    beschreibung: str = ""
    uebergangsfristen: Optional[datetime] = None
    
    def get_betroffene_anlagen(self) -> List[str]:
        """Hole alle betroffenen Anlagen-URNs"""
        return [
            anlage_urn for anlage_urn, auswirkung in self.auswirkung_auf_anlagen.items()
            if auswirkung in [AuswirkungsArt.DIREKT, AuswirkungsArt.INDIREKT]
        ]
```

---

## 3. UI-Komponenten für Anlagen-Lebenszyklus

### 3.1 Anlagen-Timeline-View

```python
import tkinter as tk
from datetime import datetime, timedelta
from typing import List

class AnlagenTimelineView(tk.Canvas):
    """
    Timeline-Ansicht für Anlagen-Lebenszyklus
    
    Visualisiert:
    - Lebenszyklus-Phasen (Genehmigung → Betrieb → Stilllegung)
    - Prozesse als Balken
    - Ereignisse als Marker
    - Rechtliche Änderungen als vertikale Linien
    - Zyklische Events (Überwachungen, Meldungen)
    """
    
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#F5F5F5")
        self.controller = controller
        
        # Timeline-Einstellungen
        self.start_date = None
        self.end_date = None
        self.zoom_level = 1.0
        self.offset_x = 0
        
        # Aktuelle Anlage
        self.anlage = None
        
        # Bind events
        self.bind("<MouseWheel>", self.on_zoom)
        self.bind("<B1-Motion>", self.on_pan)
        self.bind("<Button-1>", self.on_click)
        self.bind("<Motion>", self.on_hover)
    
    def render_anlage(self, anlage: Anlage):
        """
        Rendere Anlagen-Lebenszyklus
        
        Args:
            anlage: Anlage-Objekt
        """
        self.anlage = anlage
        self.delete("all")
        
        if not anlage.genehmigungsdatum:
            return
        
        # Zeitspanne berechnen
        self.start_date = anlage.genehmigungsdatum
        self.end_date = anlage.geplante_stilllegung or datetime.now() + timedelta(days=365*5)
        
        # Hauptphasen zeichnen
        self._draw_lifecycle_phases()
        
        # Prozesse zeichnen
        self._draw_processes()
        
        # Ereignisse zeichnen
        self._draw_events()
        
        # Rechtliche Änderungen zeichnen
        self._draw_legal_changes()
        
        # Zyklische Events zeichnen
        self._draw_cyclic_events()
        
        # Legende
        self._draw_legend()
    
    def _draw_lifecycle_phases(self):
        """Zeichne Lebenszyklus-Phasen als Hintergrund-Bereiche"""
        # Genehmigungsphase
        if self.anlage.genehmigungsdatum and self.anlage.inbetriebnahme:
            x1 = self._date_to_x(self.anlage.genehmigungsdatum)
            x2 = self._date_to_x(self.anlage.inbetriebnahme)
            self.create_rectangle(x1, 50, x2, 150, fill="#FFE5B4", outline="", 
                                 tags="phase_genehmigung")
            self.create_text((x1 + x2) / 2, 100, text="Genehmigung", 
                           font=("Arial", 12, "bold"), tags="phase_label")
        
        # Betriebsphase
        if self.anlage.inbetriebnahme:
            x1 = self._date_to_x(self.anlage.inbetriebnahme)
            x2 = self._date_to_x(self.anlage.geplante_stilllegung or self.end_date)
            self.create_rectangle(x1, 50, x2, 150, fill="#B4E5FF", outline="",
                                 tags="phase_betrieb")
            self.create_text((x1 + x2) / 2, 100, text="Betrieb", 
                           font=("Arial", 12, "bold"), tags="phase_label")
        
        # Stilllegungsphase (geplant)
        if self.anlage.geplante_stilllegung:
            x1 = self._date_to_x(self.anlage.geplante_stilllegung)
            x2 = self._date_to_x(self.anlage.geplante_stilllegung + timedelta(days=365))
            self.create_rectangle(x1, 50, x2, 150, fill="#FFB4B4", outline="",
                                 tags="phase_stilllegung")
            self.create_text((x1 + x2) / 2, 100, text="Stilllegung", 
                           font=("Arial", 12, "bold"), tags="phase_label")
    
    def _draw_processes(self):
        """Zeichne VPB-Prozesse als Balken"""
        y_offset = 200
        
        for process_urn in self.anlage.prozesse:
            # Prozess vom Controller laden
            process = self.controller.get_process_by_urn(process_urn)
            if not process:
                continue
            
            x1 = self._date_to_x(process.start_time)
            x2 = self._date_to_x(process.end_time)
            
            # Farbe nach Status
            color = self._get_process_color(process.status)
            
            # Prozess-Balken
            self.create_rectangle(x1, y_offset, x2, y_offset + 30,
                                fill=color, outline="#333", width=1,
                                tags=f"process_{process.id}")
            
            # Prozess-Titel
            self.create_text((x1 + x2) / 2, y_offset + 15,
                           text=process.title, font=("Arial", 9),
                           tags=f"process_{process.id}")
            
            y_offset += 40
    
    def _draw_events(self):
        """Zeichne Ereignisse als Marker"""
        for ereignis in self.anlage.ereignisse:
            x = self._date_to_x(ereignis.datum)
            y = self._get_event_y_position(ereignis.typ)
            
            # Event-Symbol
            symbol = self._get_event_symbol(ereignis.typ)
            color = self._get_event_color(ereignis.typ)
            
            # Marker zeichnen
            if ereignis.erledigt:
                # Ausgefüllter Kreis
                self.create_oval(x - 8, y - 8, x + 8, y + 8,
                               fill=color, outline="#333", width=2,
                               tags=f"event_{ereignis.urn}")
            else:
                # Offener Kreis
                self.create_oval(x - 8, y - 8, x + 8, y + 8,
                               fill="white", outline=color, width=3,
                               tags=f"event_{ereignis.urn}")
            
            # Symbol im Kreis
            self.create_text(x, y, text=symbol, font=("Arial", 10, "bold"),
                           tags=f"event_{ereignis.urn}")
            
            # Frist-Indikator
            if ereignis.is_frist_abgelaufen:
                self.create_text(x, y - 20, text="⚠", fill="red",
                               font=("Arial", 14), tags=f"event_{ereignis.urn}")
    
    def _draw_legal_changes(self):
        """Zeichne rechtliche Änderungen als vertikale Linien"""
        # Rechtliche Änderungen vom Controller laden
        changes = self.controller.get_legal_changes_for_anlage(self.anlage.urn)
        
        for change in changes:
            x = self._date_to_x(change.aenderungsdatum)
            
            # Vertikale Linie
            color = self._get_change_color(change.auswirkung_auf_anlagen.get(self.anlage.urn))
            style = "solid" if change.auswirkung_auf_anlagen.get(self.anlage.urn) == AuswirkungsArt.DIREKT else "dashed"
            
            if style == "dashed":
                self.create_line(x, 50, x, 500, fill=color, width=2, dash=(5, 3),
                               tags=f"legal_change_{change.urn}")
            else:
                self.create_line(x, 50, x, 500, fill=color, width=3,
                               tags=f"legal_change_{change.urn}")
            
            # Label
            self.create_text(x + 5, 60, text=change.beschreibung[:30] + "...",
                           font=("Arial", 8), anchor="nw", angle=90,
                           tags=f"legal_change_{change.urn}")
    
    def _draw_cyclic_events(self):
        """Zeichne zyklische Events (Überwachungen, Meldungen)"""
        # Überwachungen (alle 3 Jahre)
        if self.anlage.inbetriebnahme:
            current = self.anlage.inbetriebnahme
            while current < self.end_date:
                x = self._date_to_x(current)
                y = 400
                
                # Überwachungs-Symbol
                self.create_rectangle(x - 10, y - 10, x + 10, y + 10,
                                    fill="#4169E1", outline="#333",
                                    tags="cyclic_ueberwachung")
                self.create_text(x, y, text="👁", font=("Arial", 10),
                               tags="cyclic_ueberwachung")
                
                current += timedelta(days=365 * 3)  # Alle 3 Jahre
        
        # Emissionsberichte (jährlich)
        if self.anlage.inbetriebnahme:
            current = self.anlage.inbetriebnahme + timedelta(days=365)
            while current < self.end_date:
                x = self._date_to_x(current)
                y = 450
                
                # Berichts-Symbol
                self.create_rectangle(x - 8, y - 8, x + 8, y + 8,
                                    fill="#32CD32", outline="#333",
                                    tags="cyclic_bericht")
                self.create_text(x, y, text="📄", font=("Arial", 8),
                               tags="cyclic_bericht")
                
                current += timedelta(days=365)  # Jährlich
    
    def _draw_legend(self):
        """Zeichne Legende"""
        legend_x = 50
        legend_y = 550
        
        legends = [
            ("Genehmigungsphase", "#FFE5B4"),
            ("Betriebsphase", "#B4E5FF"),
            ("Stilllegungsphase", "#FFB4B4"),
            ("Direkte Rechtsänderung", "#DC143C"),
            ("Indirekte Rechtsänderung", "#FFA500"),
            ("Überwachung (3-jährlich)", "#4169E1"),
            ("Emissionsbericht (jährlich)", "#32CD32"),
        ]
        
        for i, (label, color) in enumerate(legends):
            x = legend_x + (i % 3) * 250
            y = legend_y + (i // 3) * 25
            
            self.create_rectangle(x, y, x + 20, y + 15, fill=color, outline="#333")
            self.create_text(x + 25, y + 8, text=label, anchor="w", font=("Arial", 9))
    
    def _date_to_x(self, date: datetime) -> int:
        """Konvertiere Datum zu X-Koordinate"""
        if not self.start_date or not self.end_date:
            return 0
        
        total_days = (self.end_date - self.start_date).days
        days_from_start = (date - self.start_date).days
        
        # X-Position (100px Offset, 1000px verfügbar)
        x = 100 + (days_from_start / total_days) * 1000 * self.zoom_level + self.offset_x
        return int(x)
    
    def _get_event_symbol(self, typ: EreignisTyp) -> str:
        """Hole Symbol für Ereignistyp"""
        symbols = {
            EreignisTyp.AENDERUNGSGENEHMIGUNG: "✓",
            EreignisTyp.ANZEIGEPFLICHTIGE_AENDERUNG: "⚡",
            EreignisTyp.WIEDERKEHRENDE_UEBERWACHUNG: "👁",
            EreignisTyp.EMISSIONSBERICHT: "📄",
            EreignisTyp.STOERFALL_MELDUNG: "⚠",
            EreignisTyp.STILLLEGUNG_ANGEZEIGT: "🛑",
        }
        return symbols.get(typ, "•")
    
    def _get_event_color(self, typ: EreignisTyp) -> str:
        """Hole Farbe für Ereignistyp"""
        # Genehmigungen: Grün
        if typ in [EreignisTyp.ERSTGENEHMIGUNG, EreignisTyp.AENDERUNGSGENEHMIGUNG]:
            return "#32CD32"
        # Anzeigen: Orange
        elif "ANZEIGE" in typ.name:
            return "#FFA500"
        # Überwachung: Blau
        elif "UEBERWACHUNG" in typ.name:
            return "#4169E1"
        # Meldungen: Gelb
        elif "MELDUNG" in typ.name or "BERICHT" in typ.name:
            return "#FFD700"
        # Stilllegung: Rot
        elif "STILLLEGUNG" in typ.name:
            return "#DC143C"
        else:
            return "#808080"
    
    def on_click(self, event):
        """Handle click event"""
        # Finde geklicktes Objekt
        items = self.find_overlapping(event.x - 5, event.y - 5, event.x + 5, event.y + 5)
        
        for item in items:
            tags = self.gettags(item)
            
            # Ereignis geklickt
            if any(tag.startswith("event_") for tag in tags):
                event_urn = [tag for tag in tags if tag.startswith("event_")][0].replace("event_", "")
                self.controller.show_event_details(event_urn)
                break
            
            # Prozess geklickt
            elif any(tag.startswith("process_") for tag in tags):
                process_id = [tag for tag in tags if tag.startswith("process_")][0].replace("process_", "")
                self.controller.show_process_details(process_id)
                break
            
            # Rechtliche Änderung geklickt
            elif any(tag.startswith("legal_change_") for tag in tags):
                change_urn = [tag for tag in tags if tag.startswith("legal_change_")][0].replace("legal_change_", "")
                self.controller.show_legal_change_details(change_urn)
                break
```

### 3.2 Anlagen-Übersicht Panel

```python
class AnlagenUebersichtPanel(tk.Frame):
    """
    Übersicht-Panel für Anlagen
    
    Zeigt:
    - Anlagen-Liste
    - Filter nach Status, Typ
    - Suchfunktion
    """
    
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # Suchfeld
        search_frame = tk.Frame(self)
        search_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(search_frame, text="Suche:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self._on_search_change)
        tk.Entry(search_frame, textvariable=self.search_var, width=30).pack(side=tk.LEFT, padx=5)
        
        # Filter
        filter_frame = tk.Frame(self)
        filter_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(filter_frame, text="Status:").pack(side=tk.LEFT)
        self.status_var = tk.StringVar(value="Alle")
        status_combo = ttk.Combobox(filter_frame, textvariable=self.status_var,
                                   values=["Alle", "Genehmigungsverfahren", "In Betrieb", "Stillgelegt"],
                                   width=20)
        status_combo.pack(side=tk.LEFT, padx=5)
        status_combo.bind("<<ComboboxSelected>>", lambda e: self._apply_filters())
        
        # Anlagen-Liste
        list_frame = tk.Frame(self)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Treeview
        columns = ("Bezeichnung", "Typ", "Status", "Betreiber")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="tree headings")
        
        self.tree.heading("#0", text="ID")
        for col in columns:
            self.tree.heading(col, text=col)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.config(yscrollcommand=scrollbar.set)
        
        # Bind events
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
    
    def load_anlagen(self, anlagen: List[Anlage]):
        """Lade Anlagen in Liste"""
        self.tree.delete(*self.tree.get_children())
        
        for anlage in anlagen:
            self.tree.insert("", tk.END, text=anlage.urn.split(":")[-1],
                           values=(
                               anlage.bezeichnung,
                               anlage.typ.value,
                               anlage.status.value,
                               anlage.betreiber
                           ))
    
    def _on_select(self, event):
        """Handle Anlagen-Auswahl"""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            anlage_id = item["text"]
            self.controller.select_anlage(anlage_id)
```

---

## 4. URN-Erweiterungen für Anlagen

```python
# In vqb_frontend/utils/urn.py ergänzen:

def create_facility_urn(anlage_id: str) -> URN:
    """
    Create URN for BImSchG facility
    
    Args:
        anlage_id: Facility identifier
    
    Returns:
        URN for facility
    
    Example:
        >>> urn = create_facility_urn("feuerungsanlage-potsdam-001")
        >>> str(urn)
        'urn:vcc:facility:bimschg:feuerungsanlage-potsdam-001'
    """
    return URN(
        namespace=URNNamespace.FACILITY,
        type="bimschg",
        identifier=anlage_id
    )

def create_event_urn(anlage_id: str, ereignis_typ: str, datum: datetime) -> URN:
    """
    Create URN for facility event
    
    Args:
        anlage_id: Facility identifier
        ereignis_typ: Event type
        datum: Event date
    
    Returns:
        URN for event
    """
    timestamp = datum.strftime("%Y%m%d")
    return URN(
        namespace=URNNamespace.EVENT,
        type=ereignis_typ,
        identifier=f"{anlage_id}:{timestamp}"
    )
```

---

## 5. Beispiel: Vollständiger Lebenszyklus

```python
from datetime import datetime, timedelta

# Anlage erstellen
anlage = Anlage(
    urn="urn:vcc:facility:bimschg:feuerungsanlage-potsdam-001",
    bezeichnung="Großfeuerungsanlage Potsdam",
    typ=AnlagenTyp.FEUERUNGSANLAGE,
    betreiber="Stadtwerke Potsdam GmbH",
    standort="urn:vcc:fed:kommune:potsdam",
    status=AnlagenStatus.IN_BETRIEB,
    genehmigungsdatum=datetime(2020, 1, 15),
    inbetriebnahme=datetime(2020, 6, 1),
    geplante_stilllegung=datetime(2040, 12, 31),
    rechtliche_grundlagen=[
        "urn:vcc:legal:norm:bimschg:year:2024:para:4",  # Genehmigungspflicht
        "urn:vcc:legal:norm:13bimschv:year:2023",       # Großfeuerungsanlagen-Verordnung
        "urn:vcc:legal:norm:bimschg:year:2024:para:5",  # Betreiberpflichten
    ]
)

# Ereignisse hinzufügen
ereignisse = [
    # Erstgenehmigung
    AnlagenEreignis(
        urn="urn:vcc:event:erstgenehmigung:feuerungsanlage-potsdam-001:20200115",
        typ=EreignisTyp.ERSTGENEHMIGUNG,
        datum=datetime(2020, 1, 15),
        anlage_urn=anlage.urn,
        prozess_urn="urn:vcc:vpb:process:genehmigung-potsdam-001",
        erledigt=True
    ),
    
    # Anlagenänderung mit Anzeigepflicht
    AnlagenEreignis(
        urn="urn:vcc:event:anzeigepflichtige_aenderung:feuerungsanlage-potsdam-001:20220315",
        typ=EreignisTyp.ANZEIGEPFLICHTIGE_AENDERUNG,
        datum=datetime(2022, 3, 15),
        anlage_urn=anlage.urn,
        beschreibung="Umstellung auf Erdgas",
        erledigt=True
    ),
    
    # Neue BImSchV 2023
    AnlagenEreignis(
        urn="urn:vcc:event:rechtsvorschrift_geaendert:13bimschv:20230101",
        typ=EreignisTyp.RECHTSVORSCHRIFT_GEAENDERT,
        datum=datetime(2023, 1, 1),
        anlage_urn=anlage.urn,
        rechtsnorm_urn="urn:vcc:legal:norm:13bimschv:year:2023",
        auswirkung=AuswirkungsArt.INDIREKT,
        beschreibung="Novellierung 13. BImSchV - neue Grenzwerte",
        frist=datetime(2024, 1, 1),  # Übergangsfrist
        erledigt=False
    ),
    
    # Wiederkehrende Überwachung
    AnlagenEreignis(
        urn="urn:vcc:event:wiederkehrende_ueberwachung:feuerungsanlage-potsdam-001:20230601",
        typ=EreignisTyp.WIEDERKEHRENDE_UEBERWACHUNG,
        datum=datetime(2023, 6, 1),
        anlage_urn=anlage.urn,
        erledigt=True
    ),
    
    # Emissionsbericht (fällig)
    AnlagenEreignis(
        urn="urn:vcc:event:emissionsbericht:feuerungsanlage-potsdam-001:20250331",
        typ=EreignisTyp.EMISSIONSBERICHT,
        datum=datetime(2024, 12, 31),  # Berichtsjahr
        anlage_urn=anlage.urn,
        beschreibung="Emissionsbericht 2024",
        frist=datetime(2025, 3, 31),
        erledigt=False
    )
]

anlage.ereignisse = ereignisse

# Rechtliche Änderung
aenderung_13bimschv = RechtlicheAenderung(
    urn="urn:vcc:legal:change:13bimschv:20230101",
    norm_urn="urn:vcc:legal:norm:13bimschv:year:2023",
    aenderungsdatum=datetime(2023, 1, 1),
    aenderungstyp="novellierung",
    betroffene_paragraphen=["§3", "§4", "Anhang 1"],
    auswirkung_auf_anlagen={
        anlage.urn: AuswirkungsArt.INDIREKT
    },
    beschreibung="Verschärfung der Emissionsgrenzwerte für NOx und SO2",
    uebergangsfristen=datetime(2024, 1, 1)
)
```

---

## 6. Integration mit VQB

### Main Window Integration

```python
class VQBApplication(tk.Tk):
    """VQB mit Anlagen-Lebenszyklus-View"""
    
    def _create_ui(self):
        # ... existing code ...
        
        # Tabbed View erweitern
        self.anlagen_tab = ttk.Frame(self.tabbed_view)
        self.tabbed_view.add(self.anlagen_tab, text="Anlagen (BImSchG)")
        
        # Paned Window für Anlagen-View
        anlagen_paned = tk.PanedWindow(self.anlagen_tab, orient=tk.HORIZONTAL)
        anlagen_paned.pack(fill=tk.BOTH, expand=True)
        
        # Linkes Panel: Anlagen-Übersicht
        self.anlagen_uebersicht = AnlagenUebersichtPanel(anlagen_paned, self.controller)
        anlagen_paned.add(self.anlagen_uebersicht, width=300)
        
        # Rechtes Panel: Timeline
        self.anlagen_timeline = AnlagenTimelineView(anlagen_paned, self.controller)
        anlagen_paned.add(self.anlagen_timeline)
```

---

## 7. Zusammenfassung

Der **Anlagen-Lebenszyklus-View** bietet:

1. **Vollständige Timeline**: Von Genehmigung bis Beräumung
2. **Ereignis-Tracking**: Alle relevanten Anlagen-Ereignisse
3. **Rechtliche Änderungen**: Visualisierung direkter und indirekter Auswirkungen
4. **Zyklische Events**: Überwachungen, Meldungen, Berichte
5. **Fristenmanagement**: Überfällige und anstehende Pflichten
6. **VCC-URN Integration**: Einheitliche Identifikation

**Use Cases**:
- Behörden: Überwachung mehrerer Anlagen
- Betreiber: Compliance-Management
- Gutachter: Anlagen-Historie analysieren
- Planer: Neue Anlagen konzipieren

---

**Version**: 1.2  
**Status**: Konzept-Erweiterung  
**Nächste Schritte**: Implementierung Timeline-View mit Beispieldaten
