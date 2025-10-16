# 🌳 VERITAS Process Tree Architecture

**Dynamische Pfadverfolgung mit Tree-basierter Step-Struktur**

---

## 🎯 Problem: Lineare Pipeline vs. Dynamische Verzweigung

### ❌ Bisherige Annahme (Linear):
```
Step 1 (NLP) → Step 2 (RAG) → Step 3 (Hypothesis) → Step 4 (Response)
```

**Problem:**
- Was wenn Hypothesis mehrere RAG-Queries triggert?
- Was wenn Missing Information nachträglich kommt?
- Was wenn Quality Check fehlschlägt → Re-Generation nötig?

### ✅ Neue Architektur (Tree):
```
Root (User Query)
├─ Step 1: NLP Pre-Processing
├─ Step 2: Initial RAG Retrieval
│   ├─ Step 2.1: Semantic Search (ChromaDB)
│   └─ Step 2.2: Graph Search (Neo4j)
├─ Step 3: Hypothesis Generation
│   ├─ Step 3.1: Missing Info Detection
│   │   └─ Step 3.1.1: User Form Submission (async wait)
│   ├─ Step 3.2: Additional RAG (basierend auf Hypothesis)
│   │   ├─ Step 3.2.1: Bundesland-spezifische LBO
│   │   └─ Step 3.2.2: Prozess-Graph Navigation
│   └─ Step 3.3: Hypothesis Refinement
├─ Step 4: Evidence Evaluation
├─ Step 5: Template Construction
└─ Step 6: Answer Generation
    ├─ Step 6.1: Text Generation (streaming)
    ├─ Step 6.2: Quality Check (Completeness)
    │   └─ Step 6.2.1: Re-Generation (if failed)
    └─ Step 6.3: Quality Check (Accuracy)
```

---

## 📊 Process Tree JSON Schema

### Root Structure

