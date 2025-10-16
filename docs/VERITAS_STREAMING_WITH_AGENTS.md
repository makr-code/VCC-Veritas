# VERITAS Streaming bei Agenten-Tätigkeit

Datum: 21. September 2025  
Version: 1.0

> Kurz erklärt: Stellen Sie sich eine Paketverfolgung vor. Sie sehen live, wo Ihr Paket ist (abgeholt, sortiert, unterwegs). Genauso zeigt VERITAS live an, in welchem Bearbeitungsschritt Ihre Frage gerade ist – inklusive Zwischenresultaten.

---

## 🎯 Ziel
Dieses Dokument erklärt die Streaming-Funktionalität während der Agenten-Verarbeitung – sowohl im Backend (FastAPI + Progress-System) als auch im Frontend (`veritas_app.py` mit `VeritasStreamingService` und `StreamingUIMixin`).

---

## 🔧 Architekturüberblick

```mermaid
graph TD
    U[User] -->|Frage| F[Frontend (veritas_app.py)]
    F -->|POST /v2/query/stream| B[Backend (FastAPI)]
    B -->|Agenten-Pipeline| A[Agent Orchestrator]
    A -->|Zwischenergebnisse| PM[Progress Manager]
    PM -->|SSE Events| F
    F -->|Cancel /cancel/{session}| B
    B -->|Stop Processing| A
```

> Analogie: Ein Callcenter verteilt Ihr Anliegen an mehrere Fachabteilungen. Jede meldet zurück, wie weit sie ist. Bei Bedarf können Sie den Vorgang stoppen.

---

## 🖥️ Frontend-Streaming

### Was passiert für mich als Nutzer?
- Sie stellen eine Frage.
- Sofort erscheint ein Fortschrittsbalken und kurze Statusmeldungen (z. B. „Rechtslage prüfen…“).
- Zwischenergebnisse können frühzeitig eingeblendet werden (Etappenerfolge).
- Ein Abbrechen-Knopf ist verfügbar, solange noch gearbeitet wird.

### Komponenten
- `veritas_streaming_service.py`
  - `VeritasStreamingService`: Startet Streams, liest Live-Updates, reicht sie an die Oberfläche weiter.
  - `StreamingUIMixin`: Sorgt für Fortschrittsanzeige, Status-Text und Abbrechen-Knopf.
- Integration in `veritas_app.py`
  - `ChatWindowBase(…, StreamingUIMixin)`: Die bestehende Oberfläche bleibt, wird nur erweitert.
  - `_handle_message()` erkennt Streaming-Meldungen und aktualisiert die Anzeige.

### Ablauf in 5 Schritten
1. Frage stellen → System prüft „Streaming aktiv?“ → Start anfordern.
2. Verbindung zur Live-Update-Leitung (SSE) wird aufgebaut.
3. Fortschritt und Zwischenergebnisse treffen ein und werden angezeigt.
4. Nach Abschluss erscheint die fertige Antwort, der Fortschrittsbalken wird beendet.
5. Optional: Abbrechen → Die Bearbeitung wird angehalten und entsprechend angezeigt.

> Tipp: Live-Updates erhöhen Transparenz und verkürzen das gefühlte Warten, weil man sieht, dass gearbeitet wird.

---

## 🧠 Backend-Streaming

### In einfachen Worten
Das Backend ist die „Werkstatt“. Es teilt Ihre Frage in Aufgaben auf, verteilt sie an digitale Fachkräfte (Agenten) und meldet regelmäßig den Bearbeitungsstand an die Oberfläche.

### Kernmodule
- `veritas_api_backend.py`
  - `POST /v2/query/stream`: Startsignal mit Ihrer Frage.
  - `GET /progress/{session_id}`: Die Live-Update-Leitung (Server-Sent Events).
  - `POST /cancel/{session_id}`: Stoppt die Bearbeitung.
- `veritas_streaming_progress.py`
  - `VeritasProgressManager`: Merkt sich, was gerade läuft und in welchem Schritt.
  - `VeritasProgressStreamer`: Schickt die Live-Updates zuverlässig nach außen.

