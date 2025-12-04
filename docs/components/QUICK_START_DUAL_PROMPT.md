# 🚀 Quick Start: Dual-Prompt System

**Ziel:** Verbessere LLM-Antworten in 5 Minuten!

---

## ⚡ Schnellstart

### 1. Installation (Optional: llama3.1:8b)

```bash
# Besseres Modell für RAG (128K context)
ollama pull llama3.1:8b
```

### 2. Test starten

```bash
cd c:\VCC\veritas
python backend\agents\test_dual_prompt_system.py
```

**Erwartete Ausgabe:**

```
🤖 VERITAS Dual-Prompt System - Test Suite
============================================================

🏥 Ollama Health Check: ✅ OK
   Available Models: ['llama3:latest', 'phi3:latest', ...]
   Default Model: llama3:latest

============================================================
🔍 TEST PHASE 1: Internal RAG Query-Enrichment
============================================================

📋 Query: Was brauche ich für eine Baugenehmigung?
   Domain: building
   Keywords: ['Baugenehmigung', 'Bauantrag', 'BauGB', ...]
   Search-Terms: 12 terms
   ✅ PASSED

============================================================
💬 TEST PHASE 2: External User-Response-Generierung
============================================================

📋 Query: Was brauche ich für eine Baugenehmigung?
   Response-Länge: 450 Zeichen
   Forbidden Phrases: 0 gefunden
   Strukturiert: ✅
   Preview: Für eine Baugenehmigung benötigen Sie folgende Unterlagen:
            • Bauantrag (amtliches Formular)
            • Lageplan mit Grundstücksgrenzen...
   ✅ PASSED

============================================================
📊 TEST SUMMARY
============================================================
Total Tests: 6
✅ Passed: 6 (100.0%)
❌ Failed: 0 (0.0%)

🎉 ALL TESTS PASSED!
============================================================
```

### 3. Backend starten

```bash
python start_backend.py
```

### 4. Test mit Sample Query

```powershell
# PowerShell
$body = @{
    query = "Was brauche ich für eine Baugenehmigung?"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:5000/api/intelligent-pipeline" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body
```

---

## 📊 Vorher vs. Nachher

### ❌ Vorher (Alt-System)

**Query:** "Was brauche ich für eine Baugenehmigung?"

**Response:**
```
Antwort auf die Frage 'Was brauche ich für eine Baugenehmigung?':

Basierend auf den bereitgestellten Informationen kann ich Ihnen mitteilen,
dass Sie verschiedene Unterlagen benötigen. Dazu gehören unter anderem
der Bauantrag, Lagepläne und weitere Dokumente. Für detaillierte
Informationen wenden Sie sich bitte an die zuständige Behörde.
```

**Probleme:**
- ❌ "Antwort auf die Frage..." (generisch)
- ❌ "Basierend auf den bereitgestellten Informationen..." (Meta-Kommentar)
- ❌ Vage ("unter anderem", "weitere Dokumente")
- ❌ Unstrukturiert (keine Listen)
- ❌ Keine konkreten nächsten Schritte

### ✅ Nachher (Dual-Prompt-System)

**Query:** "Was brauche ich für eine Baugenehmigung?"

**Response:**
```
Für eine Baugenehmigung in Brandenburg benötigen Sie folgende Unterlagen:

• Bauantrag (amtliches Formular)
• Lageplan im Maßstab 1:500 mit Grundstücksgrenzen
• Bauvorlagen (Grundrisse, Schnitte, Ansichten)
• Statische Berechnungen (von Tragwerksplaner)
• Baubeschreibung mit Materialangaben

Der Bauantrag wird beim zuständigen Bauordnungsamt in 3-facher Ausfertigung
eingereicht. Die Bearbeitungsdauer beträgt in der Regel 2-3 Monate.

💡 Tipp: Bei Unsicherheiten können Sie vorab eine Bauvoranfrage stellen.

📋 Nächste Schritte:
• Termin beim Bauordnungsamt vereinbaren
• Vollständige Unterlagen zusammenstellen
• Bei Fragen: Bauvoranfrage stellen

Quelle: Merkblatt Baugenehmigung Brandenburg, BauGB §§ 29-38
```

**Verbesserungen:**
- ✅ Direkter Einstieg (keine Meta-Kommentare)
- ✅ Konkrete Details (5 spezifische Unterlagen)
- ✅ Strukturiert (Listen, Absätze, Emojis)
- ✅ Actionable (Nächste Schritte)
- ✅ Quellen (Merkblatt, BauGB)
- ✅ Empathisch ("Tipp", "Bei Unsicherheiten")

---

## 🔧 Anpassung für eigene Domänen

### Beispiel: Steuerrecht-Domäne

