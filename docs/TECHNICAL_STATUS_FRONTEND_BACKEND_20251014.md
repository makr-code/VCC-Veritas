# Technischer Statusbericht — Frontend & Backend

Datum: 14. Oktober 2025

Ziel
----
Diese Ausarbeitung beschreibt den aktuellen technischen Stand der Implementierung für das `veritas` Projekt, getrennt nach Frontend und Backend, sowie deren Wechselwirkung. Ziel ist es,

- einen klaren technischen Überblick zu geben,
- die strategischen Kernentscheidungen zu dokumentieren,
- einen umsetzbaren "blauen Faden" (Implementierungs- & Release-Fahrplan) zu liefern,
- sowie konkrete Acceptance-Kriterien, KPIs und Risikominderungsmaßnahmen vorzuschlagen.

Die Sprache ist gezielt operational: einzelne Schritte sind so formuliert, dass Entwickler sie unmittelbar in Tasks/Commits überführen können.

Inhaltsübersicht
----------------
1. Zusammenfassung
2. Überblick Architektur
3. Backend — Komponenten und Status
   - 3.1 Core-Services
   - 3.2 API-Schicht
   - 3.3 Datenmanagement & Speicher
   - 3.4 Integrationen (RAG, Vector DB, LLMs)
   - 3.5 Observability, Logging, Tests
4. Frontend — Komponenten und Status
   - 4.1 UI-Architektur & Rendering
   - 4.2 Client-Server Kommunikation (WebSocket/HTTP)
   - 4.3 UI-Komponenten (Citations, Suggestions, Sources)
   - 4.4 Tests & QA
5. Wechselwirkung — Schnittstellen & Datenfluss
6. Fehlerfälle, Edge-Cases und Resilienz
7. Security & Zugriffskontrolle
8. Deployment & Betriebshinweise
9. Offene Punkte & Empfehlungen
10. Anhang — wichtige Dateien/Orte im Repo

1. Zusammenfassung
------------------

Kernaussage
~~~~~~~~~~~
Das Projekt befindet sich in einem stabilen Funktions-Prototyp-Zustand: alle zentralen Domänen (Retrieval, Reranking, Assembly, Streaming UI) sind vorhanden und integriert. Für den Produktionsbetrieb sind jedoch gezielte Arbeiten in den Bereichen Stabilisierung, Observability, Sicherheit und automatisierter Qualitätssicherung erforderlich.

Wesentliche Stärken
- Modularer Backend-Stack mit klaren Schnittstellen (API, Agenten, Services)
- Pluggable Integrationen für Vector DBs und LLM-Adapter (leicht austauschbar)
- Frontend mit reichhaltigen UI-Elementen für Quellen- und Zitationsdarstellung sowie Streaming-Unterstützung

Haupt-Risiken
- Fehlende End-to-End-Integrationstests für produktionsnahe LLM/Vector-DB-Szenarien
- Unvollständige Observability (Metrics/Tracing) und Secrets-Management
- Einige relative Dokumenten-Links und PKI-Verweise im Repo benötigen Bereinigung

Erwartetes Ergebnis dieser Roadmap
- Produktionsfähige Plattform mit definierten KPI-Budgets für Retrieval und Rerank
- CI-gesteuerte Testlandschaft mit deterministischen Mocks für LLM/Vector
- Klar dokumentierte Betriebsschritte (health, metrics, secrets)

2. Überblick Architektur
------------------------
- Monorepo-Struktur mit klarer Trennung `backend/`, `frontend/`, `docs/`, `shared/`, `uds3/`.
- Backend exposed REST/HTTP Endpoints (Controller/Endpoint-Layer), Worker/Agent-Schicht für asynchrone Tasks, und Integrationsservices (RAG, LLM, DB).
- Frontend besteht aus modularen UI-Komponenten (Markdown-Renderer, Citation-Parser, Source-Panels) und verwendet WebSocket-Streaming für Live-Antworten.
- Persistenz-Layer: eine Kombination aus relationalen/metadaten SQLite (in `data/`), Vector DB (konfigurierbar), und lokale Datei-basierte Logs.

