# 🔬 JSON-basierte wissenschaftliche Methodik - Orchestrator-Integration

**Version:** v7.0 (Configuration-Driven Scientific Reasoning)  
**Erstellt:** 12. Oktober 2025, 21:15 Uhr  
**Status:** 📋 DESIGN - Paradigmenwechsel zu JSON-Konfiguration

---

## 🎯 Paradigmenwechsel: Von Hard-Coded zu Configuration-Driven

### ❌ **Bisheriger Ansatz (v5.0/v6.0): Hard-Coded Services**

```python
# Fest verdrahtete Python-Klassen
class HypothesisService:
    async def generate(...):
        # Hard-coded Logik

class SynthesisService:
    async def synthesize_evidence(...):
        # Hard-coded Logik

class ValidationService:
    async def validate_hypothesis(...):
        # Hard-coded Logik
```

**Probleme:**
- ❌ Nicht flexibel (Code-Änderungen nötig)
- ❌ Schwer erweiterbar
- ❌ LLM kann Ablauf nicht selbst optimieren

---

### ✅ **Neuer Ansatz (v7.0): JSON-Konfiguration + Orchestrator**

```json
{
  "scientific_method_config": {
    "version": "1.0",
    "phases": [
      {
        "phase_id": "hypothesis",
        "prompt_template": "hypothesis_generation.txt",
        "output_schema": {...}
      },
      {
        "phase_id": "synthesis",
        "prompt_template": "evidence_synthesis.txt",
        "output_schema": {...}
      }
    ]
  }
}
```

**Vorteile:**
- ✅ **Flexibel:** Neue Phasen ohne Code-Änderung
- ✅ **LLM-optimierbar:** Prompts + Ablauf anpassbar
- ✅ **Versionierbar:** Verschiedene Methoden-Konfigurationen
- ✅ **Orchestrator-kompatibel:** Passt zu DYNAMIC_AGENT_TASK_BLUEPRINTS Pattern

---