```json
{
  "process_id": "uuid-process-1234",
  "user_id": "uuid-user-5678",
  "query": "Ist für meinen Carport eine Baugenehmigung nötig?",
  "timestamp_start": "2025-10-12T18:45:00.000Z",
  "timestamp_end": "2025-10-12T18:45:05.800Z",
  "total_duration_ms": 5800,
  "status": "completed",
  
  "process_tree": {
    "root": {
      "step_id": "root",
      "step_type": "query_root",
      "status": "completed",
      "timestamp_start": "2025-10-12T18:45:00.000Z",
      "timestamp_end": "2025-10-12T18:45:05.800Z",
      "duration_ms": 5800,
      "result": {
        "final_response": {
          "answer": "...",
          "confidence": 0.78,
          "quality_metrics": {...}
        }
      },
      "children": [
        {
          "step_id": "step_nlp",
          "step_type": "nlp_preprocessing",
          "parent_id": "root",
          "status": "completed",
          "timestamp_start": "2025-10-12T18:45:00.000Z",
          "timestamp_end": "2025-10-12T18:45:00.150Z",
          "duration_ms": 150,
          "result": {
            "nlp": {
              "language": "de",
              "intent": "rechtliche_bewertung",
              "entities": ["Carport", "Baugenehmigung"],
              "complexity": "medium"
            }
          },
          "children": []
        },
        {
          "step_id": "step_rag_initial",
          "step_type": "rag_retrieval",
          "parent_id": "root",
          "status": "completed",
          "timestamp_start": "2025-10-12T18:45:00.150Z",
          "timestamp_end": "2025-10-12T18:45:00.550Z",
          "duration_ms": 400,
          "result": {
            "documents_found": 15,
            "top_score": 0.92,
            "documents": [...]
          },
          "children": [
            {
              "step_id": "step_rag_semantic",
              "step_type": "semantic_search",
              "parent_id": "step_rag_initial",
              "status": "completed",
              "timestamp_start": "2025-10-12T18:45:00.150Z",
              "timestamp_end": "2025-10-12T18:45:00.270Z",
              "duration_ms": 120,
              "result": {
                "source": "chromadb",
                "query": "Carport Baugenehmigung",
                "results_count": 15,
                "top_documents": [...]
              },
              "children": []
            },
            {
              "step_id": "step_rag_graph",
              "step_type": "graph_search",
              "parent_id": "step_rag_initial",
              "status": "completed",
              "timestamp_start": "2025-10-12T18:45:00.270Z",
              "timestamp_end": "2025-10-12T18:45:00.400Z",
              "duration_ms": 130,
              "result": {
                "source": "neo4j",
                "query": "MATCH (n:Concept {name: 'Baugenehmigung'})-[r*1..2]-(related) RETURN n,r,related",
                "nodes_found": 8,
                "relationships_found": 12,
                "graph_context": [...]
              },
              "children": []
            }
          ]
        },
        {
          "step_id": "step_hypothesis",
          "step_type": "hypothesis_generation",
          "parent_id": "root",
          "status": "completed",
          "timestamp_start": "2025-10-12T18:45:00.550Z",
          "timestamp_end": "2025-10-12T18:45:01.750Z",
          "duration_ms": 1200,
          "result": {
            "hypothesis": {
              "required_criteria": [...],
              "missing_information": [...],
              "confidence_estimate": 0.55
            }
          },
          "children": [
            {
              "step_id": "step_hypothesis_llm",
              "step_type": "llm_call",
              "parent_id": "step_hypothesis",
              "status": "completed",
              "timestamp_start": "2025-10-12T18:45:00.600Z",
              "timestamp_end": "2025-10-12T18:45:01.200Z",
              "duration_ms": 600,
              "result": {
                "model": "llama3.1:70b",
                "prompt_type": "hypothesis_generation",
                "tokens_input": 1247,
                "tokens_output": 487,
                "tokens_total": 1734,
                "response": {...}
              },
              "children": []
            },
            {
              "step_id": "step_missing_info_form",
              "step_type": "interactive_form_wait",
              "parent_id": "step_hypothesis",
              "status": "completed",
              "timestamp_start": "2025-10-12T18:45:01.200Z",
              "timestamp_end": "2025-10-12T18:45:01.500Z",
              "duration_ms": 300,
              "result": {
                "form_displayed": true,
                "user_input": {
                  "bundesland": "Baden-Württemberg",
                  "carport_groesse": "25",
                  "grundstueckslage": "Bebauungsplan Innenbereich"
                }
              },
              "children": []
            },
            {
              "step_id": "step_rag_additional",
              "step_type": "rag_retrieval_refined",
              "parent_id": "step_hypothesis",
              "status": "completed",
              "timestamp_start": "2025-10-12T18:45:01.500Z",
              "timestamp_end": "2025-10-12T18:45:01.750Z",
              "duration_ms": 250,
              "result": {
                "trigger": "hypothesis_missing_info_resolved",
                "refined_query": "LBO Baden-Württemberg §50 Verfahrensfreiheit Carport 25m²",
                "documents_found": 5,
                "documents": [...]
              },
              "children": [
                {
                  "step_id": "step_rag_lbo_specific",
                  "step_type": "semantic_search",
                  "parent_id": "step_rag_additional",
                  "status": "completed",
                  "timestamp_start": "2025-10-12T18:45:01.500Z",
                  "timestamp_end": "2025-10-12T18:45:01.650Z",
                  "duration_ms": 150,
                  "result": {
                    "query": "LBO Baden-Württemberg §50",
                    "results_count": 3,
                    "top_documents": [...]
                  },
                  "children": []
                },
                {
                  "step_id": "step_rag_process_graph",
                  "step_type": "graph_traversal",
                  "parent_id": "step_rag_additional",
                  "status": "completed",
                  "timestamp_start": "2025-10-12T18:45:01.650Z",
                  "timestamp_end": "2025-10-12T18:45:01.750Z",
                  "duration_ms": 100,
                  "result": {
                    "query": "MATCH (n:Process {name: 'Baugenehmigung BW'})-[r*1..3]-(step) RETURN n,r,step",
                    "process_steps": [...]
                  },
                  "children": []
                }
              ]
            }
          ]
        },
        {
          "step_id": "step_evidence",
          "step_type": "evidence_evaluation",
          "parent_id": "root",
          "status": "completed",
          "timestamp_start": "2025-10-12T18:45:01.750Z",
          "timestamp_end": "2025-10-12T18:45:01.900Z",
          "duration_ms": 150,
          "result": {
            "documents_evaluated": 20,
            "documents_used": 8,
            "evidence_scores": [...]
          },
          "children": []
        },
        {
          "step_id": "step_template",
          "step_type": "template_construction",
          "parent_id": "root",
          "status": "completed",
          "timestamp_start": "2025-10-12T18:45:01.900Z",
          "timestamp_end": "2025-10-12T18:45:02.100Z",
          "duration_ms": 200,
          "result": {
            "base_framework": "verwaltungsrechtliche_frage",
            "sections_generated": 4,
            "template": {...}
          },
          "children": []
        },
        {
          "step_id": "step_answer",
          "step_type": "answer_generation",
          "parent_id": "root",
          "status": "completed",
          "timestamp_start": "2025-10-12T18:45:02.100Z",
          "timestamp_end": "2025-10-12T18:45:05.800Z",
          "duration_ms": 3700,
          "result": {
            "response": "...",
            "tokens_generated": 2847,
            "quality_metrics": {
              "completeness": 0.95,
              "accuracy": 0.92,
              "consistency": 0.88
            }
          },
          "children": [
            {
              "step_id": "step_answer_llm",
              "step_type": "llm_call_streaming",
              "parent_id": "step_answer",
              "status": "completed",
              "timestamp_start": "2025-10-12T18:45:02.100Z",
              "timestamp_end": "2025-10-12T18:45:05.400Z",
              "duration_ms": 3300,
              "result": {
                "model": "llama3.1:70b",
                "prompt_type": "adaptive_response",
                "tokens_generated": 2847,
                "chunks_emitted": 142
              },
              "children": []
            },
            {
              "step_id": "step_quality_completeness",
              "step_type": "quality_check",
              "parent_id": "step_answer",
              "status": "completed",
              "timestamp_start": "2025-10-12T18:45:05.400Z",
              "timestamp_end": "2025-10-12T18:45:05.550Z",
              "duration_ms": 150,
              "result": {
                "check_type": "completeness",
                "score": 0.95,
                "passed": true,
                "criteria_addressed": 19,
                "criteria_total": 20
              },
              "children": []
            },
            {
              "step_id": "step_quality_accuracy",
              "step_type": "quality_check",
              "parent_id": "step_answer",
              "status": "completed",
              "timestamp_start": "2025-10-12T18:45:05.550Z",
              "timestamp_end": "2025-10-12T18:45:05.700Z",
              "duration_ms": 150,
              "result": {
                "check_type": "accuracy",
                "score": 0.92,
                "passed": true,
                "sources_cited": 8,
                "sources_valid": 8,
                "hallucinations_detected": 0
              },
              "children": []
            },
            {
              "step_id": "step_quality_consistency",
              "step_type": "quality_check",
              "parent_id": "step_answer",
              "status": "completed",
              "timestamp_start": "2025-10-12T18:45:05.700Z",
              "timestamp_end": "2025-10-12T18:45:05.800Z",
              "duration_ms": 100,
              "result": {
                "check_type": "consistency",
                "score": 0.88,
                "passed": true,
                "contradictions_detected": 0
              },
              "children": []
            }
          ]
        }
      ]
    }
  },
  
  "metadata": {
    "total_steps": 17,
    "total_llm_calls": 2,
    "total_rag_queries": 4,
    "total_tokens_used": 4581,
    "total_documents_retrieved": 20,
    "total_documents_used": 8,
    "branching_points": 2,
    "max_depth": 4,
    "parallel_executions": 2
  }
}
```

