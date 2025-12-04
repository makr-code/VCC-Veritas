# DUAL-MODE PROMPT INTEGRATION - FINALE VERSION

## 🎯 Problem-Diagnose

**Test-Ergebnis 1 (FEHLGESCHLAGEN):**
```
❌ Zitationen: 0/3
❌ Direkte Zitate: 0/2
❌ Legal Refs: 0/3
📊 GESAMT: 0/3 Kriterien erfüllt (0.0%)
```

**Root Cause:**
- Backend nutzt `SupervisorAgent.synthesize_results()`
- SupervisorAgent hatte **kein Enhanced Prompt System**
- VerwaltungsrechtPrompts Integration in `veritas_api_module.py` wurde ignoriert

## ✅ Lösung: Dual-Mode Prompt System

### Was ist das Dual-Mode System?

Das System in `backend/agents/veritas_enhanced_prompts.py` hat **3 Modi**:

1. **INTERNAL_RAG** - Query-Enrichment für bessere Retrieval-Qualität
2. **USER_FACING** - Natürliche Antworten mit **IEEE-Zitationen** ⭐
3. **HYBRID** - Kombiniert beide Modi

### USER_FACING_RESPONSE Template (Das richtige!)

**System-Prompt Features:**
```python
PERSÖNLICHKEIT:
- Freundlich, zugänglich
- Präzise, aber nicht steif

ZITATIONSREGELN (ZWINGEND!):
- JEDER Fakt MUSS mit [N] zitiert werden
- [N] = Position in Quellenliste (1-basiert)
- Zitation DIREKT nach Fakt: "§ 58 regelt...[1]"

FORMAT:
1. Direkte Antwort (MIT [N] Zitationen!)
2. Details (MIT [N] Zitationen!)
3. Quellen (automatisch)
4. Nächste Schritte
5. 💡 Vorschläge (3-5 Follow-ups)
```

**User-Prompt Variables:**
- `{query}` - User-Frage
- `{rag_context}` - Kontext aus Dokumenten
- `{agent_results}` - Agent-Erkenntnisse
- `{source_list}` - **Verfügbare Quellen für [N] Zitationen**

**Beispiel Output (EXZELLENT):**
```
Für eine Baugenehmigung in Brandenburg benötigen Sie folgende Unterlagen[1]:

• Bauantrag (amtliches Formular)
• Lageplan mit Grundstücksgrenzen
• Bauvorlagen[2]

Die Bearbeitungsdauer beträgt 2-3 Monate[3].

💡 Vorschläge:
• Welche Kosten fallen an?
• Welche Fristen muss ich beachten?
```

## 🔧 Implementierte Änderungen

### Datei 1: `backend/agents/veritas_supervisor_agent.py`

**Import geändert (Zeile 41):**
```python
# ALT:
from backend.agents.veritas_enhanced_prompts import VerwaltungsrechtPrompts

# NEU:
from backend.agents.veritas_enhanced_prompts import EnhancedPromptTemplates, PromptMode
```

**synthesize_results() ersetzt (Zeile 668):**

**ALT (Kein Enhanced Prompt):**
```python
synthesis_prompt = self.SYNTHESIS_PROMPT.format(
    original_query=original_query,
    agent_results=agent_results_json
)
```

**NEU (Dual-Mode System):**
```python
# 1. Bereite Daten auf
rag_context = "\n\n".join([
    f"[{i}] {agent.agent_type}: {agent.response_text}"
    for i, agent in enumerate(deduplicated, 1)
])

source_list = "\n".join([
    f"[{i}] Agent: {agent.agent_type} (Conf: {agent.confidence_score:.2f})"
    for i, agent in enumerate(deduplicated, 1)
])

# 2. Nutze USER_FACING_RESPONSE
system_prompt = EnhancedPromptTemplates.get_system_prompt(
    mode=PromptMode.USER_FACING,
    domain="general"
)

user_prompt = EnhancedPromptTemplates.get_user_prompt(
    mode=PromptMode.USER_FACING,
    domain="general",
    query=original_query,
    rag_context=rag_context,
    agent_results=agent_results_text,
    source_list=source_list  # ⭐ Für IEEE-Zitationen!
)

full_prompt = f"{system_prompt}\n\n{user_prompt}"
```

## 📊 Erwartete Verbesserung

**Vorher (Baseline):**
- 0% IEEE-Zitationen
- 1.6% Direkte Zitate
- 32% Aspect Coverage
- 0% Follow-up Suggestions

**Nachher (USER_FACING_RESPONSE):**
- **60-80%** IEEE-Zitationen ✅ (Prompt erzwingt [N] nach jedem Fakt)
- **40-60%** Direkte Zitate (natürlicher Output)
- **50-70%** Aspect Coverage (strukturierte Antworten)
- **80-100%** Follow-up Suggestions (Template fordert 3-5 Vorschläge)

## 🧪 Test-Anweisungen

### Schritt 1: Backend neu starten
```bash
# Backend-Terminal (Strg+C falls läuft)
python start_backend.py
```

### Schritt 2: Prompt-Verbesserungstest
```bash
cd tests
python test_prompt_improvement.py
```

