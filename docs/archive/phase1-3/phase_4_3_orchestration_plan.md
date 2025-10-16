# Phase 4.3 – RAG-Agent-Orchestrierung

## Überblick
- Die `IntelligentMultiAgentPipeline` verarbeitet Anfragen bereits sequenziell (Analyse → RAG → Agenten → Aggregation) und liefert Mock-RAG-Daten.
- `RAG_INTEGRATION_AVAILABLE` lädt `MultiDatabaseAPI` und `OptimizedUnifiedDatabaseStrategy`, wird aber nicht genutzt; bei fehlenden Abhängigkeiten läuft ein Mock-Zweig.
- Agenten werden aktuell in `_step_agent_selection` heuristisch zusammengestellt; Prioritäten oder RAG-Signale fließen nicht in die Entscheidung ein.
- Der `AgentOrchestrator` besitzt JSON-Schema-basierte Pipelines, kann aber nur statisch zwischen Basic/Standard/Advanced-Schemata wechseln.
- `AgentPipelineManager` trackt Prioritäten und Queries, arbeitet jedoch ohne RAG-Kontext und ohne engere Kopplung zur intelligenten Pipeline.

## Anforderungen laut TODO 4.3
1. **RAG-Ergebnisse integrieren**: Vektor-, Graph- und Relational-Ergebnisse müssen normalisiert, bewertet und der Pipeline zur Verfügung gestellt werden.
2. **Agent-Selektion über JSON-Schema**: Agentenauswahl soll aus Analyse + RAG-Kontext gespeist werden.
3. **Dynamische Pipeline-Generierung**: Laufzeit-Anpassung der Agenten-Pipeline auf Basis von Komplexität, Domain und RAG-Signalen.
4. **Agent-Prioritäts-System**: Gewichtung der Agent-Aufgaben nach Relevanz-Scores und Kontextbedarf.

## Relevante Komponenten
- `backend/agents/veritas_intelligent_pipeline.py`
  - `_step_rag_search`, `_step_agent_selection`, `_step_parallel_agent_execution`
  - `self.pipeline_steps` speichert Schritt-Metadaten, geeignet für Priorität & Monitoring.
- `backend/agents/veritas_api_agent_orchestrator.py`
  - JSON-Schemata (`basic`, `standard`, `advanced`) und dynamische Agenten-Resolver.
  - Kann Pipeline-Taks mit Priorität und Abhängigkeiten erzeugen.
- `backend/agents/veritas_api_agent_pipeline_manager.py`
  - Enthält Query-Prioritäten, Tracks, Statistiken und Agent-Ergebnisse.
- `backend/agents/veritas_ollama_client.py`
  - Liefert LLM-Kommentare und Synthese; braucht RAG-Kontext in sauberen Strukturen.
- Externe Layer: `database/database_api.py`, `uds3/uds3_core.py` (bereits importiert; tatsächliche API-Aufrufe werden in der Implementation validiert).

## Technische Leitplanken & Annahmen
- `MultiDatabaseAPI` stellt eine vereinheitlichte Methode (z. B. `unified_search` / `query`) bereit, die RAG-Ergebnisse liefert. Wir kapseln externe APIs in einem neuen Service, damit die Pipeline testbar bleibt.
- Bei fehlenden Abhängigkeiten (aktueller Mock-Modus) müssen wir deterministische Testdaten bereitstellen.
- Agent-Prioritäten werden als Float (`0.0–1.0`) geführt, analog zu bestehenden Schema-Dateien.
- Pipeline-Schritte sollen rückwärtskompatibel bleiben: Wenn RAG ausfällt, greifen Mock-Daten und Standard-Agenten.

## Umsetzungsschritte
1. **RAG Context Service erstellen**
   - Neuer Modulvorschlag: `backend/agents/rag_context_service.py` mit `RAGContextBuilder`.
   - Aufgaben:
     - Normalisierung von Vector-/Graph-/Relational-Ergebnissen in folgendes Schema:
       ```json
       {
         "documents": [{"id": str, "title": str, "snippet": str, "relevance": float, "domain_tags": [str]}],
         "vector": {"matches": [...], "statistics": {...}},
         "graph": {"related_entities": [...], "confidence": float},
         "relational": {"metadata_hits": int, "filters": [...]} 
       }
       ```
     - Fallback-Generator mit reproduzierbaren Dummy-Daten, falls `RAG_INTEGRATION_AVAILABLE` `False` meldet oder die externe Anfrage fehlschlägt.
     - Logging + Timing-Metriken.
   - Unit-Test-Ansatz: Mocking von MultiDatabaseAPI/UDS3, Prüfung der Normalisierung.

