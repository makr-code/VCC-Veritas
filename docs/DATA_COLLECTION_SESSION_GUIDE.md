# 📊 Datensammlung Session Guide

**Datum:** 17. Oktober 2025  
**Ziel:** 15-20 diverse Test-Queries zur Validierung des Token-Management-Systems  
**Session-Dauer:** 30-45 Minuten

---

## 🎯 Session-Ziele

1. **Diversität testen**: Verschiedene Query-Typen, Komplexitäten, Domänen
2. **System validieren**: Budget-Allocation, Intent-Classification, Domain-Detection
3. **Baseline etablieren**: Erste Referenz-Daten für spätere Optimierungen
4. **Probleme identifizieren**: Edge Cases, Unknown Intents, Overflow-Situationen

---

## 📝 Test-Query-Plan

### Block 1: Simple Queries (quick_answer) - 5 Queries

**Erwartung:** 250-400 tokens, <30s, quick_answer, Complexity 1-4

| # | Query | Domäne | Erwartetes Budget |
|---|-------|--------|-------------------|
| 1 | "Was ist ein Bauantrag?" | Baurecht | ~250 tokens |
| 2 | "Wo beantrage ich eine Baugenehmigung?" | Baurecht | ~300 tokens |
| 3 | "Was bedeutet Lärmschutz?" | Umweltrecht | ~250 tokens |
| 4 | "Wer ist für Verkehrsschilder zuständig?" | Verkehrsrecht | ~300 tokens |
| 5 | "Was ist ein Verwaltungsakt?" | Verwaltungsrecht | ~350 tokens |

### Block 2: Medium Queries (explanation) - 5 Queries

**Erwartung:** 600-1000 tokens, <35s, explanation, Complexity 5-7

| # | Query | Domäne | Erwartetes Budget |
|---|-------|--------|-------------------|
| 6 | "Wie beantrage ich eine Baugenehmigung in Stuttgart?" | Baurecht | ~800 tokens |
| 7 | "Welche Unterlagen brauche ich für einen Bauantrag?" | Baurecht | ~700 tokens |
| 8 | "Wie funktioniert die Lärmschutzverordnung?" | Umweltrecht | ~850 tokens |
| 9 | "Wie kann ich gegen einen Bußgeldbescheid vorgehen?" | Verkehrsrecht | ~750 tokens |
| 10 | "Wie läuft ein Widerspruchsverfahren ab?" | Verwaltungsrecht | ~900 tokens |

### Block 3: Complex Queries (analysis/research) - 5 Queries

**Erwartung:** 1000-1500+ tokens, 30-40s, explanation/analysis, Complexity 8-10

| # | Query | Domäne | Erwartetes Budget |
|---|-------|--------|-------------------|
| 11 | "Erkläre das Ermessen der Behörde im Verwaltungsverfahren" | Verwaltungsrecht | ~1200 tokens |
| 12 | "Was bedeutet Verhältnismäßigkeitsprinzip in der Verwaltung?" | Verwaltungsrecht | ~1300 tokens |
| 13 | "Wie wird die Abwägung bei Bebauungsplänen durchgeführt?" | Baurecht | ~1400 tokens |
| 14 | "Erkläre die Lärmgrenzwerte für Wohngebiete und Gewerbegebiete" | Umweltrecht | ~1100 tokens |
| 15 | "Was sind die Voraussetzungen für eine Fahrerlaubnisentziehung?" | Verkehrsrecht | ~1000 tokens |

### Block 4: Edge Cases (Optional) - 3-5 Queries

**Ziel:** Overflow auslösen, Unknown Intents finden