3. Backend — Komponenten und Status
----------------------------------

3.1 Core-Services
------------------
- `veritas_api_core.py` / `veritas_api_backend.py` bilden das Herzstück des Backends: sie implementieren Request-Handling, Middleware (Auth, Rate-Limiting Hooks), Error-Handling und Routing.
- `agents/` enthält modulare Agenten (Pipeline-Manager, Orchestratoren, Worker) für langlaufende oder aufwändige Aufgaben (Batch-Retrieval, Re-Ranking Jobs, Export-Pipelines).
- Implementierungsdetails (konkret):
  - Request-Context: Ein kleines Context-Objekt wird beim Eintreffen jeder Anfrage erzeugt und enthält request-id, user-id (falls auth vorhanden), trace-id sowie debug-level. Dieses Objekt wird an alle internen Services weitergegeben und in Logs referenziert.
  - Middleware-Pattern: Auth, Input-Validation und Rate-Limiting sind als separable Middleware implementiert; empfehlenswert ist ein Contract-Test-Set, das gegen diese Middleware validiert.
  - Fehler-Handling: Standard-Fehlercodes (4xx/5xx) mit Fehler-IDs; Vorschlag: strukturierte Fehlerpayloads {code, id, message, hints} für bessere Analyse.
- Status & ToDo:
  - Core-Endpunkte stehen; Erweiterung: Contract-Tests pro Endpunkt (Mock-Frontend) und Middleware-Integrationstests.

3.2 API-Schicht
---------------
- Endpunkte (Kern):
  - Conversation/Query API (sync & streaming): unterstützt prompt-Parameter, context windows, streaming token chunks und incremental source metadata.
  - Document/Chunk Management: indexieren, chunking, meta-tagging, tagging für KGE/KK.
  - Feedback, Reranking Hooks: Feedback-Endpoints (collect/annotate) und Re-Ranking Hooks für experimentelle Modelle.
  - Admin/Inspection Endpoints: health, index-status, metrics snapshot.
- Implementation: Controller/Handler-Pattern, mit klaren Contracts (JSON-Schema) für Request/Response-Formate.
- Status & Empfehlungen: Dokumentation vorhanden; dringend empfohlen sind:
  - Contract-Tests (OpenAPI/JSON-Schema basierte Tests) zwischen API und Frontend
  - Stabilisierung der response-schemas (backward-compatible changes only)

3.3 Datenmanagement & Speicher
------------------------------
- Persistenz-Layer:
  - Relationale Metadaten: SQLite für Development/CI; für Produktion ist Postgres o.ä. zu bevorzugen.
  - Vector-Index: Abstrakte Schicht, Treiber-Pattern implementiert (Chroma/FAISS/Remote). Wichtig: Reproducible Indexing Pipelines (deterministisches chunking & hashing) sind in der Roadmap.
  - Blob/Document-Store: Dateisystem-basiert in Dev; S3/Blob empfohlen im Produktiveinsatz.
- Status & Empfehlungen (konkret):
  - Chunk-Hashing: implementiere SHA256-/BLAKE2-Hashes pro Chunk (content + normalization) und speichere ihn in Metadaten, um idempotente Reindexierung möglich zu machen.
  - Reindex-Strategie: inkrementelles Reindexing mit Checkpoint-Dateien; Full Reindex nur im Wartungsfenster.
  - Storage Empfehlung: Dev=SQLite, Prod=Postgres + Managed VectorDB (Chroma/Annoy/FAISS auf managed infra) + S3-compatible blob store.

