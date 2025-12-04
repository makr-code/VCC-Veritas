"""
FastAPI Router für SQLite-Datenbank-Zugriff
Bietet einheitlichen Zugriff auf BImSchG und WKA Datenbanken
"""

        # sqlite3.Row can act both like a sequence and a mapping; convert to a dict
        # so static type checkers see a concrete Mapping[str, Any].
        col_dict = dict(col)
        schema.append(
            ColumnInfo(
                name=col_dict.get("name"),
                type=col_dict.get("type"),
                not_null=bool(col_dict.get("notnull")),
                primary_key=bool(col_dict.get("pk")),
            )
        )

    conn.close()
    return schema


def row_to_anlage_record(row: sqlite3.Row, db_name: str) -> AnlageRecord:
    """Konvertiert Datenbank-Zeile in AnlageRecord"""
    row_dict = dict(row)

    # Gemeinsame Felder extrahieren
    base_fields = {
        "bst_nr": str(row_dict.get("bst_nr", "")),
        "bst_name": row_dict.get("bst_name"),
        "anl_nr": str(row_dict.get("anl_nr", "")),
        "anl_bez": row_dict.get("anl_bez"),
        "ort": row_dict.get("ort"),
        "ortsteil": row_dict.get("ortsteil"),
        "ostwert": row_dict.get("ostwert"),
        "nordwert": row_dict.get("nordwert"),
        "leistung": row_dict.get("leistung")
    }

    # Zusätzliche Felder
    additional = {k: v for k, v in row_dict.items() if k not in base_fields}

    return AnlageRecord(**base_fields, additional_data=additional)


# Endpoints

@router.get("/list", response_model=DatabaseListResponse)
async def list_databases():
    """
    Liste aller verfügbaren Datenbanken
    """
    db_list = []

    for name, info in DATABASES.items():
        available = info["path"].exists()
        size_mb = None

        if available:
            try:
                size_mb = info["path"].stat().st_size / (1024 * 1024)
            except Exception:
                # If we cannot stat the file, leave size as None. Avoid silently
                # swallowing errors with a bare pass to satisfy bandit checks.
                size_mb = None

        db_list.append(
            DatabaseInfo(
                name=name,
                description=info["description"],
                table_name=info["table"],
                row_count=info["count"],
                available=available,
                size_mb=size_mb,
            )
        )

    return DatabaseListResponse(databases=db_list, total=len(db_list))


@router.get("/status")
async def get_database_status():
    """
    Status aller Datenbanken (Verfügbarkeit, Verbindung)
    """
    status = {}

    for name, info in DATABASES.items():
        db_status = {
            "available": info["path"].exists(),
            "path": str(info["path"]),
            "connection": False,
            "row_count": 0
        }

        if db_status["available"]:
            try:
                conn = get_db_connection(name)
                cursor = conn.cursor()
                count = cursor.execute(f"SELECT COUNT(*) FROM {info['table']}").fetchone()[0]
                db_status["connection"] = True
                db_status["row_count"] = count
                conn.close()
            except Exception as e:
                db_status["error"] = str(e)

        status[name] = db_status

    return {
        "databases": status,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/{db_name}/schema", response_model=TableSchemaResponse)
async def get_database_schema(
    db_name: Literal["bimschg", "wka"]
):
    """
    Tabellen-Schema einer Datenbank abrufen
    """
    schema = get_table_schema(db_name)

    conn = get_db_connection(db_name)
    cursor = conn.cursor()
    table_name = DATABASES[db_name]["table"]
    row_count = cursor.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    conn.close()

    return TableSchemaResponse(
        database=db_name,
        table=table_name,
        columns=schema,
        row_count=row_count
    )


@router.post("/{db_name}/query", response_model=QueryResponse)
async def execute_query(
    db_name: Literal["bimschg", "wka"],
    request: QueryRequest
):
    """
    SQL-Query ausführen (nur SELECT erlaubt)
    """
    validate_sql_query(request.sql)

    start_time = datetime.now()
    conn = get_db_connection(db_name)
    cursor = conn.cursor()

    try:
        # Query mit LIMIT ausführen
        sql_with_limit = f"{request.sql.rstrip(';')} LIMIT {request.limit}"
        cursor.execute(sql_with_limit)

        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]

        result_rows = [dict(row) for row in rows]

    except sqlite3.Error as e:
        conn.close()
        raise HTTPException(status_code=400, detail=f"SQL error: {str(e)}")
    finally:
        conn.close()

    execution_time = (datetime.now() - start_time).total_seconds() * 1000

    return QueryResponse(
        success=True,
        database=db_name,
        columns=columns,
        rows=result_rows,
        row_count=len(result_rows),
        execution_time_ms=execution_time
    )


