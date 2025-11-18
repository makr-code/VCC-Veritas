# 🔄 Prompt Improvement System - Selbstverbesserung

**Version:** 1.0
**Erstellt:** 12. Oktober 2025, 21:45 Uhr
**Status:** 📋 DESIGN - Iteratives Prompt-Tuning

---

## 🎯 Konzept: Selbstverbessernde Prompts

### Problem

**Bisheriger Ansatz:**
- ❌ Prompts als statische Text-Dateien
- ❌ Manuelle Verbesserung durch Trial & Error
- ❌ Keine Metriken zur Prompt-Qualität
- ❌ Keine systematische Iteration

### Lösung: JSON-basiertes Prompt-Management mit Feedback-Loop

```
┌─────────────────────────────────────────────────────────────────┐
│                     IMPROVEMENT CYCLE                            │
└─────────────────────────────────────────────────────────────────┘

1. EXECUTION
   User Query → ScientificPhaseExecutor → LLM Response
                                          ↓
2. METRICS COLLECTION
   QualityMetrics: JSON validity, Schema compliance, Confidence calibration
                                          ↓
3. AGGREGATION (N=10 Queries)
   PromptImprovementEngine: Aggregate metrics, Calculate quality scores
                                          ↓
4. ANALYSIS
   Compare to Targets → Identify Gaps → Generate Improvement Suggestions
                                          ↓
5. ITERATION
   Apply Changes to scientific_foundation.json → v1.0 → v1.1 → v1.2 ...
                                          ↓
                    ┌───────────────────┘
                    └─→ REPEAT CYCLE
```

---

## 📋 scientific_foundation.json Struktur

### 1. Core Principles

```json
{
  "core_principles": {
    "principles": [
      {
        "id": "evidence_based",
        "name": "Evidenzbasiert",
        "description": "Alle Aussagen müssen auf konkreten Quellen basieren",
        "importance": "critical",
        "examples": [
          "✅ 'Laut LBO BW § 50 sind Carports <30m² verfahrensfrei'",
          "❌ 'Carports sind meist genehmigungsfrei' (zu vage)"
        ]
      }
    ]
  }
}
```

**Improvement Strategy:**
- Beispiele werden basierend auf häufigen Fehlern erweitert
- Importance-Level kann angepasst werden (critical → high)

---

### 2. Scientific Method (6 Steps)

```json
{
  "scientific_method": {
    "steps": [
      {
        "step_number": 1,
        "step_id": "hypothesis",
        "name": "HYPOTHESE",
        "purpose": "Formuliere eine erste Vermutung...",
        "key_question": "Was vermute ich?",
        "output_focus": [
          "Klare Hypothese (1-2 Sätze)",
          "Prüfkriterien identifizieren",
          "Fehlende Informationen benennen"
        ]
      }
    ]
  }
}
```

**Improvement Strategy:**
- `output_focus` wird verfeinert basierend auf LLM-Output-Qualität
- `key_question` kann umformuliert werden für besseres LLM-Understanding

---

### 3. Source Quality Hierarchy

```json
{
  "source_quality_hierarchy": {
    "levels": [
      {
        "level": 1,
        "source_type": "gesetz",
        "confidence_range": [0.95, 1.0],
        "authority": "highest",
        "examples": ["BauGB", "LBO BW", "GG"],
        "rationale": "Höchste rechtliche Autorität"
      }
    ],
    "conflict_resolution_rules": [
      {
        "rule_id": "authority_precedence",
        "description": "Bei Widerspruch gewinnt die Quelle mit höherer Authority",
        "example": "LBO BW § 50 (Level 1) schlägt Merkblatt (Level 4)"
      }
    ]
  }
}
```

**Improvement Strategy:**
- Confidence-Ranges werden kalibriert basierend auf User-Feedback
- Conflict-Resolution-Rules werden erweitert bei neuen Edge-Cases

---

### 4. Output Quality Standards

```json
{
  "output_quality_standards": {
    "confidence_calibration": {
      "very_high": {
        "range": [0.90, 1.0],
        "criteria": "Klare gesetzliche Basis + keine Widersprüche + alle Infos vorhanden"
      }
    },
    "required_criteria_guidelines": {
      "minimum": 1,
      "maximum": 10,
      "best_practice": "3-5 konkrete, prüfbare Kriterien",
      "examples": [
        "✅ 'Bundesland-spezifische LBO (z.B. § 50 LBO BW)'",
        "❌ 'Rechtliche Rahmenbedingungen' (zu vage)"
      ]
    }
  }
}
```

