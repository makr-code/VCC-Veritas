"""
Immissionsschutz-Datenbank Schema Generator
===========================================

Erstellt eine vollständige relationale Datenbank-Struktur für:
- Genehmigungsverfahren
- Überwachungsmaßnahmen
- Messungen (Lärm, Emissionen)
- Auflagen und Bescheide
- Inspektionen

Mit Verknüpfungen zu bestehenden BImSchG und WKA Datenbanken.
"""

import sqlite3
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Tuple
import json

# Projekt-Root
PROJECT_ROOT = Path(__file__).parent.parent
TEST_DB_DIR = PROJECT_ROOT / "data" / "test_databases"
TEST_DB_DIR.mkdir(exist_ok=True, parents=True)

# Referenz-Datenbanken
BIMSCHG_DB = PROJECT_ROOT / "data" / "bimschg" / "BImSchG.sqlite"
WKA_DB = PROJECT_ROOT / "data" / "wka" / "wka.sqlite"

# ============================================================================
# Hilfsfunktionen
# ============================================================================

def random_date(start_year: int = 2018, end_year: int = 2025) -> str:
    """Zufälliges Datum generieren"""
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    delta = end - start
    random_days = random.randint(0, delta.days)
    random_date = start + timedelta(days=random_days)
    return random_date.strftime("%Y-%m-%d")

def random_time() -> str:
    """Zufällige Uhrzeit generieren"""
    hour = random.randint(7, 18)
    minute = random.choice([0, 15, 30, 45])
    return f"{hour:02d}:{minute:02d}:00"

# ============================================================================
# Schema-Definitionen
# ============================================================================

SCHEMAS = {
    # Genehmigungsverfahren
    "genehmigungsverfahren": """
        CREATE TABLE IF NOT EXISTS genehmigungsverfahren (
            verfahren_id TEXT PRIMARY KEY,
            bst_nr TEXT NOT NULL,
            anl_nr TEXT NOT NULL,
            verfahrensart TEXT NOT NULL,  -- Erstgenehmigung, Änderungsgenehmigung, Teilgenehmigung
            antragsdatum TEXT NOT NULL,
            entscheidungsdatum TEXT,
            status TEXT NOT NULL,  -- in_bearbeitung, genehmigt, abgelehnt, zurückgezogen
            behoerde TEXT NOT NULL,
            aktenzeichen TEXT NOT NULL,
            antragsgrund TEXT,
            oeffentliche_beteiligung INTEGER DEFAULT 0,
            uvp_erforderlich INTEGER DEFAULT 0,
            bemerkungen TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """,
    
    # Bescheide (Ergebnisse von Verfahren)
    "bescheide": """
        CREATE TABLE IF NOT EXISTS bescheide (
            bescheid_id TEXT PRIMARY KEY,
            verfahren_id TEXT NOT NULL,
            bescheiddatum TEXT NOT NULL,
            bescheidtyp TEXT NOT NULL,  -- Genehmigung, Ablehnung, Aufhebung
            rechtskraft_datum TEXT,
            befristet INTEGER DEFAULT 0,
            befristung_bis TEXT,
            nebenbestimmungen TEXT,
            auflagen_anzahl INTEGER DEFAULT 0,
            rechtsgrundlage TEXT,
            pdf_pfad TEXT,
            FOREIGN KEY (verfahren_id) REFERENCES genehmigungsverfahren(verfahren_id)
        )
    """,
    
    # Auflagen (aus Bescheiden)
    "auflagen": """
        CREATE TABLE IF NOT EXISTS auflagen (
            auflagen_id TEXT PRIMARY KEY,
            bescheid_id TEXT NOT NULL,
            auflage_nr INTEGER NOT NULL,
            auflagentext TEXT NOT NULL,
            kategorie TEXT,  -- Emissionsschutz, Lärmschutz, Naturschutz, Arbeitsschutz
            messbar INTEGER DEFAULT 0,
            grenzwert REAL,
            einheit TEXT,
            umsetzungsfrist TEXT,
            status TEXT DEFAULT 'offen',  -- offen, umgesetzt, überfällig
            FOREIGN KEY (bescheid_id) REFERENCES bescheide(bescheid_id)
        )
    """,
    
    # Überwachungsmaßnahmen
    "ueberwachung": """
        CREATE TABLE IF NOT EXISTS ueberwachung (
            ueberwachung_id TEXT PRIMARY KEY,
            bst_nr TEXT NOT NULL,
            anl_nr TEXT NOT NULL,
            ueberwachungsart TEXT NOT NULL,  -- Routineinspektion, Anlassinspektion, Messung
            geplant_datum TEXT NOT NULL,
            durchgefuehrt_datum TEXT,
            status TEXT NOT NULL,  -- geplant, durchgeführt, verschoben, abgesagt
            behoerde TEXT NOT NULL,
            pruefumfang TEXT,
            ergebnis TEXT,  -- bestanden, mängel_festgestellt, nachbesserung_erforderlich
            naechste_pruefung TEXT,
            bemerkungen TEXT
        )
    """,
    
    # Messungen (Lärm, Emissionen)
    "messungen": """
        CREATE TABLE IF NOT EXISTS messungen (
            messung_id TEXT PRIMARY KEY,
            bst_nr TEXT NOT NULL,
            anl_nr TEXT NOT NULL,
            messart TEXT NOT NULL,  -- Lärm, Luftemission, Wasser, Abfall, Erschütterung
            messdatum TEXT NOT NULL,
            messzeit TEXT NOT NULL,
            messort TEXT,
            messwert REAL NOT NULL,
            einheit TEXT NOT NULL,
            grenzwert REAL,
            ueberschreitung INTEGER DEFAULT 0,
            messmethode TEXT,
            messgeraet TEXT,
            messstelle TEXT,  -- Externe Messstelle oder Behörde
            wetterbedingungen TEXT,
            bemerkungen TEXT
        )
    """,
    
    # Mängel und Verstöße
    "maengel": """
        CREATE TABLE IF NOT EXISTS maengel (
            mangel_id TEXT PRIMARY KEY,
            ueberwachung_id TEXT,
            bst_nr TEXT NOT NULL,
            anl_nr TEXT NOT NULL,
            festgestellt_datum TEXT NOT NULL,
            mangelart TEXT NOT NULL,  -- technisch, organisatorisch, dokumentation, grenzwert
            schweregrad TEXT NOT NULL,  -- gering, mittel, schwer, kritisch
            beschreibung TEXT NOT NULL,
            massnahmen_erforderlich TEXT,
            frist_beseitigung TEXT,
            beseitigt_datum TEXT,
            status TEXT DEFAULT 'offen',  -- offen, in_bearbeitung, behoben, eskaliert
            FOREIGN KEY (ueberwachung_id) REFERENCES ueberwachung(ueberwachung_id)
        )
    """,
    
    # Betreiber-Informationen (erweitert)
    "betreiber": """
        CREATE TABLE IF NOT EXISTS betreiber (
            betreiber_id TEXT PRIMARY KEY,
            firmenname TEXT NOT NULL,
            rechtsform TEXT,
            strasse TEXT,
            plz TEXT,
            ort TEXT,
            telefon TEXT,
            email TEXT,
            ansprechpartner TEXT,
            position TEXT,
            registriert_seit TEXT,
            zertifizierungen TEXT,  -- ISO 14001, ISO 50001, etc.
            bemerkungen TEXT
        )
    """,
    
    # Betreiber-Anlagen Zuordnung
    "betreiber_anlagen": """
        CREATE TABLE IF NOT EXISTS betreiber_anlagen (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            betreiber_id TEXT NOT NULL,
            bst_nr TEXT NOT NULL,
            anl_nr TEXT NOT NULL,
            verantwortlich_seit TEXT NOT NULL,
            verantwortlich_bis TEXT,
            FOREIGN KEY (betreiber_id) REFERENCES betreiber(betreiber_id)
        )
    """,
    
    # NEUE TABELLEN - Phase 2
    
    # Dokumente
    "dokumente": """
        CREATE TABLE IF NOT EXISTS dokumente (
            dokument_id TEXT PRIMARY KEY,
            bst_nr TEXT NOT NULL,
            anl_nr TEXT NOT NULL,
            dokumenttyp TEXT NOT NULL,  -- Bescheid, Messbericht, Gutachten, Plan
            titel TEXT NOT NULL,
            erstellt_datum TEXT NOT NULL,
            gueltig_bis TEXT,
            dateipfad TEXT,
            dateigroesse_kb INTEGER,
            ersteller TEXT,
            aktenzeichen TEXT,
            status TEXT DEFAULT 'aktiv',
            bemerkungen TEXT
        )
    """,
    
    # Ansprechpartner
    "ansprechpartner": """
        CREATE TABLE IF NOT EXISTS ansprechpartner (
            ansprechpartner_id TEXT PRIMARY KEY,
            bst_nr TEXT NOT NULL,
            anl_nr TEXT NOT NULL,
            name TEXT NOT NULL,
            funktion TEXT NOT NULL,
            telefon TEXT,
            email TEXT,
            mobil TEXT,
            verfuegbarkeit TEXT,
            notfallkontakt INTEGER DEFAULT 0,
            aktiv INTEGER DEFAULT 1
        )
    """,
    
    # Wartungshistorie
    "wartung": """
        CREATE TABLE IF NOT EXISTS wartung (
            wartung_id TEXT PRIMARY KEY,
            bst_nr TEXT NOT NULL,
            anl_nr TEXT NOT NULL,
            wartungsart TEXT NOT NULL,  -- Inspektion, Reparatur, Kalibrierung
            geplant_datum TEXT NOT NULL,
            durchgefuehrt_datum TEXT,
            durchgefuehrt_von TEXT,
            kosten REAL,
            naechste_wartung TEXT,
            status TEXT NOT NULL,
            beschreibung TEXT,
            massnahmen TEXT
        )
    """,
    
    # Messreihen (Zeitreihen für Trend-Analysen)
    "messreihen": """
        CREATE TABLE IF NOT EXISTS messreihen (
            messreihe_id TEXT PRIMARY KEY,
            bst_nr TEXT NOT NULL,
            anl_nr TEXT NOT NULL,
            messart TEXT NOT NULL,
            zeitraum_von TEXT NOT NULL,
            zeitraum_bis TEXT NOT NULL,
            anzahl_messungen INTEGER,
            mittelwert REAL,
            maximalwert REAL,
            minimalwert REAL,
            standardabweichung REAL,
            ueberschreitungen_anzahl INTEGER,
            trend TEXT,  -- steigend, fallend, konstant
            bewertung TEXT
        )
    """,
    
    # Behörden-Kontakte
    "behoerden_kontakte": """
        CREATE TABLE IF NOT EXISTS behoerden_kontakte (
            kontakt_id TEXT PRIMARY KEY,
            behoerde TEXT NOT NULL,
            sachbearbeiter TEXT NOT NULL,
            abteilung TEXT,
            telefon TEXT,
            email TEXT,
            zustaendig_fuer TEXT,
            bemerkungen TEXT
        )
    """,
    
    # Compliance-Historie
    "compliance_historie": """
        CREATE TABLE IF NOT EXISTS compliance_historie (
            historie_id TEXT PRIMARY KEY,
            bst_nr TEXT NOT NULL,
            anl_nr TEXT NOT NULL,
            pruefungsdatum TEXT NOT NULL,
            pruefungstyp TEXT NOT NULL,  -- Routine, Anlassbezogen, Audit
            ergebnis TEXT NOT NULL,  -- Konform, Abweichungen, Kritisch
            bewertung_punkte INTEGER,  -- 0-100
            feststellungen TEXT,
            empfehlungen TEXT,
            folgepruefung TEXT
        )
    """
}