3.4 Integrationen (RAG, Vector DB, LLMs)
---------------------------------------
- Architekturprinzipien:
  - Trenne Retrieval (Vector Search) und Generierung (LLM Re-Ranking / Assembly) strikt.
  - Verwende deterministische Chunking-Strategien und Metadaten, damit Retrieval reproduzierbar ist.
- Implementierte Features:
  - Batch-RAG: Parallelisierte Suche über mehrere Partitionen, deduplizierende Merge-Strategie und Score-Normalisierung.
  - Query Expansion: LLM-basierte Query-Rewrites mit Fallback auf simple term-expansion.
  - Re-Ranking: Zwei-Phasen-Ansatz — schnelle heuristische Pre-Rank (Cosine + Domain Signals), danach LLM-basiertes Re-Ranking der Top-K.
- Metriken & Observability (konkret):
  - Metriken: retrieval_latency_ms, re_rank_latency_ms, retrieval_success_rate, re_rank_success_rate, topk_churn_pct, stream_throughput_tokens.
  - Instrumentierung: opentelemetry spans (retrieval, re-rank, assembly), Prometheus exporter for aggregates.
- Status & Empfehlungen:
  - Repro-Tests: setze deterministische fixtures und LLM-mocks (seeded RNG) in CI.
  - SLAs: definiere Timeout-Budgets und implementiere graceful fallback to cached/heuristic responses.

3.5 Observability, Logging, Tests
---------------------------------
- Logging & Tracing:
  - Zentralisiertes Logging vorhanden; empfehlenswert: strukturierte JSON-Logs (für ELK/Datadog ingestion) und distributed tracing (OpenTelemetry).
- Metrics:
  - Exportiere Retrieval latency, re-rank latency, success-rate, error-rate, streaming throughput.
- Tests:
  - Empfohlenes Testmatrix-Setup:
    - Unit (fast, local), Integration (service mocks), E2E (mocked LLM in CI), Staging (real LLM+Vector minimal config).
  - CI: nightly integration runs with deterministic seeds to detect regressions.

4. Frontend — Komponenten und Status
-----------------------------------

4.1 UI-Architektur & Rendering
------------------------------
- Architekturentscheidungen:
  - Verwende ein erweitertes Markdown-Rendering als Single-Source-of-Truth für Text-Rendering, damit Backend-Markup konsistent interpretiert wird.
  - Halte Rendering-Logik so stateless wie möglich; UI-States nur für interaktive Widgets (expanded source lists, selected citation).
- Komponenten:
  - `MarkdownRenderer` mit Hook-Punkten für Citation-Parsing und safe-HTML-Sanitization.
  - `SourcePanel` rendert die Source-Metadaten; ermöglicht Copy, Open-File, External-Link.
- Status & Empfehlungen (konkret):
  - Accessibility: Ensure roles/aria on interactive elements (citation, suggestion buttons).
  - Performance: Virtualize long source lists to maintain UI responsiveness.

4.2 Client-Server Kommunikation (WebSocket/HTTP)
----------------------------------------------
- Design-Highlights:
  - Streaming Protokoll über WebSocket: JSON-Lines mit typed payloads (token, source_metadata, progress, error)
  - Heartbeat & Keepalive: implementiert im client, mit reconnection strategy und exponential backoff.
- Production Concerns (konkret):
  - Backpressure: implement server-side token-windowing (e.g., send N tokens per second quotas) and client-side token-buffers.
  - Auth: Use JWTs with short TTL for WebSocket upgrades; validate per-message signature when using multi-tenant setups.

4.3 UI-Komponenten (Citations, Suggestions, Sources)
--------------------------------------------------
- Behavioural Contracts:
  - Citation clicks must be idempotent and should not re-issue queries; they only trigger UX actions (scroll/highlight) and optional analytics events.
  - Suggestions are stateless buttons that create new queries with prefilled prompt parameters.
