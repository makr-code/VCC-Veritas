"""
Immissionsschutz Test-Server - Eigenständige FastAPI Instanz
============================================================

Separater Server für Immissionsschutz-Datenbanken
Bietet vollständige relationale API für Agenten-Tests

Port: 5001 (getrennt von VERITAS Backend)
Docs: http://localhost:5001/docs
Health: http://localhost:5001/health

Datenbanken:
- BImSchG (Anlagen)
- WKA (Windkraftanlagen)
- Immissionsschutz Test DB (Verfahren, Messungen, Auflagen, etc.)
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal
import sqlite3
from pathlib import Path
from functools import lru_cache
import re
from datetime import datetime
import logging

# ============================================================================
# Logging Setup
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# ============================================================================
# Pfade
# ============================================================================

# Server liegt in: data/test_databases/immissionsschutz_test_server.py
# Projekt-Root ist 2 Ebenen höher
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATABASES = {
    "bimschg": {
        "path": PROJECT_ROOT / "data" / "bimschg" / "BImSchG.sqlite",
        "table": "bimschg",
        "description": "BImSchG genehmigte Anlagen",
        "type": "reference"
    },
    "wka": {
        "path": PROJECT_ROOT / "data" / "wka" / "wka.sqlite",
        "table": "wka",
        "description": "Windkraftanlagen",
        "type": "reference"
    },
    "immissionsschutz": {
        "path": PROJECT_ROOT / "data" / "test_databases" / "immissionsschutz_test.sqlite",
        "tables": {
            "verfahren": "genehmigungsverfahren",
            "bescheide": "bescheide",
            "auflagen": "auflagen",
            "ueberwachung": "ueberwachung",
            "messungen": "messungen",
            "maengel": "maengel",
            "dokumente": "dokumente",
            "ansprechpartner": "ansprechpartner",
            "wartung": "wartung",
            "messreihen": "messreihen",
            "behoerden_kontakte": "behoerden_kontakte",
            "compliance_historie": "compliance_historie"
        },
        "description": "Vollständige Immissionsschutz-Daten mit erweiterten Tabellen",
        "type": "test"
    }
}

# ============================================================================
# Pydantic Models
# ============================================================================

class DatabaseInfo(BaseModel):
    """Datenbank-Info"""
    name: str
    description: str
    type: str
    available: bool
    size_mb: Optional[float] = None
    tables: Optional[Dict[str, str]] = None

class AnlageBasic(BaseModel):
    """Basis-Anlagen-Daten"""
    bst_nr: str
    bst_name: Optional[str] = None
    anl_nr: str
    anl_bez: Optional[str] = None
    ort: Optional[str] = None
    ortsteil: Optional[str] = None
    ostwert: Optional[float] = None
    nordwert: Optional[float] = None

class Verfahren(BaseModel):
    """Genehmigungsverfahren"""
    verfahren_id: str
    bst_nr: str
    anl_nr: str
    verfahrensart: str
    antragsdatum: str
    entscheidungsdatum: Optional[str] = None
    status: str
    behoerde: str
    aktenzeichen: str
    oeffentliche_beteiligung: int
    uvp_erforderlich: int

class Bescheid(BaseModel):
    """Bescheid"""
    bescheid_id: str
    verfahren_id: str
    bescheiddatum: str
    bescheidtyp: str
    rechtskraft_datum: Optional[str] = None
    befristet: int
    befristung_bis: Optional[str] = None
    auflagen_anzahl: int

class Auflage(BaseModel):
    """Auflage"""
    auflagen_id: str
    bescheid_id: str
    auflage_nr: int
    auflagentext: str
    kategorie: Optional[str] = None
    messbar: int
    grenzwert: Optional[float] = None
    einheit: Optional[str] = None
    status: str

class Messung(BaseModel):
    """Messung"""
    messung_id: str
    bst_nr: str
    anl_nr: str
    messart: str
    messdatum: str
    messzeit: str
    messwert: float
    einheit: str
    grenzwert: Optional[float] = None
    ueberschreitung: int
    messstelle: Optional[str] = None

class Ueberwachung(BaseModel):
    """Überwachung"""
    ueberwachung_id: str
    bst_nr: str
    anl_nr: str
    ueberwachungsart: str
    geplant_datum: str
    durchgefuehrt_datum: Optional[str] = None
    status: str
    behoerde: str
    ergebnis: Optional[str] = None

class Mangel(BaseModel):
    """Mangel"""
    mangel_id: str
    ueberwachung_id: Optional[str] = None
    bst_nr: str
    anl_nr: str
    festgestellt_datum: str
    mangelart: str
    schweregrad: str
    beschreibung: str
    status: str

# ============================================================================
# NEUE MODELS - Phase 2
# ============================================================================

class Dokument(BaseModel):
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
    status: str

class Ansprechpartner(BaseModel):
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
    notfallkontakt: int
    aktiv: int

class Wartung(BaseModel):
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
    status: str
    beschreibung: Optional[str] = None
    massnahmen: Optional[str] = None

class Messreihe(BaseModel):
    """Messreihe (Zeitreihe)"""
    messreihe_id: str
    bst_nr: str
    anl_nr: str
    messart: str
    zeitraum_von: str
    zeitraum_bis: str
    anzahl_messungen: int
    mittelwert: float
    maximalwert: float
    minimalwert: float
    standardabweichung: float
    ueberschreitungen_anzahl: int
    trend: str
    bewertung: str

class BehoerdenKontakt(BaseModel):
    """Behörden-Kontakt"""
    kontakt_id: str
    behoerde: str
    sachbearbeiter: str
    abteilung: Optional[str] = None
    telefon: Optional[str] = None
    email: Optional[str] = None
    zustaendig_fuer: Optional[str] = None
    bemerkungen: Optional[str] = None

class ComplianceHistorie(BaseModel):
    """Compliance-Historie"""
    historie_id: str
    bst_nr: str
    anl_nr: str
    pruefungsdatum: str
    pruefungstyp: str
    ergebnis: str
    bewertung_punkte: int
    feststellungen: Optional[str] = None
    empfehlungen: Optional[str] = None
    folgepruefung: Optional[str] = None

class AnlageComplete(BaseModel):
    """Vollständige Anlagen-Daten mit allen Relationen"""
    anlage: AnlageBasic
    verfahren: List[Verfahren] = []
    bescheide: List[Bescheid] = []
    messungen: List[Messung] = []
    ueberwachungen: List[Ueberwachung] = []
    maengel: List[Mangel] = []
    statistik: Dict[str, Any] = {}

class AnlageExtended(BaseModel):
    """Erweiterte Anlagen-Daten mit ALLEN Relationen inkl. neuer Tabellen"""
    anlage: AnlageBasic
    verfahren: List[Verfahren] = []
    bescheide: List[Bescheid] = []
    messungen: List[Messung] = []
    ueberwachungen: List[Ueberwachung] = []
    maengel: List[Mangel] = []
    dokumente: List[Dokument] = []
    ansprechpartner: List[Ansprechpartner] = []
    wartungen: List[Wartung] = []
    messreihen: List[Messreihe] = []
    compliance_historie: List[ComplianceHistorie] = []
    statistik: Dict[str, Any] = {}

class StatistikResponse(BaseModel):
    """Statistik"""
    database: str
    table: Optional[str] = None
    total_records: int
    statistics: Dict[str, Any]

# ============================================================================
# Hilfsfunktionen
# ============================================================================

def get_db_connection(db_name: str) -> sqlite3.Connection:
    """Datenbankverbindung"""
    if db_name not in DATABASES:
        raise HTTPException(status_code=404, detail=f"Database '{db_name}' not found")
    
    db_info = DATABASES[db_name]
    if not db_info["path"].exists():
        raise HTTPException(status_code=500, detail=f"Database file not found")
    
    conn = sqlite3.connect(db_info["path"])
    conn.row_factory = sqlite3.Row
    return conn

def validate_sql(sql: str) -> bool:
    """SQL-Validierung (nur SELECT)"""
    sql_clean = sql.strip().upper()
    if not sql_clean.startswith("SELECT"):
        raise HTTPException(status_code=400, detail="Only SELECT queries allowed")
    
    forbidden = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE"]
    for cmd in forbidden:
        if re.search(rf'\b{cmd}\b', sql_clean):
            raise HTTPException(status_code=400, detail=f"Command '{cmd}' not allowed")
    return True

# ============================================================================
# FastAPI App
# ============================================================================

app = FastAPI(
    title="Immissionsschutz Test-Server",
    description="Eigenständige FastAPI-Instanz für Immissionsschutz-Daten",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# ============================================================================
# Root Endpoints
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Immissionsschutz Test-Server",
        "version": "1.0.0",
        "port": 5001,
        "documentation": "/docs",
        "health": "/health",
        "databases": list(DATABASES.keys())
    }

@app.get("/health")
async def health():
    """Health check"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "databases": {}
    }
    
    for name, info in DATABASES.items():
        try:
            conn = get_db_connection(name)
            conn.close()
            health_status["databases"][name] = "ok"
        except Exception as e:
            health_status["databases"][name] = f"error: {str(e)}"
            health_status["status"] = "degraded"
    
    return health_status