# ============================================================================
# Daten-Generatoren
# ============================================================================

class DataGenerator:
    """Generiert realistische Test-Daten"""
    
    VERFAHRENSARTEN = [
        "Erstgenehmigung nach § 4 BImSchG",
        "Wesentliche Änderungsgenehmigung nach § 16 BImSchG",
        "Genehmigung nach § 19 BImSchG (vereinfachtes Verfahren)",
        "Teilgenehmigung nach § 8 BImSchG"
    ]
    
    STATUS_VERFAHREN = [
        "in_bearbeitung", "genehmigt", "genehmigt", "genehmigt",  # Mehr genehmigte
        "abgelehnt", "zurückgezogen"
    ]
    
    BEHOERDEN = [
        "Landesamt für Umwelt Brandenburg",
        "Landkreis Oberhavel - Untere Immissionsschutzbehörde",
        "Stadt Potsdam - Umweltamt",
        "Landkreis Barnim - Umwelt- und Naturschutzamt",
        "Ministerium für Landwirtschaft, Umwelt und Klimaschutz Brandenburg"
    ]
    
    MESSARTEN = [
        ("Lärm_Tag", "dB(A)", 60, 70),
        ("Lärm_Nacht", "dB(A)", 45, 55),
        ("PM10", "µg/m³", 30, 50),
        ("PM2.5", "µg/m³", 20, 40),
        ("NOx", "mg/m³", 100, 200),
        ("SO2", "mg/m³", 50, 350),
        ("CO", "mg/m³", 5, 10),
        ("Ammoniak", "mg/m³", 10, 30)
    ]
    
    AUFLAGEN_KATEGORIEN = {
        "Emissionsschutz": [
            "Einhaltung der Emissionsgrenzwerte gemäß TA Luft",
            "Jährliche Messung der Staubemissionen durch akkreditierte Messstelle",
            "Installation eines kontinuierlichen Emissionsüberwachungssystems",
            "Begrenzung der Betriebsstunden auf maximal 6.000 h/Jahr"
        ],
        "Lärmschutz": [
            "Einhaltung der Immissionsrichtwerte der TA Lärm",
            "Lärmkontingentierung gemäß DIN 45691",
            "Nachtbetrieb nur mit schallgedämpften Anlagenteilen",
            "Jährliche Lärmmessung durch Sachverständigen"
        ],
        "Naturschutz": [
            "Abschaltung bei Fledermausflug (April-Oktober, 1h vor Sonnenuntergang bis Sonnenaufgang)",
            "Rotmilan-Abschaltung während Brutzeit (März-August)",
            "Ökologische Baubegleitung während Bauphase",
            "Ersatzhabitate für betroffene Arten schaffen"
        ],
        "Arbeitsschutz": [
            "Betriebsanweisung gemäß BetrSichV erstellen",
            "Jährliche Unterweisung des Personals",
            "PSA bereitstellen und Verwendung überwachen",
            "Gefährdungsbeurteilung alle 2 Jahre aktualisieren"
        ]
    }
    
    MAENGELARTEN = [
        ("technisch", "Defekte Abluftfilteranlage"),
        ("technisch", "Undichte Stelle an Biogas-Fermenter"),
        ("organisatorisch", "Betriebstagebuch nicht vollständig geführt"),
        ("dokumentation", "Fehlende Wartungsnachweise"),
        ("grenzwert", "Lärmgrenzwert nachts überschritten"),
        ("grenzwert", "PM10-Emission über Grenzwert"),
        ("technisch", "Schalldämpfer beschädigt"),
        ("organisatorisch", "Notfallplan nicht aktualisiert")
    ]
    
    def __init__(self, bst_anl_pairs: List[tuple]):
        self.bst_anl_pairs = bst_anl_pairs
    
    def generate_verfahren(self, count: int) -> List[Dict]:
        """Generiert Genehmigungsverfahren"""
        verfahren = []
        
        for i in range(count):
            bst_nr, anl_nr = random.choice(self.bst_anl_pairs)
            
            antragsdatum = random_date(2015, 2024)
            antrag_dt = datetime.strptime(antragsdatum, "%Y-%m-%d")
            
            status = random.choice(self.STATUS_VERFAHREN)
            entscheidungsdatum = None
            
            if status != "in_bearbeitung":
                # Entscheidung 3-12 Monate nach Antrag
                tage_bis_entscheidung = random.randint(90, 365)
                entscheid_dt = antrag_dt + timedelta(days=tage_bis_entscheidung)
                entscheidungsdatum = entscheid_dt.strftime("%Y-%m-%d")
            
            verfahren_id = f"V-{i+1:06d}"
            
            verfahren.append({
                "verfahren_id": verfahren_id,
                "bst_nr": bst_nr,
                "anl_nr": anl_nr,
                "verfahrensart": random.choice(self.VERFAHRENSARTEN),
                "antragsdatum": antragsdatum,
                "entscheidungsdatum": entscheidungsdatum,
                "status": status,
                "behoerde": random.choice(self.BEHOERDEN),
                "aktenzeichen": f"{random.randint(10,99)}.{random.randint(1000,9999)}/{antrag_dt.year}",
                "antragsgrund": random.choice([
                    "Kapazitätserweiterung",
                    "Modernisierung bestehender Anlage",
                    "Zusätzliche Produktionslinie",
                    "Umstellung auf neue Technologie",
                    "Gesetzliche Anforderungen"
                ]) if random.random() > 0.3 else None,
                "oeffentliche_beteiligung": 1 if random.random() > 0.6 else 0,
                "uvp_erforderlich": 1 if random.random() > 0.8 else 0,
                "bemerkungen": None,
                "created_at": datetime.now().isoformat()
            })
        
        return verfahren
    
    def generate_bescheide(self, verfahren: List[Dict]) -> List[Dict]:
        """Generiert Bescheide für genehmigte Verfahren"""
        bescheide = []
        bescheid_counter = 1
        
        for v in verfahren:
            if v["status"] != "genehmigt" or not v["entscheidungsdatum"]:
                continue
            
            entscheid_dt = datetime.strptime(v["entscheidungsdatum"], "%Y-%m-%d")
            
            # Rechtskraft 1 Monat nach Bescheid
            rechtskraft_dt = entscheid_dt + timedelta(days=30)
            
            befristet = 1 if random.random() > 0.7 else 0
            befristung_bis = None
            
            if befristet:
                # Befristung 5-20 Jahre
                jahre = random.randint(5, 20)
                befristung_bis = (rechtskraft_dt + timedelta(days=365*jahre)).strftime("%Y-%m-%d")
            
            bescheide.append({
                "bescheid_id": f"B-{bescheid_counter:06d}",
                "verfahren_id": v["verfahren_id"],
                "bescheiddatum": v["entscheidungsdatum"],
                "bescheidtyp": "Genehmigung",
                "rechtskraft_datum": rechtskraft_dt.strftime("%Y-%m-%d"),
                "befristet": befristet,
                "befristung_bis": befristung_bis,
                "nebenbestimmungen": "Siehe Auflagenverzeichnis" if random.random() > 0.5 else None,
                "auflagen_anzahl": random.randint(3, 15),
                "rechtsgrundlage": "§ 6 Abs. 1 BImSchG i.V.m. 4. BImSchV",
                "pdf_pfad": f"/dokumente/bescheide/{bescheid_counter:06d}.pdf"
            })
            
            bescheid_counter += 1
        
        return bescheide
    
    def generate_auflagen(self, bescheide: List[Dict]) -> List[Dict]:
        """Generiert Auflagen für Bescheide"""
        auflagen = []
        auflagen_counter = 1
        
        for b in bescheide:
            anzahl = b["auflagen_anzahl"]
            
            for i in range(anzahl):
                kategorie = random.choice(list(self.AUFLAGEN_KATEGORIEN.keys()))
                auflagentext = random.choice(self.AUFLAGEN_KATEGORIEN[kategorie])
                
                messbar = 1 if kategorie in ["Emissionsschutz", "Lärmschutz"] else 0
                grenzwert = None
                einheit = None
                
                if messbar and random.random() > 0.5:
                    if "Lärm" in auflagentext:
                        grenzwert = random.choice([45, 50, 55, 60, 65])
                        einheit = "dB(A)"
                    elif "Emission" in auflagentext:
                        grenzwert = random.randint(10, 200)
                        einheit = "mg/m³"
                
                # Umsetzungsfrist
                bescheid_dt = datetime.strptime(b["bescheiddatum"], "%Y-%m-%d")
                frist_tage = random.randint(90, 730)  # 3 Monate bis 2 Jahre
                umsetzungsfrist = (bescheid_dt + timedelta(days=frist_tage)).strftime("%Y-%m-%d")
                
                # Status
                if datetime.now() > datetime.strptime(umsetzungsfrist, "%Y-%m-%d"):
                    status = random.choice(["umgesetzt", "umgesetzt", "überfällig"])
                else:
                    status = random.choice(["offen", "offen", "umgesetzt"])
                
                auflagen.append({
                    "auflagen_id": f"A-{auflagen_counter:06d}",
                    "bescheid_id": b["bescheid_id"],
                    "auflage_nr": i + 1,
                    "auflagentext": auflagentext,
                    "kategorie": kategorie,
                    "messbar": messbar,
                    "grenzwert": grenzwert,
                    "einheit": einheit,
                    "umsetzungsfrist": umsetzungsfrist,
                    "status": status
                })
                
                auflagen_counter += 1
        
        return auflagen
    
    def generate_ueberwachung(self, count: int) -> List[Dict]:
        """Generiert Überwachungsmaßnahmen"""
        ueberwachung = []
        
        for i in range(count):
            bst_nr, anl_nr = random.choice(self.bst_anl_pairs)
            
            geplant_datum = random_date(2020, 2025)
            geplant_dt = datetime.strptime(geplant_datum, "%Y-%m-%d")
            
            # Status
            if geplant_dt < datetime.now():
                status = random.choice(["durchgeführt", "durchgeführt", "verschoben", "abgesagt"])
            else:
                status = "geplant"
            
            durchgefuehrt_datum = None
            ergebnis = None
            naechste_pruefung = None
            
            if status == "durchgeführt":
                # Durchführung innerhalb 14 Tage nach Planung
                durchgefuehrt_dt = geplant_dt + timedelta(days=random.randint(0, 14))
                durchgefuehrt_datum = durchgefuehrt_dt.strftime("%Y-%m-%d")
                
                ergebnis = random.choice([
                    "bestanden", "bestanden", "bestanden",
                    "mängel_festgestellt", "nachbesserung_erforderlich"
                ])
                
                # Nächste Prüfung in 1-3 Jahren
                naechste_dt = durchgefuehrt_dt + timedelta(days=365*random.randint(1, 3))
                naechste_pruefung = naechste_dt.strftime("%Y-%m-%d")
            
            ueberwachung.append({
                "ueberwachung_id": f"U-{i+1:06d}",
                "bst_nr": bst_nr,
                "anl_nr": anl_nr,
                "ueberwachungsart": random.choice([
                    "Routineinspektion",
                    "Routineinspektion",
                    "Anlassinspektion",
                    "Emissionsmessung",
                    "Lärmmessung"
                ]),
                "geplant_datum": geplant_datum,
                "durchgefuehrt_datum": durchgefuehrt_datum,
                "status": status,
                "behoerde": random.choice(self.BEHOERDEN),
                "pruefumfang": random.choice([
                    "Vollständige Anlagenbegehung",
                    "Dokumentenprüfung",
                    "Betriebstagebuchkontrolle",
                    "Emissionsmessung gemäß TA Luft",
                    "Lärmmessung gemäß TA Lärm"
                ]),
                "ergebnis": ergebnis,
                "naechste_pruefung": naechste_pruefung,
                "bemerkungen": None
            })
        
        return ueberwachung
    
    def generate_messungen(self, count: int) -> List[Dict]:
        """Generiert Messungen"""
        messungen = []
        
        for i in range(count):
            bst_nr, anl_nr = random.choice(self.bst_anl_pairs)
            
            messart, einheit, base_min, base_max = random.choice(self.MESSARTEN)
            
            messdatum = random_date(2020, 2025)
            messzeit = random_time()
            
            # Grenzwert
            grenzwert = base_max if random.random() > 0.3 else None
            
            # Messwert (meist unter Grenzwert)
            if random.random() > 0.85:  # 15% Überschreitungen
                messwert = round(random.uniform(base_max, base_max * 1.3), 2)
                ueberschreitung = 1
            else:
                messwert = round(random.uniform(base_min, base_max * 0.9), 2)
                ueberschreitung = 0
            
            messungen.append({
                "messung_id": f"M-{i+1:06d}",
                "bst_nr": bst_nr,
                "anl_nr": anl_nr,
                "messart": messart,
                "messdatum": messdatum,
                "messzeit": messzeit,
                "messort": random.choice([
                    "Anlagengrenze Nord",
                    "Anlagengrenze Süd",
                    "Wohnbebauung nächstgelegen",
                    "Schornstein",
                    "Abluftkamin"
                ]),
                "messwert": messwert,
                "einheit": einheit,
                "grenzwert": grenzwert,
                "ueberschreitung": ueberschreitung,
                "messmethode": random.choice([
                    "DIN EN ISO 9612", "TA Lärm", "VDI 2081", "DIN EN 12341"
                ]),
                "messgeraet": random.choice([
                    "Schallpegelmesser Typ 1", "Staubmessgerät isokinetisch",
                    "Gasmessgerät FTIR", "Partikelzähler"
                ]),
                "messstelle": random.choice([
                    "TÜV Nord", "DEKRA", "IHK-Sachverständiger",
                    "Landeslabor Brandenburg"
                ]),
                "wetterbedingungen": random.choice([
                    "trocken, windstill", "bewölkt, leichter Wind",
                    "Regen", "sonnig, windig"
                ]) if "Lärm" in messart else None,
                "bemerkungen": None
            })
        
        return messungen
    
    def generate_maengel(self, ueberwachung: List[Dict]) -> List[Dict]:
        """Generiert Mängel basierend auf Überwachungen"""
        maengel = []
        maengel_counter = 1
        
        # Nur für durchgeführte Überwachungen mit Mängeln
        ueberwachung_mit_maengeln = [
            u for u in ueberwachung 
            if u["ergebnis"] in ["mängel_festgestellt", "nachbesserung_erforderlich"]
        ]
        
        for u in ueberwachung_mit_maengeln:
            # 1-3 Mängel pro Überwachung
            anzahl_maengel = random.randint(1, 3)
            
            for _ in range(anzahl_maengel):
                mangelart, beschreibung = random.choice(self.MAENGELARTEN)
                
                schweregrad = random.choice([
                    "gering", "gering", "mittel", "mittel", "schwer", "kritisch"
                ])
                
                festgestellt_dt = datetime.strptime(u["durchgefuehrt_datum"], "%Y-%m-%d")
                
                # Frist abhängig von Schweregrad
                if schweregrad == "kritisch":
                    frist_tage = random.randint(7, 30)
                elif schweregrad == "schwer":
                    frist_tage = random.randint(30, 90)
                elif schweregrad == "mittel":
                    frist_tage = random.randint(90, 180)
                else:
                    frist_tage = random.randint(180, 365)
                
                frist_beseitigung = (festgestellt_dt + timedelta(days=frist_tage)).strftime("%Y-%m-%d")
                
                # Status
                if datetime.now() > datetime.strptime(frist_beseitigung, "%Y-%m-%d"):
                    status = random.choice(["behoben", "behoben", "eskaliert"])
                    beseitigt_datum = (festgestellt_dt + timedelta(days=random.randint(10, max(10, frist_tage)))).strftime("%Y-%m-%d")
                else:
                    status = random.choice(["offen", "in_bearbeitung"])
                    beseitigt_datum = None
                
                maengel.append({
                    "mangel_id": f"MG-{maengel_counter:06d}",
                    "ueberwachung_id": u["ueberwachung_id"],
                    "bst_nr": u["bst_nr"],
                    "anl_nr": u["anl_nr"],
                    "festgestellt_datum": u["durchgefuehrt_datum"],
                    "mangelart": mangelart,
                    "schweregrad": schweregrad,
                    "beschreibung": beschreibung,
                    "massnahmen_erforderlich": random.choice([
                        "Reparatur durchführen",
                        "Dokumentation nachreichen",
                        "Schulung des Personals",
                        "Technische Nachrüstung",
                        "Betriebsanweisung aktualisieren"
                    ]),
                    "frist_beseitigung": frist_beseitigung,
                    "beseitigt_datum": beseitigt_datum,
                    "status": status
                })
                
                maengel_counter += 1
        
        return maengel
    
    # ========================================================================
    # NEUE GENERATOREN - Phase 2
    # ========================================================================
    
    def generate_dokumente(self, verfahren: List[Dict], messungen: List[Dict], 
                          ueberwachung: List[Dict], count_additional: int = 500) -> List[Dict]:
        """Generiert Dokumente für alle Entitäten"""
        dokumente = []
        dok_counter = 1
        
        DOKUMENTTYPEN = {
            "verfahren": ["Antrag", "Gutachten", "Stellungnahme", "Genehmigungsbescheid"],
            "messung": ["Messbericht", "Kalibrierprotokoll", "Analyseprotokoll"],
            "ueberwachung": ["Inspektionsbericht", "Fotodokumentation", "Prüfprotokoll"],
            "allgemein": ["Plan", "Betriebsanweisung", "Sicherheitsdatenblatt", "Wartungsvertrag"]
        }
        
        # Dokumente für Verfahren
        for v in verfahren:
            anzahl = random.randint(2, 5)
            for _ in range(anzahl):
                typ = random.choice(DOKUMENTTYPEN["verfahren"])
                erstellt = datetime.strptime(v["antragsdatum"], "%Y-%m-%d") + timedelta(days=random.randint(0, 30))
                
                dokumente.append({
                    "dokument_id": f"DOK-{dok_counter:06d}",
                    "bst_nr": v["bst_nr"],
                    "anl_nr": v["anl_nr"],
                    "dokumenttyp": typ,
                    "titel": f"{typ} - Verfahren {v['verfahren_id']}",
                    "erstellt_datum": erstellt.strftime("%Y-%m-%d"),
                    "gueltig_bis": None,
                    "dateipfad": f"/dokumente/{v['bst_nr']}/{v['anl_nr']}/{dok_counter:06d}.pdf",
                    "dateigroesse_kb": random.randint(100, 5000),
                    "ersteller": random.choice(["Sachverständiger Dr. Müller", "Gutachterbüro Schmidt", 
                                               "TÜV Rheinland", "DEKRA", "Betreiber"]),
                    "aktenzeichen": v.get("aktenzeichen"),
                    "status": "aktiv",
                    "bemerkungen": None
                })
                dok_counter += 1
        
        # Dokumente für Messungen
        for m in random.sample(messungen, min(len(messungen), 200)):
            dokumente.append({
                "dokument_id": f"DOK-{dok_counter:06d}",
                "bst_nr": m["bst_nr"],
                "anl_nr": m["anl_nr"],
                "dokumenttyp": random.choice(DOKUMENTTYPEN["messung"]),
                "titel": f"Messbericht {m['messart']} - {m['messdatum']}",
                "erstellt_datum": m["messdatum"],
                "gueltig_bis": None,
                "dateipfad": f"/dokumente/{m['bst_nr']}/{m['anl_nr']}/{dok_counter:06d}.pdf",
                "dateigroesse_kb": random.randint(50, 2000),
                "ersteller": random.choice(["TÜV SÜD", "Prüfstelle Nord", "Labor West"]),
                "aktenzeichen": None,
                "status": "aktiv",
                "bemerkungen": None
            })
            dok_counter += 1
        
        # Dokumente für Überwachung
        for u in ueberwachung:
            if u["status"] == "durchgefuehrt":
                dokumente.append({
                    "dokument_id": f"DOK-{dok_counter:06d}",
                    "bst_nr": u["bst_nr"],
                    "anl_nr": u["anl_nr"],
                    "dokumenttyp": random.choice(DOKUMENTTYPEN["ueberwachung"]),
                    "titel": f"Inspektionsbericht - {u['durchgefuehrt_datum']}",
                    "erstellt_datum": u["durchgefuehrt_datum"],
                    "gueltig_bis": None,
                    "dateipfad": f"/dokumente/{u['bst_nr']}/{u['anl_nr']}/{dok_counter:06d}.pdf",
                    "dateigroesse_kb": random.randint(200, 3000),
                    "ersteller": u.get("durchgefuehrt_von", "Behörde"),
                    "aktenzeichen": None,
                    "status": "aktiv",
                    "bemerkungen": None
                })
                dok_counter += 1
        
        return dokumente
    
    def generate_ansprechpartner(self, bst_anl_pairs: List[Tuple], count: int = 300) -> List[Dict]:
        """Generiert Ansprechpartner für Anlagen"""
        ansprechpartner = []
        
        FUNKTIONEN = [
            "Betriebsleiter", "Umweltschutzbeauftragter", "Immissionsschutzbeauftragter",
            "Technischer Leiter", "Sicherheitsbeauftragter", "Geschäftsführer"
        ]
        
        VORNAMEN = ["Thomas", "Michael", "Andreas", "Stefan", "Christian", "Markus", 
                   "Julia", "Sandra", "Petra", "Sabine", "Anna", "Lisa"]
        NACHNAMEN = ["Müller", "Schmidt", "Weber", "Meyer", "Wagner", "Becker",
                    "Schulz", "Hoffmann", "Koch", "Richter"]
        
        sample_anlagen = random.sample(bst_anl_pairs, min(len(bst_anl_pairs), count))
        
        for idx, (bst_nr, anl_nr) in enumerate(sample_anlagen, 1):
            # 1-2 Ansprechpartner pro Anlage
            for _ in range(random.randint(1, 2)):
                vorname = random.choice(VORNAMEN)
                nachname = random.choice(NACHNAMEN)
                funktion = random.choice(FUNKTIONEN)
                
                ansprechpartner.append({
                    "ansprechpartner_id": f"AP-{len(ansprechpartner)+1:06d}",
                    "bst_nr": bst_nr,
                    "anl_nr": anl_nr,
                    "name": f"{vorname} {nachname}",
                    "funktion": funktion,
                    "telefon": f"0{random.randint(30,99)}{random.randint(1000000,9999999)}",
                    "email": f"{vorname.lower()}.{nachname.lower()}@firma.de",
                    "mobil": f"015{random.randint(1,9)}{random.randint(10000000,99999999)}",
                    "verfuegbarkeit": random.choice(["Mo-Fr 8-17 Uhr", "Mo-Fr 7-16 Uhr", "24/7"]),
                    "notfallkontakt": 1 if funktion == "Betriebsleiter" else 0,
                    "aktiv": 1
                })
        
        return ansprechpartner
    
    def generate_wartung(self, bst_anl_pairs: List[Tuple], count: int = 600) -> List[Dict]:
        """Generiert Wartungshistorie für Anlagen"""
        wartungen = []
        
        WARTUNGSARTEN = [
            "Routineinspektion", "Kalibrierung Messgeräte", "Filter-Austausch",
            "Reparatur Lüftung", "Software-Update", "Sicherheitsprüfung",
            "Dichtigkeitsprüfung", "Brandschutzprüfung"
        ]
        
        FIRMEN = [
            "Wartungsservice Nord GmbH", "TechService 24", "Industrie-Wartung Schmidt",
            "Anlagentechnik Meyer", "Betreiber (Eigenwartung)"
        ]
        
        sample_anlagen = random.sample(bst_anl_pairs, min(len(bst_anl_pairs), count))
        
        for idx, (bst_nr, anl_nr) in enumerate(sample_anlagen, 1):
            # 1-3 Wartungen pro Anlage in den letzten 2 Jahren
            anzahl = random.randint(1, 3)
            
            for _ in range(anzahl):
                geplant = datetime.now() - timedelta(days=random.randint(30, 730))
                
                # 80% durchgeführt
                if random.random() > 0.2:
                    durchgefuehrt = geplant + timedelta(days=random.randint(0, 14))
                    status = "durchgefuehrt"
                    naechste = durchgefuehrt + timedelta(days=random.randint(90, 365))
                else:
                    durchgefuehrt = None
                    status = random.choice(["geplant", "verschoben"])
                    naechste = geplant + timedelta(days=random.randint(30, 180))
                
                wartungen.append({
                    "wartung_id": f"W-{len(wartungen)+1:06d}",
                    "bst_nr": bst_nr,
                    "anl_nr": anl_nr,
                    "wartungsart": random.choice(WARTUNGSARTEN),
                    "geplant_datum": geplant.strftime("%Y-%m-%d"),
                    "durchgefuehrt_datum": durchgefuehrt.strftime("%Y-%m-%d") if durchgefuehrt else None,
                    "durchgefuehrt_von": random.choice(FIRMEN) if durchgefuehrt else None,
                    "kosten": round(random.uniform(200, 5000), 2) if durchgefuehrt else None,
                    "naechste_wartung": naechste.strftime("%Y-%m-%d"),
                    "status": status,
                    "beschreibung": f"Planmäßige {random.choice(WARTUNGSARTEN).lower()}",
                    "massnahmen": random.choice([
                        "Filter gewechselt, Funktion geprüft",
                        "Kalibrierung durchgeführt, Protokoll erstellt",
                        "Sichtprüfung, keine Mängel festgestellt",
                        "Verschleißteile getauscht"
                    ]) if durchgefuehrt else None
                })
        
        return wartungen
    
    def generate_messreihen(self, messungen: List[Dict]) -> List[Dict]:
        """Generiert Messreihen (aggregierte Zeitreihen) aus Einzelmessungen"""
        messreihen = []
        
        # Gruppiere Messungen nach Anlage und Messart
        grouped = {}
        for m in messungen:
            key = (m["bst_nr"], m["anl_nr"], m["messart"])
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(m)
        
        messreihe_counter = 1
        
        for (bst_nr, anl_nr, messart), gruppe in grouped.items():
            if len(gruppe) < 3:  # Mindestens 3 Messungen für eine Reihe
                continue
            
            # Sortiere nach Datum
            gruppe_sorted = sorted(gruppe, key=lambda x: x["messdatum"])
            
            werte = [m["messwert"] for m in gruppe_sorted]
            zeitraum_von = gruppe_sorted[0]["messdatum"]
            zeitraum_bis = gruppe_sorted[-1]["messdatum"]
            
            mittelwert = sum(werte) / len(werte)
            maximalwert = max(werte)
            minimalwert = min(werte)
            
            # Standardabweichung
            varianz = sum((x - mittelwert) ** 2 for x in werte) / len(werte)
            standardabweichung = varianz ** 0.5
            
            # Überschreitungen zählen
            ueberschreitungen = sum(1 for m in gruppe_sorted if m["ueberschreitung"] == 1)
            
            # Trend bestimmen (einfach: erster vs letzter Wert)
            if werte[-1] > werte[0] * 1.1:
                trend = "steigend"
            elif werte[-1] < werte[0] * 0.9:
                trend = "fallend"
            else:
                trend = "konstant"
            
            # Bewertung
            if ueberschreitungen > len(werte) * 0.2:
                bewertung = "kritisch"
            elif ueberschreitungen > 0:
                bewertung = "auffällig"
            else:
                bewertung = "unauffällig"
            
            messreihen.append({
                "messreihe_id": f"MR-{messreihe_counter:06d}",
                "bst_nr": bst_nr,
                "anl_nr": anl_nr,
                "messart": messart,
                "zeitraum_von": zeitraum_von,
                "zeitraum_bis": zeitraum_bis,
                "anzahl_messungen": len(gruppe),
                "mittelwert": round(mittelwert, 2),
                "maximalwert": round(maximalwert, 2),
                "minimalwert": round(minimalwert, 2),
                "standardabweichung": round(standardabweichung, 2),
                "ueberschreitungen_anzahl": ueberschreitungen,
                "trend": trend,
                "bewertung": bewertung
            })
            
            messreihe_counter += 1
        
        return messreihen
    
    def generate_behoerden_kontakte(self, count: int = 50) -> List[Dict]:
        """Generiert Behörden-Kontaktdaten"""
        kontakte = []
        
        BEHOERDEN = [
            "Landesamt für Umwelt Brandenburg",
            "Bezirksregierung Düsseldorf",
            "Gewerbeaufsichtsamt Berlin",
            "Landkreis Oberhavel",
            "Stadt Oranienburg",
            "Landkreis Barnim"
        ]
        
        ABTEILUNGEN = [
            "Immissionsschutz", "Anlagensicherheit", "Luftreinhaltung",
            "Lärmschutz", "Genehmigungsverfahren", "Überwachung"
        ]
        
        VORNAMEN = ["Dr. Petra", "Michael", "Susanne", "Thomas", "Andrea", "Stefan"]
        NACHNAMEN = ["Hoffmann", "Weber", "Schulze", "Richter", "Klein", "Wolf"]
        
        for i in range(count):
            vorname = random.choice(VORNAMEN)
            nachname = random.choice(NACHNAMEN)
            behoerde = random.choice(BEHOERDEN)
            abteilung = random.choice(ABTEILUNGEN)
            
            kontakte.append({
                "kontakt_id": f"BK-{i+1:06d}",
                "behoerde": behoerde,
                "sachbearbeiter": f"{vorname} {nachname}",
                "abteilung": abteilung,
                "telefon": f"033{random.randint(0,9)}{random.randint(100000,999999)}",
                "email": f"{nachname.lower()}@{behoerde.lower().replace(' ', '-')}.de",
                "zustaendig_fuer": random.choice([
                    "Genehmigungsverfahren nach BImSchG",
                    "Überwachung genehmigter Anlagen",
                    "Messprogram-Genehmigungen",
                    "Beschwerdemanagement",
                    "Anlagensicherheit"
                ]),
                "bemerkungen": None
            })
        
        return kontakte
    
    def generate_compliance_historie(self, bst_anl_pairs: List[Tuple], count: int = 400) -> List[Dict]:
        """Generiert Compliance-Prüfungshistorie"""
        historie = []
        
        PRUEFUNGSTYPEN = [
            "Routine-Audit", "Anlassbezogene Prüfung", "Zertifizierungs-Audit",
            "Nachprüfung", "Stichproben-Kontrolle"
        ]
        
        sample_anlagen = random.sample(bst_anl_pairs, min(len(bst_anl_pairs), count))
        
        for idx, (bst_nr, anl_nr) in enumerate(sample_anlagen, 1):
            # 1-2 Prüfungen pro Anlage
            for _ in range(random.randint(1, 2)):
                pruefungsdatum = datetime.now() - timedelta(days=random.randint(30, 730))
                
                # Bewertung 0-100 Punkte
                punkte = random.randint(60, 100)
                
                if punkte >= 90:
                    ergebnis = "Konform"
                    feststellungen = "Keine wesentlichen Abweichungen"
                    empfehlungen = "Weiterführung der bisherigen Praxis"
                elif punkte >= 75:
                    ergebnis = "Abweichungen"
                    feststellungen = random.choice([
                        "Kleinere Dokumentationslücken",
                        "Wartungsintervalle teilweise überschritten",
                        "Schulungsnachweise nicht vollständig"
                    ])
                    empfehlungen = "Nachbesserung innerhalb 3 Monate"
                else:
                    ergebnis = "Kritisch"
                    feststellungen = random.choice([
                        "Mehrere Grenzwertüberschreitungen",
                        "Sicherheitsmängel festgestellt",
                        "Auflagen nicht vollständig umgesetzt"
                    ])
                    empfehlungen = "Sofortige Maßnahmen erforderlich, Nachprüfung in 4 Wochen"
                
                folgepruefung = (pruefungsdatum + timedelta(days=random.randint(180, 365))).strftime("%Y-%m-%d")
                
                historie.append({
                    "historie_id": f"CH-{len(historie)+1:06d}",
                    "bst_nr": bst_nr,
                    "anl_nr": anl_nr,
                    "pruefungsdatum": pruefungsdatum.strftime("%Y-%m-%d"),
                    "pruefungstyp": random.choice(PRUEFUNGSTYPEN),
                    "ergebnis": ergebnis,
                    "bewertung_punkte": punkte,
                    "feststellungen": feststellungen,
                    "empfehlungen": empfehlungen,
                    "folgepruefung": folgepruefung
                })
        
        return historie

