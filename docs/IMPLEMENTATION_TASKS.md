# VERITAS Deep Research System - Detaillierte Task-Liste

**Letzte Aktualisierung:** 11. Oktober 2025  
**Projekt:** VERITAS/VCC Integration  
**Ziel:** Architektur-Evolution zu Enterprise Deep Research System

**Siehe auch:**
- `IMPLEMENTATION_PLAN.md` - Architektur-Gap-Analyse & Konzept
- `TODO.md` - Bestehende Feature-TODOs (v3.18.3)

---

## 📊 Übersicht

**Gesamtaufwand:** 10-16 Wochen (2.5-4 Monate)  
**Team:** 2-3 Entwickler  
**Prioritäten:** P0 (kritisch) → P1 (hoch) → P2 (mittel) → P3 (optional)

### Status-Legende
- 🔴 **P0 - Kritisch:** Blockiert andere Tasks, muss zuerst erledigt werden
- 🟡 **P1 - Hoch:** Wichtig für MVP, sollte früh angegangen werden
- 🟠 **P2 - Mittel:** Wichtig für Production, kann aber warten
- 🟢 **P3 - Niedrig:** Nice-to-have, optional

### Aufwands-Kategorien
- **S (Small):** 1-2 Tage
- **M (Medium):** 3-5 Tage
- **L (Large):** 1-2 Wochen
- **XL (Extra Large):** 3-4 Wochen

---

## 🏗️ Phase 1: Foundation (4-6 Wochen) 🔴 KRITISCH

**Ziel:** Persistentes JSON Framework + LangGraph StateGraph + Evaluator-Agent

### Sprint 1.1: Persistentes JSON Framework (2 Wochen)

#### ✅ Task 1.1.0: Vorbereitung & Analyse
- **Priorität:** 🔴 P0
- **Aufwand:** S (1 Tag)
- **Abhängigkeiten:** Keine
- **Status:** ⏳ TODO
- **Beschreibung:**
  - Bestehenden Code analysieren (`veritas_supervisor_agent.py`)
  - Bestehende State-Verwaltung dokumentieren
  - Migrationsstrategie planen (Schrittweise vs. Big Bang)
  - PostgreSQL Connection testen
- **Deliverables:**
  - Migrations-Plan Dokument
  - Liste betroffener Files
  - Rollback-Strategie
- **Verantwortlich:** Tech Lead

---

#### Task 1.1.1: Research State Schema Design
- **Priorität:** 🔴 P0
- **Aufwand:** S (1-2 Tage)
- **Abhängigkeiten:** Task 1.1.0
- **Status:** ⏳ TODO
- **Beschreibung:**
  Erstelle `backend/agents/veritas_research_state.py` mit TypedDicts für:
  - `ResearchState` - Hauptzustand
  - `ExecutionTraceEntry` - Log-Einträge
  - `GlobalState` - Kumulatives Wissen
  - `IntegrityBlock` - Hashes + Signaturen (optional)

**Code-Gerüst:**
```python
# backend/agents/veritas_research_state.py

from typing import TypedDict, List, Dict, Any, Optional
from datetime import datetime

class ExecutionTraceEntry(TypedDict):
    """Single entry in execution trace (audit log)"""
    task_id: int
    timestamp: str  # ISO 8601
    agent: str  # Agent name (e.g., "EnvironmentalAgent")
    action: str  # "EXECUTE", "EVALUATE", "SYNTHESIZE"
    input: Dict[str, Any]
    output: Dict[str, Any]
    evaluation: Optional[Dict[str, Any]]  # RAG-Triade scores
    error: Optional[str]

class GlobalState(TypedDict):
    """Cumulative knowledge across iterations"""
    known_entities: List[str]  # Extracted entities
    hypotheses: List[str]  # Working hypotheses
    rejected_paths: List[str]  # Dead ends
    confidence_scores: Dict[str, float]  # Metric name → score

class IntegrityBlock(TypedDict, total=False):
    """Cryptographic integrity (optional, Phase 3)"""
    currentStateHash: str  # SHA-256
    previousStateHash: str  # For hash chain
    stateSignature: str  # RSA signature
    qualifiedTimestampToken: Optional[str]  # eIDAS QET (optional)

class ResearchState(TypedDict):
    """Main state for a research session"""
    # Identity
    research_id: str  # UUID
    user_id: Optional[str]
    
    # Input
    initial_query: str
    query_language: str  # "de", "en"
    
    # Status
    status: str  # "IN_PROGRESS", "COMPLETED", "FAILED", "PAUSED"
    current_task: Optional[Dict[str, Any]]
    
    # Execution
    execution_trace: List[ExecutionTraceEntry]
    global_state: GlobalState
    
    # Results
    final_answer: Optional[str]
    results_summary: Optional[Dict[str, Any]]
    
    # Metadata
    timestamps: Dict[str, str]  # created_at, updated_at, completed_at
    
    # Integrity (optional)
    integrity: Optional[IntegrityBlock]
```

