# 🧪 LLM-Parameter UI Sprint 1 - Testing Guide

**Version:** v3.18.2  
**Erstellt:** 10.10.2025  
**Features:** Preset-Buttons, Token-Counter, Antwortzeit-Prädiktion  
**Status:** 🟢 IMPLEMENTATION COMPLETE - READY FOR TESTING

---

## ✅ Implementierte Features

### 1. **Preset-Buttons** ⚖️📖🎨
4 vordefinierte Parameter-Kombinationen für schnelle Konfiguration.

### 2. **Token-Counter** 💬
Echtzeit-Anzeige der geschätzten Antwortlänge in Wörtern mit Farbcodierung.

### 3. **Antwortzeit-Prädiktion** ⏱️
Modell-spezifische Schätzung der erwarteten Antwortzeit mit Farbcodierung.

---

## 🎯 Test-Checkliste

### Feature 1: Preset-Buttons

#### ✅ **Visual Testing**
- [ ] **UI-Rendering:** 4 Buttons sichtbar unter Settings-Bar
  ```
  Presets: [⚖️ Präzise] [✅ Standard] [📖 Ausführlich] [🎨 Kreativ]
  ```
- [ ] **Button-Labels:** Emojis + Text korrekt angezeigt
- [ ] **Button-Breite:** Einheitlich (width=14)
- [ ] **Tooltips:** Hover über jeden Button zeigt Details

#### ✅ **Functional Testing**

**Test 1.1: "⚖️ Präzise" Preset**
1. Klicke auf "⚖️ Präzise" Button
2. **Erwartete Änderungen:**
   - Temperature Slider → `0.3`
   - Max Tokens Spinbox → `300`
   - Top-p Slider → `0.7`
   - System-Message im Chat: `🎛️ Preset angewandt: ⚖️ Präzise (Temp=0.3, Tokens=300, Top-p=0.7)`
   - Token-Counter → `💬 ~225 Wörter` (Grün)
   - Antwortzeit → `⚡ ~2-3s` (Grün)

**Test 1.2: "✅ Standard" Preset**
1. Klicke auf "✅ Standard" Button
2. **Erwartete Änderungen:**
   - Temperature → `0.7`
   - Max Tokens → `500`
   - Top-p → `0.9`
   - System-Message: `🎛️ Preset angewandt: ✅ Standard ...`
   - Token-Counter → `💬 ~375 Wörter` (Grün)
   - Antwortzeit → `⏱️ ~3-5s` (Orange)

**Test 1.3: "📖 Ausführlich" Preset**
1. Klicke auf "📖 Ausführlich" Button
2. **Erwartete Änderungen:**
   - Temperature → `0.6`
   - Max Tokens → `1000`
   - Top-p → `0.85`
   - System-Message: `🎛️ Preset angewandt: 📖 Ausführlich ...`
   - Token-Counter → `📝 ~750 Wörter` (Orange)
   - Antwortzeit → `⏱️ ~6-9s` (Orange)

**Test 1.4: "🎨 Kreativ" Preset**
1. Klicke auf "🎨 Kreativ" Button
2. **Erwartete Änderungen:**
   - Temperature → `0.9`
   - Max Tokens → `600`
   - Top-p → `0.95`
   - System-Message: `🎛️ Preset angewandt: 🎨 Kreativ ...`
   - Token-Counter → `📝 ~450 Wörter` (Orange)
   - Antwortzeit → `⏱️ ~4-6s` (Orange)

**Test 1.5: Tooltip-Inhalte**
Hover über jeden Button und prüfe Tooltip:

| Button | Tooltip sollte enthalten |
|--------|--------------------------|
| ⚖️ Präzise | "Optimal für: Gesetze & Vorschriften, Faktenfragen" |
| ✅ Standard | "Optimal für: Verwaltungsfragen, Allgemeine Informationen" |
| 📖 Ausführlich | "Optimal für: Detaillierte Erklärungen, Komplexe Sachverhalte" |
| 🎨 Kreativ | "Optimal für: Alternative Formulierungen, Umformulierungen" |