---

## 🔄 Step Types & Result Objects

### 1. NLP Pre-Processing

```json
{
  "step_id": "step_nlp",
  "step_type": "nlp_preprocessing",
  "status": "completed",
  "result": {
    "nlp": {
      "language": "de",
      "intent": "rechtliche_bewertung",
      "entities": ["Carport", "Baugenehmigung"],
      "parsed_query": {
        "main_topic": "Baugenehmigung",
        "subtopics": ["Carport", "Verfahrensfreiheit"],
        "keywords": ["Baugenehmigung", "Carport", "BauGB", "LBO"]
      },
      "estimated_complexity": "medium",
      "sentiment": "neutral"
    }
  }
}
```

---

### 2. RAG Retrieval (Parent)

```json
{
  "step_id": "step_rag_initial",
  "step_type": "rag_retrieval",
  "status": "completed",
  "result": {
    "documents_found": 15,
    "top_score": 0.92,
    "retrieval_time_ms": 400,
    "aggregated_from_children": true
  },
  "children": [
    {
      "step_id": "step_rag_semantic",
      "step_type": "semantic_search",
      "result": {
        "source": "chromadb",
        "collection": "veritas_knowledge",
        "query": "Carport Baugenehmigung",
        "results_count": 15,
        "retrieval_time_ms": 120,
        "top_documents": [
          {
            "document_id": "doc_baugb_35",
            "title": "BauGB §35 - Bauen im Außenbereich",
            "relevance_score": 0.92,
            "chunk": "..."
          }
        ]
      }
    },
    {
      "step_id": "step_rag_graph",
      "step_type": "graph_search",
      "result": {
        "source": "neo4j",
        "query": "MATCH (n:Concept {name: 'Baugenehmigung'})-[r*1..2]-(related) RETURN n,r,related",
        "nodes_found": 8,
        "relationships_found": 12,
        "retrieval_time_ms": 130,
        "graph_context": [
          {
            "node_id": "process_baugenehmigung",
            "label": "Baugenehmigungsverfahren",
            "relationships": [...]
          }
        ]
      }
    }
  ]
}
```

---

### 3. Hypothesis Generation (mit Branching!)