**Erfolgskriterien:**
- [ ] Schema kompiliert ohne Fehler
- [ ] Alle erforderlichen Felder dokumentiert
- [ ] Type Hints korrekt (mypy clean)
- [ ] Beispiel-State zum Testen erstellt

**Verantwortlich:** Backend-Team

---

#### Task 1.1.2: PostgreSQL Migration für research_states Tabelle
- **Priorität:** 🔴 P0
- **Aufwand:** S (1 Tag)
- **Abhängigkeiten:** Task 1.1.1
- **Status:** ⏳ TODO
- **Beschreibung:**
  Erstelle SQL Migration: `migrations/001_create_research_states.sql`

**SQL Migration:**
```sql
-- migrations/001_create_research_states.sql

CREATE TABLE IF NOT EXISTS research_states (
    id UUID PRIMARY KEY,
    state_json JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status VARCHAR(50) NOT NULL,
    user_id VARCHAR(255),
    initial_query TEXT,
    
    CONSTRAINT valid_status CHECK (
        status IN ('IN_PROGRESS', 'COMPLETED', 'FAILED', 'PAUSED')
    )
);

-- Indexes for performance
CREATE INDEX idx_research_states_status ON research_states(status);
CREATE INDEX idx_research_states_updated_at ON research_states(updated_at DESC);
CREATE INDEX idx_research_states_user_id ON research_states(user_id);
CREATE INDEX idx_research_states_query_fulltext ON research_states 
    USING GIN (to_tsvector('german', initial_query));

-- Function to auto-update updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_research_states_updated_at
    BEFORE UPDATE ON research_states
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Comments
COMMENT ON TABLE research_states IS 'Persistent storage for research sessions';
COMMENT ON COLUMN research_states.state_json IS 'Full ResearchState as JSONB';
COMMENT ON COLUMN research_states.status IS 'Current state: IN_PROGRESS, COMPLETED, FAILED, PAUSED';
```

**Rollout:**
```bash
# Test in dev DB
psql -h localhost -U postgres -d veritas_dev -f migrations/001_create_research_states.sql

# Validate
psql -h localhost -U postgres -d veritas_dev -c "\d research_states"
```

**Erfolgskriterien:**
- [ ] Migration läuft ohne Fehler
- [ ] Tabelle existiert
- [ ] Alle Indizes erstellt
- [ ] Check Constraint funktioniert
- [ ] Trigger auto-updated `updated_at`

**Verantwortlich:** Database-Team

---

#### Task 1.1.3: ResearchStatePersister Implementation
- **Priorität:** 🔴 P0
- **Aufwand:** M (3-4 Tage)
- **Abhängigkeiten:** Task 1.1.1, Task 1.1.2
- **Status:** ⏳ TODO
- **Beschreibung:**
  Implementiere `backend/agents/veritas_state_persister.py`

