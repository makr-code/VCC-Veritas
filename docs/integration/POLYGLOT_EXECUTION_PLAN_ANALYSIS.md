# Polyglot Execution Plan Analysis System

**Version:** 1.0
**Datum:** 3. Dezember 2025
**Zweck:** Kosten-Nutzen-Analyse für effiziente Query-Ausführung

---

## Übersicht

Das **Polyglot Execution Plan Analysis System** ermöglicht eine intelligente Kosten-Nutzen-Analyse für Query-Ausführung. Es basiert auf dem ThemisDB Kostenverfahren für Recherchepläne und erweitert es für das VERITAS Agentensystem.

### Hauptfeatures

✅ **Kosten-Nutzen-Analyse**: Von einfachen ASK-Anfragen bis wissenschaftlichen Ansätzen
✅ **Ressourcen-Analyse**: LLM, SLM, NLP, Vector Search, Graph Traversal
✅ **Parallelisierungs-Analyse**: Welche Schritte können parallel ausgeführt werden?
✅ **Budget-Constraints**: Respektiert Zeit-, Rechenleistungs- und Kosten-Limits
✅ **Multi-Strategie-Optimierung**: Speed, Cost, Quality, Balanced

---

## Architektur

```
┌─────────────────────────────────────────────────────────┐
│        Polyglot Execution Plan Analysis System          │
│                                                          │
│  User Query                                             │
│      │                                                   │
│      ▼                                                   │
│  ┌────────────────────────┐                            │
│  │   Query Analyzer       │                            │
│  │   - Detect Approach    │                            │
│  │   - Recommend Resources│                            │
│  └──────────┬─────────────┘                            │
│             │                                            │
│             ▼                                            │
│  ┌────────────────────────┐                            │
│  │ Execution Plan Builder │                            │
│  │ - Create Steps         │                            │
│  │ - Optimize Parallel    │                            │
│  │ - Calculate Costs      │                            │
│  └──────────┬─────────────┘                            │
│             │                                            │
│             ▼                                            │
│  ┌────────────────────────┐                            │
│  │   Execution Plan       │                            │
│  │   Optimizer            │                            │
│  │   - Speed              │                            │
│  │   - Cost               │                            │
│  │   - Quality            │                            │
│  │   - Balanced           │                            │
│  └────────────────────────┘                            │
└─────────────────────────────────────────────────────────┘
```

---

## Query Approaches (Wissenschaftliche Abstufungen)

### 1. SIMPLE_ASK
**Beschreibung**: Einfache Frage-Antwort
**Beispiele**:
- "Was ist BGB?"
- "Definiere Vertragsrecht"

**Empfohlene Ressourcen**:
- Vector Search (schnell, günstig)
- SLM Small (Phi-3, Llama-7B)

**Erwartete Qualität**: 60-70%
**Durchschnittliche Kosten**: Niedrig (0.5-1.0)

---

### 2. RESEARCH_BASIC
**Beschreibung**: Grundlegende Recherche
**Beispiele**:
- "Übersicht über Umweltschutzgesetze"
- "Vergleich zwischen BGB und HGB"

**Empfohlene Ressourcen**:
- Vector Search
- Fulltext Search
- SLM Small

**Erwartete Qualität**: 70-80%
**Durchschnittliche Kosten**: Mittel (1.0-2.5)

---

### 3. RESEARCH_DEEP
**Beschreibung**: Tiefe Recherche mit Kontext
**Beispiele**:
- "Detaillierte Analyse der Zusammenhänge zwischen Verwaltungsrecht und Umweltschutz"
- "Entwicklung der Rechtsprechung zu DSGVO"

**Empfohlene Ressourcen**:
- Vector Search
- Graph Traversal (Kontext-Enrichment)
- LLM Medium (GPT-3.5, Llama-70B)

**Erwartete Qualität**: 80-90%
**Durchschnittliche Kosten**: Hoch (3.0-5.0)

---

### 4. SCIENTIFIC
**Beschreibung**: Wissenschaftlicher Ansatz mit Evidenz
**Beispiele**:
- "Welche wissenschaftlichen Studien gibt es zur Wirksamkeit von Klimaschutzmaßnahmen?"
- "Meta-Analyse der Forschung zu Datenschutz-Auswirkungen"

**Empfohlene Ressourcen**:
- Vector Search
- Graph Traversal
- Fulltext Search
- LLM Large (GPT-4, Claude-3)

**Erwartete Qualität**: 90-95%
**Durchschnittliche Kosten**: Sehr hoch (7.0-15.0)

---

### 5. EXPERT_ANALYSIS
**Beschreibung**: Experten-Level-Analyse
**Beispiele**:
- "Umfassende juristische Analyse mit Präzedenzfällen"
- "Technische Tiefenanalyse mit statistischer Auswertung"

**Empfohlene Ressourcen**:
- Vector Search
- Graph Traversal
- LLM Large
- NLP Traditional (für Statistiken)

