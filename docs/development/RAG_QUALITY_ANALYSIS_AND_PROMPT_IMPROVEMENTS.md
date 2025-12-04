# RAG Quality Analysis & Prompt-Verbesserungen für Verwaltungsrecht

**Datum:** 10. Oktober 2025
**Test-Version:** v3.19.0 Multi-Model
**Getestete Modelle:** llama3.1:latest, llama3.1:8b, mistral:latest
**Testumfang:** 15 Tests (3 Modelle × 5 komplexe Fragen)

---

## 📊 Executive Summary

### Gesamtergebnis
- **Success Rate:** 15/15 (100%) - alle Tests bestanden
- **Durchschnittliche Antwortlänge:** 984 Zeichen
- **Durchschnittliche Aspekt-Abdeckung:** 32% (⚠️ kritisch niedrig)

### 🔴 KRITISCHE PROBLEME (zu beheben)

| Problem | Häufigkeit | Kritikalität | Impact |
|---------|------------|--------------|---------|
| **0 IEEE-Zitationen** | 15/15 (100%) | 🔴 KRITISCH | Verwaltungsrechtlich **nicht belastbar** |
| **0 Follow-up-Vorschläge** | 15/15 (100%) | 🟡 HOCH | Benutzerführung fehlt komplett |
| **Niedrige Aspekt-Abdeckung** | 9/15 (60%) | 🔴 KRITISCH | Unvollständige Antworten |
| **Fehlende Paragraphen-Referenzen** | 15/15 (100%) | 🔴 KRITISCH | Keine Rechtsgrundlage nachweisbar |

### ✅ Stärken
- Alle Modelle liefern ausführliche Antworten (740-1279 Zeichen)
- Gute Struktur mit Markdown (14/15 Tests)
- 16 Quellen pro Antwort werden abgerufen (aber nicht zitiert!)

---

## 🔬 Detaillierte Problemanalyse

### Problem 1: IEEE-Zitationen fehlen komplett (0/15)

**Ist-Zustand:**
```
Antwort: "Die Baugenehmigung erfordert verschiedene Unterlagen..."
         ^^^^^^^^^^^^^^^^^^^^^^
         Keine Quellenangabe [1], [2], [3]
```

**Soll-Zustand (verwaltungsrechtlich belastbar):**
```
Antwort: "Die Baugenehmigung erfordert verschiedene Unterlagen [1][2].
         Nach § 58 LBO BW müssen folgende Voraussetzungen erfüllt sein [1]:
         - Bauvorlagen gemäß § 7 LBOVVO [3]
         - Nachweis der Standsicherheit [2]..."

[1] Landesbauordnung Baden-Württemberg (LBO BW), § 58
[2] § 55 LBO BW - Technische Nachweise
[3] LBOVVO § 7 - Bauvorlagen
```

**Warum ist das kritisch?**
- Verwaltungsrecht basiert auf **Rechtsquellen** (Gesetze, Verordnungen, Urteile)
- Ohne Zitation = nicht nachprüfbar = **rechtlich wertlos**
- Nutzer muss Rechtsgrundlage kennen für:
  - Widerspruchsverfahren
  - Verwaltungsgerichtsklagen
  - Beratungsgespräche mit Behörden

---

### Problem 2: Follow-up-Vorschläge fehlen komplett (0/15)

**Ist-Zustand:**
```json
{
  "suggestions": []  // ❌ Leer
}
```

**Soll-Zustand:**
```json
{
  "suggestions": [
    "Welche Unterlagen benötige ich für § 58 LBO BW?",
    "Wie lange dauert ein vereinfachtes Genehmigungsverfahren?",
    "Was kostet eine Baugenehmigung in Baden-Württemberg?",
    "Welche Ausnahmen gibt es nach § 50 LBO BW?"
  ]
}
```

**Impact:**
- Nutzer muss selbst wissen, welche Folgefragen relevant sind
- Keine Benutzerführung durch komplexe Verfahren
- Verpasste Chance für tiefere Exploration

---

### Problem 3: Aspekt-Abdeckung nur 32% (Ø)

**Beispiel Q1 - Baugenehmigung:**
```
Erwartete Aspekte (5):
  1. ✅ Rechtliche Voraussetzungen (§§ LBO BW)
  2. ❌ Fristen (Bearbeitungsdauer)
  3. ❌ Kosten (Gebühren)
  4. ❌ Ausnahmen (Genehmigungsfreistellung)
  5. ❌ Vereinfachtes Verfahren

Abdeckung: 1/5 = 20% ❌
```