**Code:**
```python
# backend/agents/veritas_state_persister.py

import asyncpg
import json
import logging
from typing import Optional, List, Dict, Any
from backend.agents.veritas_research_state import ResearchState

logger = logging.getLogger(__name__)

class ResearchStatePersister:
    """
    Manages persistent storage of ResearchState in PostgreSQL
    
    Features:
    - Async connection pooling
    - JSONB storage for flexibility
    - Automatic serialization/deserialization
    - Error handling with retries
    """
    
    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
        self.pool: Optional[asyncpg.Pool] = None
    
    async def init_pool(self):
        """Initialize connection pool"""
        if self.pool:
            return
        
        try:
            self.pool = await asyncpg.create_pool(
                host=self.db_config['host'],
                port=self.db_config['port'],
                user=self.db_config['user'],
                password=self.db_config['password'],
                database=self.db_config['database'],
                min_size=5,
                max_size=20,
                command_timeout=60
            )
            logger.info("✅ PostgreSQL connection pool initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize pool: {e}")
            raise
    
    async def close_pool(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Connection pool closed")
    
    async def save_state(
        self, 
        research_id: str, 
        state: ResearchState
    ):
        """
        Save or update research state
        
        Args:
            research_id: UUID of research session
            state: Complete ResearchState dict
        
        Raises:
            Exception: If DB operation fails
        """
        if not self.pool:
            await self.init_pool()
        
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO research_states (
                        id, state_json, status, user_id, initial_query
                    )
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (id) DO UPDATE SET
                        state_json = $2,
                        status = $3,
                        updated_at = NOW()
                    """,
                    research_id,
                    json.dumps(state),
                    state['status'],
                    state.get('user_id'),
                    state['initial_query']
                )
            
            logger.debug(f"✅ State saved: {research_id} (status={state['status']})")
        
        except Exception as e:
            logger.error(f"❌ Failed to save state {research_id}: {e}")
            raise
    
    async def load_state(self, research_id: str) -> Optional[ResearchState]:
        """
        Load research state by ID
        
        Args:
            research_id: UUID of research session
        
        Returns:
            ResearchState dict or None if not found
        """
        if not self.pool:
            await self.init_pool()
        
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT state_json FROM research_states WHERE id = $1",
                    research_id
                )
            
            if row:
                state = json.loads(row['state_json'])
                logger.debug(f"✅ State loaded: {research_id}")
                return state
            else:
                logger.warning(f"⚠️ State not found: {research_id}")
                return None
        
        except Exception as e:
            logger.error(f"❌ Failed to load state {research_id}: {e}")
            raise
    
    async def list_states(
        self,
        user_id: Optional[str] = None,
        status_filter: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        List research states with filters
        
        Args:
            user_id: Filter by user (optional)
            status_filter: Filter by status (optional)
            limit: Max results (default: 50)
        
        Returns:
            List of state summaries (not full states!)
        """
        if not self.pool:
            await self.init_pool()
        
        query = "SELECT id, status, initial_query, created_at, updated_at FROM research_states"
        conditions = []
        params = []
        param_idx = 1
        
        if user_id:
            conditions.append(f"user_id = ${param_idx}")
            params.append(user_id)
            param_idx += 1
        
        if status_filter:
            conditions.append(f"status = ${param_idx}")
            params.append(status_filter)
            param_idx += 1
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += f" ORDER BY updated_at DESC LIMIT ${param_idx}"
        params.append(limit)
        
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query, *params)
            
            return [dict(row) for row in rows]
        
        except Exception as e:
            logger.error(f"❌ Failed to list states: {e}")
            raise
    
    async def delete_state(self, research_id: str):
        """Delete research state"""
        if not self.pool:
            await self.init_pool()
        
        try:
            async with self.pool.acquire() as conn:
                result = await conn.execute(
                    "DELETE FROM research_states WHERE id = $1",
                    research_id
                )
            
            logger.info(f"✅ State deleted: {research_id}")
        
        except Exception as e:
            logger.error(f"❌ Failed to delete state {research_id}: {e}")
            raise
```

**Erfolgskriterien:**
- [ ] Alle Methoden implementiert
- [ ] Connection Pooling funktioniert
- [ ] Error Handling robust
- [ ] Performance: <50ms pro save/load
- [ ] Logging informativ