- Implementation Details (konkret):
  - Citation Data Model: {id:int, source_entry_id:string, confidence:float, offset_range:[start,end]}
  - DOM Mapping: data-source-id attributes + WeakMap for in-memory mapping; renderer exposes API `showSource(source_entry_id)`.
  - Source Panel actions: copy link, open in external viewer, download snippet (if blob present).

4.4 Tests & QA
---------------
- Test Strategy (konkret):
  - Implement Playwright tests that run against a CI staging endpoint with an LLM-mock server returning deterministic token streams.
  - Add visual regression snapshots for the Renderer to detect UI regressions.

5. Wechselwirkung — Schnittstellen & Datenfluss
-----------------------------------------------

5.1 Request Flow (detailed)
---------------------------
1. Frontend: user action triggers a Query object (query-text + session-context, optional filters).
2. Transport: the client chooses streaming (WebSocket) or sync (HTTP) based on UI settings or network conditions.
3. Backend pipeline (stepwise):
   a) Ingest & normalize: sanitize inputs, check cache for recent results (by query-hash + user-context).
   b) Query-Expansion (optional): call internal LLM adapter to produce 1..N expanded queries; store expansion metadata.
   c) Retrieval: parallel vector search across shards/collections; apply domain filters and metadata constraints.
   d) Pre-Rank: heuristics (cosine similarity, recency, domain-prior) to select candidate set.
   e) Re-Rank: LLM-based pairwise or listwise ranking on top-N (costly, run in worker if required).
   f) Assembly: stitch result, generate citations with source metadata and confidence scores.
   g) Response: stream tokens + incremental emissions of `source_metadata` so frontend can display sources early.
4. Frontend: incremental render pipeline consumes tokens, updates source panel and suggestion widgets; on end-of-stream, final UI state summary is presented.

5.2 Events & Feedback
----------------------
- Citation Clicks: Frontend publishes click-events (via HTTP/WebSocket) that backend may log or use to adjust ranking heuristics.
- Feedback Buttons: User feedback sent to Feedback endpoint for offline analysis and potential model fine-tuning.

5.3 Contract & Schema-Empfehlung
--------------------------------
- Response-Envelope (Backend → Frontend) sollte ein stabiles Envelope-Schema haben:
  - { request_id, status, partial: bool, payload: { tokens:[], sources:[], suggestions:[], meta:{} } }
- Benefits: Schema erlaubt Fallbacks, inkrementelle Rendering-Pfade und einfache Validation in Clients.

6. Fehlerfälle, Edge-Cases und Resilienz
--------------------------------------

6.1 Operational Patterns
------------------------
- Circuit-breaker pattern for external LLMs
- Token-bucket rate-limiter for user-level protection
- Graceful degradation: when re-rank times out, fallback to pre-rank heuristic; surface a "confidence" banner in the UI.

7. Security & Zugriffskontrolle
-----------------------------
- Auth & Authorization:
  - Adopt RBAC for admin endpoints; session-scoped tokens for user queries.
- WebSocket connections must validate JWTs on upgrade and revalidate on reconnect.
- Secrets Management:
  - Use vault solutions (HashiCorp Vault, Azure Key Vault) for LLM keys in production.
- Data governance:
  - Implement source-level access control lists (ACLs) to prevent exposing restricted documents.

8. Deployment & Betriebshinweise
-------------------------------
 - Dev: Run locally with SQLite + local Vector DB (or mock). Use `start_backend.py` and `start_frontend.py` scripts.
 - Staging/Prod: Use a managed Vector DB service for scale, configure LLM endpoints, enable logging and monitoring. Consider containerization (Docker) and a process supervisor for workers.
 - Backups: Persist SQLite snapshots and vector indexes regularly.

9. Offene Punkte & Empfehlungen
-------------------------------
Priorisierte Implementierungs-Route (Blauer Faden)
-----------------------------------------------
Ziel: Produktionsreife in 3 Sprints (3 × 2 Wochen) — exemplarischer Plan