@app.get("/databases", response_model=List[DatabaseInfo])
async def list_databases():
    """Liste aller Datenbanken"""
    db_list = []
    
    for name, info in DATABASES.items():
        available = info["path"].exists()
        size_mb = None
        
        if available:
            try:
                size_mb = info["path"].stat().st_size / (1024 * 1024)
            except:
                pass
        
        tables = info.get("tables") if info["type"] == "test" else {name: info.get("table")}
        
        db_list.append(DatabaseInfo(
            name=name,
            description=info["description"],
            type=info["type"],
            available=available,
            size_mb=size_mb,
            tables=tables
        ))
    
    return db_list

# ============================================================================
# Anlagen-Endpoints (BImSchG & WKA)
# ============================================================================

@app.get("/anlagen/search")
async def search_anlagen(
    db: Literal["bimschg", "wka"] = "bimschg",
    bst_nr: Optional[str] = None,
    anl_nr: Optional[str] = None,
    ort: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500)
):
    """Anlagen suchen"""
    conn = get_db_connection(db)
    cursor = conn.cursor()
    table = DATABASES[db]["table"]
    
    conditions = []
    params = []
    
    if bst_nr:
        conditions.append("CAST(bst_nr AS TEXT) LIKE ?")
        params.append(f"%{bst_nr}%")
    if anl_nr:
        conditions.append("anl_nr LIKE ?")
        params.append(f"%{anl_nr}%")
    if ort:
        conditions.append("ort LIKE ?")
        params.append(f"%{ort}%")
    
    where = " AND ".join(conditions) if conditions else "1=1"
    query = f"SELECT * FROM {table} WHERE {where} LIMIT ?"
    params.append(limit)
    
    rows = cursor.execute(query, params).fetchall()
    results = [dict(row) for row in rows]
    conn.close()
    
    return {"database": db, "count": len(results), "results": results}

