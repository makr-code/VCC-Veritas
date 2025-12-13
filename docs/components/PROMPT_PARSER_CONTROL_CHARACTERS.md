# Prompt Parser mit Steuerzeichen-Unterstützung

## Übersicht

Der erweiterte Prompt-Parser ermöglicht die direkte Steuerung von Agents und Endpoints über spezielle Steuerzeichen im User-Prompt, ähnlich wie in modernen Chat-Interfaces (Slack, Discord, etc.).

## Steuerzeichen

### @ - Agent-Auswahl
Wählt direkt einen spezifischen Agent aus:

```
@powerpoint - PowerPoint-Agent
@excel - Excel/Tabellen-Agent  
@outlook - Outlook-Agent (E-Mail, Kalender, Aufgaben)
@onenote - OneNote-Agent (Notizen, Dokumentation)
```

**Synonyme:**
- `@ppt`, `@presentation` → PowerPoint
- `@table`, `@tables` → Excel
- `@email`, `@mail` → Outlook
- `@note`, `@notes` → OneNote

**Beispiel:**
```
@powerpoint Erstelle eine Präsentation über Umweltschutz
```

### # - Template-Auswahl
Spezifiziert die zu verwendende Template-Kategorie:

**PowerPoint:**
- `#flowchart` - Flowchart-Diagramme
- `#process` - Prozess-Diagramme
- `#cycle` - Zyklus-Diagramme (PDCA, etc.)
- `#hierarchy` - Organigramme, Hierarchien
- `#matrix` - Matrix-Diagramme (SWOT, 2x2, etc.)
- `#list` - Listen und Aufzählungen
- `#relationship` - Beziehungs-Diagramme
- `#pyramid` - Pyramiden-Diagramme

**Excel:**
- `#data_table` - Daten-Tabellen
- `#comparison` - Vergleichs-Tabellen
- `#summary` - Zusammenfassungen
- `#schedule` - Zeitpläne

**Outlook:**
- `#email_compose` - E-Mail-Erstellung
- `#calendar_event` - Kalender-Termine
- `#task_management` - Aufgaben-Verwaltung
- `#contact_management` - Kontakt-Verwaltung

**OneNote:**
- `#meeting_notes` - Besprechungs-Notizen
- `#project_notes` - Projekt-Dokumentation
- `#checklist` - Checklisten
- `#knowledge_base` - Wissensdatenbank
- `#research_notes` - Recherche-Notizen

**Beispiel:**
```
@powerpoint #flowchart Genehmigungsprozess für Bauantrag
```

### / - Slash-Commands
Führt spezifische Befehle aus:

- `/generate` - Generiere Inhalt
- `/create` - Erstelle neues Dokument
- `/list` - Liste Templates/Optionen
- `/help` - Zeige Hilfe
- `/status` - Zeige Status
- `/templates` - Liste Templates
- `/export` - Exportiere Dokument
- `/preview` - Zeige Vorschau

**Beispiel:**
```
/list @powerpoint #templates
/generate @excel #data_table Verkaufszahlen
```

### ! - Priorität
Setzt die Priorität/Dringlichkeit:

- `!high` - Hohe Priorität
- `!urgent` - Dringlich
- `!medium` - Mittlere Priorität
- `!normal` - Normale Priorität
- `!low` - Niedrige Priorität

**Beispiel:**
```
@outlook !urgent E-Mail an Team über Meeting-Verschiebung
```

### $ - Output-Format
Spezifiziert das gewünschte Ausgabeformat:

- `$pptx` - PowerPoint
- `$pdf` - PDF-Dokument
- `$xlsx` - Excel-Datei
- `$csv` - CSV-Datei
- `$docx` - Word-Dokument
- `$html` - HTML-Datei
- `$json` - JSON-Format
- `$xml` - XML-Format
- `$msg` - Outlook-Nachricht
- `$eml` - E-Mail-Datei
- `$ics` - Kalender-Datei

**Beispiel:**
```
@powerpoint $pdf #swot Wettbewerbsanalyse
@excel $csv Monatsbericht
```