```json
{
  "step_id": "step_hypothesis",
  "step_type": "hypothesis_generation",
  "status": "completed",
  "result": {
    "hypothesis": {
      "required_criteria": [...],
      "missing_information": [...],
      "confidence_estimate": 0.55
    },
    "triggered_branches": ["step_missing_info_form", "step_rag_additional"]
  },
  "children": [
    {
      "step_id": "step_hypothesis_llm",
      "step_type": "llm_call",
      "result": {
        "model": "llama3.1:70b",
        "tokens_input": 1247,
        "tokens_output": 487,
        "response_json": {...}
      }
    },
    {
      "step_id": "step_missing_info_form",
      "step_type": "interactive_form_wait",
      "status": "completed",
      "result": {
        "form_displayed": true,
        "form_fields": ["bundesland", "carport_groesse", "grundstueckslage"],
        "user_input": {
          "bundesland": "Baden-Württemberg",
          "carport_groesse": "25",
          "grundstueckslage": "Bebauungsplan Innenbereich"
        },
        "wait_time_ms": 300
      }
    },
    {
      "step_id": "step_rag_additional",
      "step_type": "rag_retrieval_refined",
      "status": "completed",
      "result": {
        "trigger": "hypothesis_missing_info_resolved",
        "refined_query": "LBO Baden-Württemberg §50 Verfahrensfreiheit Carport 25m²",
        "documents_found": 5
      },
      "children": [
        {
          "step_id": "step_rag_lbo_specific",
          "step_type": "semantic_search",
          "result": {
            "query": "LBO Baden-Württemberg §50",
            "results_count": 3,
            "top_documents": [...]
          }
        },
        {
          "step_id": "step_rag_process_graph",
          "step_type": "graph_traversal",
          "result": {
            "query": "MATCH (n:Process {name: 'Baugenehmigung BW'})-[r*1..3]-(step) RETURN n,r,step",
            "process_steps": [...]
          }
        }
      ]
    }
  ]
}
```

---

### 4. Evidence Evaluation

```json
{
  "step_id": "step_evidence",
  "step_type": "evidence_evaluation",
  "status": "completed",
  "result": {
    "documents_evaluated": 20,
    "documents_relevant": 12,
    "documents_used": 8,
    "evidence_scores": [
      {
        "document_id": "doc_baugb_35",
        "relevance_score": 0.92,
        "criteria_coverage": ["Grundstückslage klären"],
        "used_in_response": true,
        "source_step": "step_rag_semantic"
      },
      {
        "document_id": "doc_lbo_bw_50",
        "relevance_score": 0.95,
        "criteria_coverage": ["Carport-Größe prüfen", "Verfahrensfreiheit"],
        "used_in_response": true,
        "source_step": "step_rag_lbo_specific"
      }
    ],
    "aggregated_from_steps": [
      "step_rag_semantic",
      "step_rag_graph",
      "step_rag_lbo_specific",
      "step_rag_process_graph"
    ]
  }
}
```

---

### 5. Template Construction

```json
{
  "step_id": "step_template",
  "step_type": "template_construction",
  "status": "completed",
  "result": {
    "base_framework": "verwaltungsrechtliche_frage",
    "sections_generated": 4,
    "interactive_elements": 0,
    "estimated_response_length": "medium",
    "template": {
      "sections": [
        {
          "section_id": "legal_assessment",
          "type": "markdown",
          "title": "Rechtliche Einordnung",
          "quality_requirements": {
            "completeness_min": 0.9,
            "accuracy_min": 0.92,
            "required_sources": ["BauGB", "LBO BW"]
          }
        }
      ]
    },
    "system_prompt_hash": "abc123def456",
    "token_budget": 3500
  }
}
```

---

### 6. Answer Generation (mit Quality Checks als Children!)

```json
{
  "step_id": "step_answer",
  "step_type": "answer_generation",
  "status": "completed",
  "result": {
    "response_text": "Gemäß BauGB §35 sind im Außenbereich...",
    "tokens_generated": 2847,
    "generation_time_ms": 3300,
    "chunks_emitted": 142,
    "quality_metrics": {
      "completeness": 0.95,
      "accuracy": 0.92,
      "consistency": 0.88,
      "overall_quality": 0.92
    },
    "quality_checks_passed": true
  },
  "children": [
    {
      "step_id": "step_answer_llm",
      "step_type": "llm_call_streaming",
      "result": {
        "model": "llama3.1:70b",
        "tokens_generated": 2847,
        "chunks_emitted": 142,
        "streaming_time_ms": 3300
      }
    },
    {
      "step_id": "step_quality_completeness",
      "step_type": "quality_check",
      "status": "completed",
      "result": {
        "check_type": "completeness",
        "score": 0.95,
        "passed": true,
        "threshold": 0.90,
        "criteria_addressed": 19,
        "criteria_total": 20,
        "missing_criteria": ["Widerspruchsverfahren"]
      }
    },
    {
      "step_id": "step_quality_accuracy",
      "step_type": "quality_check",
      "status": "completed",
      "result": {
        "check_type": "accuracy",
        "score": 0.92,
        "passed": true,
        "threshold": 0.92,
        "sources_cited": 8,
        "sources_valid": 8,
        "sources_invalid": 0,
        "hallucinations_detected": 0,
        "validation_method": "rag_document_lookup"
      }
    },
    {
      "step_id": "step_quality_consistency",
      "step_type": "quality_check",
      "status": "completed",
      "result": {
        "check_type": "consistency",
        "score": 0.88,
        "passed": true,
        "threshold": 0.85,
        "contradictions_detected": 0,
        "validation_method": "semantic_similarity"
      }
    }
  ]
}
```