## 🏗️ Architektur-Übersicht

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER QUERY                                │
│            "Brauche ich eine Baugenehmigung?"                    │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              UNIFIED ORCHESTRATOR (Enhanced)                     │
│                                                                  │
│  1. Load Scientific Method Config (JSON)                        │
│  2. Enhance User Query with Base Prompt                         │
│  3. Execute Scientific Phases (Generic LLM Executor)            │
│  4. Coordinate Agent Tasks (Parallel)                           │
└────────────────────────┬────────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
┌────────────────┐ ┌──────────┐ ┌──────────────┐
│ Scientific     │ │  Agent   │ │  RAG         │
│ Phase Executor │ │  Tasks   │ │  Retrieval   │
│                │ │          │ │              │
│ JSON-driven    │ │ Existing │ │ Existing     │
│ LLM Calls      │ │ System   │ │ System       │
└────────────────┘ └──────────┘ └──────────────┘
```

---

## 📋 JSON-Konfigurationen

### 1. Scientific Method Configuration

**Datei:** `config/scientific_methods/default_method.json`

```json
{
  "method_id": "default_scientific_method",
  "version": "1.0",
  "description": "Standard wissenschaftliches Vorgehen: Hypothese → Synthese → Analyse → Validation → Conclusion → Metacognition",
  "created_at": "2025-10-12T21:00:00Z",
  
  "base_prompts": {
    "user_query_enhancement": {
      "template_file": "prompts/scientific/user_query_enhancement.txt",
      "purpose": "Erweitert User-Query mit wissenschaftlichem Kontext",
      "variables": ["user_query", "detected_domain", "complexity_estimate"]
    },
    "scientific_foundation": {
      "template_file": "prompts/scientific/scientific_foundation.txt",
      "purpose": "Basis-Prompt für alle wissenschaftlichen Phasen",
      "content": "Du bist ein wissenschaftlicher Assistent. Deine Aufgabe ist es, Fragen systematisch und evidenzbasiert zu beantworten. Befolge die wissenschaftliche Methodik: Hypothese → Evidenz sammeln → Analysieren → Validieren → Schlussfolgern."
    }
  },
  
  "phases": [
    {
      "phase_id": "hypothesis",
      "phase_number": 1,
      "phase_name": "Hypothesengenerierung",
      "description": "Erste Vermutung basierend auf Query + RAG",
      
      "dependencies": {
        "requires_phases": [],
        "requires_data": ["user_query", "rag_results"]
      },
      
      "execution": {
        "type": "llm_call",
        "model": "llama3.1:latest",
        "temperature": 0.4,
        "max_tokens": 1000,
        "timeout_seconds": 30
      },
      
      "prompt_construction": {
        "template_file": "prompts/scientific/phase1_hypothesis.txt",
        "input_mapping": {
          "user_query": "query_text",
          "rag_results": "rag_context"
        },
        "context_inclusion": {
          "scientific_foundation": true,
          "previous_phases": false
        }
      },
      
      "output_schema": {
        "type": "object",
        "required": ["hypothesis", "required_criteria", "missing_information", "confidence"],
        "properties": {
          "hypothesis": {
            "type": "string",
            "description": "Erste Vermutung zur Beantwortung der Frage"
          },
          "required_criteria": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Welche Kriterien müssen geprüft werden?"
          },
          "missing_information": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Welche Informationen fehlen noch?"
          },
          "confidence": {
            "type": "number",
            "minimum": 0.0,
            "maximum": 1.0
          },
          "reasoning": {
            "type": "string",
            "description": "Begründung für die Hypothese"
          }
        }
      },
      
      "validation_rules": [
        {
          "rule": "confidence_in_range",
          "field": "confidence",
          "min": 0.0,
          "max": 1.0
        },
        {
          "rule": "required_criteria_not_empty",
          "field": "required_criteria",
          "min_items": 1
        }
      ],
      
      "retry_policy": {
        "max_retries": 2,
        "retry_on": ["invalid_json", "validation_failed"],
        "backoff_seconds": 1
      }
    },
    
    {
      "phase_id": "synthesis",
      "phase_number": 2,
      "phase_name": "Evidenz-Synthese",
      "description": "Aggregiere und verknüpfe RAG-Ergebnisse",
      
      "dependencies": {
        "requires_phases": ["hypothesis"],
        "requires_data": ["hypothesis_output", "rag_results"]
      },
      
      "execution": {
        "type": "llm_call",
        "model": "llama3.1:latest",
        "temperature": 0.3,
        "max_tokens": 2000,
        "timeout_seconds": 45
      },
      
      "prompt_construction": {
        "template_file": "prompts/scientific/phase2_synthesis.txt",
        "input_mapping": {
          "hypothesis": "phases.hypothesis.output",
          "rag_results": "rag_context"
        },
        "context_inclusion": {
          "scientific_foundation": true,
          "previous_phases": ["hypothesis"]
        }
      },
      
      "output_schema": {
        "type": "object",
        "required": ["evidence_clusters", "cross_references", "gaps"],
        "properties": {
          "evidence_clusters": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "theme": {"type": "string"},
                "sources": {"type": "array"},
                "synthesis": {"type": "string"},
                "strength": {"type": "number"}
              }
            }
          },
          "cross_references": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "source1": {"type": "string"},
                "source2": {"type": "string"},
                "relationship": {"type": "string", "enum": ["supporting", "contradicting", "citing"]},
                "strength": {"type": "number"}
              }
            }
          },
          "gaps": {
            "type": "array",
            "items": {"type": "string"}
          }
        }
      }
    },
    
    {
      "phase_id": "analysis",
      "phase_number": 3,
      "phase_name": "Muster-Analyse",
      "description": "Erkenne Muster, Konflikte, Anomalien in Evidence",
      
      "dependencies": {
        "requires_phases": ["synthesis"],
        "requires_data": ["synthesis_output"]
      },
      
      "execution": {
        "type": "llm_call",
        "model": "llama3.1:latest",
        "temperature": 0.3,
        "max_tokens": 2000,
        "timeout_seconds": 45
      },
      
      "prompt_construction": {
        "template_file": "prompts/scientific/phase3_analysis.txt",
        "input_mapping": {
          "evidence_clusters": "phases.synthesis.output.evidence_clusters"
        },
        "context_inclusion": {
          "scientific_foundation": true,
          "previous_phases": ["hypothesis", "synthesis"]
        }
      },
      
      "output_schema": {
        "type": "object",
        "required": ["patterns", "conflicts", "anomalies"],
        "properties": {
          "patterns": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "type": {"type": "string"},
                "description": {"type": "string"},
                "evidence": {"type": "array"},
                "confidence": {"type": "number"}
              }
            }
          },
          "conflicts": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "type": {"type": "string"},
                "sources": {"type": "array"},
                "resolution": {"type": "object"}
              }
            }
          },
          "anomalies": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "description": {"type": "string"},
                "impact": {"type": "string"},
                "recommendation": {"type": "string"}
              }
            }
          }
        }
      }
    },
    
    {
      "phase_id": "validation",
      "phase_number": 4,
      "phase_name": "Hypothesen-Validierung",
      "description": "Teste Hypothese gegen Evidence, update Confidence",
      
      "dependencies": {
        "requires_phases": ["hypothesis", "synthesis", "analysis"],
        "requires_data": ["hypothesis_output", "synthesis_output", "analysis_output"]
      },
      
      "execution": {
        "type": "llm_call",
        "model": "llama3.1:latest",
        "temperature": 0.2,
        "max_tokens": 1500,
        "timeout_seconds": 40
      },
      
      "prompt_construction": {
        "template_file": "prompts/scientific/phase4_validation.txt",
        "input_mapping": {
          "hypothesis": "phases.hypothesis.output",
          "synthesis": "phases.synthesis.output",
          "analysis": "phases.analysis.output"
        },
        "context_inclusion": {
          "scientific_foundation": true,
          "previous_phases": ["hypothesis", "synthesis", "analysis"]
        }
      },
      
      "output_schema": {
        "type": "object",
        "required": ["hypothesis_test", "validation_checks"],
        "properties": {
          "hypothesis_test": {
            "type": "object",
            "properties": {
              "original": {"type": "string"},
              "result": {"type": "string", "enum": ["CONFIRMED", "PARTIALLY_CONFIRMED", "REJECTED"]},
              "refined": {"type": "string"},
              "evidence_score": {
                "type": "object",
                "properties": {
                  "supporting": {"type": "number"},
                  "contradicting": {"type": "number"},
                  "neutral": {"type": "number"}
                }
              },
              "confidence_change": {
                "type": "object",
                "properties": {
                  "before": {"type": "number"},
                  "after": {"type": "number"},
                  "reason": {"type": "string"}
                }
              }
            }
          },
          "validation_checks": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "criterion": {"type": "string"},
                "status": {"type": "string", "enum": ["VALIDATED", "NEEDS_USER_INPUT", "FAILED"]},
                "evidence": {"type": "string"},
                "confidence": {"type": "number"}
              }
            }
          }
        }
      }
    },
    
    {
      "phase_id": "conclusion",
      "phase_number": 5,
      "phase_name": "Schlussfolgerung",
      "description": "Finale Antwort-Generierung mit allen wissenschaftlichen Schritten",
      
      "dependencies": {
        "requires_phases": ["validation"],
        "requires_data": ["validation_output", "synthesis_output", "analysis_output"]
      },
      
      "execution": {
        "type": "llm_call",
        "model": "llama3.1:latest",
        "temperature": 0.3,
        "max_tokens": 4000,
        "timeout_seconds": 60
      },
      
      "prompt_construction": {
        "template_file": "prompts/scientific/phase5_conclusion.txt",
        "input_mapping": {
          "validation": "phases.validation.output",
          "synthesis": "phases.synthesis.output",
          "analysis": "phases.analysis.output"
        },
        "context_inclusion": {
          "scientific_foundation": true,
          "previous_phases": ["hypothesis", "synthesis", "analysis", "validation"]
        }
      },
      
      "output_schema": {
        "type": "object",
        "required": ["conclusion", "conditions", "next_steps"],
        "properties": {
          "conclusion": {
            "type": "object",
            "properties": {
              "main_answer": {"type": "string"},
              "confidence": {"type": "number"},
              "certainty_level": {"type": "string", "enum": ["HIGH", "MEDIUM", "LOW"]},
              "sources": {"type": "array"}
            }
          },
          "conditions": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "type": {"type": "string"},
                "description": {"type": "string"},
                "legal_basis": {"type": "string"},
                "user_action_required": {"type": "boolean"}
              }
            }
          },
          "next_steps": {
            "type": "array",
            "items": {"type": "string"}
          }
        }
      }
    },
    
    {
      "phase_id": "metacognition",
      "phase_number": 6,
      "phase_name": "Selbstreflexion",
      "description": "Bewerte Reasoning Quality, identifiziere Unsicherheiten",
      
      "dependencies": {
        "requires_phases": ["conclusion"],
        "requires_data": ["all_phases_output"]
      },
      
      "execution": {
        "type": "llm_call",
        "model": "llama3.1:latest",
        "temperature": 0.2,
        "max_tokens": 2000,
        "timeout_seconds": 45
      },
      
      "prompt_construction": {
        "template_file": "prompts/scientific/phase6_metacognition.txt",
        "input_mapping": {
          "all_phases": "phases"
        },
        "context_inclusion": {
          "scientific_foundation": true,
          "previous_phases": ["hypothesis", "synthesis", "analysis", "validation", "conclusion"]
        }
      },
      
      "output_schema": {
        "type": "object",
        "required": ["metacognitive_assessment", "quality_metrics"],
        "properties": {
          "metacognitive_assessment": {
            "type": "object",
            "properties": {
              "overall_confidence": {"type": "number"},
              "reasoning_quality": {
                "type": "object",
                "properties": {
                  "evidence_strength": {"type": "number"},
                  "source_diversity": {"type": "number"},
                  "logical_consistency": {"type": "number"},
                  "completeness": {"type": "number"}
                }
              },
              "uncertainty_sources": {"type": "array"},
              "knowledge_gaps": {"type": "array"},
              "improvement_suggestions": {"type": "array"}
            }
          },
          "quality_metrics": {
            "type": "object",
            "properties": {
              "answer_completeness": {"type": "number"},
              "answer_accuracy": {"type": "number"},
              "answer_relevance": {"type": "number"},
              "user_actionability": {"type": "number"}
            }
          }
        }
      }
    }
  ],
  
  "orchestration_config": {
    "parallel_execution": {
      "enabled": true,
      "max_parallel_phases": 2,
      "parallel_groups": [
        {
          "group_id": "evidence_gathering",
          "phases": ["synthesis", "rag_retrieval"],
          "description": "Kann parallel laufen"
        }
      ]
    },
    
    "error_handling": {
      "phase_failure_strategy": "continue_with_warning",
      "critical_phases": ["hypothesis", "validation", "conclusion"],
      "optional_phases": ["metacognition"]
    },
    
    "streaming": {
      "enabled": true,
      "stream_phase_start": true,
      "stream_phase_complete": true,
      "stream_intermediate_results": false
    }
  }
}
```

---

### 2. Base Prompt Templates (JSON-basiert)

**Datei:** `config/prompts/scientific_foundation.json`

```json
{
  "scientific_foundation": {
    "version": "1.0.0",
    "last_updated": "2025-10-12T21:30:00Z",
    "improvement_iteration": 1,
    
    "core_principles": {
      "title": "Wissenschaftliche Grundprinzipien",
      "description": "Du bist ein wissenschaftlicher Assistent...",
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
        },
        ...
      ]
    },
    
    "scientific_method": {
      "title": "Die 6 Schritte wissenschaftlichen Arbeitens",
      "steps": [
        {
          "step_number": 1,
          "step_id": "hypothesis",
          "name": "HYPOTHESE",
          "purpose": "Formuliere eine erste Vermutung...",
          "key_question": "Was vermute ich basierend auf den RAG-Ergebnissen?"
        },
        ...
      ]
    },
    
    "source_quality_hierarchy": {
      "levels": [
        {
          "level": 1,
          "source_type": "gesetz",
          "confidence_range": [0.95, 1.0],
          "authority": "highest"
        },
        ...
      ],
      "conflict_resolution_rules": [...]
    },
    
    "prompt_improvement": {
      "improvement_metrics": [
        {
          "metric_id": "json_validity_rate",
          "target": 0.98,
          "current": null,
          "improvement_actions": [...]
        }
      ],
      "feedback_integration": {...},
      "version_history": [...]
    }
  }
}
```

**Vorteile:**
- ✅ **Versionierbar:** version_history tracked
- ✅ **Iterativ verbessert:** improvement_metrics + feedback_integration
- ✅ **Strukturiert:** Maschinenlesbar
- ✅ **LLM-optimierbar:** Automatisches Prompt-Tuning

---

**Datei:** `config/prompts/scientific/user_query_enhancement.txt`

```text
# USER QUERY ENHANCEMENT