@app.get("/anlagen/{db}/{bst_nr}/{anl_nr}")
async def get_anlage(
    db: Literal["bimschg", "wka"],
    bst_nr: str,
    anl_nr: str
):
    """Einzelne Anlage abrufen"""
    conn = get_db_connection(db)
    cursor = conn.cursor()
    table = DATABASES[db]["table"]
    
    query = f"SELECT * FROM {table} WHERE CAST(bst_nr AS TEXT) = ? AND anl_nr = ?"
    row = cursor.execute(query, (bst_nr, anl_nr)).fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Anlage not found")
    
    return dict(row)

# ============================================================================
# Verfahren-Endpoints
# ============================================================================

@app.get("/verfahren/search", response_model=List[Verfahren])
async def search_verfahren(
    bst_nr: Optional[str] = None,
    anl_nr: Optional[str] = None,
    status: Optional[str] = None,
    von_datum: Optional[str] = None,
    bis_datum: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000)
):
    """Verfahren suchen"""
    conn = get_db_connection("immissionsschutz")
    cursor = conn.cursor()
    
    conditions = []
    params = []
    
    if bst_nr:
        conditions.append("bst_nr LIKE ?")
        params.append(f"%{bst_nr}%")
    if anl_nr:
        conditions.append("anl_nr LIKE ?")
        params.append(f"%{anl_nr}%")
    if status:
        conditions.append("status = ?")
        params.append(status)
    if von_datum:
        conditions.append("antragsdatum >= ?")
        params.append(von_datum)
    if bis_datum:
        conditions.append("antragsdatum <= ?")
        params.append(bis_datum)
    
    where = " AND ".join(conditions) if conditions else "1=1"
    query = f"SELECT * FROM genehmigungsverfahren WHERE {where} LIMIT ?"
    params.append(limit)
    
    rows = cursor.execute(query, params).fetchall()
    conn.close()
    
    return [Verfahren(**dict(row)) for row in rows]

@app.get("/verfahren/{verfahren_id}")
async def get_verfahren(verfahren_id: str):
    """Einzelnes Verfahren mit Bescheiden und Auflagen"""
    conn = get_db_connection("immissionsschutz")
    cursor = conn.cursor()
    
    # Verfahren
    verfahren = cursor.execute(
        "SELECT * FROM genehmigungsverfahren WHERE verfahren_id = ?",
        (verfahren_id,)
    ).fetchone()
    
    if not verfahren:
        conn.close()
        raise HTTPException(status_code=404, detail="Verfahren not found")
    
    # Bescheide
    bescheide = cursor.execute(
        "SELECT * FROM bescheide WHERE verfahren_id = ?",
        (verfahren_id,)
    ).fetchall()
    
    # Auflagen (für alle Bescheide)
    auflagen = []
    for bescheid in bescheide:
        auflagen_rows = cursor.execute(
            "SELECT * FROM auflagen WHERE bescheid_id = ?",
            (bescheid["bescheid_id"],)
        ).fetchall()
        auflagen.extend([dict(row) for row in auflagen_rows])
    
    conn.close()
    
    return {
        "verfahren": dict(verfahren),
        "bescheide": [dict(b) for b in bescheide],
        "auflagen": auflagen
    }

# ============================================================================
# Messungen-Endpoints
# ============================================================================

@app.get("/messungen/search", response_model=List[Messung])
async def search_messungen(
    bst_nr: Optional[str] = None,
    anl_nr: Optional[str] = None,
    messart: Optional[str] = None,
    ueberschreitung: Optional[bool] = None,
    von_datum: Optional[str] = None,
    bis_datum: Optional[str] = None,
    limit: int = Query(200, ge=1, le=2000)
):
    """Messungen suchen"""
    conn = get_db_connection("immissionsschutz")
    cursor = conn.cursor()
    
    conditions = []
    params = []
    
    if bst_nr:
        conditions.append("bst_nr LIKE ?")
        params.append(f"%{bst_nr}%")
    if anl_nr:
        conditions.append("anl_nr LIKE ?")
        params.append(f"%{anl_nr}%")
    if messart:
        conditions.append("messart LIKE ?")
        params.append(f"%{messart}%")
    if ueberschreitung is not None:
        conditions.append("ueberschreitung = ?")
        params.append(1 if ueberschreitung else 0)
    if von_datum:
        conditions.append("messdatum >= ?")
        params.append(von_datum)
    if bis_datum:
        conditions.append("messdatum <= ?")
        params.append(bis_datum)
    
    where = " AND ".join(conditions) if conditions else "1=1"
    query = f"SELECT * FROM messungen WHERE {where} ORDER BY messdatum DESC LIMIT ?"
    params.append(limit)
    
    rows = cursor.execute(query, params).fetchall()
    conn.close()
    
    return [Messung(**dict(row)) for row in rows]