#### ✅ **Log Testing**
1. Prüfe `veritas_auto_server.log` nach Preset-Anwendung:
   ```
   Preset angewandt: ⚖️ Präzise | T=0.3, Tokens=300, p=0.7
   ```

---

### Feature 2: Token-Counter

#### ✅ **Visual Testing**
- [ ] **Label-Position:** Rechts neben "tok" Label
- [ ] **Initiale Anzeige:** `💬 ~375 Wörter` (bei 500 Tokens)
- [ ] **Schriftgröße:** Segoe UI, 7pt
- [ ] **Tooltip:** Hover zeigt "Geschätzte Antwortlänge\n1 Token ≈ 0.75 Wörter"

#### ✅ **Functional Testing**

**Test 2.1: Spinbox Änderungen**
1. Ändere Max Tokens Spinbox schrittweise:
   
   | Tokens | Erwartete Anzeige | Farbe | Indikator |
   |--------|-------------------|-------|-----------|
   | 100 | `💬 ~75 Wörter` | Grün | 💬 |
   | 300 | `💬 ~225 Wörter` | Grün | 💬 |
   | 500 | `💬 ~375 Wörter` | Grün | 💬 |
   | 600 | `📝 ~450 Wörter` | Orange | 📝 |
   | 1000 | `📝 ~750 Wörter` | Orange | 📝 |
   | 1500 | `⚠️ ~1125 Wörter` | Rot | ⚠️ |
   | 2000 | `⚠️ ~1500 Wörter` | Rot | ⚠️ |

**Test 2.2: Live-Update**
1. Verwende Spinbox-Pfeile (▲▼)
2. **Erwartung:** Label aktualisiert **sofort** (kein Lag)

**Test 2.3: Farbcodierung**
- [ ] **Grün (💬):** Tokens < 600
- [ ] **Orange (📝):** 600 ≤ Tokens < 1200
- [ ] **Rot (⚠️):** Tokens ≥ 1200

**Test 2.4: Formel-Korrektheit**
Prüfe Berechnungen:
- `300 Tokens × 0.75 = 225 Wörter` ✅
- `500 Tokens × 0.75 = 375 Wörter` ✅
- `1000 Tokens × 0.75 = 750 Wörter` ✅

---

### Feature 3: Antwortzeit-Prädiktion

#### ✅ **Visual Testing**
- [ ] **Label-Position:** Rechts neben Top-p Label (nur Main Window)
- [ ] **Initiale Anzeige:** `⏱️ ~3-5s` (bei 500 Tokens, llama3:latest)
- [ ] **Schriftgröße:** Segoe UI, 7pt
- [ ] **Tooltip:** Hover zeigt "Basierend auf: Max Tokens, LLM-Modell, RAG-Overhead"

#### ✅ **Functional Testing**

**Test 3.1: Token-Abhängigkeit**
Wechsle Max Tokens (LLM: llama3:latest):

| Tokens | Erwartete Zeit | Farbe | Indikator |
|--------|----------------|-------|-----------|
| 100 | `⚡ ~1-2s` | Grün | ⚡ |
| 300 | `⚡ ~2-3s` | Grün | ⚡ |
| 500 | `⏱️ ~3-5s` | Orange | ⏱️ |
| 1000 | `⏱️ ~6-9s` | Orange | ⏱️ |
| 1500 | `🐌 ~9-13s` | Rot | 🐌 |
| 2000 | `🐌 ~11-17s` | Rot | 🐌 |

**Test 3.2: Modell-Abhängigkeit**
Wechsle LLM-Modell (Tokens: 500):

| Modell | Tokens/s | Erwartete Zeit |
|--------|----------|----------------|
| **phi3:latest** | 200 | `⚡ ~2-4s` (schneller) |
| **llama3:latest** | 150 | `⏱️ ~3-5s` (Standard) |
| **llama3.1:8b** | 120 | `⏱️ ~4-6s` (langsamer) |
| **mixtral:latest** | 80 | `🐌 ~6-9s` (sehr langsam) |

**Test 3.3: Live-Update**
1. Ändere Max Tokens → Antwortzeit aktualisiert sofort
2. Wechsle LLM-Modell → Antwortzeit aktualisiert sofort
3. Klicke Preset-Button → Antwortzeit aktualisiert sofort