**Improvement Strategy:**
- Beispiele werden automatisch erweitert basierend auf häufigen Vage-Criteria
- Confidence-Criteria werden verfeinert bei Calibration-Error

---

### 5. Prompt Improvement Metadata

```json
{
  "prompt_improvement": {
    "improvement_metrics": [
      {
        "metric_id": "json_validity_rate",
        "name": "JSON Validität",
        "target": 0.98,
        "current": 0.92,  ← Updated automatisch
        "improvement_actions": [
          "Beispiele für valides JSON hinzufügen",
          "Häufige Fehler explizit verbieten"
        ]
      }
    ],
    "version_history": [
      {
        "version": "1.0.0",
        "date": "2025-10-12",
        "changes": "Initial version",
        "quality_score": 0.85,
        "tested_queries": 10
      },
      {
        "version": "1.1.0",
        "date": "2025-10-15",
        "changes": "Confidence-Calibration verfeinert; Vage-Criteria Beispiele hinzugefügt",
        "quality_score": 0.91,
        "tested_queries": 20
      }
    ]
  }
}
```

---

## 🔧 Improvement Engine: PromptImprovementEngine

### Komponenten

**Datei:** `backend/services/prompt_improvement_engine.py`

```python
class PromptImprovementEngine:
    """
    Engine für iterative Verbesserung von scientific_foundation.json

    WORKFLOW:
    1. Collect Metrics von jeder Query
    2. Aggregate Metrics über N Queries (default: 10)
    3. Identify Improvement Opportunities (Target-Gaps)
    4. Generate Improvement Suggestions
    5. Apply Improvements → New Version
    """

    def record_query_metrics(self, metrics: QualityMetrics):
        """Record Metrics von einer Query-Execution"""

    def analyze_and_improve(self) -> Dict[str, Any]:
        """Analyze Metrics + Generate Improvement Suggestions"""

    def apply_improvements(self, suggestions: List[Dict]) -> str:
        """Apply Improvements → New Version (v1.0 → v1.1)"""
```

---

### Quality Metrics (gesammelt pro Query)

```python
@dataclass
class QualityMetrics:
    query_id: str
    timestamp: str

    # JSON Validity
    json_valid: bool
    json_parse_error: Optional[str]

    # Schema Compliance
    schema_valid: bool
    missing_fields: List[str]

    # Confidence Calibration
    predicted_confidence: float  # LLM prediction
    actual_confidence: float     # User rating (1-5 → 0.0-1.0)

    # Required Criteria Quality
    num_criteria: int
    vague_criteria: List[str]  # Zu vage formulierte Kriterien

    # Source Citation
    citations_found: int
    citations_expected: int

    # Metacognition
    improvement_suggestions: List[str]  # Aus Phase 6
```

**Collection Point:**
```python
# In UnifiedOrchestratorV7.process_query()

# Nach Execution aller Phasen:
metrics = QualityMetrics(
    query_id=query_id,
    timestamp=datetime.now().isoformat(),
    json_valid=all(phase["status"] == "success" for phase in scientific_results.values()),
    schema_valid=True,  # Validation erfolgt in ScientificPhaseExecutor
    predicted_confidence=scientific_results["metacognition"]["output"]["overall_confidence"],
    actual_confidence=None,  # Later: User-Feedback
    num_criteria=len(scientific_results["hypothesis"]["output"]["required_criteria"]),
    vague_criteria=self._detect_vague_criteria(scientific_results["hypothesis"]["output"]),
    citations_found=self._count_citations(scientific_results),
    citations_expected=len(scientific_results["synthesis"]["output"]["evidence_clusters"]),
    improvement_suggestions=scientific_results["metacognition"]["output"]["metacognitive_assessment"]["improvement_suggestions"]
)

improvement_engine.record_query_metrics(metrics)
```

---

### Aggregation & Analysis (alle 10 Queries)

```python
def _aggregate_metrics(self) -> Dict[str, Any]:
    """
    Aggregate über N Queries

    Returns:
        {
            "json_validity_rate": 0.95,
            "schema_validity_rate": 0.98,
            "avg_num_criteria": 4.2,
            "avg_vague_criteria": 0.8,
            "citation_rate": 0.92,
            "confidence_calibration_error": 0.12,
            "common_improvement_suggestions": [
                {"suggestion": "Mehr Beispiele für Confidence", "frequency": 7}
            ]
        }
    """
```