# ============================================================================
# Überwachung-Endpoints
# ============================================================================

@app.get("/ueberwachung/search", response_model=List[Ueberwachung])
async def search_ueberwachung(
    bst_nr: Optional[str] = None,
    anl_nr: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000)
):
    """Überwachungen suchen"""
    conn = get_db_connection("immissionsschutz")
    cursor = conn.cursor()
    
    conditions = []
    params = []
    
    if bst_nr:
        conditions.append("bst_nr LIKE ?")
        params.append(f"%{bst_nr}%")
    if anl_nr:
        conditions.append("anl_nr LIKE ?")
        params.append(f"%{anl_nr}%")
    if status:
        conditions.append("status = ?")
        params.append(status)
    
    where = " AND ".join(conditions) if conditions else "1=1"
    query = f"SELECT * FROM ueberwachung WHERE {where} LIMIT ?"
    params.append(limit)
    
    rows = cursor.execute(query, params).fetchall()
    conn.close()
    
    return [Ueberwachung(**dict(row)) for row in rows]

# ============================================================================
# Mängel-Endpoints
# ============================================================================

@app.get("/maengel/search", response_model=List[Mangel])
async def search_maengel(
    bst_nr: Optional[str] = None,
    anl_nr: Optional[str] = None,
    status: Optional[str] = None,
    schweregrad: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000)
):
    """Mängel suchen"""
    conn = get_db_connection("immissionsschutz")
    cursor = conn.cursor()
    
    conditions = []
    params = []
    
    if bst_nr:
        conditions.append("bst_nr LIKE ?")
        params.append(f"%{bst_nr}%")
    if anl_nr:
        conditions.append("anl_nr LIKE ?")
        params.append(f"%{anl_nr}%")
    if status:
        conditions.append("status = ?")
        params.append(status)
    if schweregrad:
        conditions.append("schweregrad = ?")
        params.append(schweregrad)
    
    where = " AND ".join(conditions) if conditions else "1=1"
    query = f"SELECT * FROM maengel WHERE {where} LIMIT ?"
    params.append(limit)
    
    rows = cursor.execute(query, params).fetchall()
    conn.close()
    
    return [Mangel(**dict(row)) for row in rows]

# ============================================================================
# Komplexe Queries - Cross-Database
# ============================================================================

@app.get("/anlage-complete/{bst_nr}/{anl_nr}", response_model=AnlageComplete)
async def get_anlage_complete(
    bst_nr: str,
    anl_nr: str,
    include_messungen: bool = True,
    include_verfahren: bool = True
):
    """
    Vollständige Anlagen-Daten mit allen Relationen
    Cross-Database Query über BImSchG/WKA + Immissionsschutz
    """
    # 1. Basis-Anlage (BImSchG oder WKA)
    anlage_data = None
    
    try:
        conn_bimschg = get_db_connection("bimschg")
        cursor = conn_bimschg.cursor()
        row = cursor.execute(
            "SELECT * FROM bimschg WHERE CAST(bst_nr AS TEXT) = ? AND anl_nr = ?",
            (bst_nr, anl_nr)
        ).fetchone()
        conn_bimschg.close()
        
        if row:
            anlage_data = dict(row)
    except:
        pass
    
    if not anlage_data:
        try:
            conn_wka = get_db_connection("wka")
            cursor = conn_wka.cursor()
            row = cursor.execute(
                "SELECT * FROM wka WHERE bst_nr = ? AND anl_nr = ?",
                (bst_nr, anl_nr)
            ).fetchone()
            conn_wka.close()
            
            if row:
                anlage_data = dict(row)
        except:
            pass
    
    if not anlage_data:
        raise HTTPException(status_code=404, detail="Anlage not found")
    
    # 2. Relationale Daten
    conn = get_db_connection("immissionsschutz")
    cursor = conn.cursor()
    
    # Verfahren
    verfahren = []
    bescheide = []
    if include_verfahren:
        verfahren_rows = cursor.execute(
            "SELECT * FROM genehmigungsverfahren WHERE bst_nr LIKE ? AND anl_nr LIKE ?",
            (f"%{bst_nr}%", f"%{anl_nr}%")
        ).fetchall()
        verfahren = [Verfahren(**dict(row)) for row in verfahren_rows]
        
        # Bescheide
        for v in verfahren:
            bescheid_rows = cursor.execute(
                "SELECT * FROM bescheide WHERE verfahren_id = ?",
                (v.verfahren_id,)
            ).fetchall()
            bescheide.extend([Bescheid(**dict(row)) for row in bescheid_rows])
    
    # Messungen
    messungen = []
    if include_messungen:
        messung_rows = cursor.execute(
            "SELECT * FROM messungen WHERE bst_nr LIKE ? AND anl_nr LIKE ? LIMIT 50",
            (f"%{bst_nr}%", f"%{anl_nr}%")
        ).fetchall()
        messungen = [Messung(**dict(row)) for row in messung_rows]
    
    # Überwachungen
    ueberwachung_rows = cursor.execute(
        "SELECT * FROM ueberwachung WHERE bst_nr LIKE ? AND anl_nr LIKE ? LIMIT 20",
        (f"%{bst_nr}%", f"%{anl_nr}%")
    ).fetchall()
    ueberwachungen = [Ueberwachung(**dict(row)) for row in ueberwachung_rows]
    
    # Mängel
    maengel_rows = cursor.execute(
        "SELECT * FROM maengel WHERE bst_nr LIKE ? AND anl_nr LIKE ? LIMIT 20",
        (f"%{bst_nr}%", f"%{anl_nr}%")
    ).fetchall()
    maengel = [Mangel(**dict(row)) for row in maengel_rows]
    
    # Statistik
    statistik = {
        "verfahren_count": len(verfahren),
        "bescheide_count": len(bescheide),
        "messungen_count": len(messungen),
        "messungen_ueberschreitungen": len([m for m in messungen if m.ueberschreitung == 1]),
        "ueberwachungen_count": len(ueberwachungen),
        "maengel_count": len(maengel),
        "maengel_offen": len([m for m in maengel if m.status == "offen"])
    }
    
    conn.close()
    
    # Basis-Anlage
    anlage_basic = AnlageBasic(
        bst_nr=str(anlage_data.get("bst_nr", "")),
        bst_name=anlage_data.get("bst_name"),
        anl_nr=str(anlage_data.get("anl_nr", "")),
        anl_bez=anlage_data.get("anl_bez"),
        ort=anlage_data.get("ort"),
        ortsteil=anlage_data.get("ortsteil"),
        ostwert=anlage_data.get("ostwert"),
        nordwert=anlage_data.get("nordwert")
    )
    
    return AnlageComplete(
        anlage=anlage_basic,
        verfahren=verfahren,
        bescheide=bescheide,
        messungen=messungen,
        ueberwachungen=ueberwachungen,
        maengel=maengel,
        statistik=statistik
    )

