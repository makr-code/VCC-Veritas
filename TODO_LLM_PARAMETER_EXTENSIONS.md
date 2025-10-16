# 📋 TODO: LLM-Parameter UI Erweiterungen (Optional)

**Projekt:** VERITAS RAG System  
**Version:** v3.18.2 (geplant)  
**Erstellt:** 10.10.2025  
**Priorität:** NICE-TO-HAVE (alle Features bereits funktional)

---

## ✅ Abgeschlossen (v3.18.1)

- [x] Max Tokens Spinbox (100-2000)
- [x] Top-p Slider (0.0-1.0)
- [x] Erweiterte Tooltips mit Multi-line Support
- [x] Klickbare Hilfe-Links in Tooltips
- [x] `_open_help_docs()` Methode (plattformübergreifend)
- [x] Vollständige Dokumentation (LLM_PARAMETERS.md)
- [x] Parameter-Flow Frontend → Backend → Ollama ✅

---

## 🎯 Optional Features (Priorisiert)

### 🥇 HIGH PRIORITY

#### 1. Preset-Buttons für schnelle Konfiguration
**Geschätzter Aufwand:** 30-45 Minuten  
**Nutzen:** ⭐⭐⭐⭐⭐ (Sehr hoch - User-Convenience)

**Beschreibung:**
4 Preset-Buttons zum schnellen Umschalten zwischen typischen Konfigurationen.

**UI-Mockup:**
```
┌─────────────────────────────────────────────────────────────┐
│  Presets: [⚖️ Präzise] [✅ Standard] [📖 Ausführlich] [🎨 Kreativ] │
└─────────────────────────────────────────────────────────────┘
```

**Parameter-Sets:**

| Preset | Temp | Tokens | Top-p | Use Case |
|--------|------|--------|-------|----------|
| **⚖️ Präzise** | 0.3 | 300 | 0.7 | Gesetze, Fakten |
| **✅ Standard** | 0.7 | 500 | 0.9 | Verwaltungsfragen |
| **📖 Ausführlich** | 0.6 | 1000 | 0.85 | Analysen |
| **🎨 Kreativ** | 0.9 | 600 | 0.95 | Umformulierungen |

**Implementation:**

```python
# In veritas_app.py, _create_settings_controls()

def _create_preset_buttons(self, parent):
    """Erstellt Preset-Buttons"""
    preset_frame = ttk.Frame(parent)
    preset_frame.pack(fill=tk.X, padx=5, pady=3)
    
    ttk.Label(preset_frame, text="Presets:", font=('Segoe UI', 8)).pack(side=tk.LEFT, padx=(0, 5))
    
    presets = [
        ("⚖️ Präzise", 0.3, 300, 0.7, "Fakten, Gesetze"),
        ("✅ Standard", 0.7, 500, 0.9, "Verwaltungsfragen"),
        ("📖 Ausführlich", 0.6, 1000, 0.85, "Detaillierte Analysen"),
        ("🎨 Kreativ", 0.9, 600, 0.95, "Alternative Formulierungen")
    ]
    
    for label, temp, tokens, topp, tooltip_text in presets:
        btn = ttk.Button(
            preset_frame,
            text=label,
            command=lambda t=temp, tk=tokens, p=topp: self._apply_preset(t, tk, p),
            width=12
        )
        btn.pack(side=tk.LEFT, padx=2)
        
        if UI_COMPONENTS_AVAILABLE:
            Tooltip(btn, f"{label}\n\n{tooltip_text}\n\nTemp: {temp} | Tokens: {tokens} | Top-p: {p}")

def _apply_preset(self, temperature, max_tokens, top_p):
    """Wendet Preset an"""
    self.temperature_var.set(temperature)
    self.max_tokens_var.set(max_tokens)
    self.top_p_var.set(top_p)
    
    # Labels aktualisieren
    self._update_temperature_label(temperature)
    self._update_topp_label(top_p)
    
    # System-Message im Chat
    self.add_system_message(
        f"🎛️ Preset angewandt: Temp={temperature}, Tokens={max_tokens}, Top-p={top_p}"
    )
    
    logger.info(f"Preset angewandt: T={temperature}, Tokens={max_tokens}, p={top_p}")
```