Sprint 1 — Stabilisierung & Observability (2 Wochen):
 - Implementiere structured logging (JSON), add OpenTelemetry tracing hooks.
 - Export basic Prometheus metrics (retrieval latency, re-rank latency, error rates).
 - Add health endpoints and readiness/liveness probes.
 - Create deterministic LLM/Vector mocks for CI (unit-level mocking harness).
 - Link-Cleanup: address critical broken links documented in link-check report (low-effort/high-value).

Sprint 2 — Robustness & Security (2 Wochen):
 - Implement JWT-based auth for HTTP & WebSocket.
 - Add rate-limiting and circuit-breaker around LLM calls; implement retry-with-backoff.
 - Harden reconnection/backpressure logic for streaming; validate with load tests.
 - Begin DB migration planning (schema diffs SQLite → Postgres).

Sprint 3 — Quality & Release (2 Wochen):
 - Add Playwright E2E tests for core flows (streaming query → render → citation click → source open).
 - Run load tests for retrieval & re-rank pipeline, tune budgets and shard sizes.
 - Finalize documentation, security review and create a release candidate branch.

10. Anhang — wichtige Dateien & Orte
-----------------------------------
 - Backend entrypoints: `start_backend.py`, `backend/veritas_api_backend.py`, `backend/veritas_api_core.py`
 - Frontend entrypoints: `start_frontend.py`, `veritas_frontend_streaming.py`, `veritas_app.py`
 - Config: `config/config.py`
 - Data: `data/veritas_backend.sqlite`, `data/veritas_auto_server.log`
 - Docs (recent): `docs/PHASE5_HYPOTHESIS_GENERATION.md`, `docs/PHASE4_RAG_INTEGRATION.md`, `docs/archive/*`

Checkliste / Deliverables (kurz)
--------------------------------
- Logging & Tracing integriert (OpenTelemetry)
- Prometheus metrics endpoint & health probes
- JWT authentication for API & WebSocket
- Basic circuit-breaker and retry policies for LLM calls
- Deterministic LLM/Vector mocks for CI
- Playwright E2E tests for streaming flows

Abschluss
---------
Diese Fassung erweitert die technische Ausarbeitung um konkrete Implementierungsschritte, Metriken und Teststrategien sowie einen priorisierten Sprint-Plan. Nächste Schritte können sein: Erzeugung von Tasks/Issues aus der Checkliste, Erstellung eines 1‑seitigen TL;DR für Management oder unmittelbarer Start mit Sprint 1, sobald Sie die Freigabe erteilen.
11. Neu identifizierte Funktionen aus jüngsten Docs
--------------------------------------------------
In den zuletzt erstellten/aktualisierten Dokumenten (Phase- & Implementation-Gaps) wurden mehrere spezialisierte Funktionen beschrieben, die im Bericht bisher nur kurz erwähnt oder nicht detailliert behandelt wurden. Die folgenden Kurzbeschreibungen, Auswirkungen und empfohlenen Maßnahmen habe ich in den Bericht übernommen:

- Hypothesis Generation (HypothesisGenerator)
  - Was: Pipeline-Komponente, die aus Query + RAG-Context Hypothesen als strukturierte JSON erzeugt (Prompting via LLM, Schema-Output).
  - Impact: Erlaubt adaptive, hypothesis-driven Templates und reduziert LLM-Kosten durch fokussierte Re-Ranking-Aufrufe.
  - Acceptance: Hypothesis-Schema definiert + Unit-Test mit deterministischem LLM-Mock; End-to-end: Hypothesis führt zu plausiblen Template-Auswahlen in 90% der Fixtures.
  - Nächste Schritte: Implementieren ackend/services/hypothesis_service.py und ackend/models/hypothesis.py; Integrationstest mit seeded mock-LM.
  - Priorität: Hoch (Sprint 2 / optional Sprint 1 subtask).