### Event-Typen verständlich
- `stage_update`: „Wir sind im nächsten Schritt.“
- `intermediate_result`: „Eine Teilauswertung ist fertig.“
- `llm_thinking`: „Formulieren/Verknüpfen läuft gerade.“
- `stage_complete`: „Fertig – hier ist das Ergebnis.“
- `cancelled`/`error`: „Abgebrochen/Fehler aufgetreten.“

### Abbrechen (Cancellation)
- Das System prüft alle paar Momente, ob ein Abbruch gewünscht ist.
- Falls ja, werden laufende Arbeiten sauber beendet und ein Abbruch-Hinweis gesendet.

---

## 🔄 End-to-End Workflow (Agenten)

1. Frontend sendet Start:
```http
POST /v2/query/stream
{"query":"Baugenehmigung EFH?","session_id":"sess_123","enable_intermediate_results":true}
```
2. Backend startet Bearbeitung, erstellt eine Sitzungs-ID und beginnt mit den Schritten.
3. Backend streamt Live-Events (gekürztes Beispiel):
```text
event: stage_update
data: {"stage":"agent_processing","progress":35,"message":"construction worker started"}

event: intermediate_result
data: {"agent_type":"construction","summary":"Bauordnung geprüft"}

event: llm_thinking
data: {"thinking_step":"cross_domain_consistency"}

event: stage_complete
data: {"stage":"completed","final_result":"Antragsschritte…"}
```
4. Frontend zeigt den Fortschritt, Teil-Ergebnisse und am Ende die Gesamtausgabe.
5. Optional Abbruch:
```http
POST /cancel/sess_123
{"reason":"user_cancelled"}
```
6. Backend markiert als abgebrochen → sendet `event: cancelled`.

---

## 🧪 Häufige Stolpersteine & Lösungen

- Nichts erscheint im Frontend:
  - Prüfen, ob die Live-Update-Leitung (`/progress/{session_id}`) erreichbar ist.
  - CORS- und Firewall-Einstellungen prüfen.
- Abbrechen reagiert nicht:
  - Sicherstellen, dass die Agenten regelmäßig auf „abgebrochen?“ prüfen.
- Zu viele Events hintereinander:
  - Evtl. „Entschleunigung“/Bündelung aktivieren, damit die UI flüssig bleibt.

---

## 🧭 Best Practices

- Live-Updates lean halten (kurze, klare Meldungen).
- Nur die Oberfläche (Main-Thread) aktualisieren; Hintergrundarbeit im Thread/Async.
- Abbruch immer ermöglichen, solange noch gearbeitet wird.
- Nutzerpräferenzen anbieten: „Zwischenergebnisse anzeigen?“, „Denk-Schritte anzeigen?“

---

## ▶️ Quickstart

### Backend starten (lokal)
```powershell
python veritas_api_backend.py
```

### Frontend starten
```powershell
python veritas_app.py
```

### Manuelle Prüfung (optional)
```powershell
# Start Streaming
curl -X POST http://127.0.0.1:5000/v2/query/stream -H "Content-Type: application/json" -d '{"query":"Umweltauflagen Industrie","session_id":"sess_1","enable_streaming":true}'

# Live-Updates ansehen (im Browser)
http://127.0.0.1:5000/progress/sess_1

# Abbrechen
curl -X POST http://127.0.0.1:5000/cancel/sess_1 -H "Content-Type: application/json" -d '{"reason":"user_cancelled"}'
```

---

## 🧾 Mini-Glossar
- **Agent**: Digitale Fachkraft mit Spezialgebiet (z. B. Bauen, Umwelt).
- **Streaming/SSE**: Live-Updates vom Server an die Oberfläche.
- **Session-ID**: Kennzeichen für einen Vorgang – wie eine Auftragsnummer.
- **Zwischenergebnis**: Etappenerfolg, bevor alles fertig ist.
- **Abbrechen**: Vorgang stoppen, solange er noch läuft.

## ❓ FAQ
- Kann ich ohne Technik-Know-how arbeiten?
  - Ja. Die Oberfläche ist selbsterklärend. Diese Doku dient nur zum Verständnis.
- Was passiert bei Abbruch?
  - Laufende Arbeiten stoppen; es werden keine dauerhaften Änderungen vorgenommen.
- Woher kommen die Infos?
  - Aus zugelassenen Datenquellen (z. B. Ämter-APIs, Datenbanken) – je nach Thema.