# ============================================================================
# Statistik-Endpoints
# ============================================================================

@app.get("/statistik/overview")
async def statistik_overview():
    """Gesamtstatistik aller Datenbanken"""
    conn = get_db_connection("immissionsschutz")
    cursor = conn.cursor()
    
    stats = {
        "verfahren": {
            "total": cursor.execute("SELECT COUNT(*) FROM genehmigungsverfahren").fetchone()[0],
            "genehmigt": cursor.execute("SELECT COUNT(*) FROM genehmigungsverfahren WHERE status = 'genehmigt'").fetchone()[0],
            "in_bearbeitung": cursor.execute("SELECT COUNT(*) FROM genehmigungsverfahren WHERE status = 'in_bearbeitung'").fetchone()[0],
        },
        "messungen": {
            "total": cursor.execute("SELECT COUNT(*) FROM messungen").fetchone()[0],
            "ueberschreitungen": cursor.execute("SELECT COUNT(*) FROM messungen WHERE ueberschreitung = 1").fetchone()[0],
        },
        "ueberwachung": {
            "total": cursor.execute("SELECT COUNT(*) FROM ueberwachung").fetchone()[0],
            "geplant": cursor.execute("SELECT COUNT(*) FROM ueberwachung WHERE status = 'geplant'").fetchone()[0],
            "mit_maengeln": cursor.execute("SELECT COUNT(*) FROM ueberwachung WHERE ergebnis IN ('mängel_festgestellt', 'nachbesserung_erforderlich')").fetchone()[0],
        },
        "maengel": {
            "total": cursor.execute("SELECT COUNT(*) FROM maengel").fetchone()[0],
            "offen": cursor.execute("SELECT COUNT(*) FROM maengel WHERE status = 'offen'").fetchone()[0],
            "kritisch": cursor.execute("SELECT COUNT(*) FROM maengel WHERE schweregrad = 'kritisch' AND status != 'behoben'").fetchone()[0],
        }
    }
    
    conn.close()
    
    return {
        "timestamp": datetime.now().isoformat(),
        "statistics": stats
    }

# ============================================================================
# NEUE ENDPOINTS - Phase 2
# ============================================================================

@app.get("/dokumente/search", tags=["Dokumente"])
async def search_dokumente(
    bst_nr: Optional[str] = None,
    anl_nr: Optional[str] = None,
    dokumenttyp: Optional[str] = None,
    status: str = "aktiv",
    limit: int = 50
):
    """Suche Dokumente"""
    conn = get_db_connection("immissionsschutz")
    cursor = conn.cursor()
    
    query = "SELECT * FROM dokumente WHERE status = ?"
    params = [status]
    
    if bst_nr:
        query += " AND bst_nr = ?"
        params.append(bst_nr)
    
    if anl_nr:
        query += " AND anl_nr = ?"
        params.append(anl_nr)
    
    if dokumenttyp:
        query += " AND dokumenttyp = ?"
        params.append(dokumenttyp)
    
    query += " ORDER BY erstellt_datum DESC LIMIT ?"
    params.append(limit)
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    columns = [desc[0] for desc in cursor.description]
    dokumente = [dict(zip(columns, row)) for row in rows]
    
    conn.close()
    
    return {
        "count": len(dokumente),
        "dokumente": dokumente
    }