**Verantwortlich:** Backend-Team

---

#### Task 1.1.4: Integration in SupervisorAgent
- **Priorität:** 🔴 P0
- **Aufwand:** M (4-5 Tage)
- **Abhängigkeiten:** Task 1.1.3
- **Status:** ⏳ TODO
- **Beschreibung:**
  Erweitere `backend/agents/veritas_supervisor_agent.py` um State Persistence

**Änderungen:**

1. **Import & Initialization:**
```python
# backend/agents/veritas_supervisor_agent.py

from backend.agents.veritas_state_persister import ResearchStatePersister
from backend.agents.veritas_research_state import ResearchState, ExecutionTraceEntry
import uuid
from datetime import datetime

class SupervisorAgent:
    def __init__(self, db_config, ...):
        # ... existing init ...
        
        # NEW: State Persister
        self.persister = ResearchStatePersister(db_config)
        asyncio.create_task(self.persister.init_pool())  # Init pool async
```

2. **Extend `process_query()` Method:**
```python
async def process_query(
    self,
    query: str,
    context: Dict[str, Any],
    research_id: Optional[str] = None  # NEW parameter
) -> Dict[str, Any]:
    """
    Process query with persistent state
    
    Args:
        query: User question
        context: Request context
        research_id: UUID to resume research (optional)
    
    Returns:
        {
            "research_id": "uuid-...",
            "response_text": "...",
            "sources": [...],
            "status": "COMPLETED"
        }
    """
    
    # Load or create state
    if research_id:
        logger.info(f"🔄 Resuming research: {research_id}")
        state = await self.persister.load_state(research_id)
        
        if not state:
            raise ValueError(f"Research {research_id} not found")
    else:
        logger.info(f"🆕 Starting new research")
        state = self._create_initial_state(query)
    
    try:
        # Process while IN_PROGRESS
        while state['status'] == 'IN_PROGRESS':
            # Execute next step
            result = await self._execute_next_step(state)
            
            # Log to execution trace
            trace_entry: ExecutionTraceEntry = {
                "task_id": len(state['execution_trace']) + 1,
                "timestamp": datetime.utcnow().isoformat(),
                "agent": result.agent_type,
                "action": "EXECUTE",
                "input": {"query": state['current_task']['query']},
                "output": result.dict(),
                "evaluation": None,  # Will be filled by Evaluator
                "error": None
            }
            
            state['execution_trace'].append(trace_entry)
            
            # Update timestamps
            state['timestamps']['updated_at'] = datetime.utcnow().isoformat()
            
            # Persist state
            await self.persister.save_state(state['research_id'], state)
            logger.debug(f"💾 State saved (task {trace_entry['task_id']})")
        
        # Mark as completed
        state['status'] = 'COMPLETED'
        state['timestamps']['completed_at'] = datetime.utcnow().isoformat()
        await self.persister.save_state(state['research_id'], state)
        
        logger.info(f"✅ Research completed: {state['research_id']}")
        
        return {
            "research_id": state['research_id'],
            "response_text": state['final_answer'],
            "sources": self._extract_sources(state),
            "status": state['status'],
            "execution_trace_length": len(state['execution_trace'])
        }
    
    except Exception as e:
        logger.error(f"❌ Research failed: {e}")
        
        # Mark as failed
        state['status'] = 'FAILED'
        state['execution_trace'].append({
            "task_id": len(state['execution_trace']) + 1,
            "timestamp": datetime.utcnow().isoformat(),
            "agent": "SupervisorAgent",
            "action": "ERROR",
            "input": {},
            "output": {},
            "error": str(e)
        })
        
        await self.persister.save_state(state['research_id'], state)
        raise

def _create_initial_state(self, query: str) -> ResearchState:
    """Create new research state"""
    research_id = str(uuid.uuid4())
    
    return {
        "research_id": research_id,
        "user_id": None,  # TODO: Get from context
        "initial_query": query,
        "query_language": "de",
        "status": "IN_PROGRESS",
        "current_task": {"query": query, "step": 1},
        "execution_trace": [],
        "global_state": {
            "known_entities": [],
            "hypotheses": [],
            "rejected_paths": [],
            "confidence_scores": {}
        },
        "final_answer": None,
        "results_summary": None,
        "timestamps": {
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
    }
```