Original Query: {{user_query}}

Detected Domain: {{detected_domain}}
Estimated Complexity: {{complexity_estimate}}

---

## Wissenschaftliche Fragestellung

Die Nutzer-Frage wird nun im wissenschaftlichen Kontext bearbeitet:

**Kernanliegen:** {{user_query}}

**Wissenschaftliche Zielsetzung:**
- Evidenzbasierte Beantwortung
- Identifikation fehlender Informationen
- Strukturierte Schlussfolgerung mit Handlungsempfehlungen

**Verfügbare Ressourcen:**
- RAG-System: Semantische Suche + Graph-basierte Prozess-Navigation
- Domain-Agents: {{available_agents}}
- Datenbanken: PostgreSQL, Neo4j, ChromaDB, CouchDB

Beginne mit Phase 1: Hypothesengenerierung.
```

---

**Datei:** `config/prompts/scientific/phase1_hypothesis.txt`

```text
# PHASE 1: HYPOTHESENGENERIERUNG

{{scientific_foundation}}

---

## Aufgabe

Basierend auf der Nutzer-Frage und den RAG-Ergebnissen, erstelle eine **erste wissenschaftliche Hypothese**.

### User Query
{{user_query}}

### RAG-Kontext (Verfügbare Evidenzen)

{{rag_results}}

---

## Deine Aufgabe

1. **Formuliere eine Hypothese:** Was ist deine erste Vermutung zur Beantwortung der Frage?

2. **Identifiziere Prüfkriterien:** Welche konkreten Kriterien müssen geprüft werden, um die Frage zu beantworten?