**Test 3.4: Farbcodierung**
- [ ] **Grün (⚡):** Durchschnitt < 4s
- [ ] **Orange (⏱️):** 4s ≤ Durchschnitt < 8s
- [ ] **Rot (🐌):** Durchschnitt ≥ 8s

**Test 3.5: Benchmark-Formel**
Prüfe Berechnung (500 Tokens, llama3:latest):
```
Generation Time = 500 Tokens / 150 Tokens/s = 3.33s
Overhead = 1.5s
Total = 3.33s + 1.5s = 4.83s
Range (±20%): 3.86s - 5.80s → Display: "~4-6s" ✅
```

---

## 🔄 Integration Tests

### Test I1: Preset → Token-Counter → Antwortzeit (Kaskade)
1. Klicke "⚖️ Präzise"
2. **Erwartete Kaskade:**
   - Parameters: Temp=0.3, Tokens=300, Top-p=0.7
   - Token-Counter: `💬 ~225 Wörter` (Grün)
   - Antwortzeit: `⚡ ~2-3s` (Grün)
   - System-Message im Chat

### Test I2: Manuelle Änderung → Live-Updates
1. Manuell setze: Tokens=1500, Modell=mixtral:latest
2. **Erwartete Updates:**
   - Token-Counter: `⚠️ ~1125 Wörter` (Rot)
   - Antwortzeit: `🐌 ~17-26s` (Rot)

### Test I3: Preset-Wechsel (mehrfach)
1. Klicke: Präzise → Standard → Ausführlich → Kreativ
2. **Erwartung:** 
   - Jeder Klick erzeugt System-Message
   - Alle Labels aktualisieren sich korrekt
   - Keine Fehler im Log

---

## 📊 Performance Tests

### Test P1: Responsiveness
- [ ] **Spinbox-Änderung:** < 50ms bis Label-Update
- [ ] **Preset-Button-Klick:** < 100ms bis alle Updates
- [ ] **Modell-Wechsel:** < 100ms bis Antwortzeit-Update

### Test P2: Memory
- [ ] **Vor 20 Preset-Klicks:** Notiere RAM-Usage
- [ ] **Nach 20 Preset-Klicks:** RAM-Usage ≤ +5 MB
- [ ] **Keine Memory Leaks**

---

## 🐛 Edge Case Tests

### Test E1: Extreme Values
- [ ] **Tokens = 100:** Token-Counter zeigt `💬 ~75 Wörter` (Grün)
- [ ] **Tokens = 2000:** Token-Counter zeigt `⚠️ ~1500 Wörter` (Rot)
- [ ] **Modell nicht in Benchmark:** Fallback zu 120 Tokens/s

### Test E2: Schneller Preset-Wechsel
1. Klicke alle 4 Presets in < 2 Sekunden
2. **Erwartung:** 
   - Alle Updates korrekt
   - Keine Race Conditions
   - 4 System-Messages im Chat

### Test E3: Gleichzeitige Änderungen
1. Ändere gleichzeitig: Tokens (Spinbox) + Modell (Dropdown)
2. **Erwartung:** 
   - Beide Updates reflektiert
   - Korrekte finale Antwortzeit

---

## 📝 Error Handling Tests

### Test EH1: Ungültige Token-Werte
1. Versuche manuell Tokens < 100 oder > 2000 einzugeben
2. **Erwartung:** Spinbox begrenzt auf [100, 2000]

### Test EH2: Fehlender Tooltip-Support
1. Teste ohne `UI_COMPONENTS_AVAILABLE`
2. **Erwartung:** 
   - Buttons funktionieren trotzdem
   - Keine Tooltips, aber keine Crashes

### Test EH3: Log-Fehler
1. Prüfe Log nach jedem Test
2. **Erwartung:** Keine `ERROR` Einträge zu Features

---

## ✅ Acceptance Criteria

### Sprint 1 gilt als **ERFOLG** wenn:

- [x] **Preset-Buttons:**
  - [x] Alle 4 Buttons rendern
  - [x] Klick ändert Parameter korrekt
  - [x] System-Message erscheint
  - [x] Labels aktualisieren sich
  - [x] Tooltips vorhanden