**Ursache:**
- LLM antwortet nur auf ersten Aspekt der Frage
- Komplexe Multi-Teil-Fragen werden nicht vollständig beantwortet
- Prompt instruiert nicht zur vollständigen Abdeckung aller Aspekte

---

### Problem 4: Fehlende Paragraphen-Referenzen

**Ist-Zustand:**
```
"Die Baugenehmigung wird vom Baurechtsamt erteilt..."
```

**Soll-Zustand:**
```
"Die Baugenehmigung wird vom Baurechtsamt erteilt (§ 58 Abs. 1 LBO BW)..."
```

**Verwaltungsrechtliche Relevanz:**
- Jede Aussage muss auf Rechtsgrundlage basieren
- Paragraphen-Referenzen ermöglichen Nachprüfung
- Bei Widerspruch/Klage: Rechtsgrundlage ist essentiell

---

## 🎯 Konkrete Prompt-Verbesserungen

### Verbesserung 1: IEEE-Zitationen erzwingen

**AKTUELLER PROMPT (vermutlich):**
```python
prompt = f"""
Beantworte die folgende Frage basierend auf dem Kontext:

Frage: {question}

Kontext: {retrieved_documents}

Antwort:
"""
```

**VERBESSERTER PROMPT:**
```python
prompt = f"""
Du bist ein Experte für Verwaltungsrecht mit Schwerpunkt Baurecht Baden-Württemberg.

WICHTIGE ZITATIONS-REGELN (ZWINGEND):
1. Verwende IEEE-Zitationen [1], [2], [3] für JEDE Aussage
2. Zitiere MINDESTENS 3-5 verschiedene Quellen
3. Setze Zitationen DIREKT nach der zitierten Aussage: "...Voraussetzung [1][2]."
4. Am Ende: Liste ALLE Quellen im Format:
   [1] Quelle 1: {source_title}
   [2] Quelle 2: {source_title}

AUFBAU DER ANTWORT (ZWINGEND):
1. **Hauptantwort** mit IEEE-Zitationen [1][2][3]
2. **Paragraphen-Referenzen** (z.B. § 58 LBO BW)
3. **Quellen-Liste** am Ende

Frage: {question}

VERFÜGBARE QUELLEN:
{format_sources_for_prompt(retrieved_documents)}

BEISPIEL für korrekte Zitation:
"Die Baugenehmigung erfordert Bauvorlagen [1]. Nach § 58 LBO BW sind folgende Unterlagen einzureichen [1][2]:
- Lageplan [3]
- Bauzeichnungen [2]

[1] Landesbauordnung Baden-Württemberg (LBO BW), § 58
[2] § 7 LBOVVO - Bauvorlagen
[3] VwV LBO BW zu § 58"

DEINE ANTWORT (MIT ZITATIONEN):
"""
```

---

### Verbesserung 2: Follow-up-Vorschläge generieren

**ZUSÄTZLICHER PROMPT-TEIL:**
```python
# NACH der Hauptantwort

follow_up_prompt = f"""
Generiere 4-5 verwaltungsrechtlich relevante Follow-up-Fragen basierend auf:

1. Der Benutzerfrage: {question}
2. Deiner Antwort
3. Typischen nächsten Schritten in Verwaltungsverfahren

ANFORDERUNGEN:
- Spezifisch und handlungsorientiert
- Bezug zu konkreten Paragraphen (z.B. § 58 LBO BW)
- Chronologisch sinnvoll (nächste Verfahrensschritte)
- Praktisch relevant für Bauherren/Architekten

FORMAT (JSON):
{{
  "suggestions": [
    "Welche Unterlagen benötige ich für § 58 LBO BW?",
    "Wie lange dauert die Bearbeitung nach § 59 LBO BW?",
    "Was kostet die Baugenehmigung gemäß Gebührenordnung?",
    "Welche Ausnahmen gibt es nach § 50 LBO BW?"
  ]
}}
"""
```

---

### Verbesserung 3: Multi-Aspekt-Abdeckung erzwingen