3. **Erkenne fehlende Informationen:** Was fehlt noch (Nutzer-Input, Daten, Kontext)?

4. **Schätze Confidence:** Wie sicher bist du basierend auf den verfügbaren Informationen? (0.0-1.0)

5. **Begründe deine Hypothese:** Warum kommst du zu dieser Vermutung?

---

## Output Format (JSON)

```json
{
  "hypothesis": "Deine Vermutung (1-2 Sätze)",
  "required_criteria": [
    "Kriterium 1 (konkret, prüfbar)",
    "Kriterium 2",
    "..."
  ],
  "missing_information": [
    "Fehlende Info 1 (z.B. 'Bundesland nicht angegeben')",
    "Fehlende Info 2",
    "..."
  ],
  "confidence": 0.65,
  "reasoning": "Begründung: Warum diese Hypothese? Welche RAG-Ergebnisse unterstützen sie?"
}
```

**Wichtig:**
- `required_criteria`: Mind. 1 Kriterium (konkret benennbar)
- `confidence`: 0.0-1.0 (niedrig bei vielen fehlenden Infos)
- `reasoning`: Referenziere konkrete RAG-Ergebnisse

Antworte NUR mit dem JSON-Output.
```

---

**Datei:** `config/prompts/scientific/phase2_synthesis.txt`

```text
# PHASE 2: EVIDENZ-SYNTHESE

{{scientific_foundation}}

---

## Kontext: Bisheriger Prozess

### Phase 1: Hypothese
{{phases.hypothesis.output}}

---

## Aufgabe

Basierend auf der Hypothese und den RAG-Ergebnissen, **aggregiere und verknüpfe alle Evidenzen**.

### RAG-Ergebnisse
{{rag_results}}

---

## Deine Aufgabe

1. **Clustere Evidenzen nach Themen:** Gruppiere RAG-Ergebnisse nach den `required_criteria` aus der Hypothese

2. **Erkenne Cross-References:** Finde Verweise zwischen Dokumenten (z.B. "siehe § 50 LBO", "vgl. § 35 BauGB")

3. **Synthetisiere pro Cluster:** Fasse jedes Thema in 1-2 Sätzen zusammen

4. **Bewerte Cluster-Stärke:** Wie stark sind die Evidenzen? (Anzahl Quellen + Quellenqualität)

5. **Identifiziere Gaps:** Welche Themen aus der Hypothese haben KEINE Evidenzen?

---

## Output Format (JSON)

```json
{
  "evidence_clusters": [
    {
      "theme": "Thema 1 (z.B. 'Verfahrensfreiheit Baden-Württemberg')",
      "sources": [
        {
          "source": "LBO BW § 50 Abs. 1",
          "content": "Bis 30m² ohne Aufenthaltsräume frei",
          "confidence": 0.95,
          "contradicts": [],
          "supports": []
        }
      ],
      "synthesis": "Zusammenfassung des Themas (1-2 Sätze)",
      "strength": 0.92
    }
  ],
  "cross_references": [
    {
      "source1": "LBO BW § 50",
      "source2": "VGH Mannheim 3 S 2543/19",
      "relationship": "supporting",
      "strength": 0.85
    }
  ],
  "gaps": [
    "Kein Ergebnis zu: Sonderfall Grenzgarage",
    "..."
  ]
}
```

Antworte NUR mit dem JSON-Output.
```

---

**Datei:** `config/prompts/scientific/phase5_conclusion.txt`

```text
# PHASE 5: SCHLUSSFOLGERUNG

{{scientific_foundation}}

---

## Wissenschaftlicher Prozess (bisher)

### Phase 1: Hypothese
{{phases.hypothesis.output}}

### Phase 2: Synthese
{{phases.synthesis.output}}

### Phase 3: Analyse
{{phases.analysis.output}}

### Phase 4: Validation
{{phases.validation.output}}

---

## Aufgabe

Basierend auf dem **vollständigen wissenschaftlichen Prozess**, formuliere eine **gesicherte Schlussfolgerung**.

---

## Deine Aufgabe

1. **Hauptantwort:** Beantworte die ursprüngliche Nutzer-Frage klar und präzise

2. **Confidence & Certainty:** Wie sicher ist die Antwort nach Validation? (HIGH/MEDIUM/LOW)

3. **Quellen:** Liste die wichtigsten Evidenzen auf

4. **Bedingungen:** Welche Voraussetzungen muss der Nutzer erfüllen?

5. **Nächste Schritte:** Was soll der Nutzer konkret tun?

---

## Output Format (JSON)

```json
{
  "conclusion": {
    "main_answer": "Die Antwort auf die Nutzer-Frage (2-4 Sätze, präzise)",
    "confidence": 0.90,
    "certainty_level": "HIGH",
    "sources": [
      "LBO BW § 50 Abs. 1 (Verfahrensfreiheit)",
      "LBO BW § 5 Abs. 1 (Abstandsflächen)",
      "VGH Mannheim 3 S 2543/19 (Carport = Gebäude)"
    ]
  },
  "conditions": [
    {
      "type": "size_limit",
      "description": "Carport muss <30m² sein",
      "legal_basis": "LBO BW § 50 Abs. 1",
      "user_action_required": true,
      "form_question": "Wie groß ist Ihr geplanter Carport? (m²)"
    }
  ],
  "next_steps": [
    "1. Carport-Größe prüfen (Formular ausfüllen)",
    "2. Abstandsflächen prüfen (mind. 2,5m zu Nachbargrenze)",
    "3. Falls alle Bedingungen erfüllt: Bauanzeige statt Antrag"
  ]
}
```

**Wichtig:**
- `main_answer`: Direkte Antwort auf ursprüngliche Frage
- `conditions`: Nur relevante Bedingungen (max. 5)
- `next_steps`: Konkrete Handlungsschritte für Nutzer

Antworte NUR mit dem JSON-Output.
```

---

## 🔧 Generic Scientific Phase Executor

**Datei:** `backend/services/scientific_phase_executor.py` (~400 LOC)

```python
#!/usr/bin/env python3
"""
GENERIC SCIENTIFIC PHASE EXECUTOR
==================================

JSON-driven Execution von wissenschaftlichen Phasen

Author: VERITAS System
Version: 1.0
"""