- Adaptive Template Construction (AdaptiveTemplateGenerator)
  - Was: Generiert dynamische Response-Templates (fact_retrieval, comparison, timeline, calculation, visual) auf Basis der Hypothese.
  - Impact: Standardisiert Antwort-Layouts, erleichtert Widget-Rendering und QA-Automation.
  - Acceptance: 5 Template-Typen implementiert; Template-Validation-Schema; Rendering-Preview in Frontend (mock-stream).
  - Nächste Schritte: ackend/services/template_service.py, model-Klassen und Template-Repository anlegen; Beispiel-Templates und Tests erstellen.
  - Priorität: Mittel-Hoch (Sprint 2).

- Response Quality Monitoring (ResponseQualityMonitor)
  - Was: Automatischer Quality Gate zur Prüfung von Vollständigkeit, Informationslücken und zur Erzeugung interaktiver Missing-Info-Formulare.
  - Impact: Verbessert Antwort-Qualität, reduziert Nachfragen und ermöglicht gezielte User-Interaktion zur Lückenschließung.
  - Acceptance: QualityReport-Schema, automatischer Form-Generator, Integration mit Feedback-Endpoint.
  - Nächste Schritte: ackend/services/quality_monitor.py und ackend/models/quality_report.py implementieren; UI-Connector definieren.
  - Priorität: Mittel (Sprint 3).

- NDJSON Streaming + Widgets/Forms im Stream
  - Was: Erweiterung des Streaming-Protokolls um strukturierte NDJSON-Nachrichten (text_chunk, widget, form, metadata) zur Live-Auslieferung von interaktiven Elementen.
  - Impact: Ermöglicht frühes Anzeigen von Tabellen/Charts/Formularen während Streaming; reduziert perceived latency.
  - Acceptance: Schema-Dokumentation + serverseitige Serializer + clientseitiger Parser/Dispatcher; Playwright E2E, ensuring widgets appear during stream.
  - Nächste Schritte: ackend/models/streaming_protocol.py ergänzen; eritas_streaming_service um widget/form Typen erweitern; rontend/streaming_client.py + widget-Renderer hinzufügen.
  - Priorität: Hoch (Sprint 1 / Sprint 2 tasks).

- NLPService / ProcessBuilder / ProcessExecutor
  - Was: Ergänzende Services zur Frage-Analyse (NER, Intent), zur Prozessgenerierung (ProcessTree) und zur sicheren parallelen Ausführung (ProcessExecutor).
  - Impact: Wandelt freie Queries in orchestrierbare Prozessschritte um; ermöglicht Supervisor- und Agent-basiertes Workflowing.
  - Acceptance: NLPService liefert entity/intent/params mit >90% Accuracy on golden fixtures; ProcessBuilder erzeugt konsistentes ProcessTree; ProcessExecutor führt parallel aus und aggregiert Ergebnisse.
  - Nächste Schritte: Priorisierte Implementierung (siehe Gap-Analysis TODOs in IMPLEMENTATION_GAP_ANALYSIS_TODO.md).
  - Priorität: Hoch (Sprint 1).

- Frontend: NDJSON-Client & Widget-Renderer
  - Was: Client-Komponente, die NDJSON-Streaming-Nachrichten parst, Widgets rendert (table/chart/form/button) und interaktive Events an Backend weiterleitet.
  - Impact: Erlaubt volle Nutzung der Streaming-Widgets; reduziert Friktion für interaktive Nachfragen.
  - Acceptance: Streaming-Client benötigt ein Dispatcher-Interface, Widget-Renderer-Factories und Unit-Tests (snapshot + DOM checks).
  - Nächste Schritte: rontend/streaming_client.py und rontend/widgets/-Module anlegen; Playwright-Tests definieren.
  - Priorität: Mittel-Hoch (Sprint 2).

Diese Ergänzungen wurden dem Bericht als eigenes Kapitel übernommen sowie als ToDos in die priorisierte Roadmap integriert.



