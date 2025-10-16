# 🚀 VERITAS v7.0 - Implementation TODO

**JSON-basierte wissenschaftliche Methodik mit Selbstverbesserung**

**Erstellt:** 12. Oktober 2025, 22:15 Uhr  
**Status:** 🟡 **READY TO START** - Implementation Phase  
**Timeline:** 11-15 Tage (optimiert)  
**LOC:** ~2,300 LOC (78-83% Reduktion vs v5.0/v6.0)

---

## 📊 Quick Status Overview

```
┌─────────────────────────────────────────────────────────────┐
│  PHASE OVERVIEW                                              │
├─────────────────────────────────────────────────────────────┤
│  Phase 1: JSON Configs           ✅ 100% COMPLETE (2.5 h)   │
│  Phase 2: Generic Executor       ✅ 100% COMPLETE (1.5 h)   │
│  Phase 3: Improvement Engine     ✅ 100% (Existing)         │
│  Phase 4: Unified Orchestrator   ✅ 100% COMPLETE (4.5 h)   │
│  Phase 5: Testing & Refinement   ⏳ 10% (E2E Test Created)  │
├─────────────────────────────────────────────────────────────┤
│  Total Progress: 95% Complete (4.5 of 5 phases DONE)        │
│  Remaining: Run E2E Test + Tune Prompts (4-6 hours)         │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 PHASE 1: JSON Configuration (2-3 Tage)

**Status:** ✅ **50% COMPLETE** (1 von 2 Komponenten fertig)  
**Remaining:** 1-2 Tage

### ✅ COMPLETED

- [x] **scientific_foundation.json** (375 Zeilen)
  - File: `config/prompts/scientific_foundation.json`
  - Created: 12.10.2025, 21:30 Uhr
  - Status: ✅ JSON Syntax validated
  - Content:
    - [x] core_principles (5 principles mit ✅/❌ examples)
    - [x] scientific_method (6 steps: hypothesis → metacognition)
    - [x] source_quality_hierarchy (5 levels: gesetz → unbekannt)
    - [x] output_quality_standards (confidence_calibration, criteria_guidelines)
    - [x] prompt_improvement (4 metrics, version_history)

### ⏳ TODO: default_method.json

- [ ] **Create: config/scientific_methods/default_method.json** (400 Zeilen)
  - **Aufwand:** 1-2 Tage
  - **Structure:**
    ```json
    {
      "method_id": "default_scientific_method",
      "version": "1.0.0",
      "phases": [
        {
          "phase_id": "hypothesis",
          "phase_number": 1,
          "name": "Hypothesengenerierung",
          "prompt_template": "prompts/scientific/phase1_hypothesis.txt",
          "output_schema": {
            "type": "object",
            "required": ["hypothesis", "required_criteria", "confidence"],
            "properties": {
              "hypothesis": {"type": "string"},
              "required_criteria": {"type": "array"},
              "missing_information": {"type": "array"},
              "confidence": {"type": "number"},
              "reasoning": {"type": "string"}
            }
          },
          "execution": {
            "model": "llama3.2:latest",
            "temperature": 0.3,
            "max_tokens": 800
          },
          "dependencies": ["rag_semantic", "rag_graph"],
          "retry_policy": {
            "max_retries": 3,
            "validation_rules": ["json_valid", "schema_valid"]
          }
        },
        // ... 5 weitere Phasen (synthesis, analysis, validation, conclusion, metacognition)
      ],
      "orchestration_config": {
        "sequential": true,
### ✅ COMPLETE: Phase 1 - JSON Configuration

**Status:** ✅ 100% COMPLETE (Aufwand: 2.5 Stunden, 12. Oktober 2025)

**Files Created (9 files, ~3,300 Zeilen):**
- [x] `config/scientific_foundation.json` (375 Zeilen) ✅ DONE
- [x] `config/scientific_methods/default_method.json` (650 Zeilen) ✅ DONE + VALIDATED
- [x] `config/prompts/scientific/phase1_hypothesis.json` (330 Zeilen) ✅ DONE + VALIDATED
- [x] `config/prompts/scientific/phase2_synthesis.json` (340 Zeilen) ✅ DONE + VALIDATED
- [x] `config/prompts/scientific/phase3_analysis.json` (310 Zeilen) ✅ DONE + VALIDATED
- [x] `config/prompts/scientific/phase4_validation.json` (340 Zeilen) ✅ DONE + VALIDATED
- [x] `config/prompts/scientific/phase5_conclusion.json` (380 Zeilen) ✅ DONE + VALIDATED
- [x] `config/prompts/scientific/phase6_metacognition.json` (450 Zeilen) ✅ DONE + VALIDATED
- [x] `config/prompts/scientific/user_query_enhancement.json` (50 Zeilen) ✅ DONE + VALIDATED

**All JSON files validated:** PowerShell JSON syntax check passed ✅

**Achievements:**
- JSON-basierte Prompts (maschinenlesbar, versionierbar, strukturiert)
- Konsistente Struktur: system_prompt + instructions + quality_guidelines + examples + common_mistakes
- Umfassende Dokumentation: 5-6 instruction steps pro Phase
- Integration mit scientific_foundation.json (source_quality_hierarchy)
- Beispiele: 2-3 complete examples pro Phase (good vs. bad)
- Anti-Patterns: 4-5 common_mistakes pro Phase mit Korrekturen

**Next:** Phase 2 - ScientificPhaseExecutor (lädt diese JSONs + führt LLM-Calls aus)
    
    - [ ] `config/prompts/scientific/phase3_analysis.txt` (70 Zeilen)
      - **Content:**
        - Task: "Erkenne Muster + Widersprüche in Evidence Clusters"
        - Input: {{synthesis_result}}
        - Output: patterns, contradictions, conflict_resolution
    
    - [ ] `config/prompts/scientific/phase4_validation.txt` (70 Zeilen)
      - **Content:**
        - Task: "Teste Hypothese gegen Evidenzen"
        - Input: {{hypothesis}}, {{analysis_result}}
        - Output: validation_status, supporting_evidence, contradicting_evidence
    
    - [ ] `config/prompts/scientific/phase5_conclusion.txt` (70 Zeilen)
      - **Content:**
        - Task: "Finale Synthese → Gesicherte Antwort"
        - Input: {{validation_result}}, {{all_evidences}}
        - Output: main_answer, action_recommendations, confidence
    
    - [ ] `config/prompts/scientific/phase6_metacognition.txt` (70 Zeilen)
      - **Content:**
        - Task: "Selbstbewertung → Confidence + Gaps"
        - Input: {{conclusion_result}}
        - Output: confidence_assessment, information_gaps, improvement_suggestions

### ⏳ TODO: User Query Enhancement Template

- [ ] **Create: config/prompts/scientific/user_query_enhancement.txt** (30 Zeilen)
  - **Content:**
    ```text
    # USER QUERY ENHANCEMENT
    
    Original Query: {{user_query}}
    Detected Domain: {{detected_domain}}
    Estimated Complexity: {{complexity_estimate}}
    
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
    
    Beginne mit Phase 1: Hypothesengenerierung.
    ```

---

## 🛠️ PHASE 2: Scientific Phase Executor (3-4 Tage)

**Status:** ⏳ **0% COMPLETE** - Design fertig, Implementation TODO  
**LOC:** ~400 LOC  
**Dependency:** Phase 1 (JSON Configs) muss fertig sein

### Tasks

- [ ] **Create: backend/services/scientific_phase_executor.py** (~400 LOC)
  - **Aufwand:** 3-4 Tage
  
  - [ ] **1. Class Definition + Initialization** (~50 LOC)
    ```python
    class ScientificPhaseExecutor:
        """
        Generic Executor für wissenschaftliche Phasen.
        
        FEATURES:
        - Lädt JSON-Konfiguration (default_method.json + scientific_foundation.json)
        - Jinja2 Template Rendering
        - LLM Call Execution
        - JSON Schema Validation
        - Retry Logic
        """
        
        def __init__(
            self,
            method_config_path: str,
            prompts_dir: str,
            foundation_path: str,
            ollama_client: OllamaClient
        ):
            # Load method config
            self.method_config = self._load_json(method_config_path)
            
            # Load scientific foundation
            self.scientific_foundation = self._load_json(foundation_path)
            
            # Setup Jinja2 environment
            self.jinja_env = jinja2.Environment(
                loader=jinja2.FileSystemLoader(prompts_dir)
            )
            
            # LLM client
            self.ollama_client = ollama_client
            
            logger.info(f"✅ ScientificPhaseExecutor initialized")
            logger.info(f"   Method: {self.method_config['method_id']}")
            logger.info(f"   Phases: {len(self.method_config['phases'])}")
    ```
  
  - [ ] **2. Execute Phase (Main Method)** (~80 LOC)
    ```python
    async def execute_phase(
        self,
        phase_id: str,
        context: PhaseExecutionContext
    ) -> PhaseResult:
        """
        Execute eine wissenschaftliche Phase.
        
        Args:
            phase_id: "hypothesis", "synthesis", "analysis", etc.
            context: PhaseExecutionContext mit previous_phases, rag_results, etc.
        
        Returns:
            PhaseResult mit output, confidence, metadata
        """
        phase_config = self._get_phase_config(phase_id)
        
        # 1. Construct Prompt
        prompt = self._construct_prompt(phase_config, context)
        
        # 2. Execute LLM Call (with retry)
        response = await self._execute_llm_call_with_retry(
            prompt, phase_config
        )
        
        # 3. Parse & Validate Output
        output = self._parse_and_validate_output(
            response, phase_config["output_schema"]
        )
        
        # 4. Create Result
        result = PhaseResult(
            phase_id=phase_id,
            output=output,
            raw_response=response,
            execution_time=execution_time,
            metadata={
                "model": phase_config["execution"]["model"],
                "temperature": phase_config["execution"]["temperature"],
                "retries": retry_count
            }
        )
        
        return result
    ```
  
  - [ ] **3. Construct Prompt (Jinja2 Rendering)** (~60 LOC)
    ```python
    def _construct_prompt(
        self,
        phase_config: Dict,
        context: PhaseExecutionContext
    ) -> str:
        """
        Konstruiere Prompt via Jinja2 Template.
        
        Template Variables:
        - {{scientific_foundation}}: JSON als String
        - {{user_query}}: Original User Query
        - {{rag_results}}: RAG Search Results
        - {{previous_phases}}: Outputs von vorherigen Phasen
        """
        template_path = phase_config["prompt_template"]
        template = self.jinja_env.get_template(template_path)
        
        # Resolve data paths (e.g., "phases.hypothesis.output")
        template_vars = {
            "scientific_foundation": json.dumps(
                self.scientific_foundation, indent=2, ensure_ascii=False
            ),
            "user_query": context.user_query,
            "rag_results": context.rag_results,
            "detected_domain": context.detected_domain,
            "complexity_estimate": context.complexity_estimate,
            "available_agents": context.available_agents
        }
        
        # Add previous phase outputs
        for prev_phase_id, prev_result in context.previous_phases.items():
            # {{hypothesis}} → previous_phases["hypothesis"]["output"]
            template_vars[prev_phase_id] = prev_result.output
        
        # Render
        prompt = template.render(**template_vars)
        
        logger.debug(f"Prompt constructed for {phase_config['phase_id']}")
        logger.debug(f"Prompt length: {len(prompt)} chars")
        
        return prompt
    ```
  
  - [ ] **4. Execute LLM Call with Retry** (~80 LOC)
    ```python
    async def _execute_llm_call_with_retry(
        self,
        prompt: str,
        phase_config: Dict
    ) -> str:
        """
        Execute LLM Call mit Retry-Logik.
        
        Retry bei:
        - JSON Parse Error
        - Schema Validation Error
        - LLM Timeout
        """
        retry_policy = phase_config["retry_policy"]
        max_retries = retry_policy["max_retries"]
        validation_rules = retry_policy["validation_rules"]
        
        for attempt in range(max_retries):
            try:
                # LLM Call
                response = await self.ollama_client.generate(
                    prompt=prompt,
                    model=phase_config["execution"]["model"],
                    temperature=phase_config["execution"]["temperature"],
                    max_tokens=phase_config["execution"]["max_tokens"]
                )
                
                # Pre-Validation
                if "json_valid" in validation_rules:
                    self._validate_json(response)
                
                if "schema_valid" in validation_rules:
                    self._validate_schema(response, phase_config["output_schema"])
                
                logger.info(f"✅ LLM Call successful (attempt {attempt + 1})")
                return response
                
            except (json.JSONDecodeError, ValidationError) as e:
                logger.warning(f"Retry {attempt + 1}/{max_retries}: {e}")
                
                if attempt == max_retries - 1:
                    raise RuntimeError(f"Max retries exceeded: {e}")
                
                # Adjust temperature für Retry
                phase_config["execution"]["temperature"] *= 0.8
        
        raise RuntimeError("Unexpected retry loop exit")
    ```
  
  - [ ] **5. Parse & Validate Output** (~60 LOC)
    ```python
    def _parse_and_validate_output(
        self,
        response: str,
        schema: Dict
    ) -> Dict:
        """
        Parse JSON response + validate gegen Schema.
        """
        # Extract JSON from code blocks
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try raw JSON
            json_str = response.strip()
        
        # Parse JSON
        try:
            output = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"JSON Parse Error: {e}")
            logger.error(f"Response: {response[:500]}")
            raise
        
        # Validate Schema (jsonschema)
        try:
            jsonschema.validate(instance=output, schema=schema)
        except jsonschema.ValidationError as e:
            logger.error(f"Schema Validation Error: {e}")
            logger.error(f"Output: {json.dumps(output, indent=2)}")
            raise
        
        return output
    ```
  
  - [ ] **6. Helper Methods** (~70 LOC)
    ```python
    def _get_phase_config(self, phase_id: str) -> Dict:
        """Get phase config from method_config."""
        for phase in self.method_config["phases"]:
            if phase["phase_id"] == phase_id:
                return phase
        raise ValueError(f"Phase {phase_id} not found")
    
    def _load_json(self, path: str) -> Dict:
        """Load JSON file."""
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _validate_json(self, response: str):
        """Validate JSON syntax."""
        json.loads(response)  # Raises JSONDecodeError
    
    def _validate_schema(self, response: str, schema: Dict):
        """Validate JSON schema."""
        output = json.loads(response)
        jsonschema.validate(instance=output, schema=schema)
    ```

- [ ] **Create: backend/models/phase_execution_context.py** (~50 LOC)
  ```python
  @dataclass
  class PhaseExecutionContext:
      """Context für Phase-Execution."""
      user_query: str
      rag_results: Dict
      detected_domain: str
      complexity_estimate: str
      available_agents: List[str]
      previous_phases: Dict[str, PhaseResult] = field(default_factory=dict)
  
  @dataclass
  class PhaseResult:
      """Result einer Phase."""
      phase_id: str
      output: Dict
      raw_response: str
      execution_time: float
      metadata: Dict
  ```

---

## ✅ PHASE 3: Prompt Improvement Engine (0 Tage)

**Status:** ✅ **100% COMPLETE** - Already implemented  
**LOC:** 500 LOC  
**Files:**
- ✅ `backend/services/prompt_improvement_engine.py` (500 LOC)
- ✅ `docs/PROMPT_IMPROVEMENT_SYSTEM.md` (1,500 Zeilen)

**No Action Required** - Already created on 12.10.2025, 21:45 Uhr

---

## 🎯 PHASE 4: Unified Orchestrator v7.0 (REAL Systems)

**Status:** ✅ **100% COMPLETE** (Aufwand: 4.5 Stunden, 13. Oktober 2025)  
**LOC:** ~840 LOC (570 orchestrator + 150 integration + 120 test)  
**Real Integration:** UDS3 (ChromaDB + Neo4j) + Ollama (llama3.2)

### ✅ COMPLETED

- [x] **UnifiedOrchestratorV7.py** (570 LOC) - Mock Version ✅ DONE (12.10.2025, 00:45 Uhr)
  - File: `backend/orchestration/unified_orchestrator_v7.py`
  - Features:
    - [x] Dual execution modes (streaming + non-streaming)
    - [x] StreamEvent dataclass (NDJSON format)
    - [x] Sequential 6-phase execution
    - [x] Context passing between phases
    - [x] Progress tracking (0% → 100%)
  - Test: `tests/test_unified_orchestrator_v7.py` (120 LOC)
  - Test Results: ✅ 27 events, 38ms, 0 errors

- [x] **Real UDS3 Integration** (150 LOC) ✅ DONE (13.10.2025, 02:15 Uhr)
  - **UDS3 Imports:**
    - [x] `UDS3HybridSearchAgent` from `backend.agents.veritas_uds3_hybrid_agent`
    - [x] `get_optimized_unified_strategy` from `uds3` (sys.path handling)
  - **Constructor Changes:**
    - [x] Parameter: `rag_service` → `uds3_strategy`
    - [x] Auto-initialization: If `uds3_strategy=None` → `get_optimized_unified_strategy()`
    - [x] Create `self.search_agent = UDS3HybridSearchAgent(uds3_strategy)`
  - **RAG Collection (_collect_rag_results):**
    - [x] Replace mock with `self.search_agent.hybrid_search()`
    - [x] Hybrid search: `weights={"vector": 0.6, "graph": 0.4}`
    - [x] Convert `SearchResult` → RAG format (`{semantic: [...], graph: [...], hybrid: [...]}`)
    - [x] Error handling with mock fallback

- [x] **Real Ollama Integration** (ScientificPhaseExecutor) ✅ DONE (13.10.2025, 02:20 Uhr)
  - File: `backend/services/scientific_phase_executor.py`
  - **Imports:**
    - [x] `VeritasOllamaClient, OllamaRequest, OllamaResponse`
  - **LLM Call (_execute_llm_call_with_retry):**
    - [x] Create `OllamaRequest(model, prompt, temperature, max_tokens, system)`
    - [x] Execute `ollama_client.generate_response(request, stream=False)`
    - [x] Parse response: `response.response → llm_output`
    - [x] Temperature adjustment on retry: `temp × 0.9^attempt`
    - [x] Exponential backoff: `1.0 × 1.5^attempt` seconds
    - [x] Mock fallback if `ollama_client=None`

- [x] **End-to-End Test Suite** (330 LOC) ✅ DONE (13.10.2025, 02:25 Uhr)
  - File: `tests/test_unified_orchestrator_v7_real.py`
  - **Test 1: Streaming Mode**
    - [x] Initialize `VeritasOllamaClient` + health check
    - [x] Initialize `UnifiedOrchestratorV7` (UDS3 auto-init)
    - [x] Process query with streaming (collect all events)
    - [x] Log progress/processing_step/phase_complete/final_result
    - [x] Validation checks (6 assertions)
  - **Test 2: Non-Streaming Mode**
    - [x] Process query without streaming
    - [x] Measure total duration
    - [x] Log final answer
  - **Validation Checks:**
    - [x] All 6 phases executed
    - [x] Final result received
    - [x] No errors
    - [x] All phases successful
    - [x] Confidence > 0.5

- [x] **Documentation** ✅ DONE (13.10.2025, 02:30 Uhr)
  - [x] `docs/PHASE4_REAL_INTEGRATION_REPORT.md` (1,200+ Zeilen)
  - [x] `docs/QUICK_START_V7_REAL.md` (400+ Zeilen)
  - [x] `docs/PHASE4_COMPLETION_REPORT.md` (updated)

### 📊 Real Integration Architecture

```
User Query
    ↓
UnifiedOrchestratorV7
    ↓
├─ Query Enhancement (optional)
├─ UDS3 Hybrid Search (REAL)
│   ├─ ChromaDB Vector Search (60% weight)
│   ├─ Neo4j Graph Search (40% weight)
│   └─ Top 10 results → {semantic: [...], graph: [...]}
├─ Phase 1: Hypothesis (REAL Ollama)
│   ├─ Ollama Request: llama3.2, temp=0.3, tokens=800
│   └─ Response: {required_criteria, missing_info, confidence}
├─ Phase 2: Synthesis (REAL Ollama)
├─ Phase 3: Analysis (REAL Ollama)
├─ Phase 4: Validation (REAL Ollama)
├─ Phase 5: Conclusion (REAL Ollama)
└─ Phase 6: Metacognition (REAL Ollama)
    ↓
Final Answer (from Phase 5)
  
  - [ ] **1. Class Definition + Initialization** (~80 LOC)
    ```python
    class UnifiedOrchestratorV7:
        """
        Unified Orchestrator für v7.0 JSON-Driven Architecture.
        
        FEATURES:
        - Koordiniert Scientific Phases (ScientificPhaseExecutor)
        - Koordiniert Agent Tasks (AgentOrchestrator)
        - Integriert Prompt Improvement (PromptImprovementEngine)
        - Dual-Track Execution (Generic + Agent)
        """
        
        def __init__(
            self,
            scientific_executor: ScientificPhaseExecutor,
            agent_orchestrator: AgentOrchestrator,
            improvement_engine: PromptImprovementEngine,
            rag_service: RAGService
        ):
            self.scientific_executor = scientific_executor
            self.agent_orchestrator = agent_orchestrator
            self.improvement_engine = improvement_engine
            self.rag_service = rag_service
            
            logger.info("✅ UnifiedOrchestratorV7 initialized")
    ```
  
  - [ ] **2. Process Query (Main Entry Point)** (~120 LOC)
    ```python
    async def process_query(self, user_query: str) -> Dict:
        """
        Process Query mit Scientific Method + Agent Coordination.
        
        WORKFLOW:
        1. Load scientific_foundation.json
        2. Enhance user query mit base prompt
        3. RAG Retrieval (semantic + graph)
        4. Execute Scientific Phases (1-6)
        5. Coordinate Agent Tasks (parallel)
        6. Collect Quality Metrics
        7. Record to PromptImprovementEngine
        
        Returns:
            {
                "scientific_process": {...},
                "agent_results": {...},
                "final_answer": "...",
                "quality_metrics": {...}
            }
        """
        query_id = str(uuid.uuid4())
        start_time = time.time()
        
        # 1. Enhance Query
        enhanced_query = self._enhance_user_query(user_query)
        
        # 2. RAG Retrieval
        rag_results = await self.rag_service.retrieve(enhanced_query)
        
        # 3. Create Execution Context
        context = PhaseExecutionContext(
            user_query=user_query,
            rag_results=rag_results,
            detected_domain=self._detect_domain(user_query),
            complexity_estimate=self._estimate_complexity(user_query),
            available_agents=self._get_available_agents()
        )
        
        # 4. Execute Scientific Phases (sequential)
        scientific_results = await self._execute_scientific_phases(context)
        
        # 5. Coordinate Agent Tasks (parallel)
        agent_results = await self._coordinate_agents(scientific_results, context)
        
        # 6. Collect Quality Metrics
        metrics = self._collect_quality_metrics(
            query_id, scientific_results, agent_results
        )
        
        # 7. Record Metrics (triggers improvement after 10 queries)
        self.improvement_engine.record_query_metrics(metrics)
        
        execution_time = time.time() - start_time
        
        return {
            "query_id": query_id,
            "scientific_process": scientific_results,
            "agent_results": agent_results,
            "final_answer": scientific_results["conclusion"]["output"]["main_answer"],
            "quality_metrics": asdict(metrics),
            "execution_time": execution_time
        }
    ```
  
  - [ ] **3. Execute Scientific Phases** (~80 LOC)
    ```python
    async def _execute_scientific_phases(
        self,
        context: PhaseExecutionContext
    ) -> Dict[str, PhaseResult]:
        """
        Execute alle 6 wissenschaftlichen Phasen sequenziell.
        """
        phases = ["hypothesis", "synthesis", "analysis", 
                  "validation", "conclusion", "metacognition"]
        
        results = {}
        
        for phase_id in phases:
            logger.info(f"🔬 Executing Phase: {phase_id}")
            
            result = await self.scientific_executor.execute_phase(
                phase_id, context
            )
            
            results[phase_id] = result
            
            # Update context mit neuem Result
            context.previous_phases[phase_id] = result
            
            logger.info(f"✅ Phase {phase_id} completed in {result.execution_time:.2f}s")
        
        return results
    ```
  
  - [ ] **4. Coordinate Agents** (~60 LOC)
    ```python
    async def _coordinate_agents(
        self,
        scientific_results: Dict[str, PhaseResult],
        context: PhaseExecutionContext
    ) -> Dict:
        """
        Koordiniere Agent Tasks basierend auf Hypothesis.
        
        Example:
        - Hypothesis identifiziert "Environmental Domain"
        → Dispatch Environmental Agent + Database Agent
        """
        hypothesis = scientific_results["hypothesis"].output
        
        # Identify Required Agents
        required_agents = self._identify_required_agents(hypothesis)
        
        # Dispatch Agents (via existing AgentOrchestrator)
        agent_results = await self.agent_orchestrator.execute_pipeline(
            query=context.user_query,
            agents=required_agents,
            context={
                "hypothesis": hypothesis,
                "rag_results": context.rag_results
            }
        )
        
        return agent_results
    ```
  
  - [ ] **5. Collect Quality Metrics** (~100 LOC)
    ```python
    def _collect_quality_metrics(
        self,
        query_id: str,
        scientific_results: Dict,
        agent_results: Dict
    ) -> QualityMetrics:
        """
        Collect Quality Metrics für PromptImprovementEngine.
        """
        # Extract Conclusion
        conclusion = scientific_results["conclusion"].output
        
        # Extract Metacognition
        metacognition = scientific_results["metacognition"].output
        
        # Calculate Metrics
        metrics = QualityMetrics(
            query_id=query_id,
            timestamp=datetime.now().isoformat(),
            
            # JSON Validity (alle Phasen valid?)
            json_valid=all(
                r.output is not None for r in scientific_results.values()
            ),
            
            # Schema Compliance
            schema_valid=True,  # Already validated in executor
            
            # Confidence Calibration
            predicted_confidence=conclusion.get("confidence", 0.0),
            actual_confidence=None,  # User-Feedback (optional)
            
            # Required Criteria Quality
            num_criteria=len(
                scientific_results["hypothesis"].output.get("required_criteria", [])
            ),
            vague_criteria=self._detect_vague_criteria(
                scientific_results["hypothesis"].output.get("required_criteria", [])
            ),
            
            # Source Citation
            citations_found=self._count_citations(conclusion),
            citations_expected=len(scientific_results["synthesis"].output.get("evidence_clusters", [])),
            
            # Improvement Suggestions
            improvement_suggestions=metacognition.get(
                "metacognitive_assessment", {}
            ).get("improvement_suggestions", [])
        )
        
        return metrics
    ```
  
  - [ ] **6. Helper Methods** (~80 LOC)
    ```python
    def _enhance_user_query(self, user_query: str) -> str:
        """Enhance query mit scientific base prompt."""
        # Load user_query_enhancement template
        template = self.scientific_executor.jinja_env.get_template(
            "scientific/user_query_enhancement.txt"
        )
        return template.render(user_query=user_query)
    
    def _detect_domain(self, query: str) -> str:
        """Simple domain detection."""
        # TODO: NLP-based domain detection
        return "administrative"
    
    def _estimate_complexity(self, query: str) -> str:
        """Estimate query complexity."""
        # TODO: Complexity estimation (low/medium/high)
        return "medium"
    
    def _get_available_agents(self) -> List[str]:
        """Get list of available agents."""
        return ["environmental", "database", "quality_assessor"]
    
    def _identify_required_agents(self, hypothesis: Dict) -> List[str]:
        """Identify required agents basierend auf hypothesis."""
        # TODO: Smart agent selection
        return ["database"]
    
    def _detect_vague_criteria(self, criteria: List[str]) -> List[str]:
        """Detect vage formulierte Kriterien."""
        vague_words = ["vielleicht", "eventuell", "möglicherweise", "ungefähr"]
        vague = []
        for criterion in criteria:
            if any(word in criterion.lower() for word in vague_words):
                vague.append(criterion)
        return vague
    
    def _count_citations(self, conclusion: Dict) -> int:
        """Count source citations in conclusion."""
        # Count references to sources
        text = json.dumps(conclusion)
        return text.count("LBO") + text.count("§") + text.count("VGH")
    ```

---

## 🧪 PHASE 5: Testing & Refinement (3-4 Tage)

**Status:** ⏳ **0% COMPLETE**  
**LOC:** ~800 LOC  
**Dependency:** Phase 2+4 müssen fertig sein

### Tasks

- [ ] **Unit Tests: ScientificPhaseExecutor** (~200 LOC)
  - File: `tests/test_scientific_phase_executor.py`
  - [ ] Test: Load JSON configs
  - [ ] Test: Jinja2 template rendering
  - [ ] Test: JSON parsing + validation
  - [ ] Test: Retry logic
  - [ ] Test: Error handling (invalid JSON, schema mismatch)

- [ ] **Unit Tests: PromptImprovementEngine** (~150 LOC)
  - File: `tests/test_prompt_improvement_engine.py`
  - [ ] Test: Metrics collection
  - [ ] Test: Aggregation (10 queries)
  - [ ] Test: Quality score calculation
  - [ ] Test: Improvement suggestions generation
  - [ ] Test: Version increment (1.0.0 → 1.1.0)

- [ ] **Integration Tests: UnifiedOrchestratorV7** (~200 LOC)
  - File: `tests/test_unified_orchestrator_v7.py`
  - [ ] Test: Full query execution (6 phases)
  - [ ] Test: Agent coordination
  - [ ] Test: Metrics collection
  - [ ] Test: Improvement engine integration

- [ ] **End-to-End Test: Real Query** (~100 LOC)
  - File: `tests/test_e2e_carport_query.py`
  - [ ] Query: "Brauche ich eine Baugenehmigung für einen Carport in Baden-Württemberg?"
  - [ ] Validate: All 6 phases executed
  - [ ] Validate: Hypothesis generated
  - [ ] Validate: Evidence synthesized
  - [ ] Validate: Conclusion reached
  - [ ] Validate: Metacognition present
  - [ ] Validate: Quality metrics collected

- [ ] **Prompt Refinement basierend auf Tests** (~150 LOC)
  - [ ] Run 10 test queries
  - [ ] Collect metrics
  - [ ] Analyze quality scores
  - [ ] Refine prompts (scientific_foundation.json)
  - [ ] Re-test nach Refinement
  - [ ] Document improvements

---

## 📅 Timeline & Milestones

```
┌─────────────────────────────────────────────────────────────────┐
│  TIMELINE (11-15 Tage Total, 9-12 Tage Remaining)               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Week 1 (Tag 1-5)                                               │
│  ├─ Tag 1: ✅ scientific_foundation.json (DONE)                │
│  ├─ Tag 2: ⏳ default_method.json                              │
│  ├─ Tag 3: ⏳ Phase Prompts (6 Templates)                      │
│  ├─ Tag 4: ⏳ ScientificPhaseExecutor (Part 1)                 │
│  └─ Tag 5: ⏳ ScientificPhaseExecutor (Part 2)                 │
│                                                                  │
│  Week 2 (Tag 6-10)                                              │
│  ├─ Tag 6: ⏳ UnifiedOrchestratorV7 (Part 1)                   │
│  ├─ Tag 7: ⏳ UnifiedOrchestratorV7 (Part 2)                   │
│  ├─ Tag 8: ⏳ Unit Tests                                        │
│  ├─ Tag 9: ⏳ Integration Tests                                │
│  └─ Tag 10: ⏳ E2E Tests                                        │
│                                                                  │
│  Week 3 (Tag 11-12, Optional)                                   │
│  ├─ Tag 11: ⏳ Prompt Refinement                               │
│  └─ Tag 12: ⏳ Performance Optimization                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Milestones

- **Milestone 1:** Phase 1 Complete (Tag 3)
  - ✅ scientific_foundation.json
  - ⏳ default_method.json
  - ⏳ 6 Phase Prompts
  - **Status:** 33% Complete

- **Milestone 2:** Phase 2 Complete (Tag 5)
  - ⏳ ScientificPhaseExecutor
  - ⏳ PhaseExecutionContext
  - **Status:** 0% Complete

- **Milestone 3:** Phase 4 Complete (Tag 7)
  - ⏳ UnifiedOrchestratorV7
  - **Status:** 0% Complete

- **Milestone 4:** Phase 5 Complete (Tag 10)
  - ⏳ Unit + Integration + E2E Tests
  - **Status:** 0% Complete

- **Milestone 5:** Production Ready (Tag 12)
  - ⏳ Prompt Refinement
  - ⏳ Performance Optimization
  - ⏳ Documentation Update
  - **Status:** 0% Complete

---

## 🎯 Next Steps (TODAY!)

### Option 1: Complete Phase 1 (Recommended ⭐)

**Timeline:** 1-2 Tage  
**Priority:** HIGH

```powershell
# 1. Create default_method.json
New-Item -ItemType Directory -Force -Path "config\scientific_methods"
code "config\scientific_methods\default_method.json"

# 2. Create Phase Prompts (6 files)
New-Item -ItemType Directory -Force -Path "config\prompts\scientific"
code "config\prompts\scientific\phase1_hypothesis.txt"
code "config\prompts\scientific\phase2_synthesis.txt"
code "config\prompts\scientific\phase3_analysis.txt"
code "config\prompts\scientific\phase4_validation.txt"
code "config\prompts\scientific\phase5_conclusion.txt"
code "config\prompts\scientific\phase6_metacognition.txt"

# 3. Validate JSON
python -c "import json; json.load(open('config/prompts/scientific_foundation.json'))"
python -c "import json; json.load(open('config/scientific_methods/default_method.json'))"
```

### Option 2: Start Phase 2 (Parallel Möglich)

**Timeline:** 3-4 Tage  
**Priority:** MEDIUM

```powershell
# 1. Create ScientificPhaseExecutor
New-Item -ItemType Directory -Force -Path "backend\services"
code "backend\services\scientific_phase_executor.py"

# 2. Create Models
New-Item -ItemType Directory -Force -Path "backend\models"
code "backend\models\phase_execution_context.py"

# 3. Test with Mock Data
python backend\services\scientific_phase_executor.py
```

### Option 3: Review & Refine (Low Priority)

**Timeline:** 1 Tag  
**Priority:** LOW

```powershell
# 1. Review scientific_foundation.json
code "config\prompts\scientific_foundation.json"

# 2. Adjust Quality Targets (optional)
# - JSON Validity: 98% → 95%?
# - Confidence Calibration: 85% → 90%?

# 3. Review Prompt Improvement Engine
code "backend\services\prompt_improvement_engine.py"
```

---

## 📊 Progress Tracking

### Overall Progress

```
Phase 1: JSON Configs           [████████░░] 50% (1-2 Tage remaining)
Phase 2: Generic Executor       [░░░░░░░░░░]  0% (3-4 Tage remaining)
Phase 3: Improvement Engine     [██████████] 100% (DONE ✅)
Phase 4: Unified Orchestrator   [░░░░░░░░░░]  0% (3-4 Tage remaining)
Phase 5: Testing & Refinement   [░░░░░░░░░░]  0% (3-4 Tage remaining)
────────────────────────────────────────────────────────────────
Total Progress:                 [███░░░░░░░] 30% (9-12 Tage remaining)
```

### Files Created

```
✅ config/prompts/scientific_foundation.json (375 Zeilen)
✅ backend/services/prompt_improvement_engine.py (500 LOC)
✅ docs/SCIENTIFIC_METHOD_JSON_ARCHITECTURE.md (8,000 Zeilen)
✅ docs/PROMPT_IMPROVEMENT_SYSTEM.md (1,500 Zeilen)
✅ docs/V7_EXECUTIVE_SUMMARY.md (600 Zeilen)
✅ docs/V7_IMPLEMENTATION_TODO.md (Dieses Dokument)
────────────────────────────────────────────────────────────────
Total Created: 6 files, ~11,500 Zeilen
```

### Files TODO

```
⏳ config/scientific_methods/default_method.json (400 Zeilen)
⏳ config/prompts/scientific/phase1_hypothesis.txt (70 Zeilen)
⏳ config/prompts/scientific/phase2_synthesis.txt (70 Zeilen)
⏳ config/prompts/scientific/phase3_analysis.txt (70 Zeilen)
⏳ config/prompts/scientific/phase4_validation.txt (70 Zeilen)
⏳ config/prompts/scientific/phase5_conclusion.txt (70 Zeilen)
⏳ config/prompts/scientific/phase6_metacognition.txt (70 Zeilen)
⏳ config/prompts/scientific/user_query_enhancement.txt (30 Zeilen)
⏳ backend/services/scientific_phase_executor.py (400 LOC)
⏳ backend/models/phase_execution_context.py (50 LOC)
⏳ backend/services/unified_orchestrator_v7.py (500 LOC)
⏳ tests/test_scientific_phase_executor.py (200 LOC)
⏳ tests/test_prompt_improvement_engine.py (150 LOC)
⏳ tests/test_unified_orchestrator_v7.py (200 LOC)
⏳ tests/test_e2e_carport_query.py (100 LOC)
────────────────────────────────────────────────────────────────
Total TODO: 15 files, ~2,350 Zeilen/LOC
```

---

## 🎉 Summary

**VERITAS v7.0 Implementation ist bereit zu starten!**

**Completed:**
- ✅ Design Phase (25,000+ Zeilen Dokumentation)
- ✅ scientific_foundation.json (375 Zeilen)
- ✅ PromptImprovementEngine (500 LOC)
- ✅ Complete Architecture (v7.0 JSON-Driven)

**Remaining:**
- ⏳ 15 Files (~2,350 LOC)
- ⏳ 9-12 Tage Implementation
- ⏳ 5 Phasen (1 bereits 50% fertig)

**Benefits:**
- 78-83% weniger Code als v5.0/v6.0
- Automatische Selbstverbesserung alle 10 Queries
- JSON-basierte Konfiguration (flexibel + versionierbar)
- Maschinenlesbar + LLM-optimierbar

**Next Action:** Start Phase 1 (default_method.json + 6 Phase Prompts) 🚀

---

**Viel Erfolg bei der Implementation!** 💪

**Letzte Aktualisierung:** 12. Oktober 2025, 22:15 Uhr  
**Version:** 1.0 (Initial Implementation TODO)