import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from dataclasses import dataclass
from jinja2 import Template

logger = logging.getLogger(__name__)

@dataclass
class PhaseExecutionContext:
    """Kontext für Phase-Execution"""
    user_query: str
    rag_results: Dict
    previous_phases: Dict[str, Dict]  # {phase_id: output}
    agent_results: Optional[Dict] = None

class ScientificPhaseExecutor:
    """
    Generic Executor für wissenschaftliche Phasen
    
    CONFIGURATION-DRIVEN:
    - Lädt Phase-Config aus JSON
    - Konstruiert Prompts via Jinja2 Templates
    - Ruft LLM mit Config-Parameters
    - Validiert Output gegen JSON Schema
    """
    
    def __init__(
        self,
        method_config_path: str,
        prompts_dir: str,
        ollama_client
    ):
        """
        Args:
            method_config_path: Pfad zu scientific_method.json
            prompts_dir: Verzeichnis mit Prompt-Templates
            ollama_client: OllamaClient für LLM Calls
        """
        self.method_config_path = method_config_path
        self.prompts_dir = Path(prompts_dir)
        self.ollama_client = ollama_client
        
        # Load Scientific Method Config
        with open(method_config_path, 'r', encoding='utf-8') as f:
            self.method_config = json.load(f)
        
        # Load Base Prompts
        self.base_prompts = self._load_base_prompts()
        
        logger.info(f"✅ Scientific Method loaded: {self.method_config['method_id']}")
        logger.info(f"📋 Phases: {len(self.method_config['phases'])}")
    
    def _load_base_prompts(self) -> Dict[str, str]:
        """Lade Base Prompts (scientific_foundation, user_query_enhancement)"""
        base_prompts = {}
        
        for prompt_id, prompt_config in self.method_config["base_prompts"].items():
            template_file = prompt_config["template_file"]
            template_path = self.prompts_dir / template_file
            
            if template_path.exists():
                with open(template_path, 'r', encoding='utf-8') as f:
                    base_prompts[prompt_id] = f.read()
                logger.info(f"  ✅ Loaded base prompt: {prompt_id}")
            else:
                logger.warning(f"  ⚠️ Base prompt not found: {template_path}")
        
        return base_prompts
    
    async def execute_phase(
        self,
        phase_id: str,
        context: PhaseExecutionContext
    ) -> Dict[str, Any]:
        """
        Execute eine wissenschaftliche Phase
        
        Args:
            phase_id: ID der Phase (z.B. "hypothesis", "synthesis")
            context: Execution Context (Query, RAG, Previous Phases)
        
        Returns:
            {
                "phase_id": "hypothesis",
                "status": "success",
                "output": {...},  # JSON gemäß output_schema
                "execution_time": 1.234,
                "llm_tokens": 850
            }
        """
        
        # 1. Get Phase Config
        phase_config = self._get_phase_config(phase_id)
        if not phase_config:
            raise ValueError(f"Phase '{phase_id}' not found in method config")
        
        # 2. Check Dependencies
        self._check_dependencies(phase_config, context)
        
        # 3. Construct Prompt
        prompt = await self._construct_prompt(phase_config, context)
        
        # 4. Execute LLM Call
        llm_response = await self._execute_llm_call(phase_config, prompt)
        
        # 5. Parse & Validate Output
        output = self._parse_and_validate_output(phase_config, llm_response)
        
        # 6. Return Result
        return {
            "phase_id": phase_id,
            "status": "success",
            "output": output,
            "execution_time": llm_response.get("execution_time", 0),
            "llm_tokens": llm_response.get("tokens_used", 0)
        }
    
    def _get_phase_config(self, phase_id: str) -> Optional[Dict]:
        """Finde Phase Config by ID"""
        for phase in self.method_config["phases"]:
            if phase["phase_id"] == phase_id:
                return phase
        return None
    
    def _check_dependencies(
        self,
        phase_config: Dict,
        context: PhaseExecutionContext
    ):
        """Check ob required phases bereits executed sind"""
        required_phases = phase_config["dependencies"]["requires_phases"]
        
        for required_phase_id in required_phases:
            if required_phase_id not in context.previous_phases:
                raise ValueError(
                    f"Phase '{phase_config['phase_id']}' requires '{required_phase_id}' "
                    f"but it has not been executed yet"
                )
    
    async def _construct_prompt(
        self,
        phase_config: Dict,
        context: PhaseExecutionContext
    ) -> str:
        """
        Konstruiere Prompt via Jinja2 Template
        
        Schritte:
        1. Load Phase Template (z.B. phase1_hypothesis.txt)
        2. Include Base Prompts (scientific_foundation)
        3. Map Input Variables (user_query, rag_results, previous_phases)
        4. Render Jinja2 Template
        """
        
        prompt_config = phase_config["prompt_construction"]
        
        # 1. Load Template
        template_file = prompt_config["template_file"]
        template_path = self.prompts_dir / template_file
        
        if not template_path.exists():
            raise FileNotFoundError(f"Prompt template not found: {template_path}")
        
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # 2. Prepare Template Variables
        template_vars = {}
        
        # Include Base Prompts
        if prompt_config["context_inclusion"]["scientific_foundation"]:
            template_vars["scientific_foundation"] = self.base_prompts.get("scientific_foundation", "")
        
        # Include Previous Phases
        if prompt_config["context_inclusion"]["previous_phases"]:
            template_vars["phases"] = {}
            for prev_phase_id in prompt_config["context_inclusion"]["previous_phases"]:
                if prev_phase_id in context.previous_phases:
                    template_vars["phases"][prev_phase_id] = context.previous_phases[prev_phase_id]
        
        # Map Input Variables
        input_mapping = prompt_config["input_mapping"]
        for template_var, data_path in input_mapping.items():
            # Resolve data path (z.B. "phases.hypothesis.output")
            value = self._resolve_data_path(data_path, context)
            template_vars[template_var] = value
        
        # 3. Render Template
        template = Template(template_content)
        prompt = template.render(**template_vars)
        
        return prompt
    
    def _resolve_data_path(self, data_path: str, context: PhaseExecutionContext) -> Any:
        """
        Resolve data path like "phases.hypothesis.output" to actual value
        
        Supported paths:
        - "query_text" → context.user_query
        - "rag_context" → context.rag_results
        - "phases.{phase_id}.output" → context.previous_phases[phase_id]["output"]
        """
        
        if data_path == "query_text":
            return context.user_query
        
        elif data_path == "rag_context":
            return json.dumps(context.rag_results, indent=2, ensure_ascii=False)
        
        elif data_path.startswith("phases."):
            # Extract phase_id and field
            parts = data_path.split(".")
            phase_id = parts[1]
            field = ".".join(parts[2:]) if len(parts) > 2 else "output"
            
            if phase_id in context.previous_phases:
                phase_data = context.previous_phases[phase_id]
                
                # Navigate nested dict
                current = phase_data
                for key in field.split("."):
                    if isinstance(current, dict) and key in current:
                        current = current[key]
                    else:
                        return None
                
                # Convert to JSON if dict/list
                if isinstance(current, (dict, list)):
                    return json.dumps(current, indent=2, ensure_ascii=False)
                else:
                    return current
        
        return None
    
    async def _execute_llm_call(
        self,
        phase_config: Dict,
        prompt: str
    ) -> Dict:
        """Execute LLM Call mit Config-Parameters"""
        
        execution_config = phase_config["execution"]
        
        # LLM Call via Ollama Client
        response = await self.ollama_client.generate(
            prompt=prompt,
            model=execution_config["model"],
            temperature=execution_config["temperature"],
            max_tokens=execution_config["max_tokens"],
            timeout=execution_config.get("timeout_seconds", 60)
        )
        
        return response
    
    def _parse_and_validate_output(
        self,
        phase_config: Dict,
        llm_response: Dict
    ) -> Dict:
        """
        Parse LLM Response (JSON) und validiere gegen Schema
        
        Schritte:
        1. Extract JSON from LLM response
        2. Parse JSON
        3. Validate against output_schema (jsonschema)
        4. Apply validation_rules
        """
        
        # 1. Extract JSON (LLM response ist plain text)
        response_text = llm_response.get("response", "")
        
        # Find JSON in response (zwischen ```json und ```)
        import re
        json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Fallback: Assume entire response is JSON
            json_str = response_text.strip()
        
        # 2. Parse JSON
        try:
            output = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON Parse Error: {e}")
            logger.error(f"Response: {response_text[:500]}")
            raise ValueError(f"LLM did not return valid JSON: {e}")
        
        # 3. Validate against output_schema
        output_schema = phase_config["output_schema"]
        self._validate_schema(output, output_schema)
        
        # 4. Apply validation_rules
        if "validation_rules" in phase_config:
            self._apply_validation_rules(output, phase_config["validation_rules"])
        
        return output
    
    def _validate_schema(self, output: Dict, schema: Dict):
        """Validate output against JSON Schema (simple implementation)"""
        
        # Check required fields
        if "required" in schema:
            for field in schema["required"]:
                if field not in output:
                    raise ValueError(f"Required field '{field}' missing in output")
        
        # Check properties (type validation)
        if "properties" in schema:
            for field, field_schema in schema["properties"].items():
                if field in output:
                    value = output[field]
                    expected_type = field_schema.get("type")
                    
                    # Simple type check
                    if expected_type == "string" and not isinstance(value, str):
                        raise ValueError(f"Field '{field}' must be string, got {type(value)}")
                    elif expected_type == "number" and not isinstance(value, (int, float)):
                        raise ValueError(f"Field '{field}' must be number, got {type(value)}")
                    elif expected_type == "array" and not isinstance(value, list):
                        raise ValueError(f"Field '{field}' must be array, got {type(value)}")
                    elif expected_type == "object" and not isinstance(value, dict):
                        raise ValueError(f"Field '{field}' must be object, got {type(value)}")
    
    def _apply_validation_rules(self, output: Dict, rules: List[Dict]):
        """Apply custom validation rules"""
        
        for rule in rules:
            rule_type = rule["rule"]
            field = rule["field"]
            
            if rule_type == "confidence_in_range":
                value = output.get(field)
                if value is not None:
                    if not (rule["min"] <= value <= rule["max"]):
                        raise ValueError(
                            f"Field '{field}' must be in range [{rule['min']}, {rule['max']}], "
                            f"got {value}"
                        )
            
            elif rule_type == "required_criteria_not_empty":
                value = output.get(field, [])
                min_items = rule.get("min_items", 1)
                if len(value) < min_items:
                    raise ValueError(
                        f"Field '{field}' must have at least {min_items} items, "
                        f"got {len(value)}"
                    )