2. **`_step_rag_search` auf Service umstellen**
   - Service injizieren (`self.rag_service = RAGContextBuilder(...)`) während `initialize()`.
   - Reale Suchanfragen (`query_text`, optionale Filter aus `request.user_context`).
   - RAG-Ergebnis mit Kontext-Qualitätsscore, Aggregatsstatistiken und Fallback-Metadaten (`"fallback": True`).
   - Speichern von Timings und Confidence-Werten in `step.result` für Monitoring.

3. **Agent-Selektion RAG-basiert erweitern**
   - Mapping definieren: Domain + RAG-Dokument-Tags → erforderliche Agenten.
   - Heuristiken verbessern:
     - Mehr Dokumente mit `domain_tags=['environmental']` → `environmental`-Agent priorisieren.
     - Hohe Graph-Beziehungen zu `Behörden` → `authority_mapping`-Agent hinzufügen.
   - Integration in `_step_agent_selection`:
     - Agentenliste aus Analyse (`analysis.required_agents`) + RAG-Insights verschmelzen.
     - Priorität je Agent = Baseline (aus Schema) × RAG-Relevanz × Komplexitätsfaktor.
     - Ergebnisstruktur erweitern um `priority_map`, `selection_reasoning` (hilft für Debugging & LLM-Kommentare).

4. **Dynamische Pipeline-Generierung aktivieren**
   - `AgentOrchestrator.preprocess_query` um Parameter `rag_context` erweitern; Schema-Wahl auf Domain + Komplexität + RAG-Signale stützen.
   - Möglichkeit, zusätzliche Tasks einzuschleusen:
     - Beispiel: Wenn Relational-Result `metadata_hits` < Threshold, füge `manual_validation`-Agent ein.
     - Wenn Vector-Suche top Dokument mit `quality < 0.6`, triggere `quality_assessor`.
   - Prioritäten (`AgentPipelineTask.priority`) auf Grundlage des neuen `priority_map` anpassen.
   - Rückmeldung an Pipeline: `execution_plan.parallel_agents` sortiert nach Score, `sequential_agents` mit Abhängigkeiten aus Schema.

5. **Agent-Prioritäts-System & Monitoring**
   - Neue Metriken in `IntelligentMultiAgentPipeline.stats` und `processing_metadata` aufnehmen (`rag_documents_found`, `agent_priority_spread`, `fallback_used`).
   - Erweiterung von `_step_parallel_agent_execution` für Prioritätsbehandlung (z. B. sortieren bevor Threads gestartet werden, Zeit-Slices anhand Score).
   - Optionale Persistenz: `AgentPipelineManager` kann `priority` und `rag_context` speichern, damit spätere Schritte (z. B. Monitoring) konsistent bleiben.

6. **Test- & Validierungsstrategie**
   - **Unit**: RAG-Service (Normalisierung), Agent-Selektion (Mapping), Prioritätserzeugung.
   - **Integration (async)**: Simulierter Pipeline-Lauf mit fallback aktiviert; Validierung von `agent_selection.priority_map` und finaler Response.
   - **Manuell**: Erweiterung von `tests/manual/test_ollama_fallback.py` oder neues Skript `tests/manual/test_pipeline_phase4_3.py` für End-to-End-Mock.

## Risiken & Abhängigkeiten
- Externe Module (`database_api`, `uds3_core`) fehlen lokal → Umsetzung muss Mock-fähig bleiben, reale Integration erst nach Bereitstellung.
- `AgentOrchestrator` ist umfangreich; dynamische Eingriffe in JSON-Schemas brauchen gründliche Tests, um bestehende Flows nicht zu brechen.
- Performance: Zusätzliche Priorisierung und RAG-Auswertung darf den Gesamtdurchlauf (Ziel < 5 s) nicht wesentlich erhöhen → Caching, Timeout-Handling einplanen.

## Empfohlene Reihenfolge & Milestones
1. **Milestone A**: RAG-Service + `_step_rag_search` liefert strukturierte Ergebnisse (Mock + Real).  _Dauer ca. 1–2 Tage_
2. **Milestone B**: Agent-Selektion nutzt RAG-Signale, Prioritäten werden berechnet.  _Dauer ca. 1 Tag_
3. **Milestone C**: Dynamische Pipeline-Anpassung über Orchestrator & Manager.  _Dauer ca. 1–2 Tage_
4. **Milestone D**: Tests, Monitoring, Dokumentation.  _Dauer ca. 1 Tag_

## Quick Wins / Folgeaufgaben
- Ergänzung eines `PipelineDiagnostics`-Endpunkts im Backend, um live RAG- und Prioritätsdaten einzusehen.
- Vorbereitung eines Feature-Flags (`enable_dynamic_agent_priorities`) für stufenweisen Rollout.
- Dokumentation in `STATUS_REPORT.md` aktualisieren, sobald Milestone A erreicht ist.