**Datei:** `frontend/veritas_app.py`  
**Zeilen:** ~1310 (nach top_p Slider)

**Testing:**
- [ ] Buttons rendern korrekt
- [ ] Preset-Anwendung funktioniert
- [ ] Labels aktualisieren sich
- [ ] System-Message erscheint
- [ ] Tooltips zeigen Details

---

#### 2. Token-Counter & Antwortlängen-Schätzung
**Geschätzter Aufwand:** 45-60 Minuten  
**Nutzen:** ⭐⭐⭐⭐ (Hoch - Transparenz)

**Beschreibung:**
Zeigt geschätzte Antwortlänge und Token-Verbrauch in Echtzeit.

**UI-Mockup:**
```
┌─────────────────────────────────────────────────────────────┐
│  📝 Max Tokens: [500 ▲▼] tok                                │
│  💬 Geschätzte Antwortlänge: ~375 Wörter (~1500 Zeichen)    │
└─────────────────────────────────────────────────────────────┘
```

**Implementation:**

```python
# In veritas_app.py

def _create_token_counter_label(self, parent):
    """Erstellt Token-Counter Label"""
    self.token_info_label = ttk.Label(
        parent,
        text="💬 Geschätzte Antwortlänge: ~375 Wörter",
        font=('Segoe UI', 8),
        foreground='#666666'
    )
    self.token_info_label.pack(side=tk.LEFT, padx=(10, 0))

def _update_tokens_label(self, *args):
    """Aktualisiert Token-Counter bei Spinbox-Änderung"""
    try:
        tokens = self.max_tokens_var.get()
        
        # Token → Wörter (Deutsch: 1 Token ≈ 0.75 Wörter)
        estimated_words = int(tokens * 0.75)
        
        # Token → Zeichen (Deutsch: 1 Token ≈ 4 Zeichen)
        estimated_chars = int(tokens * 4)
        
        # Label aktualisieren
        if hasattr(self, 'token_info_label'):
            self.token_info_label.config(
                text=f"💬 Geschätzte Antwortlänge: ~{estimated_words} Wörter (~{estimated_chars} Zeichen)"
            )
    except Exception as e:
        logger.error(f"Fehler beim Aktualisieren des Token-Counters: {e}")
```

**Datei:** `frontend/veritas_app.py`  
**Zeilen:** ~1245 (nach max_tokens_spinbox)

**Erweitert:**
- [ ] Token → Wörter Konversion (0.75 Faktor)
- [ ] Token → Zeichen Konversion (4 Faktor)
- [ ] Live-Update bei Spinbox-Änderung
- [ ] Farbcodierung (Grün <500, Orange 500-1000, Rot >1000)

---

#### 3. Antwortzeit-Prädiktion
**Geschätzter Aufwand:** 30-45 Minuten  
**Nutzen:** ⭐⭐⭐ (Mittel - Erwartungsmanagement)

**Beschreibung:**
Schätzt Antwortzeit basierend auf max_tokens und Modell.

**UI-Mockup:**
```
┌─────────────────────────────────────────────────────────────┐
│  ⏱️ Geschätzte Antwortzeit: ~3-5 Sekunden                   │
└─────────────────────────────────────────────────────────────┘
```

**Implementation:**