**PROMPT-ENHANCEMENT:**
```python
# Automatisch Aspekte aus Frage extrahieren
question_aspects = extract_aspects_from_question(question)
# z.B. ["Voraussetzungen", "Fristen", "Kosten", "Ausnahmen"]

prompt_with_aspects = f"""
Die Frage enthält {len(question_aspects)} ASPEKTE. Du MUSST ALLE davon abdecken:

{chr(10).join([f"{i+1}. {aspect}" for i, aspect in enumerate(question_aspects)])}

STRUKTURIERE deine Antwort nach diesen Aspekten:

## 1. {question_aspects[0]}
[Antwort mit Zitationen [1][2]]

## 2. {question_aspects[1]}
[Antwort mit Zitationen [3][4]]

... (für jeden Aspekt)

Wenn zu einem Aspekt KEINE Informationen in den Quellen vorhanden sind:
- Schreibe: "Zu {aspect} liegen keine Informationen vor."
- Schlage Follow-up vor: "Bitte konkretisiere deine Frage zu {aspect}."
"""
```

---

### Verbesserung 4: Paragraphen-Referenzen betonen

**ZUSÄTZLICHE INSTRUKTIONEN:**
```python
legal_reference_instructions = """
RECHTSQUELLEN-ANFORDERUNGEN (verwaltungsrechtlich zwingend):

1. Jede Rechtsaussage MUSS eine Rechtsgrundlage haben:
   - Paragraphen: § 58 LBO BW, § 7 LBOVVO
   - Artikel: Art. 14 GG
   - Urteile: BVerwG 4 C 16.08
   - Verordnungen: LBOVVO, MBO

2. FORMAT:
   - "Nach § 58 Abs. 1 LBO BW..."
   - "Gemäß Art. 14 GG..."
   - "Laut VwV LBO BW zu § 58..."

3. Bei Unsicherheit:
   - "In der Regel nach § 58 LBO BW..."
   - "Üblicherweise gemäß § 59 LBO BW..."
   - "Siehe auch § 7 LBOVVO..."

BEISPIEL:
"Die Baugenehmigung wird vom Baurechtsamt erteilt (§ 58 Abs. 1 LBO BW) [1].
Die Bearbeitungsfrist beträgt in der Regel 3 Monate (§ 59 Abs. 2 LBO BW) [2]."
"""
```

---

## 🛠️ Implementierung: Verbesserter System-Prompt

**Datei:** `backend/agents/veritas_enhanced_prompts.py`