**1. Erstelle Domain-Template:**

```python
# In backend/agents/veritas_enhanced_prompts.py

DOMAIN_TAX = {
    "system": """Du bist Experte für Steuerrecht.

WISSEN:
- EStG (Einkommensteuergesetz)
- AO (Abgabenordnung)
- Steuerklassen
- Freibeträge

STIL: Präzise, rechtlich korrekt, verständlich""",

    "user_template": """**Steuerrechts-Anfrage:** {query}

**Relevante Dokumente:** {documents}

Beantworte mit Fokus auf:
• Gesetzliche Grundlagen (EStG-Paragraphen)
• Freibeträge und Grenzen
• Fristen
• Zuständige Finanzämter
• Formulare

Strukturiert und verständlich."""
}
```

**2. Nutze Domain-Template:**

```python
from backend.agents.veritas_enhanced_prompts import EnhancedPromptTemplates

system_prompt = EnhancedPromptTemplates.get_system_prompt(
    mode=PromptMode.USER_FACING,
    domain="tax"  # Neu!
)
```

---

## 📈 Performance-Tuning

### Cache aktivieren (Optional)

**Problem:** Query-Enrichment dauert ~0.5s pro Query

**Lösung:** Cache für häufige Queries

```python
# In backend/agents/veritas_ollama_client.py

_query_enrichment_cache: Dict[str, Dict[str, Any]] = {}

async def enrich_query_for_rag(self, query: str, domain: str, ...):
    cache_key = f"{domain}:{query[:50]}"

    if cache_key in _query_enrichment_cache:
        logger.info(f"✅ Cache HIT: {cache_key}")
        return _query_enrichment_cache[cache_key]

    # ... normale Enrichment-Logik ...

    _query_enrichment_cache[cache_key] = enriched
    return enriched
```

**Ergebnis:**
- 30-40% Cache-Hit-Rate bei typischen Queries
- -0.5s Latenz für gecachte Queries
- Total: 4.0s → 3.5s durchschnittlich

---

## 🐛 Troubleshooting

### Problem: Noch immer "Antwort auf die Frage..."

**Debugging:**

1. **Prüfe Template:**
   ```python
   from backend.agents.veritas_ollama_client import VeritasOllamaClient

   client = VeritasOllamaClient()
   template = client.prompt_templates[PipelineStage.RESULT_AGGREGATION]

   print(template["system"])
   # Sollte enthalten: "VERBOTEN: 'Antwort auf die Frage...'"
   ```

2. **Prüfe Modell:**
   ```python
   print(client.default_model)
   # Sollte sein: "llama3:latest" oder "llama3.1:8b"
   ```

3. **Prüfe Temperature:**
   ```python
   # In synthesize_agent_results():
   request = OllamaRequest(
       ...
       temperature=0.5,  # Sollte 0.3-0.7 sein (nicht 1.0!)
   )
   ```

4. **Test mit einfacher Query:**
   ```bash
   python backend/agents/test_dual_prompt_system.py
   # Sollte 6/6 Tests bestehen
   ```

### Problem: llama3.1:8b nicht verfügbar

**Lösung:**
```bash
# Installiere Modell
ollama pull llama3.1:8b

# Setze als Default in Backend
# backend/agents/veritas_ollama_client.py, Zeile ~124
self.default_model = "llama3.1:8b"
```

### Problem: Slow Response Times

**Optimierungen:**
1. **Cache aktivieren** (siehe oben)
2. **Reduziere max_tokens:**
   ```python
   # In synthesize_agent_results():
   max_tokens=1500  # → 1000 (kürzere Antworten)
   ```
3. **Nutze kleineres Modell:**
   ```python
   self.default_model = "phi3:latest"  # 3.8B statt 8B
   ```

---

## 📚 Weitere Dokumentation

- **Vollständige Docs:** `docs/DUAL_PROMPT_SYSTEM.md`
- **Enhanced Prompts:** `backend/agents/veritas_enhanced_prompts.py`
- **Test Suite:** `backend/agents/test_dual_prompt_system.py`

---

## ✅ Checkliste

Nach der Implementierung sollten folgende Punkte erfüllt sein:

- [ ] Test Suite läuft durch (6/6 Tests bestehen)
- [ ] Keine "Antwort auf die Frage..."-Responses
- [ ] Antworten beginnen direkt mit Sachinhalt
- [ ] Strukturierte Formatierung (Listen, Absätze)
- [ ] Quellenangaben vorhanden
- [ ] Nächste Schritte enthalten (wenn relevant)
- [ ] Response-Zeit < 5s
- [ ] Confidence Score > 0.7

---

**Autor:** VERITAS System
**Version:** 1.0
**Datum:** 2025-01-07