# ============================================================================
# Hauptfunktion
# ============================================================================

def create_test_databases():
    """Erstellt alle Test-Datenbanken mit randomisierten Daten"""
    
    print("="*80)
    print("  Immissionsschutz Test-Datenbanken Generator")
    print("="*80)
    print()
    
    # 1. BST/ANL Paare aus bestehenden DBs extrahieren
    print("📚 Lade Referenzdaten aus BImSchG und WKA...")
    
    bst_anl_pairs = []
    
    # BImSchG
    if BIMSCHG_DB.exists():
        conn = sqlite3.connect(BIMSCHG_DB)
        cursor = conn.cursor()
        rows = cursor.execute("SELECT CAST(bst_nr AS TEXT), anl_nr FROM bimschg LIMIT 500").fetchall()
        bst_anl_pairs.extend(rows)
        conn.close()
        print(f"✅ {len(rows)} Anlagen aus BImSchG geladen")
    
    # WKA
    if WKA_DB.exists():
        conn = sqlite3.connect(WKA_DB)
        cursor = conn.cursor()
        rows = cursor.execute("SELECT bst_nr, anl_nr FROM wka LIMIT 500").fetchall()
        bst_anl_pairs.extend(rows)
        conn.close()
        print(f"✅ {len(rows)} Anlagen aus WKA geladen")
    
    print(f"📊 Gesamt: {len(bst_anl_pairs)} BST/ANL Paare verfügbar")
    print()
    
    if not bst_anl_pairs:
        print("❌ Keine Referenzdaten gefunden!")
        return
    
    # 2. Generator initialisieren
    generator = DataGenerator(bst_anl_pairs)
    
    # 3. Datenbank erstellen
    db_path = TEST_DB_DIR / "immissionsschutz_test.sqlite"
    
    print(f"🗄️  Erstelle Datenbank: {db_path}")
    print()
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Schemas erstellen
    print("📋 Erstelle Tabellen...")
    for table_name, schema in SCHEMAS.items():
        cursor.execute(schema)
        print(f"   ✅ {table_name}")
    
    conn.commit()
    print()
    
    # 4. Daten generieren und einfügen
    print("🎲 Generiere Testdaten...")
    print()
    
    # Verfahren
    print("   📝 Genehmigungsverfahren...")
    verfahren = generator.generate_verfahren(count=800)
    for v in verfahren:
        placeholders = ", ".join(["?"] * len(v))
        cursor.execute(
            f"INSERT INTO genehmigungsverfahren VALUES ({placeholders})",
            tuple(v.values())
        )
    print(f"   ✅ {len(verfahren)} Verfahren erstellt")
    
    # Bescheide
    print("   📄 Bescheide...")
    bescheide = generator.generate_bescheide(verfahren)
    for b in bescheide:
        placeholders = ", ".join(["?"] * len(b))
        cursor.execute(
            f"INSERT INTO bescheide VALUES ({placeholders})",
            tuple(b.values())
        )
    print(f"   ✅ {len(bescheide)} Bescheide erstellt")
    
    # Auflagen
    print("   📌 Auflagen...")
    auflagen = generator.generate_auflagen(bescheide)
    for a in auflagen:
        placeholders = ", ".join(["?"] * len(a))
        cursor.execute(
            f"INSERT INTO auflagen VALUES ({placeholders})",
            tuple(a.values())
        )
    print(f"   ✅ {len(auflagen)} Auflagen erstellt")
    
    # Überwachung
    print("   🔍 Überwachungsmaßnahmen...")
    ueberwachung = generator.generate_ueberwachung(count=1200)
    for u in ueberwachung:
        placeholders = ", ".join(["?"] * len(u))
        cursor.execute(
            f"INSERT INTO ueberwachung VALUES ({placeholders})",
            tuple(u.values())
        )
    print(f"   ✅ {len(ueberwachung)} Überwachungen erstellt")
    
    # Messungen
    print("   📊 Messungen...")
    messungen = generator.generate_messungen(count=3000)
    for m in messungen:
        placeholders = ", ".join(["?"] * len(m))
        cursor.execute(
            f"INSERT INTO messungen VALUES ({placeholders})",
            tuple(m.values())
        )
    print(f"   ✅ {len(messungen)} Messungen erstellt")
    
    # Mängel
    print("   ⚠️  Mängel...")
    maengel = generator.generate_maengel(ueberwachung)
    for mg in maengel:
        placeholders = ", ".join(["?"] * len(mg))
        cursor.execute(
            f"INSERT INTO maengel VALUES ({placeholders})",
            tuple(mg.values())
        )
    print(f"   ✅ {len(maengel)} Mängel erstellt")
    
    # NEUE TABELLEN - Phase 2
    print()
    print("   🆕 Erweiterte Tabellen werden befüllt...")
    
    # Dokumente
    print("   📁 Dokumente...")
    dokumente = generator.generate_dokumente(verfahren, messungen, ueberwachung, count_additional=500)
    for d in dokumente:
        placeholders = ", ".join(["?"] * len(d))
        cursor.execute(
            f"INSERT INTO dokumente VALUES ({placeholders})",
            tuple(d.values())
        )
    print(f"   ✅ {len(dokumente)} Dokumente erstellt")
    
    # Ansprechpartner
    print("   👤 Ansprechpartner...")
    ansprechpartner = generator.generate_ansprechpartner(bst_anl_pairs, count=300)
    for ap in ansprechpartner:
        placeholders = ", ".join(["?"] * len(ap))
        cursor.execute(
            f"INSERT INTO ansprechpartner VALUES ({placeholders})",
            tuple(ap.values())
        )
    print(f"   ✅ {len(ansprechpartner)} Ansprechpartner erstellt")
    
    # Wartung
    print("   🔧 Wartungshistorie...")
    wartungen = generator.generate_wartung(bst_anl_pairs, count=600)
    for w in wartungen:
        placeholders = ", ".join(["?"] * len(w))
        cursor.execute(
            f"INSERT INTO wartung VALUES ({placeholders})",
            tuple(w.values())
        )
    print(f"   ✅ {len(wartungen)} Wartungen erstellt")
    
    # Messreihen
    print("   📈 Messreihen (Zeitreihen)...")
    messreihen = generator.generate_messreihen(messungen)
    for mr in messreihen:
        placeholders = ", ".join(["?"] * len(mr))
        cursor.execute(
            f"INSERT INTO messreihen VALUES ({placeholders})",
            tuple(mr.values())
        )
    print(f"   ✅ {len(messreihen)} Messreihen erstellt")
    
    # Behörden-Kontakte
    print("   🏛️  Behörden-Kontakte...")
    behoerden = generator.generate_behoerden_kontakte(count=50)
    for bk in behoerden:
        placeholders = ", ".join(["?"] * len(bk))
        cursor.execute(
            f"INSERT INTO behoerden_kontakte VALUES ({placeholders})",
            tuple(bk.values())
        )
    print(f"   ✅ {len(behoerden)} Behörden-Kontakte erstellt")
    
    # Compliance-Historie
    print("   📋 Compliance-Historie...")
    compliance = generator.generate_compliance_historie(bst_anl_pairs, count=400)
    for ch in compliance:
        placeholders = ", ".join(["?"] * len(ch))
        cursor.execute(
            f"INSERT INTO compliance_historie VALUES ({placeholders})",
            tuple(ch.values())
        )
    print(f"   ✅ {len(compliance)} Compliance-Prüfungen erstellt")
    
    conn.commit()
    
    # 5. Statistiken
    print()
    print("="*80)
    print("✅ Datenbank erfolgreich erstellt!")
    print("="*80)
    print(f"📍 Pfad: {db_path}")
    print(f"💾 Größe: {db_path.stat().st_size / (1024*1024):.2f} MB")
    print()
    print("📊 Datensätze:")
    print(f"   - Genehmigungsverfahren: {len(verfahren):,}")
    print(f"   - Bescheide: {len(bescheide):,}")
    print(f"   - Auflagen: {len(auflagen):,}")
    print(f"   - Überwachungen: {len(ueberwachung):,}")
    print(f"   - Messungen: {len(messungen):,}")
    print(f"   - Mängel: {len(maengel):,}")
    print()
    print("📊 Erweiterte Tabellen:")
    print(f"   - Dokumente: {len(dokumente):,}")
    print(f"   - Ansprechpartner: {len(ansprechpartner):,}")
    print(f"   - Wartungen: {len(wartungen):,}")
    print(f"   - Messreihen: {len(messreihen):,}")
    print(f"   - Behörden-Kontakte: {len(behoerden):,}")
    print(f"   - Compliance-Historie: {len(compliance):,}")
    print("="*80)
    
    # 6. Schema-Dokumentation speichern
    schema_doc = {
        "database": "immissionsschutz_test.sqlite",
        "description": "Vollständige relationale Immissionsschutz-Datenbank für Agenten-Tests",
        "created": datetime.now().isoformat(),
        "tables": {}
    }
    
    for table_name in SCHEMAS.keys():
        count = cursor.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        columns = cursor.execute(f"PRAGMA table_info({table_name})").fetchall()
        
        schema_doc["tables"][table_name] = {
            "row_count": count,
            "columns": [
                {
                    "name": col[1],
                    "type": col[2],
                    "not_null": bool(col[3]),
                    "primary_key": bool(col[5])
                }
                for col in columns
            ]
        }
    
    schema_file = PROJECT_ROOT / "docs" / "database_schema_immissionsschutz_test.json"
    with open(schema_file, 'w', encoding='utf-8') as f:
        json.dump(schema_doc, f, indent=2, ensure_ascii=False)
    
    print(f"📄 Schema-Dokumentation: {schema_file}")
    print()
    
    conn.close()


if __name__ == "__main__":
    create_test_databases()