```

---

## 🎯 Integration: Unified Orchestrator + Scientific Method

**Datei:** `backend/services/unified_orchestrator_v7.py` (~500 LOC)

```python
#!/usr/bin/env python3
"""
UNIFIED ORCHESTRATOR v7.0
=========================

JSON-basierte wissenschaftliche Methodik + Agent-Integration

Author: VERITAS System
Version: 7.0 (Configuration-Driven)
"""

import logging
from typing import Dict, Any, List
from pathlib import Path

from backend.services.scientific_phase_executor import (
    ScientificPhaseExecutor,
    PhaseExecutionContext
)
from backend.agents.veritas_api_agent_orchestrator import AgentOrchestrator

logger = logging.getLogger(__name__)

class UnifiedOrchestratorV7:
    """
    Unified Orchestrator mit JSON-basierter wissenschaftlicher Methodik
    
    ARCHITEKTUR:
    1. Load Scientific Method Config (JSON)
    2. Enhance User Query mit Base Prompt
    3. Execute Scientific Phases (Generic Executor)
    4. Coordinate Agent Tasks (Parallel)
    5. Aggregate Results
    """
    
    def __init__(
        self,
        method_config_path: str,
        prompts_dir: str,
        ollama_client,
        agent_orchestrator: AgentOrchestrator,
        rag_service
    ):
        """
        Args:
            method_config_path: Pfad zu scientific_method.json
            prompts_dir: Verzeichnis mit Prompt-Templates
            ollama_client: Ollama Client für LLM Calls
            agent_orchestrator: Existing Agent Orchestrator
            rag_service: RAG Service für semantic/graph search
        """
        
        self.scientific_executor = ScientificPhaseExecutor(
            method_config_path=method_config_path,
            prompts_dir=prompts_dir,
            ollama_client=ollama_client
        )
        
        self.agent_orchestrator = agent_orchestrator
        self.rag_service = rag_service
        self.ollama_client = ollama_client
        
        logger.info("✅ Unified Orchestrator v7.0 initialized (Configuration-Driven)")
    
    async def process_query(self, user_query: str, user_id: str) -> Dict[str, Any]:
        """
        Main Entry Point: Process User Query mit wissenschaftlicher Methodik
        
        Returns:
            {
                "query": "...",
                "scientific_process": {
                    "hypothesis": {...},
                    "synthesis": {...},
                    "analysis": {...},
                    "validation": {...},
                    "conclusion": {...},
                    "metacognition": {...}
                },
                "agent_results": {...},
                "final_answer": "...",
                "confidence": 0.90
            }
        """
        
        logger.info(f"🔬 Processing Query (Scientific Method): {user_query}")
        
        # Step 1: NLP Preprocessing (existing)
        nlp_result = await self._nlp_preprocessing(user_query)
        
        # Step 2: RAG Retrieval (parallel: semantic + graph)
        rag_results = await self._rag_retrieval(user_query, nlp_result)
        
        # Step 3: Enhance User Query with Base Prompt
        enhanced_query = self._enhance_user_query(user_query, nlp_result)
        
        # Step 4: Initialize Execution Context
        context = PhaseExecutionContext(
            user_query=enhanced_query,
            rag_results=rag_results,
            previous_phases={}
        )
        
        # Step 5: Execute Scientific Phases (Sequential with Dependencies)
        scientific_results = {}
        
        phases_to_execute = [
            "hypothesis",
            "synthesis",
            "analysis",
            "validation",
            "conclusion",
            "metacognition"
        ]
        
        for phase_id in phases_to_execute:
            logger.info(f"  🔬 Executing Phase: {phase_id}")
            
            phase_result = await self.scientific_executor.execute_phase(
                phase_id=phase_id,
                context=context
            )
            
            scientific_results[phase_id] = phase_result
            
            # Update context for next phase
            context.previous_phases[phase_id] = phase_result
            
            logger.info(f"  ✅ Phase '{phase_id}' completed in {phase_result['execution_time']:.2f}s")
        
        # Step 6: Coordinate Agent Tasks (Parallel wenn möglich)
        agent_results = await self._coordinate_agents(
            user_query,
            nlp_result,
            scientific_results
        )
        
        # Step 7: Final Response
        return {
            "query": user_query,
            "scientific_process": {
                phase_id: result["output"]
                for phase_id, result in scientific_results.items()
            },
            "agent_results": agent_results,
            "final_answer": scientific_results["conclusion"]["output"]["conclusion"]["main_answer"],
            "confidence": scientific_results["metacognition"]["output"]["metacognitive_assessment"]["overall_confidence"],
            "quality_metrics": scientific_results["metacognition"]["output"]["quality_metrics"]
        }
    
    def _enhance_user_query(self, user_query: str, nlp_result: Dict) -> str:
        """Enhance User Query mit Base Prompt (user_query_enhancement.txt)"""
        
        # Load enhancement template
        enhancement_template = self.scientific_executor.base_prompts.get("user_query_enhancement", "")
        
        # Render with Jinja2
        from jinja2 import Template
        template = Template(enhancement_template)
        
        enhanced = template.render(
            user_query=user_query,
            detected_domain=nlp_result.get("domain", "general"),
            complexity_estimate=nlp_result.get("complexity", "medium"),
            available_agents=["Environmental", "Database", "Transport", "Health"]
        )
        
        return enhanced
    
    async def _coordinate_agents(
        self,
        user_query: str,
        nlp_result: Dict,
        scientific_results: Dict
    ) -> Dict:
        """
        Coordinate Agent Tasks basierend auf Scientific Results
        
        Strategie:
        - Hypothesis identifiziert required_criteria
        - Für jedes Criterion: Prüfe ob Domain-Agent benötigt
        - Dispatch Agents parallel
        """
        
        hypothesis = scientific_results["hypothesis"]["output"]
        required_criteria = hypothesis.get("required_criteria", [])
        
        # Determine which agents to call
        agents_to_call = self._determine_required_agents(required_criteria, nlp_result)
        
        # Dispatch agents (via existing AgentOrchestrator)
        agent_results = {}
        for agent_type in agents_to_call:
            logger.info(f"  🤖 Dispatching Agent: {agent_type}")
            
            # Create agent task via AgentOrchestrator
            result = await self.agent_orchestrator.execute_agent_task(
                agent_type=agent_type,
                query=user_query,
                context={
                    "hypothesis": hypothesis,
                    "nlp_result": nlp_result
                }
            )
            
            agent_results[agent_type] = result
        
        return agent_results
    
    def _determine_required_agents(
        self,
        required_criteria: List[str],
        nlp_result: Dict
    ) -> List[str]:
        """Determine which agents are needed based on criteria"""
        
        agents = []
        
        # Domain detection (keywords)
        domain = nlp_result.get("domain", "general")
        
        if domain == "environmental" or any("umwelt" in c.lower() for c in required_criteria):
            agents.append("environmental")
        
        if domain == "transport" or any("verkehr" in c.lower() for c in required_criteria):
            agents.append("transport")
        
        # Always call database agent (for structured data)
        agents.append("database")
        
        return agents