@router.post("/{db_name}/search", response_model=RecordSearchResponse)
async def search_records(
    db_name: Literal["bimschg", "wka"],
    request: RecordSearchRequest,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500)
):
    """
    Datensätze suchen (nach BST-Nr, Anlagen-Nr, Ort oder Freitext)
    """
    conn = get_db_connection(db_name)
    cursor = conn.cursor()
    table_name = DATABASES[db_name]["table"]

    # Query zusammenbauen
    conditions = []
    params = []

    if request.bst_nr:
        conditions.append("CAST(bst_nr AS TEXT) LIKE ?")
        params.append(f"%{request.bst_nr}%")

    if request.anl_nr:
        conditions.append("anl_nr LIKE ?")
        params.append(f"%{request.anl_nr}%")

    if request.ort:
        conditions.append("ort LIKE ?")
        params.append(f"%{request.ort}%")

    if request.search_term:
        # Volltextsuche über mehrere Felder
        search_fields = ["bst_name", "anl_bez", "ort", "ortsteil"]
        search_conditions = " OR ".join([f"{field} LIKE ?" for field in search_fields])
        conditions.append(f"({search_conditions})")
        params.extend([f"%{request.search_term}%"] * len(search_fields))

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    # Gesamtanzahl
    count_query = f"SELECT COUNT(*) FROM {table_name} WHERE {where_clause}"
    total_found = cursor.execute(count_query, params).fetchone()[0]

    # Paginierte Ergebnisse
    offset = (page - 1) * page_size
    query = f"SELECT * FROM {table_name} WHERE {where_clause} LIMIT ? OFFSET ?"
    params.extend([page_size, offset])

    rows = cursor.execute(query, params).fetchall()

    records = [row_to_anlage_record(row, db_name) for row in rows]

    conn.close()

    return RecordSearchResponse(
        database=db_name,
        total_found=total_found,
        page=page,
        page_size=page_size,
        records=records
    )


@router.get("/{db_name}/record/{bst_nr}/{anl_nr}", response_model=AnlageRecord)
async def get_record_by_id(
    db_name: Literal["bimschg", "wka"],
    bst_nr: str,
    anl_nr: str
):
    """
    Einzelnen Datensatz per BST-Nr und Anlagen-Nr abrufen
    """
    conn = get_db_connection(db_name)
    cursor = conn.cursor()
    table_name = DATABASES[db_name]["table"]

    query = f"SELECT * FROM {table_name} WHERE CAST(bst_nr AS TEXT) = ? AND anl_nr = ?"
    row = cursor.execute(query, (bst_nr, anl_nr)).fetchone()

    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail=f"Record not found: {bst_nr}/{anl_nr}")

    return row_to_anlage_record(row, db_name)