```python
# In veritas_app.py

# Benchmark-Daten (gemessen auf lokalem System)
MODEL_BENCHMARKS = {
    'llama3:latest': 150,      # Tokens/Sekunde
    'llama3.1:8b': 120,        # Tokens/Sekunde
    'phi3:latest': 200,        # Tokens/Sekunde (schneller, kleiner)
    'mixtral:latest': 80,      # Tokens/Sekunde (langsamer, größer)
    'codellama:latest': 130    # Tokens/Sekunde
}

def _estimate_response_time(self):
    """Schätzt Antwortzeit"""
    try:
        max_tokens = self.max_tokens_var.get()
        model = self.llm_var.get()
        
        # Tokens/Sekunde für aktuelles Modell
        tokens_per_second = MODEL_BENCHMARKS.get(model, 120)  # Default: 120
        
        # Base-Zeit (Generation)
        generation_time = max_tokens / tokens_per_second
        
        # Overhead (RAG, Agents, etc.)
        overhead = 1.5  # Sekunden
        
        # Gesamt
        total_time = generation_time + overhead
        
        # Range (±20%)
        min_time = total_time * 0.8
        max_time = total_time * 1.2
        
        return min_time, max_time
    except Exception as e:
        logger.error(f"Fehler bei Antwortzeit-Schätzung: {e}")
        return 2.0, 6.0  # Fallback

def _update_response_time_estimate(self):
    """Aktualisiert Antwortzeit-Schätzung"""
    if hasattr(self, 'response_time_label'):
        min_time, max_time = self._estimate_response_time()
        self.response_time_label.config(
            text=f"⏱️ Geschätzte Antwortzeit: ~{min_time:.0f}-{max_time:.0f} Sekunden"
        )
```

**Datei:** `frontend/veritas_app.py`  
**Zeilen:** ~1260 (nach Token-Counter)

**Features:**
- [ ] Modell-spezifische Benchmarks
- [ ] Token-basierte Berechnung
- [ ] Overhead für RAG/Agents
- [ ] ±20% Range
- [ ] Live-Update bei Parameter-Änderung

---

### 🥈 MEDIUM PRIORITY

#### 4. Parameter-History & Gespeicherte Presets
**Geschätzter Aufwand:** 60-90 Minuten  
**Nutzen:** ⭐⭐⭐ (Mittel - Power-User-Feature)

**Beschreibung:**
Speichert die letzten 5 Parameter-Kombinationen + benutzerdefinierte Presets.

**UI-Mockup:**
```
┌─────────────────────────────────────────────────────────────┐
│  📜 History: [Letzte 5 ▼]  💾 [Speichern...]  🗑️ [Löschen]  │
└─────────────────────────────────────────────────────────────┘
```

**Features:**
- Dropdown mit letzten 5 Einstellungen
- "Speichern als Preset" Dialog (Name + Beschreibung)
- JSON-Persistierung in `config/user_presets.json`
- "Löschen" Button für gespeicherte Presets

**Datei:** `frontend/veritas_app.py` + `config/user_presets.json`

**Implementation:**
```python
def _save_parameter_history(self):
    """Speichert aktuelle Parameter in History"""
    current_params = {
        'temperature': self.temperature_var.get(),
        'max_tokens': self.max_tokens_var.get(),
        'top_p': self.top_p_var.get(),
        'timestamp': datetime.now().isoformat()
    }
    
    # Lade History
    history_file = 'config/parameter_history.json'
    history = self._load_json(history_file, default=[])
    
    # Füge hinzu (max 5)
    history.insert(0, current_params)
    history = history[:5]
    
    # Speichere
    self._save_json(history_file, history)

def _load_parameter_preset(self, preset_name):
    """Lädt gespeichertes Preset"""
    presets_file = 'config/user_presets.json'
    presets = self._load_json(presets_file, default={})
    
    if preset_name in presets:
        preset = presets[preset_name]
        self.temperature_var.set(preset['temperature'])
        self.max_tokens_var.set(preset['max_tokens'])
        self.top_p_var.set(preset['top_p'])
```

---

#### 5. Visual Feedback & Farbcodierung
**Geschätzter Aufwand:** 30-45 Minuten  
**Nutzen:** ⭐⭐⭐ (Mittel - UX-Verbesserung)

**Beschreibung:**
Farbliche Kennzeichnung der Parameter-Werte (Grün=OK, Orange=Hoch, Rot=Sehr hoch).

