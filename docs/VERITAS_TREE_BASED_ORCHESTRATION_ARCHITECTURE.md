# VERITAS Tree-Based Orchestration Architecture
## Hypothesis-Driven, Multi-Plan Query Execution with Interactive Refinement

**Document Version**: 2.0  
**Created**: 2025-12-03  
**Status**: 🎯 Design Blueprint  
**Inspiration**: Gemini Deep Search, GitHub Copilot Agents

---

## 🎯 Executive Summary

This document defines a revolutionary architecture for VERITAS that transforms it from a linear RAG system into an **interactive, tree-based orchestration engine**. The system analyzes queries, generates multiple execution hypotheses, evaluates cost-benefit trade-offs, and executes the optimal plan while allowing **real-time user interaction** and query refinement during execution.

**Key Differentiators**:
- **Single `/query` endpoint** with bidirectional SSE streaming
- **Hypothesis-driven** query decomposition
- **Multi-plan evaluation** with cost-benefit analysis
- **Tree model** for execution tracking (parallel + sequential paths)
- **Token-budgeted agents** with adaptive step requests
- **Interactive refinement** - users can add queries during execution (like Copilot Agents)
- **Intelligent branch pruning** based on quality thresholds
- **Final consolidation** with cross-document reranking

---

## 📋 Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Core Workflow](#2-core-workflow)
3. [Component Architecture](#3-component-architecture)
4. [Execution Tree Model](#4-execution-tree-model)
5. [Interactive SSE Protocol](#5-interactive-sse-protocol)
6. [Cost-Benefit Analysis](#6-cost-benefit-analysis)
7. [Implementation Blueprint](#7-implementation-blueprint)
8. [Comparison to Current System](#8-comparison-to-current-system)
9. [Migration Strategy](#9-migration-strategy)
10. [Example Scenarios](#10-example-execution-scenarios)

---

## 1. Architecture Overview

### 1.1 High-Level Flow

The new architecture follows a hypothesis-driven, tree-based approach inspired by Gemini Deep Search and GitHub Copilot Agents.


```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER REQUEST                                 │
│  POST /query + SSE Connection (bidirectional)                       │
│  { "query": "...", "session_id": "...", "context": {...} }         │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    1. QUERY ANALYSIS                                 │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ QueryAnalyzer (LLM-powered)                                   │  │
│  │ • Hypothesis Generation (what does user really want?)        │  │
│  │ • Query Decomposition (break into sub-queries)               │  │
│  │ • Complexity Classification (simple → expert level)          │  │
│  │ • Domain Identification (legal, environmental, technical)    │  │
│  └──────────────────────────────────────────────────────────────┘  │
│  Output: QueryHypothesis[] + SubQuery[] + ComplexityLevel          │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│              2. EXECUTION PLAN GENERATION                            │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ ExecutionPlanGenerator                                        │  │
│  │ • Generate 3-5 alternative plans                             │  │
│  │ • Each plan: Steps + Dependencies + Resources                │  │
│  │ • Cost-Benefit Analysis (time, cost, quality, risk)         │  │
│  │ • Success Probability Estimation                             │  │
│  └──────────────────────────────────────────────────────────────┘  │
│  Output: ExecutionPlan[] with scores                                │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   3. PLAN SELECTION                                  │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ PlanSelector                                                  │  │
│  │ • Rank plans by weighted score                               │  │
│  │ • Apply user preferences (speed/cost/quality)                │  │
│  │ • Select optimal plan OR fallback plan                       │  │
│  └──────────────────────────────────────────────────────────────┘  │
│  Output: SelectedExecutionPlan                                      │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  4. TREE EXECUTION                                   │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ ExecutionTreeManager                                          │  │
│  │ • Build ExecutionTree from plan                              │  │
│  │ • Execute nodes (parallel for independent, sequential for    │  │
│  │   dependent steps)                                            │  │
│  │ • Token budget enforcement per agent                         │  │
│  │ • Stream progress via SSE                                    │  │
│  │ • Accept user refinements (new queries) → expand tree       │  │
│  └──────────────────────────────────────────────────────────────┘  │
│  Output: ExecutionTree with results at each node                    │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│              5. VERIFICATION & PRUNING                               │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ TreeVerifier / BranchEvaluator                                │  │
│  │ • Evaluate each branch result                                │  │
│  │ • Quality metrics (relevance, completeness, accuracy)        │  │
│  │ • Decide: Continue | Prune | Request More Steps             │  │
│  │ • Adaptive: Agent can request additional investigation       │  │
│  └──────────────────────────────────────────────────────────────┘  │
│  Output: Pruned tree with quality-assured branches                  │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  6. RESULT AGGREGATION                               │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ ResultAggregator                                              │  │
│  │ • Collect all successful branch results                      │  │
│  │ • Cross-document reranking                                   │  │
│  │ • Deduplication & consolidation                              │  │
│  │ • Confidence scoring                                         │  │
│  └──────────────────────────────────────────────────────────────┘  │
│  Output: ConsolidatedResults                                        │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│              7. FINAL ANSWER SYNTHESIS                               │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ AnswerSynthesizer (LLM)                                       │  │
│  │ • Generate comprehensive answer from all evidence            │  │
│  │ • Citation extraction (IEEE format)                          │  │
│  │ • Coherence & readability optimization                       │  │
│  │ • Confidence & limitations statement                         │  │
│  └──────────────────────────────────────────────────────────────┘  │
│  Output: FinalAnswer via SSE                                        │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 Design Philosophy

| Principle | Implementation |
|-----------|----------------|
| **Hypothesis-Driven** | Query → Hypotheses → Plans → Verification |
| **Tree-Based** | Parallel + Sequential execution paths in tree structure |
| **Cost-Aware** | Every plan has cost/benefit/risk analysis |
| **Interactive** | User can refine query during execution (SSE bidirectional) |
| **Adaptive** | Agents can request additional investigation steps |
| **Quality-First** | Branch pruning based on quality thresholds |
| **Token-Budgeted** | Each agent has time/token budget to prevent runaway costs |

---

## 2. Core Workflow

### 2.1 Interactive SSE Protocol (Copilot Agents Inspired)

**Key Innovation**: The user can send additional queries **during** execution that get integrated into the running tree.

```
CLIENT                                  SERVER
  │                                        │
  │  POST /query                          │
  │  + SSE connection established         │
  ├──────────────────────────────────────>│
  │                                        │
  │                                        │ (Query Analysis)
  │                                        │
  │  <event: analysis_complete>           │
  │<────────────────────────────────────────
  │  data: { hypotheses, sub_queries }    │
  │                                        │
  │                                        │ (Plan Generation)
  │                                        │
  │  <event: plan_selected>               │
  │<────────────────────────────────────────
  │  data: { plan, cost, time, quality }  │
  │                                        │
  │                                        │ (Execution Start)
  │                                        │
  │  <event: step_started>                │
  │<────────────────────────────────────────
  │  data: { step_id, description }       │
  │                                        │
  │  ** USER SENDS REFINEMENT **          │
  │  POST /query/refine                   │
  │  { session_id, query: "Was ist mit    │
  │    Artenschutz?" }                    │
  ├──────────────────────────────────────>│
  │                                        │
  │                                        │ (Process refinement)
  │                                        │ (Add to tree)
  │                                        │
  │  <event: refinement_accepted>         │
  │<────────────────────────────────────────
  │  data: { new_steps: [...] }           │
  │                                        │
  │  <event: step_completed>              │
  │<────────────────────────────────────────
  │  data: { step_id, result, quality }   │
  │                                        │
  │  <event: final_answer>                │
  │<────────────────────────────────────────
  │  data: { answer, citations, ... }     │
  │                                        │
```

This bidirectional communication pattern allows for:
- **Real-time query refinement** (like asking follow-up questions)
- **Context-aware integration** (new queries use existing research)
- **Dynamic tree expansion** (adds branches without restarting)
- **Interactive research** (user guides the investigation)

---

## 3. Component Architecture

See `/home/runner/work/VCC-Veritas/VCC-Veritas/backend/` structure:

```
backend/
├── core/
│   └── orchestration/
│       ├── tree_based_orchestrator.py          # Main orchestrator
│       ├── query_analyzer.py                    # Query → Hypotheses
│       ├── execution_plan_generator.py          # Generate plans
│       ├── plan_selector.py                     # Select optimal
│       └── execution_tree_manager.py            # Manage tree
│
├── agents/
│   ├── framework/
│   │   ├── agent_worker.py                      # Token-budgeted execution
│   │   ├── tree_verifier.py                     # Branch quality evaluation
│   │   ├── result_aggregator.py                 # Consolidate results
│   │   └── answer_synthesizer.py                # Final answer
│   │
│   └── interactive/
│       ├── sse_handler.py                       # SSE protocol
│       ├── refinement_processor.py              # Handle user refinements
│       └── session_manager.py                   # Manage sessions
```

---

## 4. Execution Tree Model

### 4.1 Example Tree Structure

```
ExecutionTree for: "Bauantrag Windkraftanlage in Naturschutzgebiet"

ROOT (session_abc123)
│
├─ STEP_1 (Vector Search) [PARALLEL]
│  ├─ SUB_1.1: Search "BImSchG Genehmigung WKA" → 15 docs
│  ├─ SUB_1.2: Search "BNatSchG Ausnahmen" → 12 docs
│  ├─ SUB_1.3: Search "Baurecht Windenergie" → 18 docs
│  └─ SUB_1.4: Search "UVP WKA" → 10 docs
│  Status: COMPLETED, Quality: 8.5/10
│
├─ STEP_2 (Graph Traversal) [PARALLEL with STEP_1]
│  └─ Traverse legal relationships (BImSchG ↔ BNatSchG)
│     Result: 45 connections, Status: COMPLETED, Quality: 9/10
│
├─ STEP_3 (Agent Baurecht) [PARALLEL with STEP_1, STEP_2]
│  ├─ Initial consultation → Preliminary findings
│  └─ AGENT_REQUESTED: Additional step
│      └─ STEP_3.1 (Fulltext search case law) → 8 precedents
│         Status: COMPLETED, Quality: 9.5/10
│
├─ STEP_4 (USER_REFINEMENT: "Was ist mit Artenschutz?") [t=2s]
│  └─ STEP_4.1 (Agent Naturschutz)
│      ├─ Search "Artenschutz Windkraft" → 14 docs
│      └─ Agent analysis → Expert findings
│         Status: COMPLETED, Quality: 9/10
│
└─ SYNTHESIS (Aggregate all branches)
   ├─ Input: Results from STEP_1, STEP_2, STEP_3, STEP_4
   ├─ Reranking: 67 docs → Top 15
   └─ LLM synthesis → Final answer
      Status: COMPLETED, Quality: 9.2/10
```

---

## 5. Implementation Blueprint

### 5.1 API Endpoints

```python
from fastapi import FastAPI, BackgroundTasks
from sse_starlette.sse import EventSourceResponse

app = FastAPI()

@app.post("/query")
async def query_endpoint(
    request: QueryRequest,
    background_tasks: BackgroundTasks
) -> EventSourceResponse:
    """
    Main query endpoint with SSE streaming.
    
    Returns SSE stream with:
    - analysis_complete
    - plan_selected
    - step_started / step_completed
    - final_answer
    """
    session_id = str(uuid4())
    sse_handler = SSEHandler(session_id)
    
    background_tasks.add_task(
        orchestrate_query,
        request=request,
        session_id=session_id,
        sse_handler=sse_handler
    )
    
    return EventSourceResponse(sse_handler.stream_events())

@app.post("/query/refine")
async def refine_query(refinement: RefinementRequest):
    """
    Handle user refinement during execution.
    
    Adds new sub-queries to existing execution tree.
    """
    session = session_manager.get_session(refinement.session_id)
    tree = session.execution_tree
    
    new_nodes = await tree_manager.handle_user_refinement(
        tree=tree,
        refinement_query=refinement.query,
        integrate_into_current=refinement.integrate
    )
    
    return {"status": "accepted", "new_steps": len(new_nodes)}
```

### 5.2 Core Data Structures

```python
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum

class ComplexityLevel(Enum):
    SIMPLE_ASK = "simple_ask"
    RESEARCH_BASIC = "research_basic"
    RESEARCH_DEEP = "research_deep"
    SCIENTIFIC = "scientific"
    EXPERT_ANALYSIS = "expert_analysis"

@dataclass
class TreeNode:
    """Node in execution tree"""
    node_id: str
    node_type: str                      # step, agent_request, user_refinement
    step: Optional['ExecutionStep']
    parent_id: Optional[str]
    children_ids: List[str]
    status: str                         # pending, running, completed
    result: Optional[Any] = None
    quality_score: Optional[float] = None

@dataclass
class ExecutionTree:
    """Complete execution tree"""
    tree_id: str
    session_id: str
    root_node: TreeNode
    nodes: Dict[str, TreeNode]
    execution_plan: Optional['ExecutionPlan']
    status: str                         # running, completed
```

---

## 6. Cost-Benefit Analysis

Every plan includes:
- **Total Cost** (€): Sum of all resource costs
- **Total Time** (seconds): Critical path duration
- **Expected Quality** (0-10): Predicted answer quality
- **Success Probability** (0-1): Likelihood of satisfactory result

Plans are ranked using weighted scoring:
```
Score = w1 * (1 - normalized_cost) 
      + w2 * (1 - normalized_time) 
      + w3 * normalized_quality
      + w4 * success_probability
```

User preference adjusts weights:
- **Speed**: w2 = 0.5 (prioritize time)
- **Cost**: w1 = 0.5 (prioritize cost)
- **Quality**: w3 = 0.5 (prioritize quality)
- **Balanced**: w1 = w2 = w3 = w4 = 0.25

---

## 7. Comparison to Current System

| Aspect | Current System | New System |
|--------|---------------|------------|
| **Query Understanding** | Direct routing | Hypothesis generation |
| **Planning** | Implicit | Explicit multi-plan |
| **Cost Awareness** | Post-execution | Pre-execution analysis |
| **Execution Model** | Linear pipeline | Tree (parallel + sequential) |
| **Interactivity** | One-shot | Bidirectional SSE |
| **Adaptivity** | Fixed steps | Dynamic expansion |
| **Quality Control** | End-only | Continuous verification |
| **User Refinement** | Not supported | **Real-time integration** |

---

## 8. Migration Strategy

### Phase 1: Foundation (Week 1-2)
- Implement data structures
- Implement QueryAnalyzer
- Implement PlanGenerator/Selector
- Unit tests

### Phase 2: Execution Engine (Week 3-4)
- Implement ExecutionTreeManager
- Implement SSEHandler
- Implement RefinementProcessor
- Integration with UDS3

### Phase 3: Quality & Aggregation (Week 5-6)
- Implement TreeVerifier
- Implement ResultAggregator
- Implement pruning logic
- Adaptive agent requests

### Phase 4: API & Integration (Week 7-8)
- New /query endpoint with SSE
- /query/refine endpoint
- Session management
- Frontend integration

### Phase 5: Testing & Optimization (Week 9-10)
- End-to-end testing
- Performance optimization
- Load testing
- Documentation

---

## 9. Example Scenarios

### Simple Query
```
Query: "Was ist §45 BNatSchG?"
Plan: Speed-Optimized (€0.01, 2s, 7/10)
Tree: Vector Search → LLM Synthesis
Result: Legal text explanation
Time: 1.8s, Cost: €0.01
```

### Complex Query with Refinement
```
Query: "Bauantrag für Windkraftanlage"
Plan: Balanced (€0.45, 8s, 9/10)
Tree: Vector + Graph + Agents (parallel)

t=2s: User adds "Was ist mit Artenschutz?"
→ Tree expanded with Naturschutz agent

Result: Comprehensive answer covering all aspects
Time: 8.2s, Cost: €0.47, Quality: 9.2/10
```

---

## 10. Conclusion

This **Tree-Based Orchestration Architecture** positions VERITAS as a world-class research system with:

✅ **Hypothesis-driven** understanding  
✅ **Multi-plan** cost-benefit evaluation  
✅ **Tree execution** (parallel + sequential)  
✅ **Interactive refinement** (Copilot Agents style)  
✅ **Adaptive agents** (request more investigation)  
✅ **Quality-based pruning**  
✅ **Token budgets** for cost control  
✅ **Full transparency** via execution tree

**Next Steps**:
1. Review and approve architecture
2. Start implementation (Phase 1)
3. Iterate based on feedback
4. Gradual migration from current system

This transforms VERITAS from a linear RAG system into an **interactive, intelligent research assistant** capable of handling simple questions to complex scientific analyses with optimal resource utilization and continuous user collaboration.