---

### 7. Quality Check Failure → Re-Generation Branch

**Scenario:** Completeness Check fails (score 0.75 < 0.90)

```json
{
  "step_id": "step_answer",
  "step_type": "answer_generation",
  "status": "completed",
  "result": {
    "attempts": 2,
    "final_quality": 0.92,
    "quality_checks_passed": true
  },
  "children": [
    {
      "step_id": "step_answer_llm_attempt1",
      "step_type": "llm_call_streaming",
      "status": "completed",
      "result": {
        "tokens_generated": 1847,
        "quality_failed": true
      }
    },
    {
      "step_id": "step_quality_completeness_attempt1",
      "step_type": "quality_check",
      "status": "failed",
      "result": {
        "check_type": "completeness",
        "score": 0.75,
        "passed": false,
        "threshold": 0.90,
        "criteria_addressed": 15,
        "criteria_total": 20,
        "missing_criteria": ["Zuständigkeit", "Verfahrensfreiheit", "Fristen", "Kosten", "Widerspruch"]
      }
    },
    {
      "step_id": "step_answer_regeneration",
      "step_type": "answer_generation_retry",
      "status": "completed",
      "result": {
        "trigger": "quality_check_failed",
        "failed_check": "completeness",
        "retry_strategy": "add_missing_criteria",
        "additional_prompt": "Bitte ergänze: Zuständigkeit, Verfahrensfreiheit, Fristen, Kosten, Widerspruch"
      },
      "children": [
        {
          "step_id": "step_answer_llm_attempt2",
          "step_type": "llm_call_streaming",
          "status": "completed",
          "result": {
            "tokens_generated": 2847,
            "quality_passed": true
          }
        },
        {
          "step_id": "step_quality_completeness_attempt2",
          "step_type": "quality_check",
          "status": "completed",
          "result": {
            "check_type": "completeness",
            "score": 0.95,
            "passed": true,
            "criteria_addressed": 19,
            "criteria_total": 20
          }
        }
      ]
    }
  ]
}
```

---

## 🎯 Tree Operations

### 1. Tree Traversal (DFS - Depth-First Search)

```python
def traverse_process_tree(node: ProcessNode, visit_fn: Callable):
    """Depth-First Traversal"""
    visit_fn(node)
    for child in node.children:
        traverse_process_tree(child, visit_fn)

# Usage: Collect all LLM calls
llm_calls = []
def collect_llm_calls(node):
    if node.step_type in ["llm_call", "llm_call_streaming"]:
        llm_calls.append(node)

traverse_process_tree(process_tree.root, collect_llm_calls)
print(f"Total LLM calls: {len(llm_calls)}")
```

---

### 2. Tree Aggregation (Bottom-Up)

```python
def aggregate_results(node: ProcessNode) -> dict:
    """Aggregate results from all children (bottom-up)"""
    # First, aggregate children
    child_results = []
    for child in node.children:
        child_result = aggregate_results(child)
        child_results.append(child_result)
    
    # Then, aggregate this node
    if node.step_type == "rag_retrieval":
        # Combine documents from all child RAG searches
        all_documents = []
        for child in child_results:
            if "documents" in child:
                all_documents.extend(child["documents"])
        
        node.result["documents"] = all_documents
        node.result["aggregated_from_children"] = True
    
    return node.result

# Usage: Aggregate all RAG results
final_result = aggregate_results(process_tree.root)
```

---

### 3. Path Extraction (Root → Leaf)

```python
def extract_path(node: ProcessNode, target_step_id: str, path: List[str] = None) -> List[str]:
    """Extract path from root to target step"""
    if path is None:
        path = []
    
    path.append(node.step_id)
    
    if node.step_id == target_step_id:
        return path
    
    for child in node.children:
        result_path = extract_path(child, target_step_id, path.copy())
        if result_path:
            return result_path
    
    return None

# Usage: Find path to specific quality check
path = extract_path(process_tree.root, "step_quality_accuracy")
print(" → ".join(path))
# Output: root → step_answer → step_quality_accuracy
```

---

### 4. Branching Point Detection

```python
def find_branching_points(node: ProcessNode) -> List[ProcessNode]:
    """Find all nodes with multiple children (branching points)"""
    branching_points = []
    
    if len(node.children) > 1:
        branching_points.append(node)
    
    for child in node.children:
        branching_points.extend(find_branching_points(child))
    
    return branching_points

# Usage: Identify dynamic decision points
branches = find_branching_points(process_tree.root)
for branch in branches:
    print(f"Branching at {branch.step_id}: {len(branch.children)} children")
```

---

### 5. Parallel Execution Detection