```python
VERWALTUNGSRECHT_SYSTEM_PROMPT = """
Du bist ein hochspezialisierter Experte für Verwaltungsrecht mit Schwerpunkt Baurecht Baden-Württemberg.

# ZITATIONS-PRINZIPIEN (ABSOLUT ZWINGEND)

1. **IEEE-Zitationen:**
   - Verwende [1], [2], [3] nach JEDER zitierten Aussage
   - Mindestens 3-5 verschiedene Quellen pro Antwort
   - Format: "Aussage [1][2]." (Zitation VOR dem Punkt)

2. **Quellen-Liste am Ende:**
   ```
   [1] Landesbauordnung Baden-Württemberg (LBO BW), § 58 - Baugenehmigung
   [2] § 7 LBOVVO - Bauvorlagen und Nachweise
   [3] VwV LBO BW zu § 58 - Verwaltungsvorschrift Baugenehmigung
   ```

3. **Paragraphen-Referenzen:**
   - Jede Rechtsaussage braucht Rechtsgrundlage
   - Format: "Nach § 58 Abs. 1 LBO BW..." oder "(§ 58 LBO BW)"
   - Bei Unsicherheit: "In der Regel nach § 58 LBO BW..."

# ANTWORT-STRUKTUR (ZWINGEND)

1. **Einleitung** (1-2 Sätze)
   - Kurze Zusammenfassung mit Hauptparagraphen

2. **Haupt-Aspekte** (nach Frage strukturiert)
   - Jeder Aspekt als eigener Abschnitt (## Überschrift)
   - Bullet-Points für Details
   - IEEE-Zitationen bei jedem Punkt

3. **Quellen-Liste**
   - Vollständige Auflistung aller [1], [2], [3]...
   - Format: [Nr] Titel - Paragraphen/Abschnitt

4. **Follow-up-Vorschläge** (4-5 Stück)
   - Verwaltungsrechtlich relevant
   - Nächste Verfahrensschritte
   - Konkrete Paragraphen-Bezüge

# QUALITÄTS-STANDARDS

- **Verwaltungsrechtliche Belastbarkeit:** Alle Aussagen müssen auf Rechtsquellen basieren
- **Vollständigkeit:** Alle in der Frage genannten Aspekte abdecken
- **Präzision:** Konkrete Paragraphen, Fristen, Beträge (wenn verfügbar)
- **Praxisrelevanz:** Handlungsempfehlungen für Bauherren/Architekten

# BEISPIEL

Frage: "Welche Fristen gelten bei Baugenehmigungen in BW?"

Antwort:
"Bei Baugenehmigungen in Baden-Württemberg gelten gesetzliche Bearbeitungsfristen (§ 59 LBO BW) [1].

## Bearbeitungsfristen

Die Baugenehmigungsbehörde muss innerhalb von **3 Monaten** entscheiden (§ 59 Abs. 2 LBO BW) [1].
Bei vereinfachten Verfahren verkürzt sich die Frist auf **1 Monat** (§ 59 Abs. 3 LBO BW) [1][2].

Bei Verzögerungen kann eine **Fristverlängerung** beantragt werden (§ 59 Abs. 4 LBO BW) [3].

## Quellen

[1] Landesbauordnung Baden-Württemberg (LBO BW), § 59 - Entscheidungsfrist
[2] VwV LBO BW zu § 59 - Beschleunigte Verfahren
[3] § 59 Abs. 4 LBO BW - Fristverlängerung

## Nächste Schritte

- Wie beantrage ich eine Fristverlängerung nach § 59 Abs. 4 LBO BW?
- Was passiert bei Fristüberschreitung (fiktive Genehmigung)?
- Welche Unterlagen beschleunigen das Verfahren nach § 58 LBO BW?
"
"""

# Funktion zum Formatieren der Quellen für das Prompt
def format_sources_for_prompt(retrieved_documents: List[Dict]) -> str:
    """
    Formatiert die abgerufenen Dokumente für das LLM-Prompt
    mit eindeutigen [1], [2], [3] Nummern
    """
    formatted = []
    for idx, doc in enumerate(retrieved_documents, 1):
        title = doc.get('metadata', {}).get('title', 'Unbekannte Quelle')
        content = doc.get('content', '')[:500]  # Erste 500 Zeichen

        formatted.append(f"""
[{idx}] {title}
---
{content}
[...]
""")

    return "\n".join(formatted)

# Haupt-Prompt-Builder
def build_verwaltungsrecht_prompt(
    question: str,
    retrieved_documents: List[Dict],
    question_aspects: List[str] = None
) -> str:
    """
    Baut das vollständige Prompt für verwaltungsrechtliche Anfragen

    Args:
        question: Benutzerfrage
        retrieved_documents: RAG-abgerufene Dokumente
        question_aspects: Optional - erkannte Aspekte der Frage

    Returns:
        Vollständiges Prompt mit System-Instruktionen
    """

    # Aspekte aus Frage extrahieren (falls nicht übergeben)
    if question_aspects is None:
        question_aspects = extract_question_aspects(question)

    aspects_instruction = ""
    if question_aspects:
        aspects_instruction = f"""
# ASPEKTE DER FRAGE (ALLE abdecken!)

Die Frage enthält {len(question_aspects)} Aspekte:
{chr(10).join([f"{i+1}. {aspect}" for i, aspect in enumerate(question_aspects)])}

Strukturiere deine Antwort nach diesen Aspekten (jeweils ## Überschrift).
"""

    prompt = f"""
{VERWALTUNGSRECHT_SYSTEM_PROMPT}

{aspects_instruction}

# FRAGE

{question}

# VERFÜGBARE QUELLEN ({len(retrieved_documents)} Dokumente)

{format_sources_for_prompt(retrieved_documents)}

# DEINE ANTWORT (mit IEEE-Zitationen [1][2][3])

"""

    return prompt

def extract_question_aspects(question: str) -> List[str]:
    """
    Extrahiert Aspekte aus Multi-Teil-Fragen

    Beispiel:
    "Welche Voraussetzungen, Fristen und Kosten..."
    → ["Voraussetzungen", "Fristen", "Kosten"]
    """
    aspects = []

    # Pattern für Listen: "X, Y und Z"
    import re
    list_pattern = r'([^,?]+)(?:,\s*([^,?]+))*(?:\s+und\s+([^,?]+))?'

    # Häufige Schlüsselwörter
    keywords = [
        "voraussetzungen", "fristen", "kosten", "ausnahmen",
        "verfahren", "unterlagen", "anforderungen", "pflichten",
        "rechte", "unterschiede", "ablauf", "rechtsmittel"
    ]

    question_lower = question.lower()

    for keyword in keywords:
        if keyword in question_lower:
            aspects.append(keyword.capitalize())

    # Mindestens 1 Aspekt zurückgeben
    if not aspects:
        aspects = ["Hauptaspekt"]

    return aspects
```