**UI-Mockup:**
```
┌─────────────────────────────────────────────────────────────┐
│  🌡️ [━━━━━━━] 0.7  ← Grün (Standard)                       │
│  📝 [800 ▲▼] tok   ← Orange (Hoch)                          │
│  🎲 [━━━━━━━] 0.95 ← Orange (Sehr hoch)                     │
└─────────────────────────────────────────────────────────────┘
```

**Color-Coding:**

| Parameter | Grün | Orange | Rot |
|-----------|------|--------|-----|
| Temperature | 0.3-0.8 | 0.8-0.95 | >0.95 |
| Max Tokens | <600 | 600-1200 | >1200 |
| Top-p | 0.7-0.95 | 0.5-0.7, 0.95-1.0 | <0.5 |

**Implementation:**
```python
def _update_temperature_label(self, value):
    """Aktualisiert Temperatur-Label mit Farbcodierung"""
    temp_value = float(value)
    
    # Farbcodierung
    if temp_value <= 0.8:
        color = '#00AA00'  # Grün
    elif temp_value <= 0.95:
        color = '#FF8800'  # Orange
    else:
        color = '#DD0000'  # Rot
    
    self.temp_label.config(text=f"{temp_value:.1f}", foreground=color)
```

---

### 🥉 LOW PRIORITY (Nice-to-Have)

#### 6. A/B Testing Split-View
**Geschätzter Aufwand:** 120-180 Minuten  
**Nutzen:** ⭐⭐ (Niedrig - Expertenfeature)

**Beschreibung:**
Sendet gleiche Query mit 2 verschiedenen Parameter-Sets parallel und zeigt Ergebnisse nebeneinander.

**UI-Mockup:**
```
┌────────────────────────────────────────────────────────────┐
│  Query: "Was brauche ich für eine Baugenehmigung?"        │
├──────────────────────────┬─────────────────────────────────┤
│  CONFIG A (Präzise)      │  CONFIG B (Ausführlich)         │
│  Temp: 0.3               │  Temp: 0.6                      │
│  Tokens: 300             │  Tokens: 1000                   │
│  Top-p: 0.7              │  Top-p: 0.85                    │
├──────────────────────────┼─────────────────────────────────┤
│  Antwort A:              │  Antwort B:                     │
│  [Kurze Antwort...]      │  [Ausführliche Antwort...]      │
│                          │                                 │
│  ⏱️ 2.3s | 🎯 0.85       │  ⏱️ 5.1s | 🎯 0.92              │
└──────────────────────────┴─────────────────────────────────┘
```

**Features:**
- Parallel-Anfragen (asyncio)
- Side-by-Side Vergleich
- Metriken (Zeit, Confidence, Länge)
- "Besser" Bewertung durch User

---

#### 7. Parameter-Analytics Dashboard
**Geschätzter Aufwand:** 90-120 Minuten  
**Nutzen:** ⭐⭐ (Niedrig - Statistik für Power-User)

**Beschreibung:**
Statistiken über verwendete Parameter-Kombinationen.

**Features:**
- Häufigste Einstellungen
- Durchschnittliche Antwortzeiten pro Config
- Confidence-Scores pro Preset
- Charts (matplotlib/plotly)

**Beispiel:**
```
┌────────────────────────────────────────┐
│  📊 Parameter Analytics (30 Tage)      │
├────────────────────────────────────────┤
│  Häufigste Presets:                    │
│  ✅ Standard: 65%                      │
│  📖 Ausführlich: 20%                   │
│  ⚖️ Präzise: 10%                       │
│  🎨 Kreativ: 5%                        │
│                                        │
│  Durchschnittliche Confidence:         │
│  ✅ Standard: 0.87                     │
│  📖 Ausführlich: 0.91                  │
│  ⚖️ Präzise: 0.82                      │
└────────────────────────────────────────┘
```

---

## 📅 Implementierungs-Roadmap

