# Mypy Priorisierte Fix-Plan (Top 30)

Datum: 2025-11-13
Scope: `backend` + `shared`

Kurz: Dieser Plan priorisiert die Dateien mit den meisten mypy-Fehlern (output aus `mypy backend shared`), ordnet eine primäre Fehlerklasse zu, schlägt eine Kurzstrategie vor und gibt eine grobe Aufwandsschätzung.

Hinweis: Nach jeder Batch von Änderungen: 1) scoped mypy für geänderte Dateien laufen lassen 2) Änderungen in `docs/changes.md` dokumentieren 3) PR mit Vorher/Nachher mypy-Counts erstellen.

| Rang | Datei | Fehleranzahl | Haupt-Fehlerklassen (Top) | Vorschlag / Fix-Strategie | Aufwand |
|---:|---|---:|---|---|---:|
| 1 | `backend/api/veritas_api_endpoint.py` | 67 | call-arg (35), Any (23) | Prüfe fehlerhafte Funktionsaufrufe; ergänze/korrekte Typannotationen an Signaturen; ersetze `Any`-Rückgaben durch präzise Dict/Model-Typen; minimal-invasive Anpassungen. | medium |
| 2 | `backend/api/veritas_api_backend_pre_v3_migration_20251018_103650.py` | 52 | name-defined (30), attr-defined (6) | Behebe Namenskonflikte / fehlende Importe; typisiere Objekte mit `Dict[str,Any]` oder konkreten Klassen. | medium |
| 3 | `backend/api/veritas_api_backend.py` | 52 | name-defined (30), attr-defined (6) | Wie oben: Namen/Aliase prüfen, lokale Typ-Annotationen, evtl. `cast` an Hotspots. | medium |
| 4 | `backend/agents/test_server_client.py` | 43 | assignment (34) | Korrigiere falsche Zuweisungen (None vs erwarteter Typ); füge Variablen-Typannotationen hinzu. | small |
| 5 | `backend/agents/veritas_intelligent_pipeline.py` | 34 | operator(14), attr-defined(5) | Operator-/Typinkonsistenzen prüfen (z.B. Addition auf optionalen Werten); annotiere Attribute. | medium |
| 6 | `backend/agents/veritas_api_agent_financial.py` | 25 | operator(6), call-arg(3) | Typfehler bei Operationen; füge lokale Annotations / safe-casts hinzu. | medium |
| 7 | `backend/agents/veritas_api_agent_traffic.py` | 23 | str(16), call-arg(3) | Stelle sicher, dass erwartete `str`-Werte tatsächlich Strings sind; normalize inputs. | small |
| 8 | `backend/agents/veritas_api_agent_dwd_weather.py` | 23 | str/object, assignment | Typannotationen für input/return, sichere Casts. | medium |
| 9 | `backend/agents/veritas_api_agent_social.py` | 21 | attr-defined(4), call-arg(3) | Attribute/Attribute-Access absichern, annotate local variables, metadata als `Any` wenn nötig. | small |
|10 | `backend/agents/veritas_api_agent_construction.py` | 21 | str(12), attr-defined(4) | String-Typen überprüfen; annotiere Collections; ggf. replace Collection->list where mutated. | small |
|11 | `backend/services/rag_service.py` | 20 | attr-defined(12), arg-type(6) | RAG-Ausgaben typisieren (z. B. Dict[str,Any]); prüfe Adapter-Schnittstellen. | medium |
|12 | `backend/agents/immissionsschutz_agent_testserver_extension.py` | 18 | no-redef(6), operator(6) | Behebe doppelte Definitionen, Operator-Typen prüfen. | small |
|13 | `backend/agents/immissionsschutz_orchestrator.py` | 18 | no-redef(13) | Namen/Duplikate auflösen, Imports prüfen. | small |
|14 | `backend/agents/framework/base_agent.py` | 17 | no-redef(15) | Konsolidiere Importe / Doppel-Definitionen; lokal typisieren wo nötig. | medium |
|15 | `backend/agents/veritas_api_agent_chemical_data.py` | 15 | arg-type(5), index(5) | Index-Fehler: `object` -> `Dict[str,Any]`/`List[...]`; annotate functions. | medium |
|16 | `backend/orchestration/unified_orchestrator_v7.py` | 14 | call-arg(5), no-any-return(3) | Fix function call signatures; präzisiere Rückgabetypen. | medium |
|17 | `backend/agents/veritas_api_agent_technical_standards.py` | 14 | index(4), operator(3) | Annotiere Collections, cast bei Bedarf; sichere Operator-Usages. | medium |
|18 | `backend/agents/test_load_performance.py` | 13 | name-defined(13) | Behebe lokale Namenskonflikte / Test-Fixtures. | small |
|19 | `backend/api/veritas_api_native.py` | 13 | attr-defined(9), name-defined(3) | Absichern von Attributzugriffen, annotiere Return-Types. | medium |
|20 | `backend/agents/veritas_api_agent_wikipedia.py` | 12 | operator(4), arg-type(4) | Operator- und Argument-Typen prüfen; lokale Annotations. | medium |
|21 | `backend/agents/framework/orchestration_controller.py` | 12 | Collection[str](11) | Convert mutable usage to `list[str]` and annotate; fix unsupported append on Sequence. | small |
|22 | `backend/api/veritas_api_module.py` | 12 | attr-defined(9), no-any-return(3) | Attribute absichern, präzisere Rückgabewerte. | medium |
|23 | `backend/agents/veritas_api_agent_rechtsrecherche.py` | 12 | attr-defined(12) | Attribute/struct fields typisieren. | medium |
|24 | `backend/agents/environmental_agent_adapter.py` | 12 | call-arg(5), no-redef(3) | Call-Arg Fehler beheben, Importe konsolidieren. | small |
|25 | `backend/mcp/veritas_mcp_server.py` | 12 | unused-ignore(12) | Entferne/verifiziere unnötige `type: ignore` Kommentare. | small |
|26 | `backend/services/pki_client.py` | 10 | assignment(4), attr-defined(3) | Typen für Pfade/Strings anpassen (Path vs str), annotate. | small |
|27 | `backend/agents/veritas_supervisor_agent_message_extension.py` | 10 | attr-defined(4), call-arg(4) | Sichere Attribute und Call-Signaturen. | small |
|28 | `backend/agents/veritas_api_agent_atmospheric_flow.py` | 10 | no-any-return(4) | Präzisiere Rückgabetypen, füge annotationen hinzu. | small |
|29 | `backend/agents/test_dwd_weather_standalone.py` | 9 | assignment(5), str/object(3) | Zuweisungs-/String-Typen fixen. | small |
|30 | `backend/agents/veritas_api_agent_verwaltungsrecht.py` | 9 | attr-defined(9) | Attribute typisieren; ggf. dataclasses/attrs einführen. | medium |

## Empfehlungen zur Arbeitsweise
- Batch-Größe: 1–3 Dateien pro Batch, nur minimal-invasive Änderungen (lokale Variablenannotationen, `cast`, kleine Signaturkorrekturen).
- Validierung pro Batch:
  - `.\.venv\Scripts\python.exe -m mypy <changed-files> --config-file pyproject.toml`
  - `pre-commit run --files <changed-files>`
  - Falls vorhanden: `.\.venv\Scripts\python.exe -m pytest tests/<relevant>`
- Dokumentation: Jeden Fix kurz in `docs/changes.md` eintragen (Datum, Autor, Dateien, Kurzbeschreibung, PR).

## Nächste Schritte (Vorschlag)
1. Starte mit einem Low‑risk Batch: `backend/agents/test_server_client.py` (assignment fixes) + `backend/agents/veritas_api_agent_social.py` (kleine attr/index fixes). Ziel: schnelle wins.
2. Re-run mypy on those files and report delta.
3. Iterative Fortsetzung: Schwerpunkt `api`-Module (`veritas_api_endpoint.py`, `veritas_api_backend.py`) anschließend.

---

*Erstellt automatisch aus `mypy_backend_shared.txt`.*
