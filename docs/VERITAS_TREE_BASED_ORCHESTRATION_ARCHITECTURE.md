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
   - 4.1 [Example Tree Structure with Cost-Benefit Tracking](#41-example-tree-structure-with-cost-benefit-tracking)
   - 4.2 [Cost-Benefit Decision Points](#42-cost-benefit-decision-points-in-tree)
5. [Interactive SSE Protocol](#5-interactive-sse-protocol)
6. [Cost-Benefit Analysis](#6-cost-benefit-analysis)
   - 6.1 [Per-Step Cost-Benefit Verification](#61-per-step-cost-benefit-verification)
   - 6.2 [Integrated Overall Cost-Benefit Tracking](#62-integrated-overall-cost-benefit-tracking)
   - 6.3 [Resource Caps and Content Sufficiency Evaluation](#63-resource-caps-and-content-sufficiency-evaluation)
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
│              5. VERIFICATION & PRUNING (Per-Step)                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ TreeVerifier / BranchEvaluator                                │  │
│  │ • **Per-Step Cost-Benefit Evaluation**                       │  │
│  │   - Actual vs Predicted Cost/Time/Quality                    │  │
│  │   - ROI check: Can branch still achieve targets?             │  │
│  │   - Early termination of unprofitable branches               │  │
│  │ • Quality metrics (relevance, completeness, accuracy)        │  │
│  │ • **Integrated Overall Cost-Benefit Tracking**               │  │
│  │   - Running totals: time spent, cost accrued, quality avg    │  │
│  │   - Budget remaining vs steps remaining                      │  │
│  │   - Forecast: Will we finish within constraints?             │  │
│  │ • Decide: Continue | Prune | Request More Steps             │  │
│  │ • Adaptive: Agent can request additional investigation       │  │
│  └──────────────────────────────────────────────────────────────┘  │
│  Output: Pruned tree + Overall execution metrics                    │
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

### 4.1 Example Tree Structure with Cost-Benefit Tracking

```
ExecutionTree for: "Bauantrag Windkraftanlage in Naturschutzgebiet"
Budget: €0.50, 30s, Quality Target: 8.5/10

ROOT (session_abc123)
│
├─ STEP_1 (Vector Search) [PARALLEL]
│  ├─ SUB_1.1: Search "BImSchG Genehmigung WKA" → 15 docs
│  ├─ SUB_1.2: Search "BNatSchG Ausnahmen" → 12 docs
│  ├─ SUB_1.3: Search "Baurecht Windenergie" → 18 docs
│  └─ SUB_1.4: Search "UVP WKA" → 10 docs
│  Status: COMPLETED, Quality: 8.5/10
│  Cost: Predicted €0.05, Actual €0.048, Variance: -4%
│  Time: Predicted 3s, Actual 2.8s, Variance: -7%
│  ROI: 8.5/0.048 = 177 ✅ EXCELLENT
│  Decision: CONTINUE
│
├─ STEP_2 (Graph Traversal) [PARALLEL with STEP_1]
│  └─ Traverse legal relationships (BImSchG ↔ BNatSchG)
│     Result: 45 connections
│     Status: COMPLETED, Quality: 9/10
│     Cost: Predicted €0.08, Actual €0.12, Variance: +50% ⚠️
│     Time: Predicted 4s, Actual 5.5s, Variance: +38%
│     ROI: 9.0/0.12 = 75 ✅ ACCEPTABLE
│     Decision: CONTINUE (high quality justifies cost overrun)
│
├─ STEP_3 (Agent Baurecht) [PARALLEL with STEP_1, STEP_2]
│  ├─ Initial consultation → Preliminary findings
│  │  Cost: Predicted €0.10, Actual €0.11, Variance: +10%
│  │  Time: Predicted 5s, Actual 5.2s, Variance: +4%
│  │  Quality: 7.5/10, ROI: 68
│  │
│  └─ AGENT_REQUESTED: Additional step
│      ├─ Per-Step Verification (t=5.2s):
│      │  Overall Metrics: Cost €0.218, Time 8.5s, Avg Quality 8.3
│      │  Forecast: Will finish on budget ✅, on time ✅
│      │  Agent requests: "Need case law for precedent"
│      │  ROI Forecast: +1.5 quality for €0.06 = ROI 25 ✅
│      │  Decision: APPROVE additional step
│      │
│      └─ STEP_3.1 (Fulltext search case law) → 8 precedents
│         Status: COMPLETED, Quality: 9.5/10
│         Cost: Predicted €0.06, Actual €0.058, Variance: -3%
│         Time: Predicted 3s, Actual 2.9s
│         ROI: (9.5-7.5)/0.058 = 34.5 ✅ GOOD
│         Decision: CONTINUE
│
├─ STEP_4 (USER_REFINEMENT: "Was ist mit Artenschutz?") [t=11.6s]
│  ├─ Per-Step Overall Verification:
│  │  Current Metrics: Cost €0.276, Time 11.6s, Avg Quality 8.5
│  │  Budget Remaining: €0.224, Time 18.4s
│  │  User Refinement Cost Estimate: €0.10, Time 6s
│  │  Projected Total: €0.376, Time 17.6s ✅ Within budget
│  │  Decision: ACCEPT refinement
│  │
│  └─ STEP_4.1 (Agent Naturschutz)
│      ├─ Search "Artenschutz Windkraft" → 14 docs
│      └─ Agent analysis → Expert findings
│         Status: COMPLETED, Quality: 9/10
│         Cost: Predicted €0.10, Actual €0.095, Variance: -5%
│         Time: Predicted 6s, Actual 5.8s
│         ROI: 9.0/0.095 = 94.7 ✅ EXCELLENT
│         Decision: BRANCH SUCCESSFUL
│
├─ [PRUNED] STEP_5 (Agent Umweltverträglichkeit)
│  ├─ Initial estimate: €0.15, Time 8s, Expected Quality: 7/10
│  │  Per-Step Verification (t=17.4s):
│  │  Current Metrics: Cost €0.371, Time 17.4s, Avg Quality 8.75
│  │  Budget Remaining: €0.129, Time 12.6s
│  │  This step would cost €0.15 → Would exceed budget
│  │  ROI: 7.0/0.15 = 46.7 (vs current average 8.75/0.371 = 23.6)
│  │  Decision: PRUNE (insufficient budget, quality already exceeds target)
│  └─ Status: PRUNED, Reason: "budget_exceeded_quality_target_met"
│
└─ SYNTHESIS (Aggregate all branches)
   ├─ Input: Results from STEP_1, STEP_2, STEP_3, STEP_4
   ├─ Reranking: 67 docs → Top 15
   └─ LLM synthesis → Final answer
      Status: COMPLETED, Quality: 9.2/10
      Cost: Predicted €0.08, Actual €0.075
      Time: Predicted 4s, Actual 3.8s
      
FINAL OVERALL METRICS:
═══════════════════════════════════════════════════════════
Time:    Total 21.2s / Budget 30s = 71% utilization ✅
Cost:    Total €0.446 / Budget €0.50 = 89% utilization ✅
Quality: Final 9.2/10 vs Target 8.5/10 = 108% achievement ✅
ROI:     9.2 / (0.446 + 21.2/60) = 18.2 EXCELLENT

Branches: 4 completed, 1 pruned
Steps:    8 completed, 1 pruned
Forecast Accuracy: 92% (predicted €0.48, actual €0.446)
═══════════════════════════════════════════════════════════
```

### 4.2 Cost-Benefit Decision Points in Tree

The example above shows **6 cost-benefit decision points**:

1. **After STEP_1** (t=2.8s): Within budget, good ROI → Continue
2. **After STEP_2** (t=5.5s): Cost overrun but high quality → Continue
3. **After STEP_3.1 Request** (t=5.2s): Agent requests more, forecast looks good → Approve
4. **After STEP_3.1** (t=8.4s): Additional step delivered value → Continue
5. **User Refinement** (t=11.6s): Check if budget allows → Accept
6. **Before STEP_5** (t=17.4s): Would exceed budget, quality already met → **Prune**

Each decision ensures **no wasteful processes** and maintains **integrated overall cost-benefit awareness**.
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
    status: str                         # pending, running, completed, pruned
    result: Optional[Any] = None
    quality_score: Optional[float] = None
    
    # Cost-Benefit Tracking (Per-Step)
    predicted_cost: float = 0.0         # Predicted cost before execution
    actual_cost: float = 0.0            # Actual cost after execution
    predicted_time: float = 0.0         # Predicted time (seconds)
    actual_time: float = 0.0            # Actual time (seconds)
    cost_variance: float = 0.0          # (actual - predicted) / predicted
    roi: float = 0.0                    # quality_improvement / actual_cost
    
    # Pruning Information
    pruned: bool = False
    prune_reason: Optional[str] = None  # e.g., "insufficient_roi", "time_budget_exceeded"

@dataclass
class Branch:
    """Represents a branch in execution tree"""
    branch_id: str
    root_node_id: str
    leaf_nodes: List[str]
    importance: float = 1.0             # Weight for overall calculation
    current_quality: float = 0.0
    
    # Branch-Level Cost-Benefit
    branch_predicted_cost: float = 0.0
    branch_actual_cost: float = 0.0
    branch_predicted_time: float = 0.0
    branch_actual_time: float = 0.0
    branch_roi: float = 0.0
    should_continue: bool = True        # False if pruned

@dataclass
class ExecutionTree:
    """Complete execution tree with integrated cost-benefit tracking"""
    tree_id: str
    session_id: str
    root_node: TreeNode
    nodes: Dict[str, TreeNode]
    branches: Dict[str, Branch]
    execution_plan: Optional['ExecutionPlan']
    status: str                         # running, completed
    
    # Overall Execution Metrics
    overall_metrics: 'OverallExecutionMetrics'
    
    # Budget Constraints
    time_budget: float                  # Maximum allowed time (seconds)
    cost_budget: float                  # Maximum allowed cost (€)
    quality_target: float               # Minimum acceptable quality (0-10)
    
    # Timestamps
    start_time: float
    end_time: Optional[float] = None
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

### 6.1 Per-Step Cost-Benefit Verification

**Critical Requirement**: Each branch must be verified at **every step** to ensure it can still achieve its cost-performance targets. This prevents wasteful execution of unprofitable branches.

#### Per-Step Evaluation Criteria

For each completed step in a branch:

1. **Actual vs Predicted Comparison**
   ```python
   actual_cost = sum(step.resource_costs for step in branch.completed_steps)
   predicted_cost = branch.initial_plan.predicted_cost
   cost_variance = (actual_cost - predicted_cost) / predicted_cost
   
   # If cost overrun > 20%, evaluate continuation
   if cost_variance > 0.20:
       should_continue = evaluate_branch_viability(branch)
   ```

2. **ROI Check (Return on Investment)**
   ```python
   # Can this branch still deliver value given remaining budget?
   remaining_budget = total_budget - actual_cost
   remaining_steps_estimated_cost = estimate_remaining_cost(branch)
   expected_quality_improvement = estimate_quality_gain(branch)
   
   roi = expected_quality_improvement / remaining_steps_estimated_cost
   
   # Prune if ROI < threshold
   if roi < min_roi_threshold:
       prune_branch(branch, reason="insufficient_roi")
   ```

3. **Quality Trajectory Analysis**
   ```python
   # Is quality improving with each step?
   quality_scores = [step.quality_score for step in branch.completed_steps]
   quality_trend = calculate_trend(quality_scores)
   
   # If quality is declining or stagnant, reconsider
   if quality_trend <= 0 and len(quality_scores) >= 2:
       evaluate_alternative_approach(branch)
   ```

4. **Time Budget Enforcement**
   ```python
   elapsed_time = current_time - branch.start_time
   predicted_remaining_time = estimate_remaining_time(branch)
   total_projected_time = elapsed_time + predicted_remaining_time
   
   # Prune if we'll exceed time budget
   if total_projected_time > time_budget:
       prune_branch(branch, reason="time_budget_exceeded")
   ```

#### Pruning Decision Matrix

| Metric | Status | Action |
|--------|--------|--------|
| Cost Variance | < 20% | ✅ Continue |
| Cost Variance | 20-50% | ⚠️ Review ROI |
| Cost Variance | > 50% | 🛑 Prune (unless exceptional quality) |
| ROI | > 2.0 | ✅ Continue |
| ROI | 1.0-2.0 | ⚠️ Monitor closely |
| ROI | < 1.0 | 🛑 Prune |
| Quality Trend | Improving | ✅ Continue |
| Quality Trend | Stable | ⚠️ Consider alternatives |
| Quality Trend | Declining | 🛑 Prune or pivot |
| Time Projection | Within budget | ✅ Continue |
| Time Projection | 10% over budget | ⚠️ Accelerate |
| Time Projection | > 20% over budget | 🛑 Prune |

### 6.2 Integrated Overall Cost-Benefit Tracking

**Critical Requirement**: Maintain a **real-time, integrated view** of overall execution metrics across all active branches.

#### Overall Metrics Dashboard

```python
@dataclass
class OverallExecutionMetrics:
    """Real-time tracking of overall execution performance"""
    
    # Time Metrics
    total_elapsed_time: float                    # Seconds since start
    predicted_remaining_time: float              # Estimated time to completion
    time_budget_remaining: float                 # time_budget - total_elapsed_time
    time_utilization: float                      # total_elapsed_time / time_budget
    
    # Cost Metrics
    total_cost_accrued: float                    # €, sum across all branches
    predicted_remaining_cost: float              # Estimated cost to completion
    cost_budget_remaining: float                 # cost_budget - total_cost_accrued
    cost_utilization: float                      # total_cost_accrued / cost_budget
    
    # Quality Metrics
    weighted_average_quality: float              # Weighted by branch importance
    best_branch_quality: float                   # Highest quality achieved so far
    quality_variance: float                      # Consistency across branches
    
    # Efficiency Metrics
    cost_per_quality_point: float                # total_cost / weighted_average_quality
    time_per_quality_point: float                # total_elapsed_time / weighted_average_quality
    overall_roi: float                           # quality / (cost + time_penalty)
    
    # Progress Metrics
    completed_steps: int                         # Total steps completed
    active_steps: int                            # Currently executing
    pending_steps: int                           # Not yet started
    pruned_steps: int                            # Terminated early
    completion_percentage: float                 # Based on critical path
    
    # Forecast Metrics
    will_finish_on_time: bool                    # Projected vs time budget
    will_finish_on_budget: bool                  # Projected vs cost budget
    will_achieve_quality_target: bool            # Projected vs quality target
    confidence_in_forecast: float                # 0-1, based on variance
```

#### Per-Step Updates

After **every step completion**, update overall metrics:

```python
def update_overall_metrics_after_step(
    step: ExecutionStep,
    branch: Branch,
    overall_metrics: OverallExecutionMetrics
) -> OverallExecutionMetrics:
    """
    Updates integrated overall cost-benefit metrics after each step.
    This ensures we always have a current view of execution health.
    """
    
    # 1. Update time metrics
    overall_metrics.total_elapsed_time = time.time() - execution_start_time
    overall_metrics.predicted_remaining_time = estimate_remaining_time_all_branches()
    overall_metrics.time_budget_remaining = time_budget - overall_metrics.total_elapsed_time
    overall_metrics.time_utilization = overall_metrics.total_elapsed_time / time_budget
    
    # 2. Update cost metrics
    overall_metrics.total_cost_accrued += step.actual_cost
    overall_metrics.predicted_remaining_cost = estimate_remaining_cost_all_branches()
    overall_metrics.cost_budget_remaining = cost_budget - overall_metrics.total_cost_accrued
    overall_metrics.cost_utilization = overall_metrics.total_cost_accrued / cost_budget
    
    # 3. Update quality metrics (weighted by branch importance)
    branch_qualities = [(b.importance, b.current_quality) for b in active_branches]
    overall_metrics.weighted_average_quality = weighted_average(branch_qualities)
    overall_metrics.best_branch_quality = max(b.current_quality for b in active_branches)
    overall_metrics.quality_variance = variance([b.current_quality for b in active_branches])
    
    # 4. Calculate efficiency metrics
    if overall_metrics.weighted_average_quality > 0:
        overall_metrics.cost_per_quality_point = (
            overall_metrics.total_cost_accrued / overall_metrics.weighted_average_quality
        )
        overall_metrics.time_per_quality_point = (
            overall_metrics.total_elapsed_time / overall_metrics.weighted_average_quality
        )
    
    # 5. Calculate overall ROI
    time_penalty = overall_metrics.total_elapsed_time / 60  # Penalty for long execution
    overall_metrics.overall_roi = overall_metrics.weighted_average_quality / (
        overall_metrics.total_cost_accrued + time_penalty
    )
    
    # 6. Update progress metrics
    overall_metrics.completed_steps = count_completed_steps()
    overall_metrics.active_steps = count_active_steps()
    overall_metrics.pending_steps = count_pending_steps()
    overall_metrics.completion_percentage = calculate_completion_percentage()
    
    # 7. Forecast future completion
    overall_metrics.will_finish_on_time = (
        overall_metrics.total_elapsed_time + overall_metrics.predicted_remaining_time 
        <= time_budget
    )
    overall_metrics.will_finish_on_budget = (
        overall_metrics.total_cost_accrued + overall_metrics.predicted_remaining_cost 
        <= cost_budget
    )
    overall_metrics.will_achieve_quality_target = (
        overall_metrics.weighted_average_quality >= quality_target
    )
    
    # 8. Confidence in forecast (based on historical variance)
    overall_metrics.confidence_in_forecast = calculate_forecast_confidence(
        historical_predictions, actual_outcomes
    )
    
    return overall_metrics
```

#### Global Decision Making

Based on overall metrics, make **execution-wide decisions**:

```python
def evaluate_overall_execution_health(
    overall_metrics: OverallExecutionMetrics
) -> ExecutionDecision:
    """
    Evaluates overall execution health and makes global decisions.
    """
    
    # Critical failure conditions
    if overall_metrics.cost_utilization > 0.90 and not overall_metrics.will_finish_on_budget:
        return ExecutionDecision.TERMINATE_ALL("Cost budget nearly exhausted")
    
    if overall_metrics.time_utilization > 0.90 and not overall_metrics.will_finish_on_time:
        return ExecutionDecision.ACCELERATE_ALL("Time budget critical")
    
    # Low ROI across all branches
    if overall_metrics.overall_roi < 1.5 and overall_metrics.completion_percentage < 0.5:
        return ExecutionDecision.PIVOT_STRATEGY("Overall ROI insufficient")
    
    # Quality concerns
    if overall_metrics.weighted_average_quality < 5.0 and overall_metrics.completion_percentage > 0.7:
        return ExecutionDecision.ADD_QUALITY_STEPS("Quality below acceptable threshold")
    
    # All good - continue execution
    if (overall_metrics.will_finish_on_time and 
        overall_metrics.will_finish_on_budget and
        overall_metrics.will_achieve_quality_target):
        return ExecutionDecision.CONTINUE("On track to meet all targets")
    
    # Need optimization
    return ExecutionDecision.OPTIMIZE_EXECUTION("Adjust branch priorities")
```

#### SSE Event Streaming

Stream overall metrics to client in real-time:

```python
{
    "event": "overall_metrics_update",
    "data": {
        "time_elapsed": "12.5s",
        "time_budget_remaining": "17.5s",
        "cost_accrued": "€0.23",
        "cost_budget_remaining": "€0.22",
        "average_quality": 8.2,
        "completion": "65%",
        "forecast": {
            "will_finish_on_time": true,
            "will_finish_on_budget": true,
            "confidence": 0.85
        },
        "branches": {
            "active": 3,
            "completed": 2,
            "pruned": 1
        }
    }
}
```

This provides **full transparency** to users about execution progress and resource utilization.

---

## 6.3 Resource Caps and Content Sufficiency Evaluation

**Critical Requirements**: 
1. When have we gathered **enough resources** (documents, data points)?
2. When has **enough time** elapsed to justify stopping?
3. How do we quantify if the content is **sufficient for a quality answer**?

### 6.3.1 Multi-Dimensional Cap System

The system implements **5 types of caps** that can trigger termination:

```python
@dataclass
class ExecutionCaps:
    """Multi-dimensional caps for execution termination"""
    
    # Time Caps
    max_total_time: float = 30.0           # Hard limit: total execution time (seconds)
    soft_time_threshold: float = 0.80       # Soft limit: 80% of time budget
    
    # Cost Caps
    max_total_cost: float = 0.50           # Hard limit: total cost (€)
    soft_cost_threshold: float = 0.85       # Soft limit: 85% of cost budget
    
    # Resource Quantity Caps
    max_documents_retrieved: int = 100      # Hard limit: total documents
    min_documents_for_answer: int = 5       # Minimum viable documents
    optimal_documents_range: tuple = (15, 30)  # Sweet spot for quality
    
    max_api_calls: int = 50                 # Hard limit: external API calls
    max_llm_invocations: int = 10           # Hard limit: LLM calls
    
    # Quality Caps (Termination Conditions)
    target_quality_score: float = 8.5       # If achieved, can terminate early
    min_acceptable_quality: float = 6.0     # Below this, must continue
    quality_plateau_threshold: float = 0.1  # If improvement < 0.1 over 3 steps
    
    # Content Sufficiency Caps
    min_evidence_coverage: float = 0.70     # 70% of query aspects must be covered
    min_source_diversity: int = 3           # Minimum different source types
    min_confidence_level: float = 0.75      # Minimum confidence in answer
```

### 6.3.2 Resource Cap Evaluation

**When to stop gathering resources?**

```python
class ResourceCapEvaluator:
    """Evaluates whether we've gathered enough resources"""
    
    def should_stop_gathering(
        self,
        current_state: ExecutionState,
        caps: ExecutionCaps
    ) -> tuple[bool, str]:
        """
        Returns (should_stop, reason)
        """
        
        # 1. HARD CAPS - Must stop
        if current_state.total_documents >= caps.max_documents_retrieved:
            return (True, "max_documents_reached")
        
        if current_state.total_api_calls >= caps.max_api_calls:
            return (True, "max_api_calls_reached")
        
        if current_state.total_time >= caps.max_total_time:
            return (True, "max_time_exceeded")
        
        if current_state.total_cost >= caps.max_total_cost:
            return (True, "max_cost_exceeded")
        
        # 2. OPTIMAL RANGE - Can stop if quality is good
        docs_in_optimal_range = (
            caps.optimal_documents_range[0] 
            <= current_state.total_documents 
            <= caps.optimal_documents_range[1]
        )
        
        if docs_in_optimal_range and current_state.quality_score >= caps.target_quality_score:
            return (True, "optimal_documents_with_quality_target")
        
        # 3. SOFT CAPS - Consider stopping
        soft_time_reached = current_state.total_time >= (
            caps.max_total_time * caps.soft_time_threshold
        )
        soft_cost_reached = current_state.total_cost >= (
            caps.max_total_cost * caps.soft_cost_threshold
        )
        
        if soft_time_reached and soft_cost_reached:
            # Check if we have minimum viable content
            has_min_docs = current_state.total_documents >= caps.min_documents_for_answer
            has_min_quality = current_state.quality_score >= caps.min_acceptable_quality
            
            if has_min_docs and has_min_quality:
                return (True, "soft_caps_reached_with_viable_content")
        
        # 4. DIMINISHING RETURNS - Stop if not improving
        if self._is_quality_plateauing(current_state, caps):
            return (True, "quality_plateau_reached")
        
        # 5. CONTENT SUFFICIENCY - Check if we have enough
        if self._is_content_sufficient(current_state, caps):
            return (True, "content_sufficiency_achieved")
        
        # Continue gathering
        return (False, "continue_gathering")
    
    def _is_quality_plateauing(
        self,
        current_state: ExecutionState,
        caps: ExecutionCaps
    ) -> bool:
        """Check if quality has stopped improving"""
        if len(current_state.quality_history) < 3:
            return False
        
        recent_qualities = current_state.quality_history[-3:]
        max_improvement = max(recent_qualities) - min(recent_qualities)
        
        return max_improvement < caps.quality_plateau_threshold
    
    def _is_content_sufficient(
        self,
        current_state: ExecutionState,
        caps: ExecutionCaps
    ) -> bool:
        """Check if content is sufficient for quality answer"""
        # Delegate to ContentSufficiencyEvaluator
        return ContentSufficiencyEvaluator().evaluate(current_state, caps)
```

### 6.3.3 Content Sufficiency Quantification

**How to quantify if search results are sufficient?**

The system uses a **multi-factor Content Sufficiency Score (CSS)**:

```python
class ContentSufficiencyEvaluator:
    """
    Quantifies whether gathered content is sufficient for a quality answer.
    Uses multiple dimensions to calculate a Content Sufficiency Score (0-1).
    """
    
    def evaluate(
        self,
        current_state: ExecutionState,
        caps: ExecutionCaps
    ) -> bool:
        """
        Returns True if content is sufficient.
        """
        css = self.calculate_content_sufficiency_score(current_state)
        return css >= 0.75  # 75% sufficiency threshold
    
    def calculate_content_sufficiency_score(
        self,
        current_state: ExecutionState
    ) -> float:
        """
        Calculates Content Sufficiency Score (CSS) using 6 dimensions.
        
        CSS = weighted average of:
        1. Evidence Coverage (30%)
        2. Source Diversity (15%)
        3. Document Quality (20%)
        4. Information Density (15%)
        5. Confidence Level (15%)
        6. Completeness (5%)
        """
        
        # 1. Evidence Coverage (30%) - How much of the query is addressed?
        evidence_coverage = self._calculate_evidence_coverage(current_state)
        
        # 2. Source Diversity (15%) - Multiple independent sources?
        source_diversity = self._calculate_source_diversity(current_state)
        
        # 3. Document Quality (20%) - Are documents authoritative?
        doc_quality = self._calculate_document_quality(current_state)
        
        # 4. Information Density (15%) - Rich, detailed information?
        info_density = self._calculate_information_density(current_state)
        
        # 5. Confidence Level (15%) - System confidence in answer
        confidence = current_state.confidence_score
        
        # 6. Completeness (5%) - All query aspects covered?
        completeness = self._calculate_completeness(current_state)
        
        # Weighted average
        css = (
            0.30 * evidence_coverage +
            0.15 * source_diversity +
            0.20 * doc_quality +
            0.15 * info_density +
            0.15 * confidence +
            0.05 * completeness
        )
        
        return css
    
    def _calculate_evidence_coverage(self, state: ExecutionState) -> float:
        """
        Evidence Coverage: How many query aspects have supporting evidence?
        
        Returns: 0-1 score
        """
        query_aspects = state.query_decomposition.aspects  # e.g., ["legal requirements", "documents needed", "deadlines"]
        
        covered_aspects = []
        for aspect in query_aspects:
            # Check if we have documents that address this aspect
            has_evidence = any(
                self._document_addresses_aspect(doc, aspect)
                for doc in state.retrieved_documents
            )
            if has_evidence:
                covered_aspects.append(aspect)
        
        coverage_ratio = len(covered_aspects) / len(query_aspects) if query_aspects else 0
        return coverage_ratio
    
    def _calculate_source_diversity(self, state: ExecutionState) -> float:
        """
        Source Diversity: Variety of independent sources.
        
        High diversity (0.9-1.0): 5+ different source types, 10+ unique sources
        Medium diversity (0.6-0.8): 3-4 source types, 5-9 unique sources
        Low diversity (0.3-0.5): 1-2 source types, 2-4 unique sources
        """
        # Count source types (legal_db, api, web, graph, etc.)
        source_types = set(doc.source_type for doc in state.retrieved_documents)
        num_source_types = len(source_types)
        
        # Count unique sources (domains, databases, etc.)
        unique_sources = set(doc.source_id for doc in state.retrieved_documents)
        num_unique_sources = len(unique_sources)
        
        # Score based on counts
        type_score = min(num_source_types / 5.0, 1.0)  # 5 types = perfect
        source_score = min(num_unique_sources / 10.0, 1.0)  # 10 sources = perfect
        
        return (type_score + source_score) / 2
    
    def _calculate_document_quality(self, state: ExecutionState) -> float:
        """
        Document Quality: Average quality/authority of retrieved documents.
        
        Uses:
        - Relevance scores from retrieval
        - Authority scores (e.g., official legal sources > blog posts)
        - Reranking scores
        """
        if not state.retrieved_documents:
            return 0.0
        
        quality_scores = []
        for doc in state.retrieved_documents:
            # Combine multiple quality signals
            relevance = doc.relevance_score  # From vector/graph search
            authority = self._get_authority_score(doc)  # Source authority
            rerank_score = doc.rerank_score if hasattr(doc, 'rerank_score') else 0.5
            
            # Weighted average
            doc_quality = (
                0.40 * relevance +
                0.30 * authority +
                0.30 * rerank_score
            )
            quality_scores.append(doc_quality)
        
        return sum(quality_scores) / len(quality_scores)
    
    def _calculate_information_density(self, state: ExecutionState) -> float:
        """
        Information Density: How much useful information per document?
        
        High density: Long documents with detailed information
        Low density: Short snippets with little detail
        """
        if not state.retrieved_documents:
            return 0.0
        
        density_scores = []
        for doc in state.retrieved_documents:
            # Length score (longer = more detailed, up to a point)
            length_score = min(len(doc.content) / 2000, 1.0)  # 2000 chars = ideal
            
            # Entity count (more entities = more information)
            entity_count = len(doc.entities) if hasattr(doc, 'entities') else 0
            entity_score = min(entity_count / 10, 1.0)  # 10 entities = good
            
            # Citation count (cited sources = authoritative)
            citation_count = len(doc.citations) if hasattr(doc, 'citations') else 0
            citation_score = min(citation_count / 5, 1.0)  # 5 citations = good
            
            density = (length_score + entity_score + citation_score) / 3
            density_scores.append(density)
        
        return sum(density_scores) / len(density_scores)
    
    def _calculate_completeness(self, state: ExecutionState) -> float:
        """
        Completeness: Are all parts of the query addressed?
        
        Uses LLM to evaluate if gathered content can answer the full query.
        """
        # Quick check: minimum documents
        if state.total_documents < 5:
            return 0.3  # Likely incomplete
        
        # LLM-based evaluation (cached for efficiency)
        prompt = f"""
        Query: {state.original_query}
        
        Retrieved Documents: {len(state.retrieved_documents)} documents
        Document Summaries: {self._get_document_summaries(state)}
        
        Question: Can the retrieved documents fully answer the query?
        
        Consider:
        1. Are all aspects of the query addressed?
        2. Is there sufficient detail for each aspect?
        3. Are there any obvious gaps?
        
        Respond with a completeness score (0-1) and brief explanation.
        Format: {{"score": 0.85, "explanation": "..."}}
        """
        
        # Call LLM (use small model for efficiency)
        llm_response = call_llm_for_completeness_check(prompt, model="small")
        
        return llm_response.get("score", 0.5)
    
    def _get_authority_score(self, doc: Document) -> float:
        """
        Authority score based on source type.
        
        Official legal databases: 1.0
        Government websites: 0.9
        Academic sources: 0.85
        Professional organizations: 0.8
        News outlets: 0.6
        Blogs/forums: 0.3
        """
        authority_map = {
            "legal_db": 1.0,
            "government": 0.9,
            "academic": 0.85,
            "professional": 0.8,
            "news": 0.6,
            "blog": 0.3,
            "unknown": 0.5
        }
        return authority_map.get(doc.source_type, 0.5)
```

### 6.3.4 Integrated Cap Decision Flow

**Complete decision flow at each step:**

```python
def evaluate_continuation_decision(
    current_state: ExecutionState,
    caps: ExecutionCaps
) -> ContinuationDecision:
    """
    Comprehensive evaluation of whether to continue or terminate.
    
    Called after EVERY step completion.
    """
    
    # 1. Check Hard Caps (Must Stop)
    should_stop, reason = ResourceCapEvaluator().should_stop_gathering(
        current_state, caps
    )
    if should_stop and "max_" in reason:
        return ContinuationDecision(
            action="TERMINATE",
            reason=reason,
            confidence=1.0
        )
    
    # 2. Check Content Sufficiency
    css = ContentSufficiencyEvaluator().calculate_content_sufficiency_score(
        current_state
    )
    
    # High sufficiency + soft cap reached = terminate
    if css >= 0.85 and should_stop:
        return ContinuationDecision(
            action="TERMINATE",
            reason=f"high_content_sufficiency ({css:.2f}) + {reason}",
            confidence=0.9,
            css=css
        )
    
    # Exceptional sufficiency = terminate even before caps
    if css >= 0.95:
        return ContinuationDecision(
            action="TERMINATE",
            reason=f"exceptional_content_sufficiency ({css:.2f})",
            confidence=0.95,
            css=css
        )
    
    # 3. Check if we're making progress
    if css < 0.40 and current_state.completed_steps >= 3:
        # Low sufficiency after 3 steps = need different approach
        return ContinuationDecision(
            action="PIVOT",
            reason=f"low_content_sufficiency ({css:.2f}) - pivot strategy",
            confidence=0.7,
            css=css
        )
    
    # 4. Continue with guidance
    if css < 0.60:
        # Need more content
        return ContinuationDecision(
            action="CONTINUE",
            reason=f"content_insufficiency ({css:.2f}) - gather more",
            confidence=0.8,
            css=css,
            recommendation="prioritize_high_quality_sources"
        )
    
    # Moderate sufficiency, continue optimistically
    return ContinuationDecision(
        action="CONTINUE",
        reason=f"moderate_sufficiency ({css:.2f}) - continue to optimize",
        confidence=0.75,
        css=css,
        recommendation="focus_on_quality_over_quantity"
    )


@dataclass
class ContinuationDecision:
    """Decision on whether to continue execution"""
    action: str                         # CONTINUE, TERMINATE, PIVOT
    reason: str                         # Human-readable reason
    confidence: float                   # Confidence in decision (0-1)
    css: Optional[float] = None         # Content Sufficiency Score
    recommendation: Optional[str] = None # Guidance for next steps
```

### 6.3.5 Real-Time Cap Monitoring (SSE)

Stream cap status to users:

```json
{
    "event": "cap_status_update",
    "data": {
        "time_cap": {
            "used": "12.5s",
            "limit": "30.0s",
            "utilization": 0.42,
            "status": "ok"
        },
        "cost_cap": {
            "used": "€0.23",
            "limit": "€0.50",
            "utilization": 0.46,
            "status": "ok"
        },
        "document_cap": {
            "retrieved": 23,
            "optimal_range": [15, 30],
            "status": "optimal"
        },
        "content_sufficiency": {
            "score": 0.78,
            "threshold": 0.75,
            "status": "sufficient",
            "breakdown": {
                "evidence_coverage": 0.85,
                "source_diversity": 0.70,
                "document_quality": 0.82,
                "information_density": 0.75,
                "confidence": 0.80,
                "completeness": 0.75
            }
        },
        "decision": {
            "action": "CONTINUE",
            "reason": "moderate_sufficiency (0.78) - continue to optimize",
            "confidence": 0.75
        }
    }
}
```

### 6.3.6 Example: Cap-Triggered Termination

```
Query: "Bauantrag Windkraft in Naturschutzgebiet"
Caps: 30s, €0.50, Quality Target 8.5/10

Step 1 (t=3s, €0.05): Vector Search → 18 docs, CSS=0.45
  Decision: CONTINUE (low CSS, well within caps)

Step 2 (t=6s, €0.13): Graph Search → +12 docs, CSS=0.62
  Decision: CONTINUE (moderate CSS, sufficient budget)

Step 3 (t=11s, €0.24): Legal Agent → +8 docs, CSS=0.76
  Decision: CONTINUE (approaching sufficiency, budget ok)

Step 4 (t=16s, €0.35): Construction Agent → +6 docs, CSS=0.82
  Decision: CONTINUE (good CSS, still have budget)

User Refinement (t=16s): "Was ist mit Artenschutz?"
  New Branch: Environmental Agent
  Cost Estimate: €0.12, Time: 6s
  Projected Total: €0.47, 22s
  CSS if added: 0.89 (estimated)
  Decision: ACCEPT (high projected CSS, within budget)

Step 5 (t=22s, €0.47): Environmental Agent → +9 docs, CSS=0.88
  ✅ TERMINATE: "high_content_sufficiency (0.88) + soft_time_reached"
  
  Breakdown:
  - Evidence Coverage: 0.92 (all query aspects covered)
  - Source Diversity: 0.85 (4 source types, 8 unique sources)
  - Document Quality: 0.90 (high authority sources)
  - Information Density: 0.82 (detailed documents)
  - Confidence: 0.85 (high system confidence)
  - Completeness: 0.90 (LLM confirms all aspects addressed)
  
  Final: 53 documents, 22s, €0.47, Quality 9.1/10
```

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
✅ **Per-step cost-benefit verification** (no wasteful processes)  
✅ **Integrated overall cost-benefit tracking** (real-time execution health)  
✅ **Multi-dimensional resource caps** (time, cost, documents, quality) **NEW**  
✅ **Content Sufficiency Score (CSS)** - 6-factor quantification **NEW**  
✅ **Intelligent termination** (stops when sufficient, not just when budget exhausted)  
✅ **Quality-based pruning** with ROI analysis  
✅ **Token budgets** for cost control  
✅ **Full transparency** via execution tree and real-time metrics

### Key Innovations

**1. Per-Step Cost-Benefit Verification**: Every branch is evaluated after each step completion to ensure it can still achieve its cost-performance targets. This prevents wasteful execution of branches that have deviated too far from their predicted cost/time/quality metrics.

**2. Integrated Overall Tracking**: A real-time dashboard of overall execution metrics (time, cost, quality, ROI) is maintained and updated after every step. This provides forecast accuracy, budget utilization monitoring, quality trajectory analysis, and global decision making.

**3. Resource Caps**: Multi-dimensional cap system with hard limits (must stop), soft limits (consider stopping), and optimal ranges (sweet spot). Includes time caps (30s max), cost caps (€0.50 max), document caps (100 max, 15-30 optimal), and quality targets (8.5/10).

**4. Content Sufficiency Quantification**: The **Content Sufficiency Score (CSS)** uses 6 dimensions to quantify whether gathered content is sufficient for a quality answer:
- **Evidence Coverage** (30%): How many query aspects have supporting evidence?
- **Source Diversity** (15%): Multiple independent sources?
- **Document Quality** (20%): Authoritative, relevant sources?
- **Information Density** (15%): Rich, detailed content?
- **Confidence Level** (15%): System confidence in answer?
- **Completeness** (5%): All aspects addressed? (LLM-evaluated)

CSS ≥ 0.75 = sufficient, CSS ≥ 0.85 = high sufficiency, CSS ≥ 0.95 = exceptional (can terminate early).

**5. Intelligent Termination**: The system doesn't just run until budget exhausted. It can terminate early when:
- CSS ≥ 0.95 (exceptional content gathered)
- CSS ≥ 0.85 + soft caps reached (high sufficiency with efficient resource use)
- Quality plateau detected (no improvement over last 3 steps)
- Optimal document range achieved with quality target met

**Example**: In a €0.50, 30s budget scenario, the system:
1. Tracks actual vs predicted cost at each step (±20% variance threshold)
2. Calculates per-step ROI (quality improvement / cost)
3. Evaluates CSS after each step (6-factor score)
4. Terminates at 22s with CSS=0.88 (high sufficiency, soft time reached)
5. Delivers 9.1/10 quality with 53 documents, €0.47 spent
6. Avoided unnecessary STEP_6 that would have exceeded budget without meaningful quality gain

**Next Steps**:
1. Review and approve architecture
2. Start implementation (Phase 1)
3. Iterate based on feedback
4. Gradual migration from current system

This transforms VERITAS from a linear RAG system into an **interactive, intelligent, cost-aware, self-regulating research assistant** capable of handling simple questions to complex scientific analyses with:
- Optimal resource utilization
- Continuous user collaboration
- **Rigorous cost-benefit governance at every step**
- **Intelligent stopping when sufficient content is gathered**
- **Quantified content quality assessment**