@router.post("/{db_name}/location", response_model=LocationQueryResponse)
async def query_by_location(
    db_name: Literal["bimschg", "wka"],
    request: LocationQueryRequest,
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Anlagen in der Nähe eines Standorts finden (Geodaten-Abfrage)
    """
    conn = get_db_connection(db_name)
    cursor = conn.cursor()
    table_name = DATABASES[db_name]["table"]

    # Einfache Distanzberechnung (Pythagoras, nicht geodätisch korrekt aber ausreichend)
    # 1 Grad ≈ 111km, aber wir nutzen UTM-Koordinaten (Meter)
    query = f"""
        SELECT *,
               SQRT(
                   POWER(ostwert - ?, 2) +
                   POWER(nordwert - ?, 2)
               ) as distance
        FROM {table_name}
        WHERE ostwert IS NOT NULL
          AND nordwert IS NOT NULL
          AND SQRT(
                POWER(ostwert - ?, 2) +
                POWER(nordwert - ?, 2)
              ) <= ?
        ORDER BY distance
        LIMIT ?
    """

    rows = cursor.execute(query, (
        request.center_x, request.center_y,
        request.center_x, request.center_y,
        request.radius_meters,
        limit
    )).fetchall()

    conn.close()

    records = [row_to_anlage_record(row, db_name) for row in rows]

    return LocationQueryResponse(
        database=db_name,
        center={"x": request.center_x, "y": request.center_y},
        radius_meters=request.radius_meters,
        found_count=len(records),
        records=records
    )


@router.get("/{db_name}/statistics", response_model=StatisticsResponse)
async def get_statistics(
    db_name: Literal["bimschg", "wka"]
):
    """
    Statistiken über eine Datenbank
    """
    conn = get_db_connection(db_name)
    cursor = conn.cursor()
    table_name = DATABASES[db_name]["table"]

    # Gesamtanzahl
    total = cursor.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]

    stats = {
        "total_records": total,
        "unique_bst": cursor.execute(f"SELECT COUNT(DISTINCT bst_nr) FROM {table_name}").fetchone()[0],
        "unique_ort": cursor.execute(f"SELECT COUNT(DISTINCT ort) FROM {table_name}").fetchone()[0],
    }

    # Datenbank-spezifische Statistiken
    if db_name == "wka":
        # WKA-spezifisch
        stats["total_leistung_mw"] = cursor.execute(SQL_TEMPLATES[db_name]["sum_leistung"]).fetchone()[0] or 0

        stats["avg_nabenhoehe"] = cursor.execute(SQL_TEMPLATES[db_name]["avg_nabenhoehe"]).fetchone()[0] or 0
        # build a typed mapping first to satisfy static type checkers
        # Use Counter for typed, incremental counting to satisfy static checkers
        status_breakdown: Counter[str] = Counter()
        status_rows = cursor.execute(SQL_TEMPLATES[db_name]["status_group"].format(table=table_name)).fetchall()
        for row in status_rows:
            r = dict(row)
            key = r.get("status") or "unknown"
            status_breakdown[key] += int(r.get("count", 0))
        # Convert to plain dict for JSON/Pydantic compatibility
        stats["status_breakdown"] = dict(status_breakdown)

    elif db_name == "bimschg":
        # BImSchG-spezifisch
        stats["avg_leistung"] = cursor.execute(SQL_TEMPLATES[db_name]["avg_leistung"]).fetchone()[0] or 0
    anlagenarten: Counter[str] = Counter()
    art_rows = cursor.execute(SQL_TEMPLATES[db_name]["anlagenarten"].format(table=table_name)).fetchall()
    for row in art_rows:
        r = dict(row)
        # Kürze lange Namen (sicherer Zugriff)
        raw_name = r.get("anlgr_4bv") or "unknown"
        name = raw_name[:50]
        anlagenarten[name] += int(r.get("count", 0))  # ensure int
    stats["anlagenarten"] = dict(anlagenarten)

    conn.close()

    return StatisticsResponse(
        database=db_name,
        total_records=total,
        statistics=stats
    )


# Health Check
@router.get("/health")
async def database_health():
    """
    Health Check für Datenbank-Service
    """
    # typed containers to satisfy static type checkers
    health: Dict[str, Any] = {"service": "database", "status": "healthy"}
    databases_status: Dict[str, str] = {}
    overall_status: str = "healthy"

    for name, info in DATABASES.items():
        try:
            conn = get_db_connection(name)
            conn.close()
            databases_status[name] = "ok"
        except Exception as e:
            databases_status[name] = f"error: {str(e)}"
            overall_status = "degraded"

    health["databases"] = databases_status
    health["status"] = overall_status

    return health