@app.get("/dokumente/{dokument_id}", tags=["Dokumente"])
async def get_dokument(dokument_id: str):
    """Einzelnes Dokument abrufen"""
    conn = get_db_connection("immissionsschutz")
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM dokumente WHERE dokument_id = ?", (dokument_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Dokument nicht gefunden")
    
    columns = [desc[0] for desc in cursor.description]
    dokument = dict(zip(columns, row))
    
    conn.close()
    
    return dokument

@app.get("/ansprechpartner/search", tags=["Ansprechpartner"])
async def search_ansprechpartner(
    bst_nr: Optional[str] = None,
    anl_nr: Optional[str] = None,
    funktion: Optional[str] = None,
    aktiv: int = 1,
    limit: int = 50
):
    """Suche Ansprechpartner"""
    conn = get_db_connection("immissionsschutz")
    cursor = conn.cursor()
    
    query = "SELECT * FROM ansprechpartner WHERE aktiv = ?"
    params = [aktiv]
    
    if bst_nr:
        query += " AND bst_nr = ?"
        params.append(bst_nr)
    
    if anl_nr:
        query += " AND anl_nr = ?"
        params.append(anl_nr)
    
    if funktion:
        query += " AND funktion LIKE ?"
        params.append(f"%{funktion}%")
    
    query += " LIMIT ?"
    params.append(limit)
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    columns = [desc[0] for desc in cursor.description]
    ansprechpartner = [dict(zip(columns, row)) for row in rows]
    
    conn.close()
    
    return {
        "count": len(ansprechpartner),
        "ansprechpartner": ansprechpartner
    }

@app.get("/wartung/search", tags=["Wartung"])
async def search_wartung(
    bst_nr: Optional[str] = None,
    anl_nr: Optional[str] = None,
    wartungsart: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50
):
    """Suche Wartungen"""
    conn = get_db_connection("immissionsschutz")
    cursor = conn.cursor()
    
    query = "SELECT * FROM wartung WHERE 1=1"
    params = []
    
    if bst_nr:
        query += " AND bst_nr = ?"
        params.append(bst_nr)
    
    if anl_nr:
        query += " AND anl_nr = ?"
        params.append(anl_nr)
    
    if wartungsart:
        query += " AND wartungsart = ?"
        params.append(wartungsart)
    
    if status:
        query += " AND status = ?"
        params.append(status)
    
    query += " ORDER BY geplant_datum DESC LIMIT ?"
    params.append(limit)
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    columns = [desc[0] for desc in cursor.description]
    wartungen = [dict(zip(columns, row)) for row in rows]
    
    conn.close()
    
    return {
        "count": len(wartungen),
        "wartungen": wartungen
    }

@app.get("/messreihen/search", tags=["Messreihen"])
async def search_messreihen(
    bst_nr: Optional[str] = None,
    anl_nr: Optional[str] = None,
    messart: Optional[str] = None,
    bewertung: Optional[str] = None,
    limit: int = 50
):
    """Suche Messreihen (Zeitreihen-Analysen)"""
    conn = get_db_connection("immissionsschutz")
    cursor = conn.cursor()
    
    query = "SELECT * FROM messreihen WHERE 1=1"
    params = []
    
    if bst_nr:
        query += " AND bst_nr = ?"
        params.append(bst_nr)
    
    if anl_nr:
        query += " AND anl_nr = ?"
        params.append(anl_nr)
    
    if messart:
        query += " AND messart = ?"
        params.append(messart)
    
    if bewertung:
        query += " AND bewertung = ?"
        params.append(bewertung)
    
    query += " ORDER BY zeitraum_bis DESC LIMIT ?"
    params.append(limit)
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    columns = [desc[0] for desc in cursor.description]
    messreihen = [dict(zip(columns, row)) for row in rows]
    
    conn.close()
    
    return {
        "count": len(messreihen),
        "messreihen": messreihen
    }

