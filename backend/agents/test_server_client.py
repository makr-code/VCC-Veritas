"""
Immissionsschutz Test-Server Client
====================================

HTTP-Client für die Kommunikation zwischen VERITAS Agents und dem
eigenständigen Immissionsschutz Test-Server (Port 5001).

Features:
- Async HTTP Requests
- Connection Pooling
- Retry Logic mit exponential backoff
- Response Caching
- Error Handling
- Request/Response Logging

Usage:
    client = TestServerClient()

    # Anlagen-Daten abrufen
    anlage = await client.get_anlage_complete("10650200000", "4001")

    # Verfahren suchen
    verfahren = await client.search_verfahren(bst_nr="10650200000")

    # Messungen abrufen
    messungen = await client.search_messungen(
        bst_nr="10650200000",
        ueberschreitung=True
    )
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple, Union

import aiohttp

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================


@dataclass
class TestServerConfig:
    """Test-Server Konfiguration"""

    host: str = "localhost"
    port: int = 5001
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    cache_ttl: int = 300  # 5 Minuten

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class AnlageBasic:
    """Basis-Anlagen-Daten"""

    bst_nr: str
    bst_name: Optional[str] = None
    anl_nr: str = ""
    anl_bez: Optional[str] = None
    ort: Optional[str] = None
    ortsteil: Optional[str] = None
    ostwert: Optional[float] = None
    nordwert: Optional[float] = None


@dataclass
class Verfahren:
    """Genehmigungsverfahren"""

    verfahren_id: str
    bst_nr: str
    anl_nr: str
    verfahrensart: str
    antragsdatum: str
    entscheidungsdatum: Optional[str] = None
    status: str = ""
    behoerde: str = ""
    aktenzeichen: str = ""
    antragsgrund: Optional[str] = None
    oeffentliche_beteiligung: int | str = 0
    uvp_erforderlich: int | str = 0
    bemerkungen: Optional[str] = None
    created_at: Optional[str] = None


@dataclass
class Messung:
    """Messung (Lärm, Emissionen)"""

    messung_id: str
    bst_nr: str
    anl_nr: str
    messart: str
    messdatum: str
    messzeit: str
    messwert: float | str
    einheit: str
    grenzwert: Optional[float | str] = None
    ueberschreitung: int | str = 0
    messort: Optional[str] = None
    messmethode: Optional[str] = None
    messgeraet: Optional[str] = None
    messstelle: Optional[str] = None
    wetterbedingungen: Optional[str] = None
    bemerkungen: Optional[str] = None


@dataclass
class Ueberwachung:
    """Überwachungsmaßnahme"""

    ueberwachung_id: str
    bst_nr: str
    anl_nr: str
    ueberwachungsart: str
    geplant_datum: str
    durchgefuehrt_datum: Optional[str] = None
    status: str = ""
    behoerde: str = ""
    pruefumfang: Optional[str] = None
    ergebnis: Optional[str] = None
    naechste_pruefung: Optional[str] = None
    bemerkungen: Optional[str] = None
    durchgefuehrt_von: Optional[str] = None


@dataclass
class Mangel:
    """Festgestellter Mangel"""

    mangel_id: str
    bst_nr: str
    anl_nr: str
    festgestellt_datum: str
    mangelart: str
    schweregrad: str
    beschreibung: str
    status: str = ""


@dataclass
class AnlageComplete:
    """Vollständige Anlagen-Daten (Cross-DB)"""

    anlage: AnlageBasic
    verfahren: List[Verfahren] = field(default_factory=list)
    messungen: List[Messung] = field(default_factory=list)
    ueberwachungen: List[Ueberwachung] = field(default_factory=list)
    maengel: List[Mangel] = field(default_factory=list)
    statistik: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# NEUE DATA CLASSES - Phase 2
# =============================================================================


@dataclass
class Dokument:
    """Dokument"""

    dokument_id: str
    bst_nr: str
    anl_nr: str
    dokumenttyp: str
    titel: str
    erstellt_datum: str
    gueltig_bis: Optional[str] = None
    dateipfad: Optional[str] = None
    dateigroesse_kb: Optional[int] = None
    ersteller: Optional[str] = None
    aktenzeichen: Optional[str] = None
    status: str = "aktiv"
    bemerkungen: Optional[str] = None


@dataclass
class Ansprechpartner:
    """Ansprechpartner"""

    ansprechpartner_id: str
    bst_nr: str
    anl_nr: str
    name: str
    funktion: str
    telefon: Optional[str] = None
    email: Optional[str] = None
    mobil: Optional[str] = None
    verfuegbarkeit: Optional[str] = None
    notfallkontakt: int | str = 0
    aktiv: int | str = 1


@dataclass
class Wartung:
    """Wartung"""

    wartung_id: str
    bst_nr: str
    anl_nr: str
    wartungsart: str
    geplant_datum: str
    durchgefuehrt_datum: Optional[str] = None
    durchgefuehrt_von: Optional[str] = None
    kosten: Optional[float] = None
    naechste_wartung: Optional[str] = None
    status: str = ""
    beschreibung: Optional[str] = None
    massnahmen: Optional[str] = None


@dataclass
class Messreihe:
    """Messreihe (Zeitreihen-Analyse)"""

    messreihe_id: str
    bst_nr: str
    anl_nr: str
    messart: str
    zeitraum_von: str
    zeitraum_bis: str
    anzahl_messungen: int | str
    mittelwert: float | str
    maximalwert: float | str
    minimalwert: float | str
    standardabweichung: float | str
    ueberschreitungen_anzahl: int | str
    trend: str  # steigend, fallend, konstant
    bewertung: str  # unauffällig, auffällig, kritisch


@dataclass
class BehoerdenKontakt:
    """Behörden-Kontakt"""

    kontakt_id: str
    behoerde: str
    sachbearbeiter: str
    abteilung: Optional[str] = None
    telefon: Optional[str] = None
    email: Optional[str] = None
    zustaendig_fuer: Optional[str] = None
    bemerkungen: Optional[str] = None


@dataclass
class ComplianceHistorie:
    """Compliance-Prüfungshistorie"""

    historie_id: str
    bst_nr: str
    anl_nr: str
    pruefungsdatum: str
    pruefungstyp: str
    ergebnis: str
    bewertung_punkte: int | str
    feststellungen: Optional[str] = None
    empfehlungen: Optional[str] = None
    folgepruefung: Optional[str] = None


@dataclass
class AnlageExtended:
    """Erweiterte Anlagen-Daten mit ALLEN Relationen"""

    anlage: AnlageBasic
    verfahren: List[Verfahren] = field(default_factory=list)
    messungen: List[Messung] = field(default_factory=list)
    ueberwachungen: List[Ueberwachung] = field(default_factory=list)
    maengel: List[Mangel] = field(default_factory=list)
    dokumente: List[Dokument] = field(default_factory=list)
    ansprechpartner: List[Ansprechpartner] = field(default_factory=list)
    wartungen: List[Wartung] = field(default_factory=list)
    messreihen: List[Messreihe] = field(default_factory=list)
    compliance_historie: List[ComplianceHistorie] = field(default_factory=list)
    statistik: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# Cache
# =============================================================================


class ResponseCache:
    """Einfacher Response-Cache mit TTL"""

    def __init__(self, ttl: int = 300):
        from typing import Tuple as _Tuple

        self.cache: Dict[str, Tuple[Any, datetime]] = {}
        self.ttl = ttl

    def get(self, key: str) -> Optional[Any]:
        if key in self.cache:
            data, timestamp = self.cache[key]
            if (datetime.now() - timestamp).seconds < self.ttl:
                return data
            else:
                del self.cache[key]
        return None

    def set(self, key: str, data: Any):
        self.cache[key] = (data, datetime.now())

    def clear(self):
        self.cache.clear()


# =============================================================================
# Test-Server Client
# =============================================================================


class TestServerClient:
    """
    HTTP-Client für Immissionsschutz Test-Server
    """

    def __init__(self, config: Optional[TestServerConfig] = None):
        self.config = config or TestServerConfig()
        self.cache = ResponseCache(ttl=self.config.cache_ttl)
        self._session: Optional[aiohttp.ClientSession] = None

        logger.info(f"TestServerClient initialisiert: {self.config.base_url}")

    async def _get_session(self) -> aiohttp.ClientSession:
        """Lazy Session Initialization"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self):
        """Session schließen"""
        if self._session and not self._session.closed:
            await self._session.close()

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        use_cache: bool = True,
    ) -> Any:
        """
        HTTP Request mit Retry-Logic
        """
        url = f"{self.config.base_url}{endpoint}"

        # Cache-Key
        cache_key = f"{method}:{endpoint}:{json.dumps(params or {}, sort_keys=True)}"

        # Cache-Lookup
        if use_cache and method == "GET":
            cached = self.cache.get(cache_key)
            if cached is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return cached

        # Retry-Loop
        for attempt in range(self.config.max_retries):
            try:
                session = await self._get_session()

                async with session.request(method, url, params=params, json=json_data) as response:
                    if response.status == 200:
                        data = await response.json()

                        # Cache speichern
                        if use_cache and method == "GET":
                            self.cache.set(cache_key, data)

                        return data

                    elif response.status == 404:
                        logger.warning(f"Resource not found: {url}")
                        return {"error": "not_found", "status": 404}

                    elif response.status >= 500:
                        # Server-Fehler -> Retry
                        if attempt < self.config.max_retries - 1:
                            delay = self.config.retry_delay * (2**attempt)
                            logger.warning(f"Server error {response.status}, retry {attempt + 1} " f"in {delay}s...")
                            await asyncio.sleep(delay)
                            continue

                    # Andere Fehler
                    error_text = await response.text()
                    logger.error(f"Request failed: {response.status} - {error_text}")
                    return {"error": "request_failed", "status": response.status}

            except aiohttp.ClientError as e:
                logger.error(f"Client error: {e}")
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(self.config.retry_delay)
                    continue
                return {"error": "connection_error", "message": str(e)}

            except Exception as e:
                logger.error(f"Unexpected error: {e}", exc_info=True)
                return {"error": "unexpected_error", "message": str(e)}

        return {"error": "max_retries_exceeded"}

    # -----------------------------------------------------------------
    # Small helpers for safe conversions from API responses
    # -----------------------------------------------------------------
    def _safe_int(self, value: Any, default: int = 0) -> int:
        try:
            if value is None:
                return default
            if isinstance(value, int):
                return value
            if isinstance(value, str) and value.isdigit():
                return int(value)
            return int(float(value))
        except Exception:
            return default

    def _safe_float(self, value: Any, default: float = 0.0) -> float:
        try:
            if value is None:
                return default
            if isinstance(value, float):
                return value
            return float(value)
        except Exception:
            return default

    # -----------------------------------------------------------------
    # Parsers for response objects that need safe numeric coercion
    # -----------------------------------------------------------------
    def _parse_messung(self, m: Dict[str, Any]) -> Messung:
        m_safe: Dict[str, Any] = dict(m)
        m_safe["messwert"] = self._safe_float(m_safe.get("messwert"))
        m_safe["grenzwert"] = None if m_safe.get("grenzwert") is None else self._safe_float(m_safe.get("grenzwert"))
        m_safe["ueberschreitung"] = self._safe_int(m_safe.get("ueberschreitung"))
        return Messung(**m_safe)

    def _parse_messreihe(self, mr: Dict[str, Any]) -> Messreihe:
        mr_safe: Dict[str, Any] = dict(mr)
        mr_safe["anzahl_messungen"] = self._safe_int(mr_safe.get("anzahl_messungen"))
        mr_safe["mittelwert"] = self._safe_float(mr_safe.get("mittelwert"))
        mr_safe["maximalwert"] = self._safe_float(mr_safe.get("maximalwert"))
        mr_safe["minimalwert"] = self._safe_float(mr_safe.get("minimalwert"))
        mr_safe["standardabweichung"] = self._safe_float(mr_safe.get("standardabweichung"))
        mr_safe["ueberschreitungen_anzahl"] = self._safe_int(mr_safe.get("ueberschreitungen_anzahl"))
        return Messreihe(**mr_safe)

    # =========================================================================
    # Health & Status
    # =========================================================================

    async def health_check(self) -> Any:
        """Health Check"""
        return await self._request("GET", "/health")

    async def get_databases(self) -> Any:
        """Liste aller Datenbanken"""
        result = await self._request("GET", "/databases")
        return result if isinstance(result, list) else []

    async def get_statistics(self) -> Any:
        """Gesamtstatistik"""
        return await self._request("GET", "/statistik/overview")

    # =========================================================================
    # Anlagen (BImSchG & WKA)
    # =========================================================================

    async def search_anlagen(
        self,
        db: str = "bimschg",
        bst_nr: Optional[str] = None,
        anl_nr: Optional[str] = None,
        ort: Optional[str] = None,
        limit: int = 50,
    ) -> Any:
        """Anlagen suchen"""
        params: Dict[str, Any] = {"db": db, "limit": limit}
        if bst_nr:
            params["bst_nr"] = bst_nr
        if anl_nr:
            params["anl_nr"] = anl_nr
        if ort:
            params["ort"] = ort

        return await self._request("GET", "/anlagen/search", params=params)

    async def get_anlage(self, db: str, bst_nr: str, anl_nr: str) -> Any:
        """Einzelne Anlage abrufen"""
        return await self._request("GET", f"/anlagen/{db}/{bst_nr}/{anl_nr}")

    # =========================================================================
    # Verfahren
    # =========================================================================

    async def search_verfahren(
        self,
        bst_nr: Optional[str] = None,
        anl_nr: Optional[str] = None,
        status: Optional[str] = None,
        von_datum: Optional[str] = None,
        bis_datum: Optional[str] = None,
        limit: int = 100,
    ) -> Any:
        """Genehmigungsverfahren suchen"""
        params: Dict[str, Any] = {"limit": limit}
        if bst_nr:
            params["bst_nr"] = bst_nr
        if anl_nr:
            params["anl_nr"] = anl_nr
        if status:
            params["status"] = status
        if von_datum:
            params["von_datum"] = von_datum
        if bis_datum:
            params["bis_datum"] = bis_datum

        result = await self._request("GET", "/verfahren/search", params=params)
        return result if isinstance(result, list) else []

    async def get_verfahren(self, verfahren_id: str) -> Any:
        """Einzelnes Verfahren mit Bescheiden und Auflagen"""
        return await self._request("GET", f"/verfahren/{verfahren_id}")

    # =========================================================================
    # Messungen
    # =========================================================================

    async def search_messungen(
        self,
        bst_nr: Optional[str] = None,
        anl_nr: Optional[str] = None,
        messart: Optional[str] = None,
        ueberschreitung: Optional[bool] = None,
        von_datum: Optional[str] = None,
        bis_datum: Optional[str] = None,
        limit: int = 200,
    ) -> Any:
        """Messungen suchen"""
        params: Dict[str, Any] = {"limit": limit}
        if bst_nr:
            params["bst_nr"] = bst_nr
        if anl_nr:
            params["anl_nr"] = anl_nr
        if messart:
            params["messart"] = messart
        if ueberschreitung is not None:
            params["ueberschreitung"] = str(ueberschreitung).lower()
        if von_datum:
            params["von_datum"] = von_datum
        if bis_datum:
            params["bis_datum"] = bis_datum

        result = await self._request("GET", "/messungen/search", params=params)
        return result if isinstance(result, list) else []

    # =========================================================================
    # Überwachung
    # =========================================================================

    async def search_ueberwachung(
        self, bst_nr: Optional[str] = None, anl_nr: Optional[str] = None, status: Optional[str] = None, limit: int = 100
    ) -> Any:
        """Überwachungsmaßnahmen suchen"""
        params: Dict[str, Any] = {"limit": limit}
        if bst_nr:
            params["bst_nr"] = bst_nr
        if anl_nr:
            params["anl_nr"] = anl_nr
        if status:
            params["status"] = status

        result = await self._request("GET", "/ueberwachung/search", params=params)
        return result if isinstance(result, list) else []

    # =========================================================================
    # Mängel
    # =========================================================================

    async def search_maengel(
        self,
        bst_nr: Optional[str] = None,
        anl_nr: Optional[str] = None,
        status: Optional[str] = None,
        schweregrad: Optional[str] = None,
        limit: int = 100,
    ) -> Any:
        """Mängel suchen"""
        params: Dict[str, Any] = {"limit": limit}
        if bst_nr:
            params["bst_nr"] = bst_nr
        if anl_nr:
            params["anl_nr"] = anl_nr
        if status:
            params["status"] = status
        if schweregrad:
            params["schweregrad"] = schweregrad

        result = await self._request("GET", "/maengel/search", params=params)
        return result if isinstance(result, list) else []

    # =========================================================================
    # Cross-Database Query (WICHTIG!)
    # =========================================================================

    async def get_anlage_complete(
        self, bst_nr: str, anl_nr: str, include_messungen: bool = True, include_verfahren: bool = True
    ) -> Optional[AnlageComplete]:
        """
        Vollständige Anlagen-Daten über alle Datenbanken

        Returns:
            AnlageComplete oder None bei Fehler
        """
        params: Dict[str, Any] = {
            "include_messungen": str(include_messungen).lower(),
            "include_verfahren": str(include_verfahren).lower(),
        }

        result = await self._request("GET", f"/anlage-complete/{bst_nr}/{anl_nr}", params=params)

        if "error" in result:
            logger.error(f"Fehler bei get_anlage_complete: {result}")
            return None

        try:
            # Parse Response
            anlage_data = result.get("anlage", {})
            anlage = AnlageBasic(**anlage_data)

            verfahren = [Verfahren(**v) for v in result.get("verfahren", [])]
            # Ensure numeric fields are converted safely for Messung
            raw_messungen = result.get("messungen", [])
            messungen = [self._parse_messung(m) for m in raw_messungen]
            ueberwachungen = [Ueberwachung(**u) for u in result.get("ueberwachungen", [])]
            maengel = [Mangel(**m) for m in result.get("maengel", [])]
            statistik = result.get("statistik", {})

            return AnlageComplete(
                anlage=anlage,
                verfahren=verfahren,
                messungen=messungen,
                ueberwachungen=ueberwachungen,
                maengel=maengel,
                statistik=statistik,
            )

        except Exception as e:
            logger.error(f"Fehler beim Parsen von AnlageComplete: {e}", exc_info=True)
            return None

    # =========================================================================
    # NEUE METHODEN - Phase 2
    # =========================================================================

    async def search_dokumente(
        self,
        bst_nr: Optional[str] = None,
        anl_nr: Optional[str] = None,
        dokumenttyp: Optional[str] = None,
        status: str = "aktiv",
        limit: int = 50,
    ) -> Any:
        """
        Suche Dokumente

        Args:
            bst_nr: BST-Nummer
            anl_nr: Anlagen-Nummer
            dokumenttyp: Typ (Bescheid, Messbericht, Gutachten, etc.)
            status: Status (aktiv, archiviert)
            limit: Max. Anzahl

        Returns:
            Liste von Dokumenten
        """
        params: Dict[str, Any] = {"status": status, "limit": limit}
        if bst_nr:
            params["bst_nr"] = bst_nr
        if anl_nr:
            params["anl_nr"] = anl_nr
        if dokumenttyp:
            params["dokumenttyp"] = dokumenttyp

        result = await self._request("GET", "/dokumente/search", params=params)
        return result.get("dokumente", [])

    async def get_dokument(self, dokument_id: str) -> Any:
        """Einzelnes Dokument abrufen"""
        result = await self._request("GET", f"/dokumente/{dokument_id}")
        return result if "error" not in result else None

    async def search_ansprechpartner(
        self,
        bst_nr: Optional[str] = None,
        anl_nr: Optional[str] = None,
        funktion: Optional[str] = None,
        aktiv: int = 1,
        limit: int = 50,
    ) -> Any:
        """
        Suche Ansprechpartner

        Args:
            bst_nr: BST-Nummer
            anl_nr: Anlagen-Nummer
            funktion: Funktion (Betriebsleiter, Umweltschutzbeauftragter, etc.)
            aktiv: Nur aktive (1) oder alle (0)
            limit: Max. Anzahl

        Returns:
            Liste von Ansprechpartnern
        """
        params: Dict[str, Any] = {"aktiv": aktiv, "limit": limit}
        if bst_nr:
            params["bst_nr"] = bst_nr
        if anl_nr:
            params["anl_nr"] = anl_nr
        if funktion:
            params["funktion"] = funktion

        result = await self._request("GET", "/ansprechpartner/search", params=params)
        return result.get("ansprechpartner", [])

    async def search_wartung(
        self,
        bst_nr: Optional[str] = None,
        anl_nr: Optional[str] = None,
        wartungsart: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> Any:
        """
        Suche Wartungen

        Args:
            bst_nr: BST-Nummer
            anl_nr: Anlagen-Nummer
            wartungsart: Art (Routineinspektion, Kalibrierung, etc.)
            status: Status (geplant, durchgeführt, verschoben)
            limit: Max. Anzahl

        Returns:
            Liste von Wartungen
        """
        params: Dict[str, Any] = {"limit": limit}
        if bst_nr:
            params["bst_nr"] = bst_nr
        if anl_nr:
            params["anl_nr"] = anl_nr
        if wartungsart:
            params["wartungsart"] = wartungsart
        if status:
            params["status"] = status

        result = await self._request("GET", "/wartung/search", params=params)
        return result.get("wartungen", [])

    async def search_messreihen(
        self,
        bst_nr: Optional[str] = None,
        anl_nr: Optional[str] = None,
        messart: Optional[str] = None,
        bewertung: Optional[str] = None,
        limit: int = 50,
    ) -> Any:
        """
        Suche Messreihen (Zeitreihen-Analysen)

        Args:
            bst_nr: BST-Nummer
            anl_nr: Anlagen-Nummer
            messart: Messart (Lärm_Tag, PM10, etc.)
            bewertung: Bewertung (unauffällig, auffällig, kritisch)
            limit: Max. Anzahl

        Returns:
            Liste von Messreihen
        """
        params: Dict[str, Any] = {"limit": limit}
        if bst_nr:
            params["bst_nr"] = bst_nr
        if anl_nr:
            params["anl_nr"] = anl_nr
        if messart:
            params["messart"] = messart
        if bewertung:
            params["bewertung"] = bewertung

        result = await self._request("GET", "/messreihen/search", params=params)
        return result.get("messreihen", [])

    async def get_kritische_messreihen(self, limit: int = 20) -> Any:
        """
        Kritische Messreihen abrufen

        Returns:
            Liste kritischer Messreihen sortiert nach Überschreitungen
        """
        result = await self._request("GET", "/messreihen/kritische", params={"limit": limit})
        raw = result or {}
        return [self._parse_messreihe(mr) for mr in raw.get("messreihen", [])]

    async def search_behoerden(self, behoerde: Optional[str] = None, abteilung: Optional[str] = None, limit: int = 50) -> Any:
        """
        Suche Behörden-Kontakte

        Args:
            behoerde: Behörden-Name (partial match)
            abteilung: Abteilung (partial match)
            limit: Max. Anzahl

        Returns:
            Liste von Behörden-Kontakten
        """
        params: Dict[str, Any] = {"limit": limit}
        if behoerde:
            params["behoerde"] = behoerde
        if abteilung:
            params["abteilung"] = abteilung

        result = await self._request("GET", "/behoerden/search", params=params)
        return result.get("kontakte", [])

    async def search_compliance(
        self, bst_nr: Optional[str] = None, anl_nr: Optional[str] = None, ergebnis: Optional[str] = None, limit: int = 50
    ) -> Any:
        """
        Suche Compliance-Historie

        Args:
            bst_nr: BST-Nummer
            anl_nr: Anlagen-Nummer
            ergebnis: Prüfungsergebnis (Konform, Abweichungen, Kritisch)
            limit: Max. Anzahl

        Returns:
            Liste von Compliance-Prüfungen
        """
        params: Dict[str, Any] = {"limit": limit}
        if bst_nr:
            params["bst_nr"] = bst_nr
        if anl_nr:
            params["anl_nr"] = anl_nr
        if ergebnis:
            params["ergebnis"] = ergebnis

        result = await self._request("GET", "/compliance/search", params=params)
        return result.get("historie", [])

    async def get_anlage_extended(
        self, bst_nr: str, anl_nr: str, include_messungen: bool = True, include_dokumente: bool = True
    ) -> Optional[AnlageExtended]:
        """
        Erweiterte Cross-Database Query: Vollständige Anlagen-Daten mit ALLEN Relationen
        inkl. Dokumente, Ansprechpartner, Wartungen, Messreihen, Compliance-Historie

        Args:
            bst_nr: BST-Nummer
            anl_nr: Anlagen-Nummer
            include_messungen: Messungen einbeziehen
            include_dokumente: Dokumente einbeziehen

        Returns:
            AnlageExtended oder None bei Fehler
        """
        params: Dict[str, Any] = {
            "include_messungen": str(include_messungen).lower(),
            "include_dokumente": str(include_dokumente).lower(),
        }

        result = await self._request("GET", f"/anlage-extended/{bst_nr}/{anl_nr}", params=params)

        if "error" in result:
            logger.error(f"Fehler bei get_anlage_extended: {result}")
            return None

        try:
            # Parse Response
            anlage_data = result.get("anlage", {})
            anlage = AnlageBasic(**anlage_data)

            verfahren = [Verfahren(**v) for v in result.get("verfahren", [])]
            # See get_anlage_complete for safe parsing of numeric fields
            raw_messungen = result.get("messungen", [])
            messungen = [self._parse_messung(m) for m in raw_messungen]
            ueberwachungen = [Ueberwachung(**u) for u in result.get("ueberwachungen", [])]
            maengel = [Mangel(**m) for m in result.get("maengel", [])]
            dokumente = [Dokument(**d) for d in result.get("dokumente", [])]
            ansprechpartner = [Ansprechpartner(**a) for a in result.get("ansprechpartner", [])]
            wartungen = [Wartung(**w) for w in result.get("wartungen", [])]
            messreihen = [Messreihe(**mr) for mr in result.get("messreihen", [])]
            compliance_historie = [ComplianceHistorie(**ch) for ch in result.get("compliance_historie", [])]
            statistik = result.get("statistik", {})

            return AnlageExtended(
                anlage=anlage,
                verfahren=verfahren,
                messungen=messungen,
                ueberwachungen=ueberwachungen,
                maengel=maengel,
                dokumente=dokumente,
                ansprechpartner=ansprechpartner,
                wartungen=wartungen,
                messreihen=messreihen,
                compliance_historie=compliance_historie,
                statistik=statistik,
            )

        except Exception as e:
            logger.error(f"Fehler beim Parsen von AnlageExtended: {e}", exc_info=True)
            return None

    # =========================================================================
    # Convenience Methods
    # =========================================================================

    async def get_grenzwertueberschreitungen(
        self, bst_nr: Optional[str] = None, anl_nr: Optional[str] = None, von_datum: Optional[str] = None, limit: int = 100
    ) -> Any:
        """Nur Grenzwertüberschreitungen abrufen"""
        return await self.search_messungen(
            bst_nr=bst_nr, anl_nr=anl_nr, ueberschreitung=True, von_datum=von_datum, limit=limit
        )

    async def get_offene_maengel(self, bst_nr: Optional[str] = None, schweregrad: Optional[str] = None) -> Any:
        """Nur offene Mängel abrufen"""
        return await self.search_maengel(bst_nr=bst_nr, status="offen", schweregrad=schweregrad)

    async def get_kritische_anlagen(self) -> Any:
        """
        Anlagen mit kritischen Mängeln oder häufigen Überschreitungen
        """
        # Kritische Mängel
        kritische_maengel = await self.search_maengel(status="offen", schweregrad="kritisch")

        # Sammle BST/ANL Paare
        anlage_ids = set()
        for mangel in kritische_maengel:
            anlage_ids.add((mangel["bst_nr"], mangel["anl_nr"]))

        # Hole Details für jede Anlage
        results = []
        for bst_nr, anl_nr in anlage_ids:
            anlage = await self.get_anlage_complete(bst_nr, anl_nr)
            if anlage:
                results.append(
                    {
                        "anlage": anlage.anlage.__dict__,
                        "kritische_maengel": len(
                            [m for m in anlage.maengel if m.schweregrad == "kritisch" and m.status == "offen"]
                        ),
                        "ueberschreitungen": anlage.statistik.get("messungen_ueberschreitungen", 0),
                    }
                )

        return results


# =============================================================================
# Singleton Instance
# =============================================================================

_test_server_client: Optional[TestServerClient] = None


def get_test_server_client(config: Optional[TestServerConfig] = None) -> TestServerClient:
    """
    Singleton-Pattern für TestServerClient
    """
    global _test_server_client

    if _test_server_client is None:
        _test_server_client = TestServerClient(config)

    return _test_server_client


# =============================================================================
# Context Manager Support
# =============================================================================


class TestServerClientContext:
    """Context Manager für automatisches Session-Cleanup"""

    def __init__(self, config: Optional[TestServerConfig] = None):
        self.config = config
        self.client: Optional[TestServerClient] = None

    async def __aenter__(self) -> TestServerClient:
        self.client = TestServerClient(self.config)
        return self.client

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.close()


# =============================================================================
# Usage Example
# =============================================================================


async def example_usage():
    """Beispiel-Nutzung"""

    # Mit Context Manager
    async with TestServerClientContext() as client:
        # Health Check
        health = await client.health_check()
        print(f"Server Status: {health.get('status')}")

        # Anlagen suchen
        anlagen = await client.search_anlagen(db="bimschg", ort="Gransee", limit=5)
        print(f"Gefundene Anlagen: {anlagen.get('count')}")

        # Vollständige Daten einer Anlage (Basis)
        anlage = await client.get_anlage_complete("10650200000", "4001")
        if anlage:
            print(f"Anlage: {anlage.anlage.bst_name}")
            print(f"Verfahren: {len(anlage.verfahren)}")
            print(f"Messungen: {len(anlage.messungen)}")
            print(f"Überschreitungen: {anlage.statistik.get('messungen_ueberschreitungen')}")

        # ERWEITERTE Daten mit allen neuen Relationen
        anlage_ext = await client.get_anlage_extended("10650200000", "4001")
        if anlage_ext:
            print(f"\n🔍 Erweiterte Daten:")
            print(f"  Dokumente: {len(anlage_ext.dokumente)}")
            print(f"  Ansprechpartner: {len(anlage_ext.ansprechpartner)}")
            print(f"  Wartungen: {len(anlage_ext.wartungen)}")
            print(f"  Messreihen: {len(anlage_ext.messreihen)}")
            print(f"  Compliance-Historie: {len(anlage_ext.compliance_historie)}")

        # Neue Suchmethoden
        dokumente = await client.search_dokumente(dokumenttyp="Messbericht", limit=5)
        print(f"\nMessberichte: {len(dokumente)}")

        kritische_messreihen = await client.get_kritische_messreihen(limit=5)
        print(f"Kritische Messreihen: {len(kritische_messreihen)}")

        wartungen = await client.search_wartung(status="geplant", limit=5)
        print(f"Geplante Wartungen: {len(wartungen)}")

        # Grenzwertüberschreitungen
        ueberschreitungen = await client.get_grenzwertueberschreitungen(limit=10)
        print(f"Grenzwertüberschreitungen: {len(ueberschreitungen)}")


if __name__ == "__main__":
    # Test
    asyncio.run(example_usage())