**Erfolgskriterien:**
- [ ] Neue Recherchen werden persistiert
- [ ] Bestehende Recherchen wiederaufsetzbar
- [ ] Execution Trace wird korrekt geloggt
- [ ] Error Handling robust
- [ ] Tests grün

**Verantwortlich:** Backend-Team

---

#### Task 1.1.5: Unit Tests für State Persistence
- **Priorität:** 🔴 P0
- **Aufwand:** S (2 Tage)
- **Abhängigkeiten:** Task 1.1.4
- **Status:** ⏳ TODO
- **Beschreibung:**
  Erstelle `tests/test_state_persister.py` mit umfassenden Tests

**Test Suite:**
```python
# tests/test_state_persister.py

import pytest
import uuid
from datetime import datetime
from backend.agents.veritas_state_persister import ResearchStatePersister
from backend.agents.veritas_research_state import ResearchState

@pytest.fixture
async def persister(db_config):
    """Create persister with test DB"""
    p = ResearchStatePersister(db_config)
    await p.init_pool()
    yield p
    await p.close_pool()

@pytest.fixture
def sample_state() -> ResearchState:
    """Create sample state for testing"""
    research_id = str(uuid.uuid4())
    return {
        "research_id": research_id,
        "user_id": "test_user",
        "initial_query": "Was regelt § 58 LBO BW?",
        "query_language": "de",
        "status": "IN_PROGRESS",
        "current_task": {"query": "...", "step": 1},
        "execution_trace": [],
        "global_state": {
            "known_entities": [],
            "hypotheses": [],
            "rejected_paths": [],
            "confidence_scores": {}
        },
        "final_answer": None,
        "results_summary": None,
        "timestamps": {
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
    }

@pytest.mark.asyncio
async def test_save_and_load_state(persister, sample_state):
    """Test: Save and load state"""
    research_id = sample_state['research_id']
    
    # Save
    await persister.save_state(research_id, sample_state)
    
    # Load
    loaded = await persister.load_state(research_id)
    
    assert loaded is not None
    assert loaded['research_id'] == research_id
    assert loaded['initial_query'] == sample_state['initial_query']
    assert loaded['status'] == 'IN_PROGRESS'

@pytest.mark.asyncio
async def test_update_existing_state(persister, sample_state):
    """Test: Update existing state"""
    research_id = sample_state['research_id']
    
    # Save initial
    await persister.save_state(research_id, sample_state)
    
    # Update status
    sample_state['status'] = 'COMPLETED'
    sample_state['final_answer'] = "Test answer"
    await persister.save_state(research_id, sample_state)
    
    # Load
    loaded = await persister.load_state(research_id)
    
    assert loaded['status'] == 'COMPLETED'
    assert loaded['final_answer'] == "Test answer"

@pytest.mark.asyncio
async def test_list_states_by_status(persister, sample_state):
    """Test: List states filtered by status"""
    # Create 3 states with different statuses
    state1 = {**sample_state, "research_id": str(uuid.uuid4()), "status": "IN_PROGRESS"}
    state2 = {**sample_state, "research_id": str(uuid.uuid4()), "status": "COMPLETED"}
    state3 = {**sample_state, "research_id": str(uuid.uuid4()), "status": "FAILED"}
    
    await persister.save_state(state1['research_id'], state1)
    await persister.save_state(state2['research_id'], state2)
    await persister.save_state(state3['research_id'], state3)
    
    # List only COMPLETED
    completed = await persister.list_states(status_filter="COMPLETED")
    
    assert len(completed) >= 1
    assert all(s['status'] == 'COMPLETED' for s in completed)

@pytest.mark.asyncio
async def test_delete_state(persister, sample_state):
    """Test: Delete state"""
    research_id = sample_state['research_id']
    
    # Save
    await persister.save_state(research_id, sample_state)
    
    # Delete
    await persister.delete_state(research_id)
    
    # Load should return None
    loaded = await persister.load_state(research_id)
    assert loaded is None

@pytest.mark.asyncio
async def test_load_nonexistent_state(persister):
    """Test: Load non-existent state returns None"""
    loaded = await persister.load_state("nonexistent-uuid")
    assert loaded is None

@pytest.mark.asyncio
async def test_execution_trace_logging(persister, sample_state):
    """Test: Execution trace is correctly stored"""
    research_id = sample_state['research_id']
    
    # Add execution trace entries
    sample_state['execution_trace'] = [
        {
            "task_id": 1,
            "timestamp": datetime.utcnow().isoformat(),
            "agent": "EnvironmentalAgent",
            "action": "EXECUTE",
            "input": {"query": "Test"},
            "output": {"answer": "..."},
            "evaluation": None,
            "error": None
        }
    ]
    
    await persister.save_state(research_id, sample_state)
    
    # Load
    loaded = await persister.load_state(research_id)
    
    assert len(loaded['execution_trace']) == 1
    assert loaded['execution_trace'][0]['agent'] == 'EnvironmentalAgent'
```