@app.get("/messreihen/kritische", tags=["Messreihen"])
async def get_kritische_messreihen(limit: int = 20):
    """Kritische Messreihen abrufen"""
    conn = get_db_connection("immissionsschutz")
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM messreihen 
        WHERE bewertung = 'kritisch' 
        ORDER BY ueberschreitungen_anzahl DESC 
        LIMIT ?
    """, (limit,))
    
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    messreihen = [dict(zip(columns, row)) for row in rows]
    
    conn.close()
    
    return {
        "count": len(messreihen),
        "messreihen": messreihen
    }

@app.get("/behoerden/search", tags=["Behörden"])
async def search_behoerden(
    behoerde: Optional[str] = None,
    abteilung: Optional[str] = None,
    limit: int = 50
):
    """Suche Behörden-Kontakte"""
    conn = get_db_connection("immissionsschutz")
    cursor = conn.cursor()
    
    query = "SELECT * FROM behoerden_kontakte WHERE 1=1"
    params = []
    
    if behoerde:
        query += " AND behoerde LIKE ?"
        params.append(f"%{behoerde}%")
    
    if abteilung:
        query += " AND abteilung LIKE ?"
        params.append(f"%{abteilung}%")
    
    query += " LIMIT ?"
    params.append(limit)
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    columns = [desc[0] for desc in cursor.description]
    kontakte = [dict(zip(columns, row)) for row in rows]
    
    conn.close()
    
    return {
        "count": len(kontakte),
        "kontakte": kontakte
    }

@app.get("/compliance/search", tags=["Compliance"])
async def search_compliance(
    bst_nr: Optional[str] = None,
    anl_nr: Optional[str] = None,
    ergebnis: Optional[str] = None,
    limit: int = 50
):
    """Suche Compliance-Historie"""
    conn = get_db_connection("immissionsschutz")
    cursor = conn.cursor()
    
    query = "SELECT * FROM compliance_historie WHERE 1=1"
    params = []
    
    if bst_nr:
        query += " AND bst_nr = ?"
        params.append(bst_nr)
    
    if anl_nr:
        query += " AND anl_nr = ?"
        params.append(anl_nr)
    
    if ergebnis:
        query += " AND ergebnis = ?"
        params.append(ergebnis)
    
    query += " ORDER BY pruefungsdatum DESC LIMIT ?"
    params.append(limit)
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    columns = [desc[0] for desc in cursor.description]
    historie = [dict(zip(columns, row)) for row in rows]
    
    conn.close()
    
    return {
        "count": len(historie),
        "historie": historie
    }

@app.get("/anlage-extended/{bst_nr}/{anl_nr}", tags=["Anlagen"])
async def get_anlage_extended(
    bst_nr: str,
    anl_nr: str,
    include_messungen: bool = True,
    include_dokumente: bool = True
):
    """
    Erweiterte Cross-Database Query: Vollständige Anlagen-Daten mit ALLEN Relationen
    inkl. neuer Tabellen (Dokumente, Ansprechpartner, Wartung, Messreihen, Compliance)
    """
    
    # 1. Basis-Anlage aus BImSchG oder WKA
    anlage = None
    
    # BImSchG
    conn_bimschg = get_db_connection("bimschg")
    cursor_bimschg = conn_bimschg.cursor()
    cursor_bimschg.execute(
        "SELECT bst_nr, bst_name, anl_nr, anl_bez, ort, ortsteil, ostwert, nordwert FROM bimschg WHERE CAST(bst_nr AS TEXT) = ? AND anl_nr = ?",
        (bst_nr, anl_nr)
    )
    row = cursor_bimschg.fetchone()
    
    if row:
        anlage = AnlageBasic(
            bst_nr=str(row[0]),
            bst_name=row[1],
            anl_nr=row[2],
            anl_bez=row[3],
            ort=row[4],
            ortsteil=row[5],
            ostwert=row[6],
            nordwert=row[7]
        )
    
    conn_bimschg.close()
    
    # Falls nicht gefunden, in WKA suchen
    if not anlage:
        conn_wka = get_db_connection("wka")
        cursor_wka = conn_wka.cursor()
        cursor_wka.execute(
            "SELECT bst_nr, bst_name, anl_nr, anl_bez, ort, ortsteil, ostwert, nordwert FROM wka WHERE bst_nr = ? AND anl_nr = ?",
            (bst_nr, anl_nr)
        )
        row = cursor_wka.fetchone()
        
        if row:
            anlage = AnlageBasic(
                bst_nr=row[0],
                bst_name=row[1],
                anl_nr=row[2],
                anl_bez=row[3],
                ort=row[4],
                ortsteil=row[5],
                ostwert=row[6],
                nordwert=row[7]
            )
        
        conn_wka.close()
    
    if not anlage:
        raise HTTPException(status_code=404, detail="Anlage nicht gefunden")
    
    # 2. Immissionsschutz-Daten
    conn_immi = get_db_connection("immissionsschutz")
    cursor_immi = conn_immi.cursor()
    
    # Verfahren
    cursor_immi.execute(
        "SELECT * FROM genehmigungsverfahren WHERE bst_nr = ? AND anl_nr = ?",
        (bst_nr, anl_nr)
    )
    verfahren_rows = cursor_immi.fetchall()
    verfahren_cols = [desc[0] for desc in cursor_immi.description]
    verfahren = [dict(zip(verfahren_cols, row)) for row in verfahren_rows]
    
    # Bescheide (für genehmigte Verfahren)
    bescheide = []
    for v in verfahren:
        cursor_immi.execute(
            "SELECT * FROM bescheide WHERE verfahren_id = ?",
            (v["verfahren_id"],)
        )
        bescheid_rows = cursor_immi.fetchall()
        bescheid_cols = [desc[0] for desc in cursor_immi.description]
        bescheide.extend([dict(zip(bescheid_cols, row)) for row in bescheid_rows])
    
    # Messungen
    messungen = []
    if include_messungen:
        cursor_immi.execute(
            "SELECT * FROM messungen WHERE bst_nr = ? AND anl_nr = ? ORDER BY messdatum DESC LIMIT 100",
            (bst_nr, anl_nr)
        )
        messungen_rows = cursor_immi.fetchall()
        messungen_cols = [desc[0] for desc in cursor_immi.description]
        messungen = [dict(zip(messungen_cols, row)) for row in messungen_rows]
    
    # Überwachungen
    cursor_immi.execute(
        "SELECT * FROM ueberwachung WHERE bst_nr = ? AND anl_nr = ? ORDER BY geplant_datum DESC LIMIT 20",
        (bst_nr, anl_nr)
    )
    ueberwachung_rows = cursor_immi.fetchall()
    ueberwachung_cols = [desc[0] for desc in cursor_immi.description]
    ueberwachungen = [dict(zip(ueberwachung_cols, row)) for row in ueberwachung_rows]
    
    # Mängel
    cursor_immi.execute(
        "SELECT * FROM maengel WHERE bst_nr = ? AND anl_nr = ? ORDER BY festgestellt_datum DESC",
        (bst_nr, anl_nr)
    )
    maengel_rows = cursor_immi.fetchall()
    maengel_cols = [desc[0] for desc in cursor_immi.description]
    maengel = [dict(zip(maengel_cols, row)) for row in maengel_rows]
    
    # NEUE TABELLEN
    
    # Dokumente
    dokumente = []
    if include_dokumente:
        cursor_immi.execute(
            "SELECT * FROM dokumente WHERE bst_nr = ? AND anl_nr = ? ORDER BY erstellt_datum DESC LIMIT 50",
            (bst_nr, anl_nr)
        )
        dokumente_rows = cursor_immi.fetchall()
        dokumente_cols = [desc[0] for desc in cursor_immi.description]
        dokumente = [dict(zip(dokumente_cols, row)) for row in dokumente_rows]
    
    # Ansprechpartner
    cursor_immi.execute(
        "SELECT * FROM ansprechpartner WHERE bst_nr = ? AND anl_nr = ? AND aktiv = 1",
        (bst_nr, anl_nr)
    )
    ansprechpartner_rows = cursor_immi.fetchall()
    ansprechpartner_cols = [desc[0] for desc in cursor_immi.description]
    ansprechpartner = [dict(zip(ansprechpartner_cols, row)) for row in ansprechpartner_rows]
    
    # Wartungen
    cursor_immi.execute(
        "SELECT * FROM wartung WHERE bst_nr = ? AND anl_nr = ? ORDER BY geplant_datum DESC LIMIT 20",
        (bst_nr, anl_nr)
    )
    wartungen_rows = cursor_immi.fetchall()
    wartungen_cols = [desc[0] for desc in cursor_immi.description]
    wartungen = [dict(zip(wartungen_cols, row)) for row in wartungen_rows]
    
    # Messreihen
    cursor_immi.execute(
        "SELECT * FROM messreihen WHERE bst_nr = ? AND anl_nr = ?",
        (bst_nr, anl_nr)
    )
    messreihen_rows = cursor_immi.fetchall()
    messreihen_cols = [desc[0] for desc in cursor_immi.description]
    messreihen = [dict(zip(messreihen_cols, row)) for row in messreihen_rows]
    
    # Compliance-Historie
    cursor_immi.execute(
        "SELECT * FROM compliance_historie WHERE bst_nr = ? AND anl_nr = ? ORDER BY pruefungsdatum DESC LIMIT 10",
        (bst_nr, anl_nr)
    )
    compliance_rows = cursor_immi.fetchall()
    compliance_cols = [desc[0] for desc in cursor_immi.description]
    compliance_historie = [dict(zip(compliance_cols, row)) for row in compliance_rows]
    
    conn_immi.close()
    
    # 3. Statistiken
    statistik = {
        "verfahren_count": len(verfahren),
        "verfahren_genehmigt": sum(1 for v in verfahren if v.get("status") == "genehmigt"),
        "bescheide_count": len(bescheide),
        "messungen_count": len(messungen),
        "messungen_ueberschreitungen": sum(1 for m in messungen if m.get("ueberschreitung") == 1),
        "ueberwachungen_count": len(ueberwachungen),
        "maengel_count": len(maengel),
        "maengel_offen": sum(1 for mg in maengel if mg.get("status") == "offen"),
        "maengel_kritisch": sum(1 for mg in maengel if mg.get("schweregrad") == "kritisch" and mg.get("status") == "offen"),
        "dokumente_count": len(dokumente),
        "ansprechpartner_count": len(ansprechpartner),
        "wartungen_count": len(wartungen),
        "wartungen_geplant": sum(1 for w in wartungen if w.get("status") == "geplant"),
        "messreihen_count": len(messreihen),
        "messreihen_kritisch": sum(1 for mr in messreihen if mr.get("bewertung") == "kritisch"),
        "compliance_count": len(compliance_historie),
        "compliance_letztes_ergebnis": compliance_historie[0].get("ergebnis") if compliance_historie else None
    }
    
    return {
        "anlage": anlage,
        "verfahren": verfahren,
        "bescheide": bescheide,
        "messungen": messungen,
        "ueberwachungen": ueberwachungen,
        "maengel": maengel,
        "dokumente": dokumente,
        "ansprechpartner": ansprechpartner,
        "wartungen": wartungen,
        "messreihen": messreihen,
        "compliance_historie": compliance_historie,
        "statistik": statistik
    }

# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    logger.info("="*70)
    logger.info("🚀 Immissionsschutz Test-Server wird gestartet...")
    logger.info("="*70)
    logger.info("Port: 5001")
    logger.info("Docs: http://localhost:5001/docs")
    logger.info("="*70)
    
    uvicorn.run(
        "immissionsschutz_test_server:app",
        host="0.0.0.0",
        port=5001,
        reload=False,
        log_level="info"
    )

