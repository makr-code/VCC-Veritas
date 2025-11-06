# VERITAS MCP Quick Start

Stand: 31. Oktober 2025

## Überblick

Der VERITAS MCP-Server (Model Context Protocol) ermöglicht die Integration von
Desktop-Anwendungen (z. B. Microsoft Word/Excel, VS Code, Claude Desktop) mit
den VERITAS-Funktionen über ein standardisiertes Protokoll (JSON-RPC über stdio).

Dieses Dokument beschreibt, wie Sie den MCP-Server lokal starten und testen.

## Voraussetzungen

- Python 3.10+
- Optional: MCP-Python-SDK (`mcp`)
- VERITAS-Repository ausgecheckt

## Installation

1) Abhängigkeiten installieren:

```powershell
pip install -r requirements.txt
```

2) (Optional) MCP-SDK installieren, um den stdio-Server zu aktivieren:

```powershell
pip install mcp
```

## Starten

- Standard (stdio, erfordert MCP-SDK):

```powershell
python start_mcp_server.py
```

- CLI-Demo (ohne MCP-SDK lauffähig):

```powershell
python start_mcp_server.py --cli
```

Die CLI-Demo führt eine Beispiel-Hybrid-Suche aus und listet verfügbare Agenten.

## Verfügbare Tools (MVP)

- `hybrid_search(query: str, top_k: int = 5)`
  - Führt VERITAS Hybrid-Suche aus (BM25 + Dense + RRF)
- `list_agents()`
  - Listet Agenten anhand der Module unter `backend/agents/`
- `execute_agent(query: str, agent_types: list[str] = [])`
  - Stub – wird im nächsten Schritt an die Multi-Agent-Pipeline angeschlossen

## Prompts (Flexibel konfigurierbar)

Die Prompts werden aus `config/mcp_prompts.json` geladen. Aktuell verfügbar:

1. **legal-research**
   - Parameter: `topic` (str), `jurisdiction` (str, default "DE")
   - Beschreibung: Juristische Recherche mit IEEE-Quellenhinweisen

2. **baurecht-query**
   - Parameter: `bauvorhaben` (str), `standort` (str)
   - Beschreibung: Baurechtliche Zulässigkeitsprüfung

3. **immissionsschutz-analyse**
   - Parameter: `vorhaben` (str), `standort` (str)
   - Beschreibung: BImSchG-Analyse (Lärm, Luft, Geruch)

4. **verwaltungsrecht-prüfung**
   - Parameter: `fragestellung` (str), `kontext` (str, optional)
   - Beschreibung: Verwaltungsrechtliche Prüfung

**Hinweis:** Prompts können einfach durch Bearbeiten von `config/mcp_prompts.json` 
angepasst oder erweitert werden, ohne den Code zu ändern.

## Prompt-Konfiguration

Um eigene Prompts hinzuzufügen, editieren Sie `config/mcp_prompts.json`:

```json
{
  "prompts": [
    {
      "name": "mein-prompt",
      "description": "Beschreibung des Prompts",
      "system_message": "System-Instruktionen für den LLM",
      "user_template": "User-Template mit {parameter1} und {parameter2}",
      "parameters": {
        "type": "object",
        "properties": {
          "parameter1": {"type": "string", "description": "..."},
          "parameter2": {"type": "string", "default": "...", "description": "..."}
        },
        "required": ["parameter1"]
      }
    }
  ]
}
```

## Resources (Dokumentenabruf)

Der MCP-Server bietet Zugriff auf VERITAS-Dokumente über ein URI-Schema:

**URI-Format:** `veritas://documents/{document_id}`

**Implementierung:**
- Sucht automatisch in PostgreSQL, ChromaDB und CouchDB
- Gibt Volltext + Metadaten zurück (JSON oder text/plain)
- Fallback bei nicht gefundenen Dokumenten

**Beispiel-Nutzung (MCP-Client):**
```typescript
const doc = await mcp.readResource("veritas://documents/doc_12345");
console.log(doc.text);       // Dokumentinhalt
console.log(doc.metadata);   // Titel, Quelle, etc.
```

## Nächste Schritte

- MCP-Tool-Registrierung mit konkreter SDK-Version verdrahten
- Prompts und Resources ergänzen (z. B. `legal-research`, `veritas://documents/{id}`)
- Word Add-In/VS Code Extension an MCP-Tools anbinden

## Troubleshooting

- „MCP-Python-SDK nicht installiert“: `pip install mcp` ausführen
- Importfehler im VERITAS-Backend: Stellen Sie sicher, dass Sie aus dem Repo-Root starten
- UDS3 nicht verfügbar: Die Hybrid-Suche nutzt Fallback-Pfade; produktiv UDS3 aktivieren
