"""
ImmissionsschutzAgent TestServer Extension

Spezialisierte Implementierung des DatabaseAgent für die Immissionsschutz-Domäne.
Erweitert die generische DatabaseAgentTestServerExtension mit domänen-spezifischen
Methoden für Grenzwertprüfungen, Trend-Analysen und Compliance-Reports.

Design:
    - Erbt von DatabaseAgentTestServerExtension
    - Nutzt TA Luft / TA Lärm Grenzwerte
    - Implementiert domänen-spezifische Analysen
    - Generiert formatierte Reports
    
Version: 1.0
Autor: VERITAS Team
Datum: 18. Oktober 2025
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from statistics import mean, stdev

try:
    from .database_agent_testserver_extension import (
        DatabaseAgentTestServerExtension,
        EntityType,
        QueryResult,
        ComplianceResult,
        ComplianceStatus
    )
    from .test_server_client import TestServerConfig
except ImportError:
    from database_agent_testserver_extension import (
        DatabaseAgentTestServerExtension,
        EntityType,
        QueryResult,
        ComplianceResult,
        ComplianceStatus
    )
    from test_server_client import TestServerConfig


# ============================================================================
# DOMAIN-SPECIFIC ENUMS
# ============================================================================

class GrenzwertTyp(str, Enum):
    """Typen von Grenzwerten im Immissionsschutz"""
    LUFT_TAGESMITTEL = "luft_tagesmittel"
    LUFT_JAHRESMITTEL = "luft_jahresmittel"
    LUFT_KURZZEITWERT = "luft_kurzzeitwert"
    LAERM_TAG = "laerm_tag"
    LAERM_NACHT = "laerm_nacht"
    LAERM_SPITZE = "laerm_spitze"


class TrendRichtung(str, Enum):
    """Trend-Richtungen für Messreihen"""
    STEIGEND = "steigend"
    FALLEND = "fallend"
    STABIL = "stabil"
    SCHWANKEND = "schwankend"
    UNBEKANNT = "unbekannt"


class RisikoKlasse(str, Enum):
    """Risiko-Klassifizierung"""
    SEHR_GERING = "sehr_gering"
    GERING = "gering"
    MITTEL = "mittel"
    HOCH = "hoch"
    SEHR_HOCH = "sehr_hoch"


# ============================================================================
# DOMAIN-SPECIFIC RESULT OBJECTS
# ============================================================================

@dataclass
class GrenzwertPruefung:
    """Ergebnis einer Grenzwertprüfung"""
    messart: str
    grenzwert: float
    grenzwert_typ: GrenzwertTyp
    aktuelle_messwerte: List[float]
    mittelwert: float
    maximum: float
    ueberschreitungen: int
    ueberschreitungen_prozent: float
    status: str  # "OK", "GRENZWERTIG", "UEBERSCHREITUNG"
    bemerkungen: List[str] = field(default_factory=list)
    
    @property
    def ist_kritisch(self) -> bool:
        return self.status == "UEBERSCHREITUNG"
    
    @property
    def grenzwertausnutzung(self) -> float:
        """Prozentuale Ausnutzung des Grenzwerts"""
        return (self.mittelwert / self.grenzwert) * 100 if self.grenzwert > 0 else 0.0


@dataclass
class TrendAnalyse:
    """Trend-Analyse einer Messreihe"""
    messart: str
    zeitraum_von: str
    zeitraum_bis: str
    anzahl_messungen: int
    trend_richtung: TrendRichtung
    trend_staerke: float  # 0.0 - 1.0
    mittelwert: float
    standardabweichung: float
    minimum: float
    maximum: float
    prognose_30_tage: Optional[float] = None
    empfehlungen: List[str] = field(default_factory=list)
    
    @property
    def ist_kritischer_trend(self) -> bool:
        return self.trend_richtung == TrendRichtung.STEIGEND and self.trend_staerke > 0.6


@dataclass
class ComplianceReport:
    """Umfassender Compliance-Report für eine Anlage"""
    bst_nr: str
    anl_nr: str
    anlagen_name: str
    erstellt_am: str
    
    # Compliance Score
    compliance_score: float  # 0.0 - 1.0
    compliance_status: ComplianceStatus
    
    # Grenzwert-Prüfungen
    grenzwert_pruefungen: List[GrenzwertPruefung]
    
    # Trends
    trend_analysen: List[TrendAnalyse]
    
    # Verfahren/Genehmigungen
    verfahren_status: Dict[str, Any]
    
    # Mängel
    maengel_offen: int
    maengel_kritisch: int
    
    # Wartung
    wartung_rueckstand: int
    naechste_wartung: Optional[str]
    
    # Empfehlungen
    empfehlungen: List[str]
    
    # Zusammenfassung
    zusammenfassung: str
    
    @property
    def ist_konform(self) -> bool:
        return self.compliance_status == ComplianceStatus.COMPLIANT
    
    @property
    def handlungsbedarf(self) -> bool:
        return self.compliance_status in [ComplianceStatus.CRITICAL, ComplianceStatus.NON_COMPLIANT]


@dataclass
class RisikoAnalyse:
    """Risiko-Analyse einer Anlage"""
    bst_nr: str
    anl_nr: str
    risiko_score: float  # 0.0 - 1.0
    risiko_klasse: RisikoKlasse
    risiko_faktoren: List[Dict[str, Any]]
    empfehlungen: List[str]
    details: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


# ============================================================================
# GRENZWERTE (TA LUFT / TA LÄRM)
# ============================================================================

GRENZWERTE_LUFT = {
    # Stickoxide (NOx) in µg/m³
    "NOx": {
        "jahresmittel": 40.0,
        "typ": GrenzwertTyp.LUFT_JAHRESMITTEL
    },
    "NO2": {
        "jahresmittel": 40.0,
        "stundenmittel": 200.0,
        "typ_jahr": GrenzwertTyp.LUFT_JAHRESMITTEL,
        "typ_stunde": GrenzwertTyp.LUFT_KURZZEITWERT
    },
    # Feinstaub
    "PM10": {
        "jahresmittel": 40.0,
        "tagesmittel": 50.0,
        "typ_jahr": GrenzwertTyp.LUFT_JAHRESMITTEL,
        "typ_tag": GrenzwertTyp.LUFT_TAGESMITTEL
    },
    "PM2.5": {
        "jahresmittel": 25.0,
        "typ": GrenzwertTyp.LUFT_JAHRESMITTEL
    },
    # Schwefeldioxid
    "SO2": {
        "jahresmittel": 50.0,
        "tagesmittel": 125.0,
        "stundenmittel": 350.0,
        "typ_jahr": GrenzwertTyp.LUFT_JAHRESMITTEL,
        "typ_tag": GrenzwertTyp.LUFT_TAGESMITTEL,
        "typ_stunde": GrenzwertTyp.LUFT_KURZZEITWERT
    },
    # Kohlenmonoxid
    "CO": {
        "8h_mittel": 10000.0,
        "typ": GrenzwertTyp.LUFT_JAHRESMITTEL
    },
    # Ozon
    "O3": {
        "8h_mittel": 120.0,
        "typ": GrenzwertTyp.LUFT_KURZZEITWERT
    }
}

GRENZWERTE_LAERM = {
    # TA Lärm - Immissionsrichtwerte in dB(A)
    "Industriegebiet": {
        "tag": 70.0,
        "nacht": 70.0,
        "typ_tag": GrenzwertTyp.LAERM_TAG,
        "typ_nacht": GrenzwertTyp.LAERM_NACHT
    },
    "Gewerbegebiet": {
        "tag": 65.0,
        "nacht": 50.0,
        "typ_tag": GrenzwertTyp.LAERM_TAG,
        "typ_nacht": GrenzwertTyp.LAERM_NACHT
    },
    "Mischgebiet": {
        "tag": 60.0,
        "nacht": 45.0,
        "typ_tag": GrenzwertTyp.LAERM_TAG,
        "typ_nacht": GrenzwertTyp.LAERM_NACHT
    },
    "Wohngebiet": {
        "tag": 55.0,
        "nacht": 40.0,
        "typ_tag": GrenzwertTyp.LAERM_TAG,
        "typ_nacht": GrenzwertTyp.LAERM_NACHT
    },
    "Kurgebiet": {
        "tag": 45.0,
        "nacht": 35.0,
        "typ_tag": GrenzwertTyp.LAERM_TAG,
        "typ_nacht": GrenzwertTyp.LAERM_NACHT
    }
}


# ============================================================================
# IMMISSIONSSCHUTZ AGENT EXTENSION
# ============================================================================

class ImmissionsschutzAgentTestServerExtension(DatabaseAgentTestServerExtension):
    """
    Spezialisierter Agent für Immissionsschutz-Domäne.
    
    Erweitert DatabaseAgentTestServerExtension mit:
        - Grenzwert-Prüfungen (TA Luft, TA Lärm)
        - Trend-Analysen
        - Risiko-Bewertungen
        - Compliance-Reports
    """
    
    def __init__(self, config: Optional[TestServerConfig] = None):
        super().__init__(config)
        
        # Logger aus Parent-Klasse
        if not hasattr(self, 'logger'):
            self.logger = logging.getLogger(self.__class__.__name__)
            self.logger.setLevel(logging.INFO)
        
        self.logger.info("ImmissionsschutzAgent initialisiert")
        
        # Domain-spezifische Konfiguration
        self.grenzwerte_luft = GRENZWERTE_LUFT
        self.grenzwerte_laerm = GRENZWERTE_LAERM
    
    # ========================================================================
    # GRENZWERT-PRÜFUNGEN
    # ========================================================================
    
    async def check_grenzwerte(
        self,
        bst_nr: str,
        anl_nr: str,
        messart: Optional[str] = None
    ) -> Dict[str, List[GrenzwertPruefung]]:
        """
        Prüft Messwerte gegen relevante Grenzwerte.
        
        Args:
            bst_nr: Betriebsstättennummer
            anl_nr: Anlagennummer
            messart: Optional - Filter für Messart
        
        Returns:
            Dict mit Listen von GrenzwertPruefung pro Kategorie
        """
        self.logger.info(f"Grenzwert-Check für {bst_nr}/{anl_nr}")
        
        # Messungen abrufen
        messungen = await self.query_messungen(
            bst_nr=bst_nr,
            anl_nr=anl_nr,
            messart=messart,
            limit=1000
        )
        
        if not messungen:
            self.logger.warning(f"Keine Messungen gefunden für {bst_nr}/{anl_nr}")
            return {"luft": [], "laerm": []}
        
        # Gruppiere nach Messart
        messungen_by_art: Dict[str, List[Dict]] = {}
        for m in messungen:
            art = m.get('messart', 'Unbekannt')
            if art not in messungen_by_art:
                messungen_by_art[art] = []
            messungen_by_art[art].append(m)
        
        # Prüfe jede Messart
        pruefungen_luft = []
        pruefungen_laerm = []
        
        for art, mess_liste in messungen_by_art.items():
            # Extrahiere Messwerte
            werte = [m.get('messwert', 0.0) for m in mess_liste if m.get('messwert') is not None]
            
            if not werte:
                continue
            
            # Luftgrenzwerte prüfen
            if art in self.grenzwerte_luft:
                pruefung = self._pruefe_luftgrenzwert(art, werte)
                if pruefung:
                    pruefungen_luft.append(pruefung)
            
            # Lärmgrenzwerte prüfen
            if "Lärm" in art or "dB" in art:
                pruefung = self._pruefe_laermgrenzwert(art, werte)
                if pruefung:
                    pruefungen_laerm.append(pruefung)
        
        return {
            "luft": pruefungen_luft,
            "laerm": pruefungen_laerm
        }
    
    def _pruefe_luftgrenzwert(
        self,
        messart: str,
        werte: List[float]
    ) -> Optional[GrenzwertPruefung]:
        """Prüft Luftmesswerte gegen Grenzwerte"""
        if messart not in self.grenzwerte_luft:
            return None
        
        grenzwert_config = self.grenzwerte_luft[messart]
        
        # Verwende Jahresmittel als Standard
        grenzwert = grenzwert_config.get('jahresmittel', grenzwert_config.get('tagesmittel', 0.0))
        grenzwert_typ = grenzwert_config.get('typ', GrenzwertTyp.LUFT_JAHRESMITTEL)
        
        # Statistik berechnen
        mittelwert = mean(werte)
        maximum = max(werte)
        ueberschreitungen = sum(1 for w in werte if w > grenzwert)
        ueberschreitungen_prozent = (ueberschreitungen / len(werte)) * 100
        
        # Status bestimmen
        if ueberschreitungen == 0:
            status = "OK"
        elif ueberschreitungen_prozent < 5:
            status = "GRENZWERTIG"
        else:
            status = "UEBERSCHREITUNG"
        
        # Bemerkungen
        bemerkungen = []
        
        if grenzwert > 0:
            ausnutzung = (mittelwert / grenzwert) * 100
            
            if ausnutzung > 90:
                bemerkungen.append(f"Grenzwert zu {ausnutzung:.1f}% ausgenutzt")
            if maximum > grenzwert * 1.5:
                bemerkungen.append(f"Maximum deutlich über Grenzwert ({maximum:.1f} µg/m³)")
        else:
            bemerkungen.append("Kein Grenzwert definiert")
        
        return GrenzwertPruefung(
            messart=messart,
            grenzwert=grenzwert,
            grenzwert_typ=grenzwert_typ,
            aktuelle_messwerte=werte[-10:],  # Letzte 10 Werte
            mittelwert=mittelwert,
            maximum=maximum,
            ueberschreitungen=ueberschreitungen,
            ueberschreitungen_prozent=ueberschreitungen_prozent,
            status=status,
            bemerkungen=bemerkungen
        )
    
    def _pruefe_laermgrenzwert(
        self,
        messart: str,
        werte: List[float]
    ) -> Optional[GrenzwertPruefung]:
        """Prüft Lärmmesswerte gegen Richtwerte"""
        # Vereinfachte Implementierung - nimmt Wohngebiet als Standard
        grenzwert_config = self.grenzwerte_laerm.get("Wohngebiet", {})
        grenzwert = grenzwert_config.get("tag", 55.0)
        grenzwert_typ = GrenzwertTyp.LAERM_TAG
        
        mittelwert = mean(werte)
        maximum = max(werte)
        ueberschreitungen = sum(1 for w in werte if w > grenzwert)
        ueberschreitungen_prozent = (ueberschreitungen / len(werte)) * 100
        
        if ueberschreitungen == 0:
            status = "OK"
        elif ueberschreitungen_prozent < 5:
            status = "GRENZWERTIG"
        else:
            status = "UEBERSCHREITUNG"
        
        return GrenzwertPruefung(
            messart=messart,
            grenzwert=grenzwert,
            grenzwert_typ=grenzwert_typ,
            aktuelle_messwerte=werte[-10:],
            mittelwert=mittelwert,
            maximum=maximum,
            ueberschreitungen=ueberschreitungen,
            ueberschreitungen_prozent=ueberschreitungen_prozent,
            status=status,
            bemerkungen=[]
        )
    
    # ========================================================================
    # TREND-ANALYSEN
    # ========================================================================
    
    async def analyze_trend(
        self,
        bst_nr: str,
        anl_nr: str,
        messart: str,
        zeitraum_tage: int = 90
    ) -> TrendAnalyse:
        """
        Analysiert Trend einer Messreihe über Zeitraum.
        
        Args:
            bst_nr: Betriebsstättennummer
            anl_nr: Anlagennummer
            messart: Messart (z.B. "PM10", "NOx")
            zeitraum_tage: Anzahl Tage rückwärts
        
        Returns:
            TrendAnalyse mit Richtung, Stärke, Prognose
        """
        self.logger.info(f"Trend-Analyse für {messart} ({zeitraum_tage} Tage)")
        
        # Messreihen abrufen
        result = await self.query_entity(
            EntityType.MESSREIHE,
            filters={
                "bst_nr": bst_nr,
                "anl_nr": anl_nr,
                "messart": messart
            },
            limit=10
        )
        
        if not result.success or not result.data:
            self.logger.warning(f"Keine Messreihen gefunden für {messart}")
            # Fallback: Einzelmessungen auswerten
            return await self._analyze_trend_from_messungen(
                bst_nr, anl_nr, messart, zeitraum_tage
            )
        
        # Neueste Messreihe
        messreihe = result.data[0] if isinstance(result.data, list) else result.data
        
        # Trend-Richtung bestimmen
        trend_str = messreihe.get('trend', 'stabil').lower()
        trend_richtung = TrendRichtung.STABIL
        
        if 'steigend' in trend_str or 'ansteigend' in trend_str:
            trend_richtung = TrendRichtung.STEIGEND
        elif 'fallend' in trend_str or 'sinkend' in trend_str:
            trend_richtung = TrendRichtung.FALLEND
        elif 'schwankend' in trend_str:
            trend_richtung = TrendRichtung.SCHWANKEND
        
        # Trend-Stärke aus Standardabweichung
        mittelwert = messreihe.get('mittelwert', 0.0)
        stdabw = messreihe.get('standardabweichung', 0.0)
        
        if mittelwert > 0:
            variationskoeffizient = stdabw / mittelwert
            trend_staerke = min(variationskoeffizient, 1.0)
        else:
            trend_staerke = 0.0
        
        # Prognose (einfache Extrapolation)
        prognose_30_tage = None
        if trend_richtung == TrendRichtung.STEIGEND:
            prognose_30_tage = mittelwert * 1.1  # +10%
        elif trend_richtung == TrendRichtung.FALLEND:
            prognose_30_tage = mittelwert * 0.9  # -10%
        else:
            prognose_30_tage = mittelwert
        
        # Empfehlungen generieren
        empfehlungen = []
        if trend_richtung == TrendRichtung.STEIGEND and trend_staerke > 0.5:
            empfehlungen.append("⚠️ Deutlich steigender Trend - Ursachen untersuchen")
            empfehlungen.append("Filterwartung oder Prozessoptimierung prüfen")
        elif messreihe.get('ueberschreitungen_anzahl', 0) > 0:
            empfehlungen.append("Grenzwertüberschreitungen dokumentieren")
            empfehlungen.append("Maßnahmen zur Emissionsreduzierung einleiten")
        
        return TrendAnalyse(
            messart=messart,
            zeitraum_von=messreihe.get('zeitraum_von', ''),
            zeitraum_bis=messreihe.get('zeitraum_bis', ''),
            anzahl_messungen=messreihe.get('anzahl_messungen', 0),
            trend_richtung=trend_richtung,
            trend_staerke=trend_staerke,
            mittelwert=mittelwert,
            standardabweichung=stdabw,
            minimum=messreihe.get('minimalwert', 0.0),
            maximum=messreihe.get('maximalwert', 0.0),
            prognose_30_tage=prognose_30_tage,
            empfehlungen=empfehlungen
        )
    
    async def _analyze_trend_from_messungen(
        self,
        bst_nr: str,
        anl_nr: str,
        messart: str,
        zeitraum_tage: int
    ) -> TrendAnalyse:
        """Fallback: Trend aus Einzelmessungen berechnen"""
        messungen = await self.query_messungen(
            bst_nr=bst_nr,
            anl_nr=anl_nr,
            messart=messart,
            limit=1000
        )
        
        if not messungen:
            return TrendAnalyse(
                messart=messart,
                zeitraum_von="",
                zeitraum_bis="",
                anzahl_messungen=0,
                trend_richtung=TrendRichtung.UNBEKANNT,
                trend_staerke=0.0,
                mittelwert=0.0,
                standardabweichung=0.0,
                minimum=0.0,
                maximum=0.0,
                empfehlungen=["Keine Daten verfügbar"]
            )
        
        # Statistik berechnen
        werte = [m.get('messwert', 0.0) for m in messungen if m.get('messwert')]
        
        if not werte:
            return TrendAnalyse(
                messart=messart,
                zeitraum_von="",
                zeitraum_bis="",
                anzahl_messungen=0,
                trend_richtung=TrendRichtung.UNBEKANNT,
                trend_staerke=0.0,
                mittelwert=0.0,
                standardabweichung=0.0,
                minimum=0.0,
                maximum=0.0
            )
        
        mittelwert = mean(werte)
        stdabw = stdev(werte) if len(werte) > 1 else 0.0
        
        # Einfacher Trend: Vergleiche erste vs. zweite Hälfte
        mid = len(werte) // 2
        erste_haelfte = mean(werte[:mid]) if mid > 0 else mittelwert
        zweite_haelfte = mean(werte[mid:]) if mid > 0 else mittelwert
        
        if zweite_haelfte > erste_haelfte * 1.1:
            trend_richtung = TrendRichtung.STEIGEND
        elif zweite_haelfte < erste_haelfte * 0.9:
            trend_richtung = TrendRichtung.FALLEND
        else:
            trend_richtung = TrendRichtung.STABIL
        
        return TrendAnalyse(
            messart=messart,
            zeitraum_von=messungen[0].get('messdatum', '') if messungen else '',
            zeitraum_bis=messungen[-1].get('messdatum', '') if messungen else '',
            anzahl_messungen=len(messungen),
            trend_richtung=trend_richtung,
            trend_staerke=0.5,
            mittelwert=mittelwert,
            standardabweichung=stdabw,
            minimum=min(werte),
            maximum=max(werte),
            prognose_30_tage=mittelwert
        )
    
    # ========================================================================
    # COMPLIANCE REPORTS
    # ========================================================================
    
    async def generate_compliance_report(
        self,
        bst_nr: str,
        anl_nr: str
    ) -> ComplianceReport:
        """
        Generiert umfassenden Compliance-Report.
        
        Kombiniert:
            - Basis-Compliance-Analyse
            - Grenzwert-Prüfungen
            - Trend-Analysen
            - Verfahrensstatus
            - Mängel & Wartung
        
        Returns:
            ComplianceReport mit allen Informationen
        """
        self.logger.info(f"Generiere Compliance-Report für {bst_nr}/{anl_nr}")
        
        # Basis-Compliance
        base_compliance = await self.analyze_compliance(bst_nr, anl_nr)
        
        # Vollständige Daten
        entity_result = await self.get_complete_entity(bst_nr, anl_nr)
        
        if not entity_result.success:
            raise ValueError(f"Anlage nicht gefunden: {bst_nr}/{anl_nr}")
        
        anlage = entity_result.data
        
        # Grenzwert-Prüfungen
        grenzwerte = await self.check_grenzwerte(bst_nr, anl_nr)
        alle_pruefungen = grenzwerte['luft'] + grenzwerte['laerm']
        
        # Trend-Analysen (für kritische Messarten)
        trend_analysen = []
        kritische_messarten = set()
        
        for pruefung in alle_pruefungen:
            if pruefung.ist_kritisch:
                kritische_messarten.add(pruefung.messart)
        
        for messart in list(kritische_messarten)[:5]:  # Max 5 Trends
            try:
                trend = await self.analyze_trend(bst_nr, anl_nr, messart)
                trend_analysen.append(trend)
            except Exception as e:
                self.logger.warning(f"Trend-Analyse für {messart} fehlgeschlagen: {e}")
        
        # Verfahrensstatus
        verfahren_status = {
            "total": len(anlage.verfahren),
            "genehmigt": sum(1 for v in anlage.verfahren if getattr(v, 'status', None) == 'genehmigt'),
            "in_bearbeitung": sum(1 for v in anlage.verfahren if getattr(v, 'status', None) == 'in Bearbeitung')
        }
        
        # Mängel
        maengel_offen = sum(1 for m in anlage.maengel if getattr(m, 'status', None) == 'offen')
        maengel_kritisch = sum(1 for m in anlage.maengel 
                              if getattr(m, 'status', None) == 'offen' and getattr(m, 'kategorie', None) == 'kritisch')
        
        # Wartung
        wartungen_geplant = sum(1 for w in anlage.wartungen if getattr(w, 'status', None) == 'geplant')
        naechste_wartung = None
        
        for w in anlage.wartungen:
            if getattr(w, 'status', None) == 'geplant' and getattr(w, 'geplant_datum', None):
                if not naechste_wartung or w.geplant_datum < naechste_wartung:
                    naechste_wartung = w.geplant_datum
        
        # Empfehlungen sammeln
        empfehlungen = list(base_compliance.recommendations)
        
        for pruefung in alle_pruefungen:
            if pruefung.ist_kritisch:
                empfehlungen.append(
                    f"🔴 {pruefung.messart}: Grenzwertüberschreitungen reduzieren "
                    f"({pruefung.ueberschreitungen_prozent:.1f}%)"
                )
        
        for trend in trend_analysen:
            if trend.ist_kritischer_trend:
                empfehlungen.extend(trend.empfehlungen)
        
        # Zusammenfassung generieren
        zusammenfassung = self._generate_zusammenfassung(
            base_compliance,
            alle_pruefungen,
            trend_analysen,
            maengel_kritisch,
            wartungen_geplant
        )
        
        return ComplianceReport(
            bst_nr=bst_nr,
            anl_nr=anl_nr,
            anlagen_name=anlage.anlage.bst_name,
            erstellt_am=datetime.now().isoformat(),
            compliance_score=base_compliance.score,
            compliance_status=base_compliance.status,
            grenzwert_pruefungen=alle_pruefungen,
            trend_analysen=trend_analysen,
            verfahren_status=verfahren_status,
            maengel_offen=maengel_offen,
            maengel_kritisch=maengel_kritisch,
            wartung_rueckstand=wartungen_geplant,
            naechste_wartung=naechste_wartung,
            empfehlungen=empfehlungen[:10],  # Top 10
            zusammenfassung=zusammenfassung
        )
    
    def _generate_zusammenfassung(
        self,
        compliance: ComplianceResult,
        pruefungen: List[GrenzwertPruefung],
        trends: List[TrendAnalyse],
        maengel_kritisch: int,
        wartungen_geplant: int
    ) -> str:
        """Generiert textuelle Zusammenfassung"""
        parts = []
        
        # Compliance-Status
        if compliance.is_compliant:
            parts.append(f"✅ Anlage ist konform (Score: {compliance.score:.1%})")
        else:
            parts.append(f"⚠️ Compliance-Status: {compliance.status.value} (Score: {compliance.score:.1%})")
        
        # Grenzwerte
        kritische_pruefungen = [p for p in pruefungen if p.ist_kritisch]
        if kritische_pruefungen:
            parts.append(
                f"🔴 {len(kritische_pruefungen)} Grenzwertüberschreitungen erkannt"
            )
        else:
            parts.append("✅ Alle Grenzwerte eingehalten")
        
        # Trends
        kritische_trends = [t for t in trends if t.ist_kritischer_trend]
        if kritische_trends:
            parts.append(f"📈 {len(kritische_trends)} kritische Trends identifiziert")
        
        # Mängel
        if maengel_kritisch > 0:
            parts.append(f"🔴 {maengel_kritisch} kritische Mängel offen")
        
        # Wartung
        if wartungen_geplant > 5:
            parts.append(f"⚙️ {wartungen_geplant} Wartungen ausstehend")
        
        return " | ".join(parts)
    
    # ========================================================================
    # RISIKO-ANALYSE
    # ========================================================================
    
    async def calculate_risk_score(
        self,
        bst_nr: str,
        anl_nr: str
    ) -> RisikoAnalyse:
        """
        Berechnet Risiko-Score einer Anlage.
        
        Faktoren:
            - Compliance-Score (40%)
            - Grenzwertüberschreitungen (30%)
            - Kritische Trends (20%)
            - Mängel (10%)
        
        Returns:
            RisikoAnalyse mit Score, Klasse, Faktoren
        """
        self.logger.info(f"Risiko-Analyse für {bst_nr}/{anl_nr}")
        
        risiko_score = 0.0
        risiko_faktoren = []
        
        # Compliance-Score (invertiert - niedrig = hohes Risiko)
        compliance = await self.analyze_compliance(bst_nr, anl_nr)
        compliance_risk = 1.0 - compliance.score
        risiko_score += compliance_risk * 0.4
        
        risiko_faktoren.append({
            "faktor": "Compliance",
            "gewicht": 0.4,
            "risiko": compliance_risk,
            "beschreibung": f"Compliance-Score: {compliance.score:.1%}"
        })
        
        # Grenzwertüberschreitungen
        grenzwerte = await self.check_grenzwerte(bst_nr, anl_nr)
        alle_pruefungen = grenzwerte['luft'] + grenzwerte['laerm']
        
        if alle_pruefungen:
            kritische_pruefungen = [p for p in alle_pruefungen if p.ist_kritisch]
            grenzwert_risk = len(kritische_pruefungen) / len(alle_pruefungen)
            risiko_score += grenzwert_risk * 0.3
            
            risiko_faktoren.append({
                "faktor": "Grenzwertüberschreitungen",
                "gewicht": 0.3,
                "risiko": grenzwert_risk,
                "beschreibung": f"{len(kritische_pruefungen)}/{len(alle_pruefungen)} kritisch"
            })
        
        # Trends
        # Vereinfachte Version - nur die 3 häufigsten Messarten prüfen
        messungen = await self.query_messungen(bst_nr=bst_nr, anl_nr=anl_nr, limit=1000)
        messarten = {}
        
        for m in messungen:
            art = m.get('messart', 'Unbekannt')
            messarten[art] = messarten.get(art, 0) + 1
        
        top_messarten = sorted(messarten.items(), key=lambda x: x[1], reverse=True)[:3]
        
        trend_risk = 0.0
        for messart, _ in top_messarten:
            try:
                trend = await self.analyze_trend(bst_nr, anl_nr, messart)
                if trend.ist_kritischer_trend:
                    trend_risk += 0.33  # Jeder kritische Trend erhöht Risiko
            except:
                pass
        
        risiko_score += trend_risk * 0.2
        
        risiko_faktoren.append({
            "faktor": "Kritische Trends",
            "gewicht": 0.2,
            "risiko": trend_risk,
            "beschreibung": f"{int(trend_risk * 3)} von 3 Trends kritisch"
        })
        
        # Mängel
        entity_result = await self.get_complete_entity(bst_nr, anl_nr)
        if entity_result.success:
            anlage = entity_result.data
            maengel_offen = sum(1 for m in anlage.maengel if getattr(m, 'status', None) == 'offen')
            maengel_kritisch = sum(1 for m in anlage.maengel 
                                  if getattr(m, 'status', None) == 'offen' and getattr(m, 'kategorie', None) == 'kritisch')
            
            if maengel_offen > 0:
                maengel_risk = min(maengel_kritisch / max(maengel_offen, 1), 1.0)
                risiko_score += maengel_risk * 0.1
                
                risiko_faktoren.append({
                    "faktor": "Offene Mängel",
                    "gewicht": 0.1,
                    "risiko": maengel_risk,
                    "beschreibung": f"{maengel_kritisch}/{maengel_offen} kritisch"
                })
        
        # Risiko-Klasse bestimmen
        if risiko_score < 0.2:
            risiko_klasse = RisikoKlasse.SEHR_GERING
        elif risiko_score < 0.4:
            risiko_klasse = RisikoKlasse.GERING
        elif risiko_score < 0.6:
            risiko_klasse = RisikoKlasse.MITTEL
        elif risiko_score < 0.8:
            risiko_klasse = RisikoKlasse.HOCH
        else:
            risiko_klasse = RisikoKlasse.SEHR_HOCH
        
        # Empfehlungen
        empfehlungen = []
        
        if risiko_klasse in [RisikoKlasse.HOCH, RisikoKlasse.SEHR_HOCH]:
            empfehlungen.append("🔴 Sofortige Prüfung und Maßnahmenplanung erforderlich")
            empfehlungen.append("Intensivierte Überwachung durchführen")
        
        for faktor in risiko_faktoren:
            if faktor['risiko'] > 0.5:
                empfehlungen.append(f"⚠️ {faktor['faktor']} adressieren: {faktor['beschreibung']}")
        
        return RisikoAnalyse(
            bst_nr=bst_nr,
            anl_nr=anl_nr,
            risiko_score=risiko_score,
            risiko_klasse=risiko_klasse,
            risiko_faktoren=risiko_faktoren,
            empfehlungen=empfehlungen,
            details={
                "compliance_score": compliance.score,
                "grenzwert_ueberschreitungen": len([p for p in alle_pruefungen if p.ist_kritisch]),
                "kritische_trends": int(trend_risk * 3)
            }
        )


# ============================================================================
# SINGLETON HELPER
# ============================================================================

_immissionsschutz_agent_instance: Optional[ImmissionsschutzAgentTestServerExtension] = None

def get_immissionsschutz_agent(
    config: Optional[TestServerConfig] = None
) -> ImmissionsschutzAgentTestServerExtension:
    """Singleton-Zugriff auf ImmissionsschutzAgent"""
    global _immissionsschutz_agent_instance
    
    if _immissionsschutz_agent_instance is None:
        _immissionsschutz_agent_instance = ImmissionsschutzAgentTestServerExtension(config)
    
    return _immissionsschutz_agent_instance


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

async def example_usage():
    """Beispiele für ImmissionsschutzAgent"""
    print("=" * 80)
    print("ImmissionsschutzAgent TestServer Extension - Examples")
    print("=" * 80)
    
    agent = get_immissionsschutz_agent()
    
    try:
        # Test-Anlage (existiert in DB)
        bst_nr = "10686360000"
        anl_nr = "4001"
        
        # 1. Grenzwert-Check
        print("\n1️⃣ Grenzwert-Check")
        print("-" * 60)
        
        grenzwerte = await agent.check_grenzwerte(bst_nr, anl_nr)
        
        print(f"Luft-Prüfungen: {len(grenzwerte['luft'])}")
        for pruefung in grenzwerte['luft'][:3]:
            print(f"  {pruefung.messart}: {pruefung.status}")
            print(f"    Mittelwert: {pruefung.mittelwert:.1f} / Grenzwert: {pruefung.grenzwert:.1f}")
            print(f"    Überschreitungen: {pruefung.ueberschreitungen} ({pruefung.ueberschreitungen_prozent:.1f}%)")
        
        # 2. Trend-Analyse
        print("\n2️⃣ Trend-Analyse")
        print("-" * 60)
        
        if grenzwerte['luft']:
            messart = grenzwerte['luft'][0].messart
            trend = await agent.analyze_trend(bst_nr, anl_nr, messart)
            
            print(f"Messart: {trend.messart}")
            print(f"Trend: {trend.trend_richtung.value} (Stärke: {trend.trend_staerke:.1%})")
            print(f"Mittelwert: {trend.mittelwert:.1f}")
            print(f"Prognose (30 Tage): {trend.prognose_30_tage:.1f}")
            
            if trend.empfehlungen:
                print("Empfehlungen:")
                for emp in trend.empfehlungen[:3]:
                    print(f"  💡 {emp}")
        
        # 3. Compliance-Report
        print("\n3️⃣ Compliance-Report")
        print("-" * 60)
        
        report = await agent.generate_compliance_report(bst_nr, anl_nr)
        
        print(f"Anlage: {report.anlagen_name}")
        print(f"Compliance-Score: {report.compliance_score:.1%}")
        print(f"Status: {report.compliance_status.value}")
        print(f"\nZusammenfassung:\n{report.zusammenfassung}")
        
        print(f"\nGrenzwert-Prüfungen: {len(report.grenzwert_pruefungen)}")
        print(f"Trend-Analysen: {len(report.trend_analysen)}")
        print(f"Offene Mängel: {report.maengel_offen} (davon {report.maengel_kritisch} kritisch)")
        
        # 4. Risiko-Analyse
        print("\n4️⃣ Risiko-Analyse")
        print("-" * 60)
        
        risiko = await agent.calculate_risk_score(bst_nr, anl_nr)
        
        print(f"Risiko-Score: {risiko.risiko_score:.1%}")
        print(f"Risiko-Klasse: {risiko.risiko_klasse.value}")
        
        print("\nRisiko-Faktoren:")
        for faktor in risiko.risiko_faktoren:
            print(f"  {faktor['faktor']}: {faktor['risiko']:.1%} (Gewicht: {faktor['gewicht']:.0%})")
            print(f"    {faktor['beschreibung']}")
        
        print("\n" + "=" * 80)
        print("✅ Alle Examples erfolgreich!")
        
    except Exception as e:
        print(f"❌ Fehler: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await agent.close()


if __name__ == "__main__":
    asyncio.run(example_usage())