---

## 📋 Implementierungs-Checkliste

### Phase 1: Prompt-Optimierung (Priorität 🔴 KRITISCH)

- [ ] **1.1** `veritas_enhanced_prompts.py` mit `VERWALTUNGSRECHT_SYSTEM_PROMPT` erstellen
- [ ] **1.2** `format_sources_for_prompt()` implementieren
- [ ] **1.3** `extract_question_aspects()` implementieren
- [ ] **1.4** `build_verwaltungsrecht_prompt()` als Haupt-Funktion

### Phase 2: Backend-Integration (Priorität 🔴 KRITISCH)

- [ ] **2.1** `/ask` Endpoint: Verwaltungsrecht-Prompt aktivieren
  ```python
  # In: backend/api/veritas_api_endpoint.py
  from backend.agents.veritas_enhanced_prompts import build_verwaltungsrecht_prompt

  @app.post("/ask")
  async def ask_question(request: RAGRequest):
      # RAG-Retrieval
      retrieved_docs = await retrieval_system.get_documents(request.question)

      # NEUER Prompt-Builder
      prompt = build_verwaltungsrecht_prompt(
          question=request.question,
          retrieved_documents=retrieved_docs
      )

      # LLM-Generierung
      response = await llm_client.generate(prompt, model=request.model)
      ...
  ```

- [ ] **2.2** Follow-up-Generierung aktivieren
  ```python
  # Post-Processing nach LLM-Response
  suggestions = await generate_follow_ups(
      question=request.question,
      answer=response["answer"],
      model=request.model
  )
  ```

- [ ] **2.3** Citation-Parsing verbessern
  ```python
  # Extrahiere [1], [2], [3] aus Antwort
  citations = extract_ieee_citations(response["answer"])

  # Validiere: Alle Zitationen haben Quellen
  if len(citations) < 3:
      logger.warning(f"Nur {len(citations)} Zitationen gefunden, erwartet ≥3")
  ```

### Phase 3: Testing & Validation (Priorität 🟡 HOCH)

- [ ] **3.1** Test-Script erweitern: Zitations-Extraktion
  ```python
  def extract_ieee_citations(answer: str) -> List[str]:
      """Findet alle [1], [2], [3] in Antwort"""
      import re
      return re.findall(r'\[(\d+)\]', answer)
  ```

- [ ] **3.2** Test-Script erweitern: Paragraphen-Erkennung
  ```python
  def extract_legal_references(answer: str) -> List[str]:
      """Findet § 58 LBO BW, Art. 14 GG, etc."""
      import re
      return re.findall(r'§\s*\d+[a-z]?\s+(?:Abs\.\s*\d+\s+)?[A-Z]{2,}', answer)
  ```

- [ ] **3.3** Vollständiger Re-Test mit neuem Prompt
  ```bash
  python tests/test_rag_quality_v3_19_0.py
  ```

- [ ] **3.4** Validierung: ≥3 Zitationen pro Antwort
- [ ] **3.5** Validierung: ≥3 Follow-ups pro Antwort
- [ ] **3.6** Validierung: Aspekt-Abdeckung >60%

### Phase 4: Fine-Tuning (Priorität 🟢 MITTEL)

- [ ] **4.1** A/B-Testing: Alter vs. neuer Prompt
- [ ] **4.2** Model-Comparison: Welches LLM befolgt Instruktionen am besten?
  - llama3.1:latest
  - llama3.1:8b
  - mistral:latest
- [ ] **4.3** Token-Optimierung: max_tokens erhöhen (800 → 1200?)
- [ ] **4.4** Temperature-Optimierung: Verwaltungsrecht = 0.3 (präziser)

---

## 🎯 Erwartete Verbesserungen nach Implementierung