```

---

## 📊 Implementation Roadmap: v7.0 (JSON-Driven)

### Phase 1: JSON Configuration Setup (2-3 Tage, 600 LOC)

**Files:**
- `config/scientific_methods/default_method.json` (~400 lines JSON)
- `config/prompts/scientific/scientific_foundation.txt` (~50 lines)
- `config/prompts/scientific/user_query_enhancement.txt` (~30 lines)
- `config/prompts/scientific/phase1_hypothesis.txt` (~60 lines)
- `config/prompts/scientific/phase2_synthesis.txt` (~70 lines)
- `config/prompts/scientific/phase3_analysis.txt` (~70 lines)
- `config/prompts/scientific/phase4_validation.txt` (~70 lines)
- `config/prompts/scientific/phase5_conclusion.txt` (~80 lines)
- `config/prompts/scientific/phase6_metacognition.txt` (~70 lines)

**Tasks:**
- [ ] Create directory structure `config/scientific_methods/`, `config/prompts/scientific/`
- [ ] Write `default_method.json` mit 6 Phasen
- [ ] Write Base Prompts (scientific_foundation, user_query_enhancement)
- [ ] Write Phase Prompts (1-6) mit Jinja2 Templates
- [ ] Validate JSON Schema (jsonschema library)

---

### Phase 2: Generic Scientific Phase Executor (3-4 Tage, 400 LOC)

**File:** `backend/services/scientific_phase_executor.py`

**Tasks:**
- [ ] `ScientificPhaseExecutor` Klasse
- [ ] `_load_base_prompts()` - Load scientific_foundation etc.
- [ ] `execute_phase()` - Main execution method
- [ ] `_construct_prompt()` - Jinja2 Template Rendering
- [ ] `_resolve_data_path()` - Resolve "phases.hypothesis.output"
- [ ] `_execute_llm_call()` - LLM Call mit Config-Parameters
- [ ] `_parse_and_validate_output()` - JSON Parsing + Schema Validation
- [ ] `_validate_schema()` - JSON Schema Validation
- [ ] `_apply_validation_rules()` - Custom Rules (confidence_in_range)

---

### Phase 3: Unified Orchestrator v7.0 (3-4 Tage, 500 LOC)

**File:** `backend/services/unified_orchestrator_v7.py`

**Tasks:**
- [ ] `UnifiedOrchestratorV7` Klasse
- [ ] `process_query()` - Main Entry Point
- [ ] `_enhance_user_query()` - Base Prompt Enhancement
- [ ] `_coordinate_agents()` - Agent Dispatch basierend auf Hypothesis
- [ ] `_determine_required_agents()` - Agent Selection Logic
- [ ] Integration mit `AgentOrchestrator` (existing)
- [ ] Integration mit `RAGService` (existing)

---

### Phase 4: Testing & Refinement (3-4 Tage, 800 LOC)

**Tasks:**
- [ ] Unit Tests für `ScientificPhaseExecutor` (~200 LOC)
- [ ] Integration Tests für `UnifiedOrchestratorV7` (~200 LOC)
- [ ] End-to-End Test: "Carport Baugenehmigung" Query (~100 LOC)
- [ ] Prompt Refinement (basierend auf Test-Ergebnissen)
- [ ] JSON Schema Validation Tests (~100 LOC)
- [ ] Documentation (~200 lines)

---

### Total v7.0 Implementation

| Component | LOC/Lines | Timeline |
|-----------|-----------|----------|
| **JSON Configs + Prompts** | ~600 lines | 2-3 Tage |
| **ScientificPhaseExecutor** | ~400 LOC | 3-4 Tage |
| **UnifiedOrchestratorV7** | ~500 LOC | 3-4 Tage |
| **Tests + Docs** | ~800 LOC | 3-4 Tage |
| **Total** | **~2,300 LOC** | **11-15 Tage** |

---

## 🎯 Benefits: v7.0 vs. v5.0/v6.0

| Metric | v5.0/v6.0 (Hard-Coded) | v7.0 (JSON-Driven + Self-Improving) | Improvement |
|--------|------------------------|-------------------------------------|-------------| 
| **Code Complexity** | 10,500-13,900 LOC | **~2,300 LOC** | **-78-83%** |
| **Flexibility** | ❌ Code-Änderungen nötig | ✅ JSON-Config ändern | ✅ |
| **LLM Optimization** | ❌ Nicht möglich | ✅ Prompts + Ablauf anpassbar | ✅ |
| **Self-Improvement** | ❌ Keine | ✅ **Automatische Iteration (10 Queries)** | ✅ |
| **Versioning** | ❌ Git-only | ✅ version_history + Metrics | ✅ |
| **Quality Metrics** | ❌ Keine | ✅ **4 Metrics tracked** | ✅ |
| **Orchestrator-Integration** | ❌ Separate Systems | ✅ Einheitliches Pattern (DYNAMIC_BLUEPRINTS) | ✅ |
| **Implementierungszeit** | 30-40 Tage | **11-15 Tage** | **-63-73%** |
| **Wartbarkeit** | ❌ Viele Python-Services | ✅ JSON + Generic Executor | ✅ |
| **Prompt-Tuning** | ❌ Manuell | ✅ **Metrics-driven Auto-Improvement** | ✅ |

### 🔄 **NEU: Selbstverbesserungsmechanismus**

```
Query 1-10 (v1.0.0) → Metrics: Confidence Error 22%
                    → Analysis: Target 15%, Gap 7%
                    → Apply Improvements → v1.1.0
                    