### + - Tags/Kategorien
Fügt Tags/Kategorien hinzu:

- `+confidential` - Vertraulich
- `+draft` - Entwurf
- `+important` - Wichtig
- `+urgent` - Dringend
- `+review` - Zur Überprüfung
- `+final` - Finale Version

**Beispiel:**
```
@onenote #meeting_notes +confidential +important Strategiemeeting
```

## Verwendungsbeispiele

### 1. PowerPoint-Präsentation mit Flowchart
```
@powerpoint #flowchart Genehmigungsprozess für Bauantrag in Stuttgart
```
**Ergebnis:**
- Agent: PowerPoint
- Template: Flowchart
- Clean Query: "Genehmigungsprozess für Bauantrag in Stuttgart"
- Endpoint: `/api/office/presentations/generate`

### 2. Excel-Tabelle als XLSX
```
@excel $xlsx #data_table Verkaufszahlen Q4 2024 nach Region
```
**Ergebnis:**
- Agent: Excel
- Template: data_table
- Format: xlsx
- Clean Query: "Verkaufszahlen Q4 2024 nach Region"

### 3. Dringende E-Mail
```
@outlook !urgent E-Mail an Team: Meeting wurde auf morgen 10 Uhr verschoben
```
**Ergebnis:**
- Agent: Outlook
- Priority: urgent
- Clean Query: "E-Mail an Team: Meeting wurde auf morgen 10 Uhr verschoben"

### 4. Vertrauliche Meeting-Notizen
```
@onenote #meeting_notes +confidential +important Strategiemeeting vom 13.12.2024
```
**Ergebnis:**
- Agent: OneNote
- Template: meeting_notes
- Tags: [confidential, important]
- Clean Query: "Strategiemeeting vom 13.12.2024"

### 5. SWOT-Analyse als PDF
```
@powerpoint #swot $pdf +draft Wettbewerbsanalyse Markt Deutschland
```
**Ergebnis:**
- Agent: PowerPoint
- Template: swot (Matrix)
- Format: pdf
- Tags: [draft]
- Clean Query: "Wettbewerbsanalyse Markt Deutschland"

### 6. Template-Liste anzeigen
```
/list @powerpoint #templates
```
**Ergebnis:**
- Command: list
- Agent: PowerPoint
- Zeigt alle verfügbaren PowerPoint-Templates

### 7. Kombinierte Steuerzeichen
```
@powerpoint #flowchart $pdf !high +draft +review Prozess-Optimierung Lieferkette
```
**Ergebnis:**
- Agent: PowerPoint
- Template: flowchart
- Format: pdf
- Priority: high
- Tags: [draft, review]
- Clean Query: "Prozess-Optimierung Lieferkette"

## API-Integration

### Standard-Endpoint (ohne Parsing)
```http
POST /api/office/process
{
  "query": "Erstelle eine Präsentation",
  "context": {}
}
```

### Enhanced SSE-Endpoint (mit Parsing)
```http
POST /api/sse/enhanced/query
{
  "query": "@powerpoint #flowchart Genehmigungsprozess",
  "parse_controls": true,
  "context": {}
}
```

**Response:**
```json
{
  "session_id": "uuid-1234",
  "parsed_prompt": {
    "original_text": "@powerpoint #flowchart Genehmigungsprozess",
    "clean_text": "Genehmigungsprozess",
    "agent": "powerpoint",
    "templates": ["flowchart"],
    "endpoint": "/api/office/presentations/generate",
    "agent_type": "presentation"
  },
  "routing_info": {
    "agent_type": "presentation",
    "endpoint": "/api/office/presentations/generate",
    "templates": ["flowchart"],
    "clean_query": "Genehmigungsprozess"
  },
  "stream_url": "/api/sse/enhanced/stream/uuid-1234",
  "status": "processing"
}
```

### SSE-Stream für Progress
```javascript
const source = new EventSource('/api/sse/enhanced/stream/uuid-1234');

source.addEventListener('progress', (e) => {
  const data = JSON.parse(e.data);
  console.log(`${data.percentage}%: ${data.message}`);
});

source.addEventListener('result', (e) => {
  const result = JSON.parse(e.data);
  console.log('Result:', result);
});

source.addEventListener('completed', (e) => {
  source.close();
});
```