**Erfolgskriterien:**
- [ ] Alle Tests grün
- [ ] Coverage >90%
- [ ] Keine Race Conditions
- [ ] Performance: <100ms pro Test

**Verantwortlich:** QA-Team

---

### Sprint 1.2: LangGraph StateGraph (2 Wochen)

*(Detaillierte Tasks siehe IMPLEMENTATION_PLAN.md - zu lang für dieses Dokument)*

**Zusammenfassung:**
- Task 1.2.1: LangGraph Installation (S)
- Task 1.2.2: VeritasAgentState Schema (S)
- Task 1.2.3: Workflow Nodes Implementation (L)
- Task 1.2.4: Conditional Edges & Router (M)
- Task 1.2.5: StateGraph Compilation (M)
- Task 1.2.6: Integration Tests (M)

---

### Sprint 1.3: Evaluator-Agent (2 Wochen)

*(Detaillierte Tasks siehe IMPLEMENTATION_PLAN.md)*

**Zusammenfassung:**
- Task 1.3.1: Evaluator Agent Implementation (L)
- Task 1.3.2: Few-Shot Prompts (M)
- Task 1.3.3: Integration in Evaluate Node (S)
- Task 1.3.4: Unit Tests (M)

---

## 🏗️ Phase 2: Datenquellen-Erweiterung (4-6 Wochen) 🟡 WICHTIG

### Sprint 2.1: Neo4j Graph Database Agent (2-3 Wochen)

*(Detaillierte Tasks siehe IMPLEMENTATION_PLAN.md)*

**Zusammenfassung:**
- Task 2.1.1: Neo4j Docker Setup (S)
- Task 2.1.2: Sample Graph Data (M)
- Task 2.1.3: Neo4j Agent Implementation (L)
- Task 2.1.4: Integration in SupervisorAgent (M)
- Task 2.1.5: Tests (M)

---

### Sprint 2.2: SearxNG Web Search Agent (2-3 Wochen)

*(Detaillierte Tasks siehe IMPLEMENTATION_PLAN.md)*

**Zusammenfassung:**
- Task 2.2.1: SearxNG Docker Setup (S)
- Task 2.2.2: Privacy Config (S)
- Task 2.2.3: SearxNG Agent Implementation (M)
- Task 2.2.4: Integration in SupervisorAgent (S)
- Task 2.2.5: Tests (M)

---

## 🏗️ Phase 3: Kryptographische Integrität (2-4 Wochen) 🟠 COMPLIANCE

### Sprint 3.1: Hash-Kette + Signaturen (2 Wochen)

*(Detaillierte Tasks siehe IMPLEMENTATION_PLAN.md)*

**Zusammenfassung:**
- Task 3.1.1: Integrity Manager Implementation (M)
- Task 3.1.2: Integration in State Persister (M)
- Task 3.1.3: Tests (M)

---