**Quality Score Calculation:**
```python
def _calculate_quality_scores(self, aggregated: Dict) -> Dict[str, float]:
    return {
        "json_validity_rate": aggregated["json_validity_rate"],
        "confidence_calibration_accuracy": 1.0 - aggregated["confidence_calibration_error"],
        "required_criteria_quality": 1.0 - (aggregated["avg_vague_criteria"] / 10),
        "source_citation_rate": aggregated["citation_rate"]
    }
```

**Compare to Targets:**
```python
# Targets from scientific_foundation.json
targets = {
    "json_validity_rate": 0.98,
    "confidence_calibration_accuracy": 0.85,
    "required_criteria_quality": 0.90,
    "source_citation_rate": 0.95
}

# Identify Gaps
opportunities = [
    {
        "metric_id": "confidence_calibration_accuracy",
        "current": 0.78,
        "target": 0.85,
        "gap": 0.07,
        "priority": "medium"
    }
]
```

---

### Improvement Suggestions

**Auto-Generated Suggestions:**

```python
suggestions = [
    {
        "target_section": "output_quality_standards.confidence_calibration",
        "change_type": "refine_criteria",
        "description": "Verfeinere Kriterien für Confidence-Ranges",
        "priority": "medium",
        "rationale": "Calibration Error: 22% (Ziel: 15%)",
        "specific_changes": {
            "very_high.criteria": "ADD: '+ Bundesland bekannt'",
            "medium.criteria": "ADD: '+ teilweise Nutzer-Input fehlt'"
        }
    },
    {
        "target_section": "output_quality_standards.required_criteria_guidelines",
        "change_type": "add_negative_examples",
        "description": "Füge häufige vage Kriterien als ❌ Beispiele hinzu",
        "priority": "high",
        "rationale": "Durchschnittlich 0.8 vage Kriterien pro Query",
        "specific_changes": {
            "examples": [
                "ADD: '❌ Rechtliche Rahmenbedingungen (zu vage)'",
                "ADD: '❌ Relevante Vorschriften (zu allgemein)'"
            ]
        }
    },
    {
        "target_section": "core_principles",
        "change_type": "llm_feedback",
        "description": "LLM-Suggestion: Mehr Beispiele für Source-Zitation",
        "priority": "high",
        "rationale": "LLM schlug dies 7x vor (Metacognition Phase 6)",
        "specific_changes": {
            "evidence_based.examples": [
                "ADD: '✅ Cluster X basiert auf LBO § Y + VGH Urteil Z'",
                "ADD: '❌ Cluster ohne Source-Referenz'"
            ]
        }
    }
]
```

---

### Apply Improvements

```python
def apply_improvements(self, suggestions: List[Dict]) -> str:
    """
    Apply Improvements zu scientific_foundation.json

    Workflow:
    1. Create Backup (scientific_foundation.json.bak)
    2. Increment Version (1.0.0 → 1.1.0)
    3. Apply Changes (per suggestion.specific_changes)
    4. Update Metadata (version, last_updated, improvement_iteration)
    5. Add to version_history
    6. Save to Disk

    Returns:
        "1.1.0"  # New version
    """

    # Example: Apply "add_negative_examples"
    if suggestion["change_type"] == "add_negative_examples":
        target_section = self._navigate_to_section(
            self.foundation,
            suggestion["target_section"]
        )

        for new_example in suggestion["specific_changes"]["examples"]:
            if new_example.startswith("ADD: "):
                example_text = new_example[5:]  # Remove "ADD: "
                target_section["examples"].append(example_text)

    # Increment version
    new_version = self._increment_version(current_version)  # 1.0.0 → 1.1.0

    # Update metadata
    self.foundation["scientific_foundation"]["version"] = new_version
    self.foundation["scientific_foundation"]["improvement_iteration"] += 1

    # Add to version history
    version_entry = {
        "version": new_version,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "changes": "; ".join([s["description"] for s in suggestions]),
        "quality_score": None,  # Will be calculated after next 10 queries
        "tested_queries": 0
    }
    self.foundation["scientific_foundation"]["prompt_improvement"]["version_history"].append(version_entry)

    # Save
    with open(self.foundation_path, 'w', encoding='utf-8') as f:
        json.dump(self.foundation, f, indent=2, ensure_ascii=False)

    return new_version
```