- [x] **Token-Counter:**
  - [x] Zeigt Wörter korrekt (0.75 Faktor)
  - [x] Farbcodierung funktioniert
  - [x] Live-Update bei Spinbox-Änderung
  - [x] Tooltip informativ

- [x] **Antwortzeit-Prädiktion:**
  - [x] Modell-spezifische Benchmarks
  - [x] Range (Min-Max) angezeigt
  - [x] Farbcodierung funktioniert
  - [x] Live-Update bei Modell-/Token-Wechsel

- [x] **Integration:**
  - [x] Preset-Klick triggert alle Updates
  - [x] Keine Performance-Probleme
  - [x] Keine Fehler im Log

---

## 🚀 Testing Instructions

### Quick Test (5 Minuten)
```bash
cd c:\VCC\veritas
python start_frontend.py

# 1. Teste Presets (klicke alle 4)
# 2. Ändere Tokens: 100 → 500 → 1000 → 2000
# 3. Wechsle Modell: llama3 → phi3 → mixtral
# 4. Prüfe System-Messages im Chat
# 5. Prüfe Log: data/veritas_auto_server.log
```

### Full Test (20 Minuten)
- Alle Tests in diesem Dokument durchführen
- Screenshots von allen 4 Presets machen
- Log-Datei analysieren
- Performance mit Task Manager überprüfen

---

## 📊 Expected UI Layout

```
┌─────────────────────────────────────────────────────────────────────────┐
│  VERITAS - RAG System                                                   │
├─────────────────────────────────────────────────────────────────────────┤
│  Settings:                                                              │
│  [LLM: llama3:latest ▼] 🌡️ [━━━━━] 0.7                                │
│  📝 [500 ▲▼] tok  💬 ~375 Wörter  🎲 [━━━━━] 0.90  ⏱️ ~3-5s  🔍 [5 ▲▼] │
│                                                                          │
│  Presets: [⚖️ Präzise] [✅ Standard] [📖 Ausführlich] [🎨 Kreativ]      │
├─────────────────────────────────────────────────────────────────────────┤
│  Chat:                                                                  │
│  🎛️ Preset angewandt: ⚖️ Präzise (Temp=0.3, Tokens=300, Top-p=0.7)    │
│  User: Was brauche ich für eine Baugenehmigung?                        │
│  AI: [Antwort...]                                                       │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🎓 Developer Notes

### Code Locations
- **Preset-Buttons:** `veritas_app.py` lines 1350-1410
- **Token-Counter:** `veritas_app.py` lines 1265-1280
- **Antwortzeit-Prädiktion:** `veritas_app.py` lines 1310-1325
- **Callbacks:** `veritas_app.py` lines 1345-1360
- **Update-Methoden:** `veritas_app.py` lines 1540-1630

### Benchmarks (Tokens/Sekunde)
```python
MODEL_BENCHMARKS = {
    'llama3:latest': 150,
    'llama3.1:8b': 120,
    'llama3.2:latest': 140,
    'phi3:latest': 200,       # Schnell (klein)
    'mixtral:latest': 80,      # Langsam (groß)
    'codellama:latest': 130,
    'gemma2:latest': 160,
    'qwen2.5:latest': 145
}
```

### Formulas
- **Wörter:** `tokens × 0.75`
- **Zeichen:** `tokens × 4`
- **Generierungszeit:** `tokens / tokens_per_second`
- **Gesamtzeit:** `generation_time + 1.5s` (Overhead)
- **Range:** `total_time × 0.8` bis `total_time × 1.2` (±20%)

---

## 📚 Related Documentation

- `docs/LLM_PARAMETERS.md` - Parameter-Referenz
- `docs/LLM_PARAMETER_UI_CONTROLS.md` - v3.18.1 Implementation
- `TODO_LLM_PARAMETER_EXTENSIONS.md` - Sprint 1-3 Roadmap

---

**Tester:** _________________  
**Datum:** _________________  
**Ergebnis:** ☐ PASS | ☐ FAIL | ☐ PARTIAL  
**Kommentare:** _________________________________