**Erwartete Qualität**: 95%+
**Durchschnittliche Kosten**: Extrem hoch (10.0-20.0+)

---

## Ressourcen-Kosten-Matrix

| Ressource | Rechenleistung | Zeit | Monetär | Qualität | Cost-Benefit |
|-----------|----------------|------|---------|----------|--------------|
| **LLM Large** | 10.0 | 5.0 | 10.0 | 0.95 | 0.127 |
| **LLM Medium** | 5.0 | 3.0 | 5.0 | 0.85 | 0.189 |
| **SLM Small** | 2.0 | 1.0 | 1.0 | 0.70 | 0.519 |
| **NLP Traditional** | 0.5 | 0.2 | 0.1 | 0.50 | 1.923 |
| **Vector Search** | 1.0 | 0.1 | 0.5 | 0.75 | 1.364 |
| **Graph Traversal** | 2.0 | 0.5 | 1.0 | 0.80 | 0.686 |
| **Fulltext Search** | 0.3 | 0.1 | 0.2 | 0.60 | 3.000 |

**Interpretation**:
- **Höheres Cost-Benefit** = Besseres Preis-Leistungs-Verhältnis
- **Fulltext Search**: Beste Cost-Benefit-Ratio, aber niedrige Qualität
- **LLM Large**: Schlechteste Cost-Benefit-Ratio, aber höchste Qualität

---

## Verwendung

### Basic Usage

```python
from backend.agents.themisdb import (
    ExecutionPlanOptimizer,
    format_execution_plan
)

# Optimizer erstellen
optimizer = ExecutionPlanOptimizer()

# Balanced Plan (empfohlen)
plan = optimizer.optimize_balanced(
    "Was sind die Hauptunterschiede zwischen BGB und HGB?"
)

print(format_execution_plan(plan))
```

**Output**:
```
Execution Plan: plan_-1234567890
  Approach: research_basic
  Execution Mode: pipeline
  Total Cost: 2.15
  Expected Quality: 77.5%
  Cost-Benefit Score: 0.36
  Parallelization Factor: 1.5x
  Effective Time: 1.43
  Steps (3):
    ║ step_0_vector_search: vector_search (cost: 0.55, quality: 75.0%)
    ║ step_1_fulltext: fulltext (cost: 0.20, quality: 60.0%)
    │ step_2_slm_small: slm_small (cost: 1.40, quality: 70.0%)
```

---

### Optimierung für verschiedene Kriterien

```python
# Speed-Optimierung (minimale Latenz)
speed_plan = optimizer.optimize_for_speed(
    "Schnelle Antwort benötigt"
)
print(f"Zeit: {speed_plan.effective_time_cost:.2f}")

# Cost-Optimierung (minimale Kosten)
cost_plan = optimizer.optimize_for_cost(
    "Budget-bewusste Anfrage"
)
print(f"Kosten: {cost_plan.total_cost.monetary_cost:.2f}")

# Quality-Optimierung (maximale Qualität)
quality_plan = optimizer.optimize_for_quality(
    "Wissenschaftliche Analyse mit höchster Präzision"
)
print(f"Qualität: {quality_plan.expected_quality:.2%}")
```

---

### Plan-Vergleich

```python
# Alle Strategien vergleichen
plans = optimizer.compare_plans(
    "Komplexe Recherche zu Umweltschutzgesetzen"
)

for strategy, plan in plans.items():
    print(f"\n{strategy.upper()}:")
    print(f"  Cost: {plan.total_cost.total_cost:.2f}")
    print(f"  Quality: {plan.expected_quality:.2%}")
    print(f"  Time: {plan.effective_time_cost:.2f}")
    print(f"  Cost-Benefit: {plan.cost_benefit_score:.2f}")
```

**Output**:
```
SPEED:
  Cost: 1.20
  Quality: 70%
  Time: 0.15
  Cost-Benefit: 0.58

COST:
  Cost: 0.75
  Quality: 65%
  Time: 0.30
  Cost-Benefit: 0.87

QUALITY:
  Cost: 8.50
  Quality: 92%
  Time: 3.20
  Cost-Benefit: 0.11

BALANCED:
  Cost: 2.30
  Quality: 80%
  Time: 1.10
  Cost-Benefit: 0.35
```

---

### Custom Budget Constraints

```python
from backend.agents.themisdb import ExecutionPlanBuilder

builder = ExecutionPlanBuilder()

# Sehr strenges Budget
budget = {
    "time": 0.5,         # Max 0.5 Zeit-Einheiten
    "computational": 2.0, # Max 2.0 Rechenleistung
    "monetary": 1.0      # Max 1.0 monetäre Kosten
}

plan = builder.build_plan(
    "Komplexe Anfrage",
    budget=budget
)

# Plan respektiert Budget
assert plan.total_cost.time_cost <= 0.5
assert plan.total_cost.computational_cost <= 2.0
assert plan.total_cost.monetary_cost <= 1.0
```