| # | Query | Erwartung |
|---|-------|-----------|
| 16 | "Erkläre mir ausführlich die gesamte Verwaltungsgerichtsordnung und alle relevanten Verfahrensarten mit Beispielen und Rechtsprechung" | Overflow (>3500 tokens?) |
| 17 | "Hallo, wie geht's?" | Unknown Intent? |
| 18 | "Vergleiche Baurecht, Umweltrecht und Verkehrsrecht" | Multi-Domain, Analysis? |
| 19 | "Was ist der Unterschied zwischen Ermessen und Beurteilungsspielraum?" | Deep Analysis, Verwaltungsrecht |
| 20 | "Liste alle Behörden in Stuttgart auf" | Unknown/Quick Answer? |

---

## 🚀 Session-Ablauf

### Vorbereitung (5 Min)

```powershell
# 1. Backend prüfen
curl http://localhost:5000/health

# 2. Monitoring-Tool starten
cd c:\VCC\veritas
python monitor_token_budgets.py
```

### Durchführung (30 Min)

**Für jede Query:**
1. ✅ Query in Monitor eingeben
2. ✅ Warten auf Response (~30s)
3. ✅ Budget-Allocation notieren
4. ✅ Intent + Confidence prüfen
5. ✅ Complexity Score notieren
6. ✅ Auffälligkeiten dokumentieren

**Zwischen den Blöcken:**
- Kurze Pause (1-2 Min)
- `stats` Command für Zwischenstand
- `domain` Command für Domain-Analyse

### Auswertung (10 Min)

```powershell
# 1. Statistiken anzeigen
# Im Monitor: stats

# 2. Domain-Analyse
# Im Monitor: domain

# 3. Empfehlungen abrufen
# Im Monitor: rec

# 4. Export
# Im Monitor: export
# Files: data/token_monitoring/session_YYYYMMDD_HHMMSS.csv + .json

# 5. Dashboard generieren
python dashboard_token_budgets.py
```

---

## 📊 Erwartete Ergebnisse

### Budget-Verteilung

| Intent Type | Erwarteter Durchschnitt | Min | Max |
|-------------|-------------------------|-----|-----|
| quick_answer | 280 tokens | 250 | 400 |
| explanation | 800 tokens | 600 | 1000 |
| analysis | 1200 tokens | 1000 | 1500 |

### Domain-Verteilung

| Domäne | Query Count | Erwartetes Avg Budget |
|--------|-------------|------------------------|
| Verwaltungsrecht | 5 | ~1000 tokens |
| Baurecht | 5 | ~800 tokens |
| Umweltrecht | 3 | ~750 tokens |
| Verkehrsrecht | 3 | ~700 tokens |

### Performance-Metriken

| Metrik | Target | Toleranz |
|--------|--------|----------|
| Avg Processing Time | <35s | <40s |
| Overflow Rate | <5% | <10% |
| Intent Unknown Rate | <5% | <10% |
| Intent Confidence Avg | >0.8 | >0.7 |

---

## 🔍 Checkliste: Was prüfen?

### Token Budget ✅
- [ ] Simple queries: 250-400 tokens
- [ ] Medium queries: 600-1000 tokens
- [ ] Complex queries: 1000-1500+ tokens
- [ ] Verwaltungsrecht: Höchstes Budget in Complex

### Intent Classification ✅
- [ ] quick_answer: Simple queries
- [ ] explanation: Medium + Complex queries
- [ ] analysis: Sehr komplexe queries (optional)
- [ ] Unknown Rate: <5%

### Complexity Detection ✅
- [ ] Simple: 1-4
- [ ] Medium: 5-7
- [ ] Complex: 8-10
- [ ] Korrelation: Höhere Complexity → Höheres Budget

### Domain Detection ✅
- [ ] Verwaltungsrecht erkannt (+1.5x weight)
- [ ] Baurecht erkannt (+1.0x weight)
- [ ] Umweltrecht erkannt (+0.8x weight)
- [ ] Verkehrsrecht erkannt (+0.8x weight)

### Performance ✅
- [ ] Avg Processing Time <35s
- [ ] Keine Timeouts
- [ ] Keine Errors
- [ ] Backend stabil