```python
def detect_parallel_steps(node: ProcessNode) -> List[List[ProcessNode]]:
    """Detect steps that can run in parallel"""
    parallel_groups = []
    
    if len(node.children) > 1:
        # Check if children have no dependencies
        independent_children = []
        for child in node.children:
            # If child doesn't depend on sibling results → parallel
            if not depends_on_siblings(child, node.children):
                independent_children.append(child)
        
        if len(independent_children) > 1:
            parallel_groups.append(independent_children)
    
    # Recurse
    for child in node.children:
        parallel_groups.extend(detect_parallel_steps(child))
    
    return parallel_groups

# Usage: Optimize execution
parallel_steps = detect_parallel_steps(process_tree.root)
for group in parallel_steps:
    step_ids = [s.step_id for s in group]
    print(f"Can run in parallel: {step_ids}")
# Output: Can run in parallel: ['step_rag_semantic', 'step_rag_graph']
```

---

## 🔄 Streaming Updates (Tree-Aware)

### Event Format (Extended)

```json
{
  "type": "processing_step",
  "step_id": "step_rag_lbo_specific",
  "parent_id": "step_rag_additional",
  "path": ["root", "step_hypothesis", "step_rag_additional", "step_rag_lbo_specific"],
  "depth": 3,
  "status": "completed",
  "timestamp": "2025-10-12T18:45:01.650Z",
  "result": {...}
}
```

**Client Rendering:**
```
Root
├─ NLP Pre-Processing ✅ (150ms)
├─ Initial RAG Retrieval ✅ (400ms)
│   ├─ Semantic Search ✅ (120ms)
│   └─ Graph Search ✅ (130ms)
├─ Hypothesis Generation ⏳ (in progress)
│   ├─ LLM Call ✅ (600ms)
│   ├─ Interactive Form ⏳ (waiting for user)
│   └─ Additional RAG 🔄 (triggered after form)
│       ├─ LBO-Specific Search ⏳ (in progress)  ← CURRENT
│       └─ Process Graph Navigation ⏸️ (pending)
```

---

## 🎯 LLM Hauptknoten-Auswertung

### Scenario: LLM generiert finale Antwort aus Tree-Ergebnissen

**Problem:**
LLM muss ALLE Ergebnisse aus dem Tree kombinieren:
- Initial RAG (step_rag_initial)
- Additional RAG (step_rag_additional)
- User Input (step_missing_info_form)
- Evidence Evaluation (step_evidence)

**Lösung: Tree-to-Context Serialization**

```python
def serialize_tree_for_llm(root: ProcessNode) -> str:
    """Convert process tree to LLM-consumable context"""
    
    context_sections = []
    
    # 1. Collect all RAG results
    rag_results = []
    def collect_rag(node):
        if node.step_type in ["semantic_search", "graph_search", "graph_traversal"]:
            rag_results.append(node.result)
    traverse_process_tree(root, collect_rag)
    
    context_sections.append("# RAG CONTEXT (Aggregated from all retrieval steps)\n")
    for i, rag in enumerate(rag_results):
        context_sections.append(f"## Source {i+1}: {rag['source']}\n")
        context_sections.append(f"{format_rag_result(rag)}\n")
    
    # 2. Collect user input
    user_inputs = []
    def collect_input(node):
        if node.step_type == "interactive_form_wait":
            user_inputs.append(node.result['user_input'])
    traverse_process_tree(root, collect_input)
    
    if user_inputs:
        context_sections.append("# USER INPUT (From interactive forms)\n")
        for inp in user_inputs:
            context_sections.append(f"{json.dumps(inp, indent=2)}\n")
    
    # 3. Include hypothesis
    hypothesis_node = find_node_by_type(root, "hypothesis_generation")
    if hypothesis_node:
        context_sections.append("# HYPOTHESIS (Required criteria to address)\n")
        context_sections.append(f"{json.dumps(hypothesis_node.result['hypothesis'], indent=2)}\n")
    
    # 4. Include evidence evaluation
    evidence_node = find_node_by_type(root, "evidence_evaluation")
    if evidence_node:
        context_sections.append("# EVIDENCE EVALUATION (Document relevance scores)\n")
        context_sections.append(f"{format_evidence(evidence_node.result)}\n")
    
    return "\n".join(context_sections)

# Usage in Answer Generation
context_for_llm = serialize_tree_for_llm(process_tree.root)
llm_response = await ollama.generate(
    model="llama3.1:70b",
    system=template.system_prompt,
    prompt=f"{context_for_llm}\n\nUSER QUERY: {original_query}\n\nGenerate response following template..."
)
```

---

## 📊 Backend Implementation

### Process Tree Manager

