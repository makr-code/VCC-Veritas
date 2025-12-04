# Veritas Backend — Wichtige Umgebungsvariablen

Diese Datei dokumentiert die wichtigsten ENV-Variablen, die das Verhalten der
Themis-Persistenz- und Queue-Logik steuern. (Keine automatischen Git-Commits
werden durch dieses Skript ausgeführt.)

Hinweis: Beispielwerte dienen als konservative Defaults. Setzen Sie Variablen
über PowerShell z. B. mit:

```powershell
$env:THEMIS_ENABLED = 'false'
$env:THEMIS_PERSISTENCE_RETRY_COUNT = '5'
$env:THEMIS_PERSISTENCE_RETRY_BACKOFF = '2' # Sekunden (Basiswert für Backoff)
```

---

## THEMIS_ENABLED
- Typ: string/boolean ("true" | "false")
- Beschreibung: Wenn `true`, versucht der Service, Themis als persistente
  Ziel-Adapter zu verwenden. Wenn `false`, wird Themis ignoriert und UDS3 dient
  als primärer Adapter für Retrieval/ingestion.
- Default: `false` (sicher für lokale Entwicklung)

## THEMIS_FAIL_POLICY
- Typ: string ("fail" | "warn" | "disable")
- Beschreibung: Steuert das Verhalten beim generellen Ausfall von Themis
  auf Adapter-Ebene (nicht speziell für persistierende Writes).
- Hinweise: Wird hauptsächlich in Adapter-Factory-Entscheidungen ausgewertet.

## THEMIS_PERSISTENCE_FAIL_POLICY
- Typ: string ("queue" | "block" | "drop")
- Beschreibung: Verhalten, wenn ein persistenter Schreibvorgang (z. B. ein
  Dokument-Insert) gegenüber Themis fehlschlägt.
  - `queue`: Enqueue die Aufgabe in der `PersistenceQueue` und versuche später
    erneut (empfohlen für hohe Verfügbarkeit).
  - `block`: Versuche synchron mehrfach (gemäß RETRY_COUNT) und gib bei
    endgültigem Fehlschlag einen Fehler an den Aufrufer zurück.
  - `drop`: Verwirf fehlgeschlagene Persistenz-Versuche (nur in Ausnahmefällen).
- Default: `queue`

## THEMIS_PERSISTENCE_RETRY_COUNT
- Typ: integer
- Beschreibung: Maximale Anzahl an Retry-Versuchen durch die `PersistenceQueue`
  bevor ein Task endgültig als fehlgeschlagen gilt.
- Default: `5`

## THEMIS_PERSISTENCE_RETRY_BACKOFF
- Typ: number (Sekunden)
- Beschreibung: Basiswert (in Sekunden) für exponentielles Backoff zwischen
  Wiederholungsversuchen. Implementierungen können z. B. `backoff * attempt` oder
  `backoff ** attempt` verwenden.
- Default: `2`

## VERITAS_API_PORT / VERITAS_API_RELOAD
- `VERITAS_API_PORT`: Port, auf dem FastAPI/Uvicorn startet (z. B. `5004`).
- `VERITAS_API_RELOAD`: `true`/`false` — ob der Server mit Auto-Reload startet
  (für Entwicklung nützlich).

---

Empfehlungen für Tests und Smoke-Runs
- Lokale Entwicklung: setze `THEMIS_ENABLED=false` und verifiziere Queue-Verhalten
  mit `THEMIS_PERSISTENCE_FAIL_POLICY=queue`.
- Staging/Integration: aktiviere `THEMIS_ENABLED=true`, setze `RETRY_COUNT=8`
  und `BACKOFF=3` für robuste Wiederholungen.

Beispiel Start (PowerShell):

```powershell
$env:THEMIS_ENABLED='false'
$env:VERITAS_API_PORT='5004'
$env:VERITAS_API_RELOAD='false'
.\.venv\Scripts\python.exe -m backend.app
```

Weitere Hinweise
- Dokumentation ist bewusst konservativ gehalten; passen Sie Policy-Werte an
  eure Betriebsanforderungen an. Falls Sie Monitoring/Metriken hinzufügen, ist
  es hilfreich, Queue-Länge und Anzahl Retries als Metriken zu exportieren.