### Overflow Handling ✅
- [ ] Bei sehr langen queries: Overflow strategy aktiviert
- [ ] Fallback funktioniert
- [ ] Max 3500-4000 tokens allocated

---

## 📝 Dokumentations-Template

### Session Notes

```markdown
## Test Session - [Datum]

**Durchgeführt:** [Zeit]  
**Queries getestet:** [Anzahl]  
**Backend:** http://localhost:5000

### Quick Stats
- Budget Range: [min] - [max] tokens
- Average: [avg] tokens
- Intent Distribution: [%]
- Domain Distribution: [%]
- Avg Processing: [s]

### Auffälligkeiten
- [ ] ...
- [ ] ...

### Empfehlungen für nächste Session
- [ ] ...
- [ ] ...
```

---

## 🚨 Troubleshooting

### Problem: Backend antwortet nicht

```powershell
# Backend-Status prüfen
Get-Process | Where-Object {$_.ProcessName -like "*python*"}

# Port prüfen
netstat -ano | findstr :5000

# Backend neu starten
python start_backend.py
```

### Problem: Token Budget = 0

**Ursache:** Response-Struktur falsch gelesen

**Lösung:** Monitor sollte automatisch `processing_metadata.token_budget` lesen

### Problem: Intent = "unknown" zu oft

**Ursache:** Query-Pattern nicht erkannt

**Lösung:**
1. Notiere Query
2. Nach Session: Intent-Classifier-Regeln erweitern
3. Pattern in `backend/services/intent_classifier.py` hinzufügen

### Problem: Overflow bei normalen Queries

**Ursache:** Budget zu hoch berechnet

**Lösung:**
1. Check RAG-Mode (sollte disabled sein für Test)
2. Check Domain-Weights
3. Nach Session: Analyzer in Dashboard nutzen

---

## 📈 Success Criteria

**Session ist erfolgreich wenn:**

✅ **Mindestens 15 Queries** getrackt  
✅ **Alle 3 Complexity-Level** abgedeckt (Simple, Medium, Complex)  
✅ **Mindestens 3 Domänen** getestet  
✅ **Intent Unknown Rate <10%**  
✅ **Keine Backend-Errors**  
✅ **CSV/JSON Export erfolgreich**  
✅ **Dashboard zeigt sinnvolle Daten**

---

## 🎯 Nach der Session

### Sofort (5 Min)

1. ✅ Export erstellen (CSV + JSON)
2. ✅ Dashboard generieren und Screenshot speichern
3. ✅ Session Notes dokumentieren
4. ✅ Auffälligkeiten notieren

### Nächste Tage (Optional)

1. 📊 Daten in Excel/Google Sheets importieren
2. 📈 Trends visualisieren
3. 🔍 Anomalien analysieren
4. 📝 Optimierungs-Ideen sammeln

### Nächste Woche

1. 🔄 Weitere Test-Session mit neuen Queries
2. 📊 Wöchentliche Dashboard-Review (Freitag)
3. 🎯 Nach 50+ Queries: Domain-Weight-Optimierung erwägen

---

## 📚 Weiterführende Docs

- [TOKEN_MONITORING_SYSTEM_GUIDE.md](TOKEN_MONITORING_SYSTEM_GUIDE.md) - Complete Guide
- [TOKEN_SYSTEM_DEPLOYMENT_GUIDE.md](TOKEN_SYSTEM_DEPLOYMENT_GUIDE.md) - Deployment Procedures
- [TOKEN_SYSTEM_PRODUCTION_DEPLOYMENT_SUCCESS.md](TOKEN_SYSTEM_PRODUCTION_DEPLOYMENT_SUCCESS.md) - Validation Results

---

**Viel Erfolg bei der ersten Datensammlung! 🚀**

**Tip:** Starte mit Block 1 (Simple Queries) um ein Gefühl für das System zu bekommen, dann steigere die Komplexität.