**Erwartung:**
```
✅ Zitationen: ≥3/3 (IEEE [1], [2], [3])
✅ Direkte Zitate: ≥2/2 (falls vorhanden)
✅ Legal Refs: ≥3/3 (§ Referenzen)
📊 GESAMT: 3/3 Kriterien erfüllt (100%)
```

### Schritt 3: Bei Erfolg - Full Golden Dataset v2
```bash
python test_rag_quality_v3_19_0.py
# Teste alle 10 Modelle mit Enhanced Prompts
# Vergleiche mit Baseline (baseline in rag_test_results_1760099947.json)
```

## 🔍 Warum funktioniert das jetzt?

**Problem vorher:**
1. Backend → Intelligent Pipeline → SupervisorAgent
2. SupervisorAgent.SYNTHESIS_PROMPT = **basic template ohne Zitationen**
3. Kein `source_list` Parameter → LLM weiß nicht was [1], [2] bedeutet

**Lösung jetzt:**
1. Backend → Intelligent Pipeline → SupervisorAgent
2. SupervisorAgent → **EnhancedPromptTemplates.USER_FACING_RESPONSE**
3. **`source_list` wird übergeben:** `[1] Agent: BuildingPermitAgent (Conf: 0.85)`
4. LLM sieht: "Für Zitationen nutze [1], [2], [3] aus source_list"
5. LLM generiert: "§ 58 LBO BW regelt...[1]" ✅

## 📁 Geänderte Dateien (Final)

1. ✅ `backend/agents/veritas_ollama_client.py`
   - Neue Methode: `list_models()` (10 Modelle statt 4)

2. ✅ `backend/api/veritas_api_module.py`
   - Import: VerwaltungsrechtPrompts (wird nicht genutzt, aber bereit)
   - Enhanced Prompt (wird von Supervisor überschrieben)

3. ✅ `backend/agents/veritas_supervisor_agent.py` ⭐ **KRITISCH**
   - Import: EnhancedPromptTemplates, PromptMode
   - synthesize_results(): Nutzt USER_FACING_RESPONSE mit source_list

4. ✅ `tests/test_rag_quality_v3_19_0.py`
   - Bugfix: start_time → query_start_time

5. ✅ `tests/analyze_golden_dataset.py` (NEU)
   - Analyse-Tool

6. ✅ `tests/test_prompt_improvement.py` (NEU)
   - Schnelltest (1 Modell, 1 Frage)

## 🎯 Kritische Unterschiede

### VerwaltungsrechtPrompts vs. EnhancedPromptTemplates

| Feature | VerwaltungsrechtPrompts | EnhancedPromptTemplates |
|---------|------------------------|------------------------|
| **Ziel** | Verwaltungsrecht-spezifisch | Multi-Domain, flexibel |
| **Modi** | Single-Mode | **3 Modi** (RAG, User, Hybrid) |
| **Zitate** | § Referenzen + "..." Quotes | **IEEE [N] Citations** ⭐ |
| **Follow-ups** | Template-basiert | **Explizit gefordert** (3-5) |
| **Backend-Integration** | Nicht verwendet | **Aktiv in Supervisor** ✅ |

**Warum EnhancedPromptTemplates?**
- ✅ Bereits im Backend integriert
- ✅ USER_FACING_RESPONSE hat **alle Features**
- ✅ IEEE-Zitationen = Standard in RAG-Systemen
- ✅ Multi-Domain (building, environmental, etc.)

## ⚠️ Fallback-Plan

Falls Test wieder fehlschlägt:

1. **Prüfe ob Supervisor wirklich genutzt wird:**
   ```python
   # In Backend-Logs suchen:
   "[ENHANCED SYNTHESIS] Nutze EnhancedPromptTemplates.USER_FACING_RESPONSE"
   ```

2. **Prüfe ob source_list übergeben wird:**
   ```python
   # Log sollte zeigen:
   "Prompt: XXXX Zeichen, Quellen: 3, Mode: USER_FACING"
   ```

3. **Wenn immer noch 0% Zitationen:**
   - Problem liegt am LLM (ignoriert Anweisungen)
   - Lösung: Few-Shot Examples direkt in Prompt einbauen
   - Alternative: Constraint-based Generation (Force [N] nach jedem Satz)

## 📊 Success Criteria

**Minimum Viable Success:**
- ≥ 50% Zitationen (1.5/3)
- ≥ 30% Direkte Zitate (0.6/2)
- ≥ 50% Legal Refs (1.5/3)

**Target Success:**
- ≥ 80% Zitationen (2.4/3)
- ≥ 60% Direkte Zitate (1.2/2)
- ≥ 70% Legal Refs (2.1/3)

**Excellent:**
- 100% Zitationen (3/3) ✅
- 100% Direkte Zitate (2/2) ✅
- 100% Legal Refs (3/3) ✅

---

**Status:** ✅ Dual-Mode Integration abgeschlossen
**Nächster Schritt:** Backend-Neustart → test_prompt_improvement.py
**Expected Result:** 60-80% Improvement (Baseline: 0% → Target: 60-80%)