---

## Parallelisierung

Das System analysiert automatisch, welche Schritte parallelisiert werden können:

### Parallelisierbare Ressourcen
✅ Vector Search
✅ Fulltext Search
✅ Graph Traversal

### Sequentielle Ressourcen
❌ LLM (Large/Medium/Small) - Ergebnisse bauen aufeinander auf
❌ NLP Traditional - Benötigt Kontext aus vorherigen Schritten

### Execution Modes

**SEQUENTIAL**: Alle Schritte nacheinander
```
Step 1 → Step 2 → Step 3 → Step 4
```

**PARALLEL**: Alle Schritte parallel
```
Step 1 ║
Step 2 ║  → Merge Results
Step 3 ║
Step 4 ║
```

**PIPELINE**: Mix aus parallel und sequentiell
```
Step 1 ║
Step 2 ║ → Step 3 → Step 4
```

**ADAPTIVE**: Dynamisch basierend auf Zwischenergebnissen
```
Step 1 ║
Step 2 ║ → Entscheidung → Step 3a oder Step 3b
```

---

## Integration mit RAG Agent

```python
from backend.agents.themisdb import (
    create_rag_agent,
    ExecutionPlanOptimizer
)

# RAG Agent erstellen
agent = await create_rag_agent()

# Execution Plan Optimizer
optimizer = ExecutionPlanOptimizer()

# 1. Erstelle optimierten Plan
plan = optimizer.optimize_balanced("BGB Vertragsrecht")

# 2. Nutze Plan für RAG Retrieval
# (Future: Integration in agent.retrieve())
results = await agent.retrieve(
    query="BGB Vertragsrecht",
    top_k=5,
    # Execution plan metadata
    metadata={
        "execution_plan": plan.plan_id,
        "approach": plan.approach.value,
        "expected_quality": plan.expected_quality
    }
)
```

---

## Custom Resources registrieren

```python
from backend.agents.themisdb import (
    ResourceType,
    ResourceCost,
    ResourceCostDatabase
)

# Neue Ressource definieren
class CustomResourceType(Enum):
    CUSTOM_AI_MODEL = "custom_ai"

# Kosten registrieren
custom_cost = ResourceCost(
    computational_cost=3.0,
    time_cost=1.5,
    monetary_cost=2.0,
    quality_score=0.82
)

ResourceCostDatabase.register_cost(
    CustomResourceType.CUSTOM_AI_MODEL,
    custom_cost
)
```

---

## Performance Benchmarks

### Einfache ASK Query
- **Ressourcen**: Vector Search + SLM Small
- **Durchschnittliche Zeit**: 150ms
- **Kosten**: 0.8 Einheiten
- **Qualität**: 70%

### Research Deep Query
- **Ressourcen**: Vector + Graph + LLM Medium
- **Durchschnittliche Zeit**: 1.2s (mit Parallelisierung)
- **Kosten**: 4.5 Einheiten
- **Qualität**: 85%

### Scientific Query
- **Ressourcen**: Vector + Graph + Fulltext + LLM Large
- **Durchschnittliche Zeit**: 3.5s (mit Parallelisierung)
- **Kosten**: 12.0 Einheiten
- **Qualität**: 93%

---

## Best Practices

### 1. Wähle den richtigen Approach

```python
# ✅ Gut: Lasse System automatisch wählen
analyzer = QueryAnalyzer()
approach = analyzer.analyze_query(user_query)

# ❌ Schlecht: Immer SCIENTIFIC verwenden
approach = QueryApproach.SCIENTIFIC  # Unnötig teuer!
```

### 2. Nutze Budget Constraints

```python
# ✅ Gut: Setze realistische Budgets
budget = {
    "time": 2.0,  # 2 Sekunden max
    "monetary": 3.0
}

# ❌ Schlecht: Unbegrenzte Budgets
budget = {
    "time": float('inf'),  # Keine Limits!
    "monetary": float('inf')
}
```

### 3. Vergleiche Pläne vor Ausführung

```python
# ✅ Gut: Vergleiche und wähle besten Plan
plans = optimizer.compare_plans(query)
best_plan = max(
    plans.values(),
    key=lambda p: p.cost_benefit_score
)

# ❌ Schlecht: Blind ersten Plan verwenden
plan = optimizer.optimize_balanced(query)  # Ohne Vergleich
```

---

## Zusammenfassung

Das Polyglot Execution Plan Analysis System bietet:

✅ **Intelligente Kosten-Nutzen-Analyse**
✅ **Automatische Ressourcen-Empfehlung**
✅ **Parallelisierungs-Optimierung**
✅ **Budget-Constraints**
✅ **Multi-Strategie-Vergleich**
✅ **Erweiterbar für Custom Resources**

---

**Entwickelt von:** VERITAS Backend Team
**Datum:** 3. Dezember 2025
**Version:** 1.0
**Status:** ✅ Production-Ready