## Python-Verwendung

### Direkter Parser-Aufruf
```python
from backend.utils.prompt_parser import parse_prompt, get_routing_info

# Parse prompt
result = parse_prompt("@powerpoint #flowchart Prozess erstellen")

print(f"Agent: {result.agent}")
print(f"Templates: {result.templates}")
print(f"Clean Text: {result.clean_text}")
print(f"Endpoint: {result.endpoint}")

# Get routing info
routing = get_routing_info("@excel $xlsx #data_table Verkaufszahlen")
print(routing)
# {
#   "agent_type": "table",
#   "endpoint": "/api/office/tables/generate",
#   "templates": ["data_table"],
#   "output_format": "xlsx",
#   "clean_query": "Verkaufszahlen"
# }
```

### Integration im Orchestrator
```python
from backend.agents.orchestrator.office_agent_orchestrator_integration import get_office_orchestrator
from backend.utils.prompt_parser import parse_prompt

orchestrator = get_office_orchestrator()

# Parse user input
query = "@powerpoint #flowchart Genehmigungsprozess"
parsed = parse_prompt(query)

# Process with orchestrator
result = await orchestrator.process_request(
    query=parsed.clean_text,
    context={
        "template": parsed.templates[0] if parsed.templates else None,
        "output_format": parsed.output_format
    }
)
```

## Best Practices

### 1. Kombiniere sinnvoll
```
✅ @powerpoint #flowchart $pdf Prozess
❌ @powerpoint @excel #flowchart (Mehrere Agents)
```

### 2. Templates vor Text
```
✅ @powerpoint #flowchart Erstelle Prozess
✅ #flowchart @powerpoint Erstelle Prozess
⚠️ Erstelle @powerpoint #flowchart Prozess (Funktioniert, aber weniger lesbar)
```

### 3. Nutze Synonyme
```
@ppt = @powerpoint
@email = @outlook
#prozess = #process
```

### 4. Tags für Metadata
```
+confidential, +draft, +important, +review
```

## Fehlerbehandlung

### Unbekannter Agent
```
@unknown_agent Test
→ Agent wird ignoriert, normale Intent-Recognition greift
```

### Ungültige Template
```
@powerpoint #invalid_template Test
→ Template wird ignoriert, Agent wählt passende Alternative
```

### Mehrere gleiche Steuerzeichen
```
@powerpoint @excel Test
→ Erster wird verwendet: powerpoint
```

## SSE-Integration

Der Prompt-Parser ist vollständig in die SSE-Endpoints integriert:

```http
GET /api/sse/enhanced/examples
```
Zeigt alle verfügbaren Control-Character-Beispiele.

```http
POST /api/sse/enhanced/query
```
Verarbeitet Query mit Prompt-Parsing und gibt Session-ID mit Stream-URL zurück.

```http
GET /api/sse/enhanced/stream/{session_id}
```
SSE-Stream für Echtzeit-Updates während der Verarbeitung.

## Testing

```bash
# Run tests
pytest tests/utils/test_prompt_parser.py -v

# Test with coverage
pytest tests/utils/test_prompt_parser.py --cov=backend.utils.prompt_parser
```

## Zusammenfassung

Der Prompt-Parser mit Steuerzeichen bietet:

✅ **Direkte Agent-Auswahl** via @mentions  
✅ **Template-Spezifikation** via #hashtags  
✅ **Slash-Commands** für Aktionen  
✅ **Prioritäts-Steuerung** via !exclamation  
✅ **Format-Wahl** via $dollar  
✅ **Tag-System** via +plus  
✅ **SSE-Integration** für Real-time Streaming  
✅ **Rückwärts-Kompatibilität** (funktioniert auch ohne Steuerzeichen)  
✅ **Mehrsprachig** (DE/EN Synonyme)  

Dies ermöglicht eine präzise und intuitive Steuerung des Office-Agent-Systems!
