# UDS3 Real Agent Integration - Implementation Plan

## Problem Statement
Currently, both streaming systems use **mock data** instead of real UDS3 database queries:

1. `IntelligentMultiAgentPipeline._generate_mock_agent_result()` (line 1703)
2. `veritas_api_backend._generate_agent_result()` (line 1050)

Both return hardcoded responses instead of querying the UDS3 vector database.

## Current Architecture

### Mock System (Currently Active)
```
User Query
    ↓
IntelligentMultiAgentPipeline
    ↓
_run_agent_task_sync()
    ↓
_generate_mock_agent_result()  ← MOCK DATA!
    ↓
Hardcoded responses
```

### Real Agent System (Exists but Not Used)
```
VERITAS Agents:
- veritas_api_agent_environmental.py
- veritas_api_agent_financial.py
- veritas_api_agent_construction.py
- veritas_api_agent_traffic.py
- etc.

UDS3 Integration:
- UDS3VectorSearchAdapter (backend/agents/veritas_uds3_adapter.py)
- OptimizedUnifiedDatabaseStrategy (uds3/uds3_core.py)
- AgentRegistry (backend/agents/veritas_api_agent_registry.py)
```

## Implementation Plan

### Step 1: Modify `_run_agent_task_sync()` in IntelligentMultiAgentPipeline

**File**: `backend/agents/veritas_intelligent_pipeline.py`
**Function**: `_run_agent_task_sync()` (line 1066)

**Current**:
```python
def _run_agent_task_sync(self, request, task, rag_context):
    # Mock-Ausführung (Placeholder für echte Agentenlogik)
    mock_result = self._generate_mock_agent_result(task.agent_type, request.query_text)
    # ...
```

**Target**:
```python
def _run_agent_task_sync(self, request, task, rag_context):
    # Echte Agent-Ausführung über Registry
    real_result = self._execute_real_agent(task.agent_type, request.query_text, rag_context)
    # ...
```

### Step 2: Implement `_execute_real_agent()` Method

**New Method** in `IntelligentMultiAgentPipeline`:

```python
def _execute_real_agent(
    self, 
    agent_type: str, 
    query: str, 
    rag_context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Führt echten VERITAS Agent aus mit UDS3 Hybrid Search
    
    Args:
        agent_type: Agent-Typ (z.B. 'environmental', 'construction')
        query: User Query
        rag_context: RAG-Kontext mit relevanten Dokumenten
        
    Returns:
        Agent-Result mit echten Daten aus UDS3
    """
    try:
        # 1. Agent-Registry nutzen
        from backend.agents.veritas_api_agent_registry import AgentRegistry
        registry = AgentRegistry()
        
        # 2. Agent-Typ mapping
        agent_type_map = {
            'geo_context': 'environmental',
            'legal_framework': 'legal',
            'document_retrieval': 'database',
            'environmental': 'environmental',
            'construction': 'construction',
            'traffic': 'traffic',
            'financial': 'financial',
            'social': 'social'
        }
        
        mapped_type = agent_type_map.get(agent_type, agent_type)
        
        # 3. Agent erstellen
        agent = registry.create_agent(mapped_type)
        
        if not agent:
            logger.warning(f"⚠️ Agent {agent_type} nicht verfügbar, Fallback auf Mock")
            return self._generate_mock_agent_result(agent_type, query)
        
        # 4. Query-Request erstellen
        from backend.agents.veritas_api_agent_core_components import TemplateQueryRequest
        
        request = TemplateQueryRequest(
            query_id=f"agent_{agent_type}_{int(time.time())}",
            query_text=query,
            context=rag_context,
            parameters={'top_k': 5, 'threshold': 0.5}
        )
        
        # 5. Agent ausführen
        response = agent.execute_query(request)
        
        # 6. Result transformieren
        if response.success:
            return {
                'agent_type': agent_type,
                'status': 'completed',
                'confidence_score': response.metadata.get('confidence', 0.75),
                'processing_time': response.processing_time_ms / 1000,
                'summary': response.results[0].content if response.results else 'Keine Ergebnisse',
                'details': '\n'.join([r.content for r in response.results[:3]]),
                'sources': [
                    {
                        'title': r.metadata.get('source', 'UDS3 Database'),
                        'relevance': r.metadata.get('score', 0.8),
                        'snippet': r.content[:200]
                    }
                    for r in response.results[:5]
                ]
            }
        else:
            # Error Fallback
            logger.error(f"❌ Agent {agent_type} failed: {response.error_message}")
            return self._generate_mock_agent_result(agent_type, query)
            
    except Exception as e:
        logger.error(f"❌ Real Agent Execution Error: {e}")
        # Graceful Degradation zu Mock
        return self._generate_mock_agent_result(agent_type, query)
```