---

## 🚀 Integration in UnifiedOrchestratorV7

```python
class UnifiedOrchestratorV7:
    def __init__(self, ...):
        # Existing
        self.scientific_executor = ScientificPhaseExecutor(...)

        # NEW: Prompt Improvement Engine
        self.improvement_engine = PromptImprovementEngine(
            foundation_path="config/prompts/scientific_foundation.json",
            metrics_db_path="data/prompt_metrics.json"
        )

    async def process_query(self, user_query: str, user_id: str) -> Dict:
        # ... existing scientific processing ...

        # Collect Metrics
        metrics = self._collect_quality_metrics(
            query_id=query_id,
            scientific_results=scientific_results,
            user_feedback=None  # Later: User-Rating
        )

        # Record Metrics (triggers improvement after 10 queries)
        self.improvement_engine.record_query_metrics(metrics)

        return result

    def _collect_quality_metrics(self, query_id, scientific_results, user_feedback) -> QualityMetrics:
        """Extract Quality Metrics from Scientific Results"""

        return QualityMetrics(
            query_id=query_id,
            timestamp=datetime.now().isoformat(),

            # JSON Validity
            json_valid=all(p["status"] == "success" for p in scientific_results.values()),
            json_parse_error=None,

            # Schema Compliance
            schema_valid=True,
            missing_fields=[],

            # Confidence Calibration
            predicted_confidence=scientific_results["metacognition"]["output"]["metacognitive_assessment"]["overall_confidence"],
            actual_confidence=user_feedback.get("confidence_rating") if user_feedback else None,

            # Required Criteria Quality
            num_criteria=len(scientific_results["hypothesis"]["output"]["required_criteria"]),
            vague_criteria=self._detect_vague_criteria(scientific_results["hypothesis"]["output"]["required_criteria"]),

            # Source Citation
            citations_found=self._count_citations(scientific_results["synthesis"]["output"]),
            citations_expected=len(scientific_results["synthesis"]["output"]["evidence_clusters"]),

            # Metacognition
            improvement_suggestions=scientific_results["metacognition"]["output"]["metacognitive_assessment"]["improvement_suggestions"]
        )

    def _detect_vague_criteria(self, criteria: List[str]) -> List[str]:
        """Detect vage formulierte Kriterien"""

        vague_keywords = [
            "rahmenbedingungen",
            "vorschriften",
            "regelungen",
            "bestimmungen",
            "aspekte",
            "faktoren"
        ]

        vague = []
        for criterion in criteria:
            if any(keyword in criterion.lower() for keyword in vague_keywords):
                vague.append(criterion)

        return vague

    def _count_citations(self, synthesis_output: Dict) -> int:
        """Count Source Citations in Evidence Clusters"""

        count = 0
        for cluster in synthesis_output["evidence_clusters"]:
            count += len(cluster.get("sources", []))

        return count
```

---

## 📊 Example: Improvement Cycle

### Initial State (v1.0.0)

```json
{
  "version": "1.0.0",
  "improvement_iteration": 1,
  "prompt_improvement": {
    "improvement_metrics": [
      {
        "metric_id": "confidence_calibration_accuracy",
        "target": 0.85,
        "current": null
      }
    ]
  }
}
```

---

### After 10 Queries: Metrics Aggregated

```json
{
  "aggregated_metrics": {
    "json_validity_rate": 0.95,
    "confidence_calibration_error": 0.22,  ← Problem!
    "avg_vague_criteria": 0.8,             ← Problem!
    "citation_rate": 0.88
  },
  "quality_scores": {
    "confidence_calibration_accuracy": 0.78,  ← Below target (0.85)
    "required_criteria_quality": 0.92,        ← OK
    "source_citation_rate": 0.88              ← Below target (0.95)
  }
}
```

---

### Improvement Suggestions Generated

```json
{
  "improvement_opportunities": [
    {
      "metric_id": "confidence_calibration_accuracy",
      "current": 0.78,
      "target": 0.85,
      "gap": 0.07,
      "priority": "medium"
    }
  ],
  "suggested_changes": [
    {
      "target_section": "output_quality_standards.confidence_calibration",
      "change_type": "refine_criteria",
      "description": "Verfeinere Kriterien für Confidence-Ranges",
      "specific_changes": {
        "very_high.criteria": "ADD: '+ Bundesland bekannt + Größe angegeben'"
      }
    }
  ]
}
```

