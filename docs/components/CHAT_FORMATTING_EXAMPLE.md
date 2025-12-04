# VERITAS Chat-Formatierung

## Backend-Response Format

Das Backend gibt folgende Struktur zurück:

```json
{
  "response_text": "**Antwort auf Ihre Frage**: ...\n\n**Geo-Kontext**: ...\n\n**System**: ...",
  "confidence_score": 0.85,
  "sources": [
    {"title": "BauGB", "url": "...", "relevance": 0.9},
    {"title": "VwVfG", "url": "...", "relevance": 0.8}
  ],
  "worker_results": {
    "geo_context": {"confidence_score": 0.85, "processing_time": 0.2},
    "legal_framework": {"confidence_score": 0.92, "processing_time": 0.3}
  },
  "follow_up_suggestions": ["Vorschlag 1", "Vorschlag 2"],
  "processing_metadata": {
    "complexity": "basic",
    "processing_time": 0.04,
    "agent_count": 3
  }
}
```

## Frontend-Formatierung

Das Frontend erweitert die Response automatisch:

### 1. Basis-Antwort
```
**Antwort auf Ihre Frage**: Was ist VERITAS?
**Geo-Kontext**: Die Anfrage bezieht sich auf den lokalen Verwaltungsbereich.
**System**: Non-Streaming Verarbeitung
```

### 2. Quellen (automatisch hinzugefügt)
```
📚 **Quellen:**
  1. BauGB (Relevanz: 90%)
  2. VwVfG (Relevanz: 80%)
  3. Gemeinde-FAQ (Relevanz: 70%)
```

### 3. Agent-Informationen (automatisch hinzugefügt)
```
🤖 **Verarbeitet von 3 Agenten:**
  • geo_context: 85% Confidence (0.20s)
  • legal_framework: 92% Confidence (0.30s)
  • document_retrieval: 78% Confidence (0.40s)
```

### 4. Metadaten (bereits im Backend enthalten)
```
💡 85% Confidence | 3 Quellen | ⚡ 0.04s | 🤖 3 Agents
```

### 5. Vorschläge (bereits im Backend enthalten)
```
🔍 **Vorschläge:**
• Welche Unterlagen sind für den Antrag erforderlich?
• Wie lange dauert das Verfahren normalerweise?
• Gibt es Beratungstermine?
```

## Chat-Display-Formatierung

Die Chat-Anzeige verwendet farbige Tags:

- **User**: Blau (#0066CC), Bold
- **VERITAS**: Grün (#006600), Normal
- **Quellen** (📚): Grau-Blau (#666699), Klein
- **Agents** (🤖): Braun (#996600), Klein
- **Metadata** (💡, 🔍): Grau (#999999), Kursiv
- **System**: Grau (#666666), Kursiv
- **Timestamp**: Hell-Grau (#999999), Klein

## Beispiel einer vollständigen Chat-Nachricht

```
[2025-10-05 20:07:51] Sie:
Was ist VERITAS?

[2025-10-05 20:07:52] 🤖 VERITAS:
**Antwort auf Ihre Frage**: Was ist VERITAS?

**Geo-Kontext**: Die Anfrage bezieht sich auf den lokalen Verwaltungsbereich.

**Rechtlicher Rahmen**: Basierend auf aktueller Rechtslage sind folgende Aspekte relevant:
- Baugesetzbuch (BauGB) Regelungen
- Verwaltungsverfahrensgesetz (VwVfG) Bestimmungen
- Kommunale Satzungen

**Dokumente**: Weitere Informationen finden Sie in den verlinkten Dokumenten.

**System**: Non-Streaming Verarbeitung (für Streaming verwenden Sie enable_streaming=true)

📚 **Quellen:**
  1. BauGB (Relevanz: 90%)
  2. VwVfG (Relevanz: 80%)
  3. Gemeinde-FAQ (Relevanz: 70%)

🤖 **Verarbeitet von 3 Agenten:**
  • geo_context: 85% Confidence (0.20s)
  • legal_framework: 92% Confidence (0.30s)
  • document_retrieval: 78% Confidence (0.40s)

💡 85% Confidence | 3 Quellen | ⚡ 0.04s | 🤖 3 Agents

🔍 **Vorschläge:**
• Welche Unterlagen sind für den Antrag erforderlich?
• Wie lange dauert das Verfahren normalerweise?
• Gibt es Beratungstermine?
```

## Statusleiste

Die Statusleiste zeigt nach der Antwort:
```
Bereit - 3 Quellen, 85% Confidence
```