### Step 3: Update `_generate_agent_result()` in API Backend

**File**: `backend/api/veritas_api_backend.py`
**Function**: `_generate_agent_result()` (line 1050)

**Current**:
```python
def _generate_agent_result(agent_type: str, query: str, complexity: str):
    # Versuche UDS3 Hybrid Search
    if uds3_strategy is not None:
        # ... UDS3 Query
        pass
    
    # Fallback: Simulierte Daten
    agent_specialties = {...}  # Hardcoded
```

**Target**:
```python
def _generate_agent_result(agent_type: str, query: str, complexity: str):
    global uds3_strategy
    
    # 1. Prüfe ob UDS3 verfügbar
    if uds3_strategy is None:
        logger.warning("⚠️ UDS3 nicht verfügbar, verwende Mock-Daten")
        return _generate_mock_agent_result(agent_type, query, complexity)
    
    # 2. UDS3 Hybrid Search ausführen
    try:
        category = agent_to_category.get(agent_type, 'general')
        
        search_result = uds3_strategy.query_across_databases(
            vector_params={
                "query_text": query,
                "top_k": 5,
                "threshold": 0.5,
                "metadata_filter": {"category": category}
            },
            graph_params=None,
            relational_params=None,
            join_strategy="union"
        )
        
        # 3. Ergebnisse transformieren
        if search_result.success and search_result.joined_results:
            documents = search_result.joined_results[:5]
            
            return {
                'agent_type': agent_type,
                'confidence_score': documents[0].get('score', 0.8),
                'processing_time': 1.5,
                'summary': documents[0].get('content', '')[:200],
                'details': '\n'.join([doc.get('content', '')[:150] for doc in documents[:3]]),
                'sources': [
                    doc.get('metadata', {}).get('source', f'UDS3 Database - {category}')
                    for doc in documents
                ],
                'status': 'completed',
                'source_documents': documents  # Für weitere Verarbeitung
            }
        else:
            logger.info(f"ℹ️ UDS3 Query für {agent_type} lieferte keine Ergebnisse")
            return _generate_mock_agent_result(agent_type, query, complexity)
            
    except Exception as e:
        logger.error(f"❌ UDS3 Query Error für {agent_type}: {e}")
        return _generate_mock_agent_result(agent_type, query, complexity)
```

### Step 4: Extract Mock Function

**File**: `backend/api/veritas_api_backend.py`

Rename existing `_generate_agent_result()` → `_generate_mock_agent_result()` and keep as fallback.

## Testing Plan

### Test 1: UDS3 Availability
```bash
python -c "
from uds3.uds3_core import get_optimized_unified_strategy
uds3 = get_optimized_unified_strategy()
print('UDS3 Available:', uds3 is not None)
"
```

### Test 2: Single Agent Execution
```python
from backend.agents.veritas_api_agent_registry import AgentRegistry

registry = AgentRegistry()
env_agent = registry.create_agent('environmental')
print("Environmental Agent:", env_agent is not None)
```

### Test 3: Full Pipeline with Real Agents
```bash
python test_dual_prompt_stuttgart.py
```

**Expected**:
- Different sources per query (not hardcoded)
- Real database snippets
- Varied confidence scores

### Test 4: Regional Differences
```bash
# Stuttgart Query
python test_dual_prompt_stuttgart.py

# Brandenburg Query  
python test_dual_prompt_brandenburg.py
```

**Expected**:
- Stuttgart results contain Stuttgart-specific sources
- Brandenburg results contain Brandenburg-specific sources
- Different agents selected based on regional context

## Rollback Strategy

If real agents fail:
1. Exception caught in `_execute_real_agent()`
2. Falls back to `_generate_mock_agent_result()`
3. System continues working (graceful degradation)

## Success Criteria

✅ UDS3 queries return real database results
✅ Agent responses contain varied data (not hardcoded)
✅ Sources are specific to query region
✅ Confidence scores based on similarity, not hash
✅ No performance degradation (< 2s per agent)
✅ Fallback works when UDS3 unavailable

## Implementation Priority

**HIGH** (Blocks production readiness):
- Step 1 & 2: Real agent execution in IntelligentMultiAgentPipeline
- Step 3 & 4: Real UDS3 queries in API backend

**MEDIUM** (Optimization):
- Caching for repeated queries
- Agent result ranking
- Error handling refinement

**LOW** (Future enhancement):
- Multi-region support
- Custom agent creation
- Dynamic agent selection