```python
# backend/services/process_tree_manager.py
from typing import List, Optional, Dict, Any, Callable
from datetime import datetime
from uuid import uuid4

class ProcessNode:
    def __init__(
        self,
        step_id: str,
        step_type: str,
        parent_id: Optional[str] = None,
        status: str = "pending"
    ):
        self.step_id = step_id
        self.step_type = step_type
        self.parent_id = parent_id
        self.status = status  # pending, in_progress, completed, failed
        self.timestamp_start: Optional[datetime] = None
        self.timestamp_end: Optional[datetime] = None
        self.duration_ms: Optional[int] = None
        self.result: Dict[str, Any] = {}
        self.children: List[ProcessNode] = []
    
    def start(self):
        self.status = "in_progress"
        self.timestamp_start = datetime.utcnow()
    
    def complete(self, result: Dict[str, Any]):
        self.status = "completed"
        self.timestamp_end = datetime.utcnow()
        self.duration_ms = int((self.timestamp_end - self.timestamp_start).total_seconds() * 1000)
        self.result = result
    
    def fail(self, error: str):
        self.status = "failed"
        self.timestamp_end = datetime.utcnow()
        self.duration_ms = int((self.timestamp_end - self.timestamp_start).total_seconds() * 1000)
        self.result = {"error": error}
    
    def add_child(self, child: 'ProcessNode'):
        self.children.append(child)
        return child
    
    def to_dict(self) -> dict:
        return {
            "step_id": self.step_id,
            "step_type": self.step_type,
            "parent_id": self.parent_id,
            "status": self.status,
            "timestamp_start": self.timestamp_start.isoformat() if self.timestamp_start else None,
            "timestamp_end": self.timestamp_end.isoformat() if self.timestamp_end else None,
            "duration_ms": self.duration_ms,
            "result": self.result,
            "children": [child.to_dict() for child in self.children]
        }

class ProcessTreeManager:
    def __init__(self):
        self.root = ProcessNode(step_id="root", step_type="query_root")
        self.current_node = self.root
        self.node_index: Dict[str, ProcessNode] = {"root": self.root}
    
    def add_step(
        self,
        step_id: str,
        step_type: str,
        parent_id: Optional[str] = None
    ) -> ProcessNode:
        """Add a new step to the tree"""
        parent = self.node_index.get(parent_id or "root")
        if not parent:
            raise ValueError(f"Parent node {parent_id} not found")
        
        node = ProcessNode(step_id=step_id, step_type=step_type, parent_id=parent.step_id)
        parent.add_child(node)
        self.node_index[step_id] = node
        self.current_node = node
        
        return node
    
    def start_step(self, step_id: str):
        node = self.node_index.get(step_id)
        if node:
            node.start()
    
    def complete_step(self, step_id: str, result: Dict[str, Any]):
        node = self.node_index.get(step_id)
        if node:
            node.complete(result)
    
    def fail_step(self, step_id: str, error: str):
        node = self.node_index.get(step_id)
        if node:
            node.fail(error)
    
    def get_path(self, step_id: str) -> List[str]:
        """Get path from root to step"""
        node = self.node_index.get(step_id)
        if not node:
            return []
        
        path = [node.step_id]
        while node.parent_id:
            node = self.node_index[node.parent_id]
            path.insert(0, node.step_id)
        
        return path
    
    def traverse(self, visit_fn: Callable[[ProcessNode], None]):
        """Depth-first traversal"""
        def _traverse(node: ProcessNode):
            visit_fn(node)
            for child in node.children:
                _traverse(child)
        
        _traverse(self.root)
    
    def aggregate_results(self, node: ProcessNode = None) -> dict:
        """Aggregate results bottom-up"""
        if node is None:
            node = self.root
        
        # Recursively aggregate children
        child_results = []
        for child in node.children:
            child_result = self.aggregate_results(child)
            child_results.append(child_result)
        
        # Aggregate based on step type
        if node.step_type == "rag_retrieval":
            all_docs = []
            for child in child_results:
                if "documents" in child:
                    all_docs.extend(child["documents"])
            
            node.result["documents"] = all_docs
            node.result["aggregated_from_children"] = True
        
        return node.result
    
    def to_dict(self) -> dict:
        # Calculate metadata
        total_steps = len(self.node_index)
        llm_calls = 0
        rag_queries = 0
        total_tokens = 0
        
        def count_nodes(node):
            nonlocal llm_calls, rag_queries, total_tokens
            if node.step_type in ["llm_call", "llm_call_streaming"]:
                llm_calls += 1
                if "tokens_total" in node.result:
                    total_tokens += node.result["tokens_total"]
            elif node.step_type in ["semantic_search", "graph_search", "graph_traversal"]:
                rag_queries += 1
        
        self.traverse(count_nodes)
        
        return {
            "process_id": str(uuid4()),
            "root": self.root.to_dict(),
            "metadata": {
                "total_steps": total_steps,
                "total_llm_calls": llm_calls,
                "total_rag_queries": rag_queries,
                "total_tokens_used": total_tokens
            }
        }
```

---

### Usage in Query Pipeline