---

### Applied Improvements → v1.1.0

```json
{
  "version": "1.1.0",
  "improvement_iteration": 2,
  "output_quality_standards": {
    "confidence_calibration": {
      "very_high": {
        "range": [0.90, 1.0],
        "criteria": "Klare gesetzliche Basis + keine Widersprüche + alle Infos vorhanden + Bundesland bekannt + Größe angegeben"
      }
    }
  },
  "prompt_improvement": {
    "version_history": [
      {
        "version": "1.0.0",
        "quality_score": 0.85,
        "tested_queries": 10
      },
      {
        "version": "1.1.0",
        "date": "2025-10-15",
        "changes": "Confidence-Calibration verfeinert",
        "quality_score": null,
        "tested_queries": 0
      }
    ]
  }
}
```

---

### After Next 10 Queries (v1.1.0 tested)

```json
{
  "quality_scores": {
    "confidence_calibration_accuracy": 0.87  ← Improved! (was 0.78)
  },
  "version_history": [
    {
      "version": "1.1.0",
      "quality_score": 0.89,  ← Updated
      "tested_queries": 10
    }
  ]
}
```

---

## 🎯 Benefits: JSON-based Prompt Management

| Aspekt | Text-based Prompts | JSON-based Prompts |
|--------|-------------------|-------------------|
| **Versionierung** | Git-only | version_history in JSON |
| **Metriken** | ❌ Keine | ✅ improvement_metrics |
| **Automatische Verbesserung** | ❌ Manuell | ✅ Auto-Iteration |
| **Maschinenlesbar** | ❌ Parsing nötig | ✅ Native JSON |
| **Strukturiert** | ❌ Freitext | ✅ Hierarchische Sections |
| **LLM-Optimierung** | ❌ Trial & Error | ✅ Metrics-driven |
| **Rollback** | Git revert | version_history + .bak |

---

## 🚀 Implementation Roadmap

### Phase 1: JSON Foundation (DONE)

- [x] Create `config/prompts/scientific_foundation.json`
- [x] Define core_principles, scientific_method, source_quality_hierarchy
- [x] Add prompt_improvement metadata structure

### Phase 2: Improvement Engine (DONE)

- [x] Create `backend/services/prompt_improvement_engine.py`
- [x] Implement QualityMetrics dataclass
- [x] Implement PromptImprovementEngine class
- [x] Methods: record_query_metrics(), analyze_and_improve(), apply_improvements()

### Phase 3: Integration (TODO)

- [ ] Update `ScientificPhaseExecutor` to load from JSON
- [ ] Update `UnifiedOrchestratorV7` to collect metrics
- [ ] Implement `_collect_quality_metrics()` method
- [ ] Implement `_detect_vague_criteria()` helper
- [ ] Implement `_count_citations()` helper

### Phase 4: Testing & Iteration (TODO)

- [ ] Test with 10 sample queries
- [ ] Collect first metrics
- [ ] Trigger first improvement cycle
- [ ] Validate v1.0.0 → v1.1.0 transition
- [ ] Monitor quality_score improvement

---

## 💡 Future Enhancements

### 1. User Feedback Integration

```python
# Frontend: User rates answer quality
user_feedback = {
    "query_id": "...",
    "confidence_rating": 4.5,  # 1-5 scale → 0.9 normalized
    "helpfulness": 5,
    "accuracy": 4,
    "completeness": 5
}

# Backend: Use for Confidence Calibration
metrics.actual_confidence = user_feedback["confidence_rating"] / 5.0
```

### 2. A/B Testing

```python
# Test v1.0 vs. v1.1 parallel
if user_id % 2 == 0:
    foundation_version = "1.0.0"
else:
    foundation_version = "1.1.0"

# Compare quality scores
compare_versions(v1_metrics, v2_metrics)
```

### 3. LLM-Assisted Improvement

```python
# Use LLM to generate improvement suggestions
llm_suggestion = await ollama_client.generate(
    prompt=f"""
    Current Prompt Performance:
    - Confidence Calibration Error: 22%
    - Target: 15%

    Suggest 3 concrete improvements to the confidence_calibration criteria.
    """,
    model="llama3.1:latest"
)

# Parse LLM suggestions → Apply to JSON
```

---

**Status:** ✅ Design Complete - Ready for Implementation Phase 3

**Next Step:** Integrate PromptImprovementEngine in UnifiedOrchestratorV7