Query 11-20 (v1.1.0) → Metrics: Confidence Error 13% ✅
                     → Quality Score: 0.85 → 0.89 (+4.7%)
```

**Tracked Metrics:**
1. **JSON Validity Rate** (Target: 98%)
2. **Confidence Calibration Accuracy** (Target: 85%)
3. **Required Criteria Quality** (Target: 90%)
4. **Source Citation Rate** (Target: 95%)

**Improvement Cycle:** Alle 10 Queries automatisch

---

## 🚀 Next Steps

**Recommendation: Implement v7.0 (JSON-Driven)!**

**Warum:**
1. ✅ **78-83% weniger Code** (2,300 LOC vs. 10,500-13,900 LOC)
2. ✅ **63-73% schnellere Implementierung** (11-15 Tage vs. 30-40 Tage)
3. ✅ **Orchestrator-kompatibel** (passt zu DYNAMIC_AGENT_TASK_BLUEPRINTS Pattern)
4. ✅ **LLM-optimierbar** (Prompts + Ablauf als JSON)
5. ✅ **Versionierbar** (verschiedene scientific_method.json möglich)

**Sofort starten:**
```bash
# 1. Create Directories
mkdir -p config/scientific_methods
mkdir -p config/prompts/scientific

# 2. Create default_method.json (Phase 1)
# 3. Create Phase Prompts (Phase 1)
# 4. Implement ScientificPhaseExecutor (Phase 2)
# 5. Implement UnifiedOrchestratorV7 (Phase 3)
```

**Soll ich die Implementation starten (Phase 1: JSON Configs erstellen)?**