### Sprint 1 (2-3h)
- [x] **Woche 1:** Preset-Buttons (HIGH-1)
- [x] **Woche 1:** Token-Counter (HIGH-2)
- [x] **Woche 1:** Antwortzeit-Prädiktion (HIGH-3)

### Sprint 2 (3-4h)
- [ ] **Woche 2:** Parameter-History (MEDIUM-4)
- [ ] **Woche 2:** Visual Feedback (MEDIUM-5)

### Sprint 3 (Optional, 5-6h)
- [ ] **Woche 3+:** A/B Testing (LOW-6)
- [ ] **Woche 3+:** Analytics Dashboard (LOW-7)

---

## 🎯 Akzeptanzkriterien

### Preset-Buttons:
- [ ] 4 Buttons rendern korrekt
- [ ] Klick wendet Parameter an
- [ ] System-Message erscheint
- [ ] Labels aktualisieren sich in Echtzeit
- [ ] Tooltips zeigen Details

### Token-Counter:
- [ ] Zeigt Wörter + Zeichen
- [ ] Aktualisiert bei Spinbox-Änderung
- [ ] Farbcodierung (Grün/Orange/Rot)
- [ ] Platzierung passt ins Layout

### Antwortzeit-Prädiktion:
- [ ] Modell-spezifische Benchmarks
- [ ] Range (Min-Max) angezeigt
- [ ] Aktualisiert bei Parameter-Änderung
- [ ] Realistisch (±20% Abweichung OK)

---

## 📊 Erfolgsmetriken

**Nach Sprint 1:**
- ✅ User können mit 1 Klick zwischen Presets wechseln
- ✅ User sehen geschätzte Antwortlänge vor dem Senden
- ✅ User kennen erwartete Antwortzeit

**Nach Sprint 2:**
- ✅ User können eigene Presets speichern
- ✅ Farbcodierung hilft bei Parameter-Wahl

**Nach Sprint 3 (Optional):**
- ✅ Experten können A/B Tests durchführen
- ✅ Statistiken zeigen optimale Parameter-Kombinationen

---

## 🔗 Verwandte Dokumentation

- ✅ `docs/LLM_PARAMETERS.md` - Vollständige Parameter-Referenz
- ✅ `docs/LLM_PARAMETER_UI_CONTROLS.md` - Implementation v3.18.1
- ✅ `docs/LLM_PARAMETER_FLOW_VERIFICATION.md` - Flow-Verifizierung
- ⏳ `docs/PRESET_SYSTEM.md` - Preset-System Docs (zu erstellen)
- ⏳ `docs/AB_TESTING_GUIDE.md` - A/B Testing Guide (zu erstellen)

---

## 🚀 Quick Start (für Entwickler)

### Preset-Buttons implementieren:

1. **Datei öffnen:** `frontend/veritas_app.py`
2. **Nach Zeile 1310 einfügen:** `_create_preset_buttons()`
3. **Methoden hinzufügen:** `_apply_preset()`
4. **Testen:** Hover + Klick

### Token-Counter implementieren:

1. **Datei öffnen:** `frontend/veritas_app.py`
2. **Nach Zeile 1245 einfügen:** `_create_token_counter_label()`
3. **Methode erweitern:** `_update_tokens_label()`
4. **Testen:** Spinbox ändern → Label updated

---

## ✅ Definition of Done

Eine Feature gilt als **DONE** wenn:

- [ ] Code implementiert & kommentiert
- [ ] UI rendert korrekt (Windows + Linux getestet)
- [ ] Tooltips vorhanden & informativ
- [ ] Funktionalität getestet (min. 3 Szenarien)
- [ ] Dokumentation aktualisiert
- [ ] Keine Errors im Log
- [ ] Performance OK (<100ms UI-Update)
- [ ] Code-Review durch 2. Entwickler

---

**Autor:** VERITAS System  
**Version:** 1.0  
**Erstellt:** 10.10.2025  
**Status:** OPEN (0/7 Features)  
**Nächste Review:** 17.10.2025
