# 🎛️ LLM-Parameter Referenz

**VERITAS RAG System - LLM Konfiguration**
**Version:** 1.0
**Datum:** 10.10.2025

---

## 📋 Inhaltsverzeichnis

1. [Übersicht](#übersicht)
2. [Temperature](#temperature)
3. [Max Tokens](#max-tokens)
4. [Top-p (Nucleus Sampling)](#top-p-nucleus-sampling)
5. [Kombinationen & Best Practices](#kombinationen--best-practices)
6. [Troubleshooting](#troubleshooting)

---

## 🎯 Übersicht

Das VERITAS RAG-System nutzt Ollama LLMs (Large Language Models) zur Generierung von Antworten. Die Qualität und Charakteristik der Antworten kann über **3 Hauptparameter** gesteuert werden:

| Parameter | Wertebereich | Standard | Funktion |
|-----------|--------------|----------|----------|
| **🌡️ Temperature** | 0.0 - 1.0 | 0.7 | Kreativität vs. Präzision |
| **📝 Max Tokens** | 100 - 2000 | 500 | Maximale Antwortlänge |
| **🎲 Top-p** | 0.0 - 1.0 | 0.9 | Vielfalt der Wortwahl |

---

## 🌡️ Temperature

### Was ist Temperature?

**Temperature** steuert die **Zufälligkeit** (Randomness) bei der Token-Auswahl im LLM.

```
Niedrige Temperature → Deterministische, präzise Antworten
Hohe Temperature → Kreative, variable Antworten
```

### Wertebereich

| Wert | Charakteristik | Anwendungsfall |
|------|----------------|----------------|
| **0.0 - 0.3** | **Deterministisch** | Fakten, Gesetze, präzise Definitionen |
| **0.4 - 0.7** | **Ausgewogen** | Standard für RAG-Systeme, Verwaltungsfragen |
| **0.8 - 1.0** | **Kreativ** | Brainstorming, alternative Formulierungen |

### Technische Details

Temperature wird beim Softmax-Sampling angewandt:

```python
P(token_i) = exp(logit_i / T) / Σ exp(logit_j / T)
```

- **T = 0.0:** Argmax (immer das wahrscheinlichste Token)
- **T = 1.0:** Unveränderte Wahrscheinlichkeitsverteilung
- **T > 1.0:** Flachere Verteilung (mehr Varianz)

### Beispiele

#### Temperature = 0.2 (Präzise)

**Query:** "Was ist eine Baugenehmigung?"

**Antwort:**
```
Eine Baugenehmigung ist ein behördlicher Verwaltungsakt nach § 29 BauGB,
der die Zulässigkeit eines Bauvorhabens bestätigt. Sie wird vom zuständigen
Bauordnungsamt erteilt und ist rechtliche Voraussetzung für den Baubeginn.
```

**Charakteristik:** Fachlich korrekt, faktisch, wenig Variation bei Wiederholung

#### Temperature = 0.7 (Ausgewogen)

**Query:** "Was ist eine Baugenehmigung?"

**Antwort:**
```
Eine Baugenehmigung ist die offizielle Erlaubnis der Bauaufsichtsbehörde
für Ihr Bauvorhaben. Ohne diese Genehmigung dürfen Sie nicht mit dem Bau
beginnen. Der Antrag wird beim zuständigen Bauordnungsamt gestellt und
prüft die Einhaltung der Bauvorschriften.
```

**Charakteristik:** Natürlich formuliert, hilfreich, leicht variierend

#### Temperature = 1.0 (Kreativ)

**Query:** "Was ist eine Baugenehmigung?"

**Antwort:**
```
Stellen Sie sich die Baugenehmigung als Ihren "Baupass" vor - eine Art
behördliches Okay für Ihr Bauprojekt. Die Behörde prüft dabei gründlich,
ob Ihre Pläne den rechtlichen Rahmenbedingungen entsprechen. Erst mit
diesem grünen Licht können Sie loslegen.
```

**Charakteristik:** Metaphern, kreative Formulierungen, stark variierend

### 💡 Empfehlung für VERITAS

**Standard: 0.7** - Ausgewogen für Verwaltungsfragen

- ✅ Natürliche Sprache
- ✅ Faktisch korrekt
- ✅ Benutzerfreundlich
- ⚠️ Leichte Variation bei Wiederholung

---

## 📝 Max Tokens

### Was sind Tokens?

**Tokens** sind die Grundeinheiten, in die Text für LLMs zerlegt wird.

```
1 Token ≈ 4 Zeichen (Deutsch)
1 Token ≈ 0.75 Wörter (Deutsch)

Beispiel: "Baugenehmigung" → 2-3 Tokens
```

### Wertebereich

| Wert | Zeichen (ca.) | Anwendungsfall |
|------|---------------|----------------|
| **100-300** | 400-1200 | Kurze, prägnante Antworten |
| **400-800** | 1600-3200 | Standard für RAG (typische Fragen) |
| **800-2000** | 3200-8000 | Ausführliche Analysen, komplexe Themen |

### Technische Details

`max_tokens` = `num_predict` in Ollama API

```python
DirectOllamaLLM(
    model="llama3:latest",
    num_predict=500  # max_tokens
)
```

**Wichtig:**
- Mehr Tokens = längere Antwortzeit
- Mehr Tokens = höhere Rechenkosten
- Max = 2048 für llama3:latest (Context Window)

### Beispiele

#### max_tokens = 150 (Kurz)

**Query:** "Was brauche ich für eine Baugenehmigung?"

**Antwort:**
```
Für eine Baugenehmigung benötigen Sie:
• Bauantrag (amtliches Formular)
• Lageplan
• Bauvorlagen (Grundrisse, Ansichten)
• Statische Berechnungen
• Baubeschreibung

Antrag beim zuständigen Bauordnungsamt einreichen.
```

**Länge:** ~150 Tokens (~600 Zeichen)

#### max_tokens = 500 (Standard)

**Query:** "Was brauche ich für eine Baugenehmigung?"

**Antwort:**
```
Für eine Baugenehmigung in Brandenburg benötigen Sie folgende Unterlagen:

• Bauantrag (amtliches Formular)
• Lageplan im Maßstab 1:500 mit Grundstücksgrenzen
• Bauvorlagen (Grundrisse, Schnitte, Ansichten)
• Statische Berechnungen (von Tragwerksplaner)
• Baubeschreibung mit Materialangaben

Der Bauantrag wird beim zuständigen Bauordnungsamt in 3-facher
Ausfertigung eingereicht. Die Bearbeitungsdauer beträgt in der
Regel 2-3 Monate.

💡 Tipp: Bei Unsicherheiten können Sie vorab eine Bauvoranfrage stellen.

📋 Nächste Schritte:
• Termin beim Bauordnungsamt vereinbaren
• Vollständige Unterlagen zusammenstellen
• Bei Fragen: Bauvoranfrage stellen

Quelle: Merkblatt Baugenehmigung Brandenburg, BauGB §§ 29-38
```

**Länge:** ~500 Tokens (~2000 Zeichen)

#### max_tokens = 1500 (Ausführlich)

**Query:** "Was brauche ich für eine Baugenehmigung?"

**Antwort:**
```
[Sehr ausführliche Antwort mit detaillierten Erklärungen zu jedem Dokument,
rechtlichen Hintergründen, Verfahrensablauf, Fristen, Kosten, Ausnahmen,
Bauvoranfrage-Prozess, zuständigen Behörden, Rechtsmitteln, etc.]
```

**Länge:** ~1500 Tokens (~6000 Zeichen)

### 💡 Empfehlung für VERITAS

**Standard: 500** - Ausgewogen für typische Fragen

- ✅ Vollständige Antworten
- ✅ Strukturiert mit Listen
- ✅ Quellen + Nächste Schritte
- ⚠️ Moderate Antwortzeit (~2-4s)

**Erhöhen auf 800-1000 für:**
- Komplexe rechtliche Analysen
- Mehrere Sub-Fragen
- Detaillierte Schritt-für-Schritt-Anleitungen

---

## 🎲 Top-p (Nucleus Sampling)

### Was ist Top-p?

**Top-p** (auch **Nucleus Sampling**) steuert die **Vielfalt der Token-Auswahl** durch Begrenzung des Wahrscheinlichkeits-Pools.

```
Niedrige Top-p → Konservativ, fokussiert auf wahrscheinlichste Tokens
Hohe Top-p → Vielfältig, bezieht auch seltenere Tokens ein
```

### Wertebereich

| Wert | Charakteristik | Anwendungsfall |
|------|----------------|----------------|
| **0.5 - 0.7** | **Konservativ** | Fachterminologie, Gesetze, technische Texte |
| **0.8 - 0.9** | **Ausgewogen** | Standard für natürliche Sprache |
| **0.95 - 1.0** | **Vielfältig** | Kreatives Schreiben, Umformulierungen |

### Technische Details

Top-p (Nucleus Sampling) wählt die **kleinste Menge von Tokens**, deren kumulierte Wahrscheinlichkeit ≥ p ist:

```python
# Sortiere Tokens nach Wahrscheinlichkeit
sorted_tokens = sort(tokens, by=probability, descending=True)

# Wähle Top-p Subset
cumulative_prob = 0.0
nucleus = []
for token in sorted_tokens:
    nucleus.append(token)
    cumulative_prob += probability(token)
    if cumulative_prob >= p:
        break

# Sample aus Nucleus
selected_token = random.choice(nucleus, weighted_by=probability)
```

**Beispiel (Top-p = 0.9):**

```
Token-Verteilung:
- "benötigen": 0.45
- "brauchen":  0.30
- "erfordern": 0.15  → Kumulativ: 0.90 (STOP)
- "verlangen": 0.05  ← Nicht im Nucleus
- "bedürfen":  0.03  ← Nicht im Nucleus
- "bedingen":  0.02  ← Nicht im Nucleus
```

### Interaktion mit Temperature

**Top-p und Temperature arbeiten zusammen:**

1. **Temperature** formt die Wahrscheinlichkeitsverteilung
2. **Top-p** begrenzt den Pool der auswählbaren Tokens

```
Temperature = 0.3, Top-p = 0.9
→ Sehr fokussiert (Temperature dominiert)

Temperature = 0.7, Top-p = 0.9
→ Ausgewogen (beide wirken)

Temperature = 1.0, Top-p = 0.5
→ Kreativ aber fokussiert (Top-p begrenzt)
```

### Beispiele

#### Top-p = 0.5 (Konservativ)

**Query:** "Wie lange dauert eine Baugenehmigung?"

**Antwort:**
```
Die Bearbeitungsdauer einer Baugenehmigung beträgt in der Regel 2-3 Monate.
Im vereinfachten Verfahren kann die Genehmigung in 4-6 Wochen vorliegen.
Die genaue Dauer hängt von der Komplexität des Bauvorhabens ab.
```

**Wortwahl:** Standardformulierungen, Fachbegriffe

#### Top-p = 0.9 (Ausgewogen)

**Query:** "Wie lange dauert eine Baugenehmigung?"

**Antwort:**
```
Die Bearbeitungszeit für Ihre Baugenehmigung liegt typischerweise bei
2-3 Monaten. Bei einem vereinfachten Genehmigungsverfahren geht es
schneller - hier können Sie mit 4-6 Wochen rechnen. Die tatsächliche
Dauer variiert je nach Komplexität Ihres Bauvorhabens und Auslastung
der Behörde.
```

**Wortwahl:** Natürliche Variation, persönliche Ansprache

#### Top-p = 0.98 (Vielfältig)

**Query:** "Wie lange dauert eine Baugenehmigung?"

**Antwort:**
```
Planen Sie für Ihre Baugenehmigung üblicherweise einen Zeitraum von
2 bis 3 Monaten ein. Sollte Ihr Projekt für das vereinfachte Verfahren
qualifizieren, verkürzt sich die Wartezeit auf etwa 4-6 Wochen. Beachten
Sie, dass die konkrete Bearbeitungsdauer von verschiedenen Faktoren
beeinflusst wird: Komplexität Ihres Vorhabens, aktuelle Behörden-
auslastung und Vollständigkeit Ihrer Unterlagen.
```

**Wortwahl:** Vielfältige Formulierungen, umschreibende Wendungen

### 💡 Empfehlung für VERITAS

**Standard: 0.9** - Ausgewogen für natürliche Sprache

- ✅ Natürliche Variationen
- ✅ Fachbegriffe + Umgangssprache
- ✅ Lesbare, hilfreiche Antworten
- ⚠️ Leichte Unvorhersehbarkeit (gewollt)

---

## 🎛️ Kombinationen & Best Practices

### Empfohlene Presets

#### 🎯 Preset 1: Präzise (Gesetze, Fakten)

```python
temperature = 0.3
max_tokens = 400
top_p = 0.7
```

**Anwendungsfall:**
- Gesetzestexte zitieren
- Technische Definitionen
- Numerische Daten (Fristen, Kosten)

**Charakteristik:**
- Sehr konsistent
- Faktisch korrekt
- Wenig Variation

---

#### ✅ Preset 2: Standard (Verwaltungsfragen)

```python
temperature = 0.7
max_tokens = 500
top_p = 0.9
```

**Anwendungsfall:**
- Typische Bürgerfragen
- Prozesserklärungen
- Allgemeine Beratung

**Charakteristik:**
- Natürliche Sprache
- Hilfreich & präzise
- Ausgewogen

---

#### 💡 Preset 3: Ausführlich (Komplexe Analysen)

```python
temperature = 0.6
max_tokens = 1000
top_p = 0.85
```

**Anwendungsfall:**
- Rechtliche Analysen
- Multi-Step Prozesse
- Detaillierte Anleitungen

**Charakteristik:**
- Umfassend
- Strukturiert
- Längere Antwortzeit

---

#### 🎨 Preset 4: Kreativ (Umformulierungen)

```python
temperature = 0.9
max_tokens = 600
top_p = 0.95
```

**Anwendungsfall:**
- Alternative Formulierungen
- Vereinfachte Erklärungen
- Metaphern, Beispiele

**Charakteristik:**
- Abwechslungsreich
- Kreative Sprache
- Höhere Varianz

---

### Parameter-Interaktion

```
┌─────────────────────────────────────┐
│  Temperature = Kreativität          │
│  Top-p = Vielfalt der Wortwahl      │
│  Max Tokens = Ausführlichkeit       │
└─────────────────────────────────────┘

Empfehlung: Passe alle 3 gemeinsam an!
```

**Beispiel-Matrix:**

| Use Case | Temp | Tokens | Top-p | Ergebnis |
|----------|------|--------|-------|----------|
| Gesetzestext | 0.2 | 300 | 0.7 | Präzise, kurz, korrekt |
| Standard-FAQ | 0.7 | 500 | 0.9 | Natürlich, hilfreich |
| Analyse | 0.6 | 1000 | 0.85 | Ausführlich, strukturiert |
| Brainstorming | 0.9 | 600 | 0.95 | Kreativ, vielfältig |

---

## 🔧 Troubleshooting

### Problem 1: Antworten zu generisch

**Symptome:**
```
"Antwort auf die Frage..."
"Basierend auf den bereitgestellten Informationen..."
```

**Lösung:**
- ✅ **Reduziere Temperature** (0.7 → 0.5)
- ✅ **Nutze Dual-Prompt-System** (siehe `docs/DUAL_PROMPT_SYSTEM.md`)
- ✅ **Upgrade auf llama3.1:8b** (bessere Instruction-Following)

---

### Problem 2: Antworten zu kurz

**Symptome:**
- Antwortet mit 2-3 Sätzen, obwohl mehr erwartet
- Bricht mitten im Satz ab

**Lösung:**
- ✅ **Erhöhe max_tokens** (500 → 800)
- ⚠️ **Prüfe Context Window** (llama3 = 8K Tokens)
- ✅ **Checke Prompt-Länge** (Query + RAG-Context verbrauchen Tokens)

---

### Problem 3: Antworten zu kreativ/unpräzise

**Symptome:**
- Erfindet Fakten ("Halluzinationen")
- Zu viele Metaphern
- Inkonsistent bei Wiederholung

**Lösung:**
- ✅ **Reduziere Temperature** (0.7 → 0.3)
- ✅ **Reduziere Top-p** (0.9 → 0.7)
- ✅ **Verbessere RAG-Context** (mehr relevante Dokumente)

---

### Problem 4: Langsame Antwortzeiten

**Symptome:**
- Antworten dauern >10 Sekunden
- UI blockiert

**Lösung:**
- ✅ **Reduziere max_tokens** (1000 → 500)
- ✅ **Nutze kleineres Modell** (llama3:latest → phi3:latest)
- ✅ **Aktiviere Query-Enrichment-Cache** (siehe `docs/DUAL_PROMPT_SYSTEM.md`)

---

## 📚 Weiterführende Ressourcen

- **Ollama Dokumentation:** https://github.com/ollama/ollama/blob/main/docs/api.md
- **llama3 Model Card:** https://ai.meta.com/llama/
- **Nucleus Sampling Paper:** https://arxiv.org/abs/1904.09751
- **VERITAS Dual-Prompt-System:** `docs/DUAL_PROMPT_SYSTEM.md`
- **Frontend Parameter-Flow:** `docs/LLM_PARAMETER_FLOW_VERIFICATION.md`

---

## 🎓 Quiz: Teste dein Wissen

**1. Welche Temperature für Gesetzestexte?**
- A) 0.2 ✅ (Präzise, deterministisch)
- B) 0.7
- C) 1.0

**2. Was bewirkt Top-p = 0.5?**
- A) Sehr kreative Antworten
- B) Konservative Wortwahl ✅ (Nur Top 50% der Tokens)
- C) Längere Antworten

**3. max_tokens = 2000 bedeutet:**
- A) Genau 2000 Wörter
- B) Maximal 2000 Token-Einheiten ✅ (~1500 Wörter)
- C) 2000 Zeichen

---

**Autor:** VERITAS System
**Version:** 1.0
**Letzte Aktualisierung:** 10.10.2025
**Lizenz:** MIT