## 🏗️ Phase 4: Prefect Macro-Orchestrierung (4-6 Wochen) 🟢 OPTIONAL

*(Nur wenn Multi-Stunden-Workflows benötigt werden)*

---

## 📊 Quick Reference: Prioritäten-Matrix

### 🔴 P0 - Sofort starten! (8-10 Wochen)

| ID | Task | Aufwand | Blockt |
|----|------|---------|--------|
| 1.1.1 | Research State Schema | S | 1.1.2, 1.1.3 |
| 1.1.2 | PostgreSQL Migration | S | 1.1.3 |
| 1.1.3 | State Persister | M | 1.1.4 |
| 1.1.4 | SupervisorAgent Integration | M | 1.1.5 |
| 1.1.5 | State Persistence Tests | S | - |
| 1.2.x | LangGraph Workflow | L | 1.3.3 |
| 1.3.x | Evaluator Agent | L | - |

### 🟡 P1 - MVP-kritisch (6-8 Wochen)

| ID | Task | Aufwand |
|----|------|---------|
| 2.1.x | Neo4j Agent | M |
| 2.2.x | SearxNG Agent | M |

### 🟠 P2 - Production (2-3 Wochen)

| ID | Task | Aufwand |
|----|------|---------|
| 3.1.x | Integrity Manager | M |

### 🟢 P3 - Optional (4-6 Wochen)

| ID | Task | Aufwand |
|----|------|---------|
| 3.2.x | TSP Timestamps | M |
| 4.x.x | Prefect | XL |

---

## 🎯 Definition of Done

**Für jede Task:**
- [ ] Code implementiert & funktioniert
- [ ] Unit Tests geschrieben (>80% Coverage)
- [ ] Integration Tests grün
- [ ] Code Review durchgeführt
- [ ] Dokumentation aktualisiert
- [ ] Performance-Check OK
- [ ] Security-Check OK
- [ ] Merged in `main`

**Für jeden Sprint:**
- [ ] Alle Tasks "Done"
- [ ] Sprint Review durchgeführt
- [ ] Demo an Stakeholder
- [ ] Retrospektive
- [ ] Dokumentation aktualisiert

---

## 📅 Zeitplan-Vorschlag

### Woche 1-2: Sprint 1.1 (Persistent State)
- Mo-Di: Task 1.1.1 (Schema)
- Mi: Task 1.1.2 (Migration)
- Do-Fr + Mo-Mi: Task 1.1.3 (Persister)
- Do-Fr + Mo-Di: Task 1.1.4 (Integration)
- Mi-Do: Task 1.1.5 (Tests)
- Fr: Sprint Review

### Woche 3-4: Sprint 1.2 (LangGraph)
- Mo-Di: Task 1.2.1-1.2.2 (Setup + Schema)
- Mi-Fr + Mo-Fr: Task 1.2.3 (Nodes)
- Mo-Mi: Task 1.2.4 (Edges)
- Do-Fr: Task 1.2.5 (Compilation)
- Mo-Mi: Task 1.2.6 (Tests)
- Do-Fr: Sprint Review

### Woche 5-6: Sprint 1.3 (Evaluator)
- Mo-Fr: Task 1.3.1 (Evaluator)
- Mo-Mi: Task 1.3.2 (Prompts)
- Do: Task 1.3.3 (Integration)
- Fr + Mo-Mi: Task 1.3.4 (Tests)
- Do-Fr: Phase 1 Review & Demo

### Woche 7-12: Phase 2 (Datenquellen)
- Woche 7-9: Sprint 2.1 (Neo4j)
- Woche 10-12: Sprint 2.2 (SearxNG)

### Woche 13-16: Phase 3 (Integrität)
- Woche 13-14: Sprint 3.1 (Hash + Sig)
- Woche 15-16: Buffer / Refactoring

---

**Ende der Task-Liste**

**Nächste Schritte:**
1. Team-Meeting: Review dieses Plans
2. Ressourcen-Allocation klären
3. Sprint 1.1 starten: Task 1.1.0 (Analyse)