```python
# backend/api/v1/query_endpoint.py
async def query_pipeline(request: QueryRequest):
    # Initialize process tree
    tree = ProcessTreeManager()
    tree.root.start()
    
    # Step 1: NLP
    step_nlp = tree.add_step("step_nlp", "nlp_preprocessing", parent_id="root")
    step_nlp.start()
    nlp_result = await nlp_service.process(request.query)
    step_nlp.complete({"nlp": nlp_result.dict()})
    yield StreamEvent(type="processing_step", step_id="step_nlp", path=tree.get_path("step_nlp"), data=step_nlp.to_dict())
    
    # Step 2: RAG (parent)
    step_rag = tree.add_step("step_rag_initial", "rag_retrieval", parent_id="root")
    step_rag.start()
    
    # Step 2.1: Semantic Search (child)
    step_semantic = tree.add_step("step_rag_semantic", "semantic_search", parent_id="step_rag_initial")
    step_semantic.start()
    semantic_results = await rag_service._semantic_search(nlp_result)
    step_semantic.complete({"source": "chromadb", "results_count": len(semantic_results), ...})
    yield StreamEvent(type="processing_step", step_id="step_rag_semantic", path=tree.get_path("step_rag_semantic"), data=step_semantic.to_dict())
    
    # Step 2.2: Graph Search (child, parallel)
    step_graph = tree.add_step("step_rag_graph", "graph_search", parent_id="step_rag_initial")
    step_graph.start()
    graph_results = await rag_service._graph_search(nlp_result)
    step_graph.complete({"source": "neo4j", "nodes_found": len(graph_results), ...})
    yield StreamEvent(type="processing_step", step_id="step_rag_graph", path=tree.get_path("step_rag_graph"), data=step_graph.to_dict())
    
    # Aggregate RAG results
    rag_aggregated = tree.aggregate_results(step_rag)
    step_rag.complete(rag_aggregated)
    yield StreamEvent(type="processing_step", step_id="step_rag_initial", path=tree.get_path("step_rag_initial"), data=step_rag.to_dict())
    
    # Step 3: Hypothesis
    step_hypothesis = tree.add_step("step_hypothesis", "hypothesis_generation", parent_id="root")
    step_hypothesis.start()
    
    # Step 3.1: LLM Call
    step_hyp_llm = tree.add_step("step_hypothesis_llm", "llm_call", parent_id="step_hypothesis")
    step_hyp_llm.start()
    hypothesis = await hypothesis_service.generate(request.query, rag_aggregated)
    step_hyp_llm.complete({"model": "llama3.1:70b", "tokens_total": 1734, "response_json": hypothesis.dict()})
    
    # Step 3.2: Interactive Form (if missing info)
    if hypothesis.missing_information:
        step_form = tree.add_step("step_missing_info_form", "interactive_form_wait", parent_id="step_hypothesis")
        step_form.start()
        yield StreamEvent(type="interactive_form", step_id="step_missing_info_form", data={"fields": hypothesis.missing_information})
        
        # Wait for user input
        user_input = await wait_for_user_input()
        step_form.complete({"form_displayed": True, "user_input": user_input})
        
        # Step 3.3: Additional RAG (triggered by user input)
        step_rag_add = tree.add_step("step_rag_additional", "rag_retrieval_refined", parent_id="step_hypothesis")
        step_rag_add.start()
        
        # ... additional RAG children (LBO-specific, Process graph)
        
        step_rag_add.complete({...})
    
    step_hypothesis.complete({"hypothesis": hypothesis.dict()})
    
    # ... continue with Evidence, Template, Answer
    
    # Final: Complete root
    tree.root.complete({"final_response": {...}})
    
    # Emit full tree
    yield StreamEvent(type="processing_complete", data=tree.to_dict())
```

---

## 🎯 Zusammenfassung

### Was haben wir erreicht?

1. ✅ **Tree-Struktur** statt linearer Pipeline
2. ✅ **Jeder Step = eigenes Result-Objekt** (isoliert)
3. ✅ **Dynamische Verzweigung** (Hypothesis → Form → Additional RAG)
4. ✅ **Parallele Ausführung** (Semantic + Graph Search)
5. ✅ **Quality Checks als Children** (nicht inline)
6. ✅ **Re-Generation Branch** (bei Quality Check Failure)
7. ✅ **Bottom-Up Aggregation** (RAG results von allen Children)
8. ✅ **LLM Hauptknoten-Auswertung** (Tree-to-Context Serialization)

### Key Insights

- 🌳 **Tree > Linear:** Ermöglicht dynamische Pfadverfolgung
- 🔄 **Children = Sub-Steps:** Semantic + Graph = Children von RAG
- 📊 **Result Aggregation:** Parent sammelt Results von Children
- 🎯 **LLM Context:** Serialize gesamten Tree für finale Antwort
- ⏱️ **Parallelisierung:** Siblings ohne Dependencies parallel ausführbar

### Nächste Schritte

Möchtest du:
1. **ProcessTreeManager implementieren?** (Python Backend)
2. **Tree Visualization im Frontend?** (Hierarchische Anzeige)
3. **Parallel Execution Optimizer?** (Automatische Parallelisierung)

Was ist deine Präferenz? 🚀