### Vorher (aktuell)
```json
{
  "answer": "Die Baugenehmigung erfordert verschiedene Unterlagen...",
  "citation_count": 0,
  "suggestions_count": 0,
  "aspect_coverage": 0.32,
  "rating": "GOOD"
}
```

### Nachher (Ziel)
```json
{
  "answer": "Die Baugenehmigung erfordert verschiedene Unterlagen (§ 58 LBO BW) [1][2]. Nach § 58 Abs. 1 LBO BW sind einzureichen [1]:

  ## Rechtliche Voraussetzungen
  - Bauvorlagen gemäß § 7 LBOVVO [3]
  - Nachweis der Standsicherheit [2]

  ## Fristen
  Bearbeitungsdauer: 3 Monate (§ 59 Abs. 2 LBO BW) [4]

  ## Kosten
  Gebühren gemäß GebO BW: 0,5% der Bausumme [5]

  [1] Landesbauordnung BW, § 58
  [2] § 55 LBO BW - Technische Nachweise
  [3] LBOVVO § 7 - Bauvorlagen
  [4] § 59 LBO BW - Entscheidungsfrist
  [5] Gebührenordnung BW - Baugenehmigung",

  "citation_count": 5,
  "suggestions_count": 4,
  "suggestions": [
    "Welche Unterlagen benötige ich für § 7 LBOVVO?",
    "Wie berechnen sich die Gebühren nach GebO BW?",
    "Was passiert bei Fristüberschreitung nach § 59 LBO BW?",
    "Welche Ausnahmen gibt es nach § 50 LBO BW?"
  ],
  "aspect_coverage": 0.80,
  "rating": "EXCELLENT"
}
```

### Metriken-Verbesserung (Ziel)

| Metrik | Vorher | Nachher (Ziel) | Verbesserung |
|--------|---------|----------------|--------------|
| IEEE-Zitationen | 0.0 | ≥3.5 | +∞% 🎯 |
| Follow-up-Vorschläge | 0.0 | ≥4.0 | +∞% 🎯 |
| Aspekt-Abdeckung | 32% | ≥65% | +103% 🎯 |
| Paragraphen-Referenzen | ~5% | ≥80% | +1500% 🎯 |
| Rating "EXCELLENT" | 33% | ≥60% | +82% 🎯 |

---

## 🚀 Next Steps

### Sofort (heute)
1. ✅ Analysebericht erstellt
2. ⏳ `veritas_enhanced_prompts.py` implementieren
3. ⏳ Backend-Integration testen

### Diese Woche
1. Vollständiger Re-Test mit neuem Prompt
2. Validierung der Verbesserungen
3. Dokumentation der Ergebnisse

### Nächste Woche
1. A/B-Testing mit Nutzern
2. Fine-Tuning der Prompts
3. Produktiv-Deployment

---

## 📚 Anhang: Verwaltungsrechtliche Anforderungen

### Rechtsquellen-Hierarchie (für Prompts relevant)

1. **Grundgesetz (GG)** - höchste Priorität
2. **Bundesgesetze** (z.B. BauGB)
3. **Landesgesetze** (z.B. LBO BW)
4. **Verordnungen** (z.B. LBOVVO)
5. **Verwaltungsvorschriften** (z.B. VwV LBO BW)
6. **Urteile** (z.B. BVerwG)

### Zitier-Standards im Verwaltungsrecht

```
§ 58 Abs. 1 Satz 2 LBO BW
│    │      │      └─ Gesetz
│    │      └─ Satz
│    └─ Absatz
└─ Paragraph

Art. 14 Abs. 1 GG
│     │   │     └─ Grundgesetz
│     │   └─ Absatz
│     └─ Nummer
└─ Artikel
```

### Typische verwaltungsrechtliche Formulierungen

| Formulierung | Rechtskraft | Verwendung |
|--------------|-------------|------------|
| "Nach § X..." | Hoch | Klare Rechtsgrundlage |
| "Gemäß § X..." | Hoch | Gesetzliche Verpflichtung |
| "In der Regel nach § X..." | Mittel | Üblicherweise |
| "Laut VwV zu § X..." | Mittel | Verwaltungspraxis |
| "Siehe auch § X..." | Niedrig | Weiterführende Info |

---

**Erstellt von:** GitHub Copilot
**Basis:** RAG Quality Test v3.19.0
**Testdaten:** `rag_test_results_1760096943.json`
**Datum:** 10. Oktober 2025, 13:50 Uhr
