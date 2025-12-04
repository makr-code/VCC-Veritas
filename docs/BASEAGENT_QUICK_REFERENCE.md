# BaseAgent Framework - Quick Reference Card 📋

**Version:** 2.0 | **Updated:** 4. Dezember 2025

---

## 🚀 Quick Start

### 1. Create New Agent

```python
from backend.agents.framework.base_agent import BaseAgent
from backend.agents.registry.api_agent_registry import AgentCapability
from backend.agents.framework.agent_monitoring import AgentMonitor
from backend.agents.framework.quality_gate import QualityGate, QualityPolicy
from backend.agents.framework.retry_handler import RetryHandler, RetryConfig

class MyAgent(BaseAgent):
    AGENT_TYPE = "my_agent"

    def __init__(self, agent_id: Optional[str] = None):
        super().__init__(agent_id=agent_id)

        # Framework Components
        self.monitor = AgentMonitor(self.AGENT_TYPE)

        # Quality Gate (REQUIRED: Use QualityPolicy)
        policy = QualityPolicy(min_quality=0.6, target_quality=0.8)
        self.quality_gate = QualityGate(policy)

        # Retry Handler (REQUIRED: Use RetryConfig)
        retry_config = RetryConfig(max_retries=3)
        self.retry_handler = RetryHandler(retry_config)

    def execute_step(self, step_data: dict) -> dict:
        """REQUIRED: Implement abstract method"""
        query = step_data.get("query", "")
        if not query:
            return {"success": False, "error": "No query"}
        result = asyncio.run(self.process_query(query))
        return result

    def get_agent_type(self) -> str:
        """REQUIRED: Return agent type"""
        return self.AGENT_TYPE

    def get_capabilities(self) -> List[AgentCapability]:
        """REQUIRED: Return capabilities"""
        return [
            AgentCapability.QUERY_PROCESSING,
            AgentCapability.DOMAIN_SPECIFIC_PROCESSING
        ]

    async def process_query(self, query: str, context: Optional[Dict] = None):
        """Your custom query processing logic"""
        # Implement your agent logic here
        return {
            "success": True,
            "results": [...],
            "confidence": 0.8
        }
```

---

## ✅ Implementation Checklist

### Required Methods
- [ ] `__init__()` - Initialize with framework components
- [ ] `execute_step()` - Implement abstract method
- [ ] `get_agent_type()` - Return agent type string
- [ ] `get_capabilities()` - Return capability list
- [ ] `process_query()` - Async query processing

### Required Framework Components
- [ ] `AgentMonitor` - Performance tracking
- [ ] `QualityGate` with `QualityPolicy` - Result validation
- [ ] `RetryHandler` with `RetryConfig` - Error recovery

### Registry Integration
- [ ] Create registration function
- [ ] Register in `domain_agent_registration.py`
- [ ] Set lifecycle type (ON_DEMAND, POOLED, PERSISTENT)
- [ ] Configure max concurrent instances

---

## 🔧 Framework Components

### AgentMonitor
```python
from backend.agents.framework.agent_monitoring import AgentMonitor

self.monitor = AgentMonitor("agent_type")

# Available methods (check implementation):
# - record_step_execution()
# - record_plan_execution()
# Note: Some methods may not be implemented yet
```

### QualityGate ✅
```python
from backend.agents.framework.quality_gate import QualityGate, QualityPolicy

# CORRECT: Use QualityPolicy object
policy = QualityPolicy(
    min_quality=0.6,      # Minimum acceptable quality
    target_quality=0.8,   # Target quality threshold
    require_review=False  # Optional human review
)
self.quality_gate = QualityGate(policy)

# ❌ WRONG: Don't use min_confidence parameter
# self.quality_gate = QualityGate(min_confidence=0.6)  # FAILS!
```

### RetryHandler ✅
```python
from backend.agents.framework.retry_handler import (
    RetryHandler,
    RetryConfig,
    RetryStrategy
)

# CORRECT: Use RetryConfig object
retry_config = RetryConfig(
    max_retries=3,
    base_delay=1.0,
    backoff_factor=2.0,
    strategy=RetryStrategy.EXPONENTIAL
)
self.retry_handler = RetryHandler(retry_config)

# ❌ WRONG: Don't use max_retries parameter
# self.retry_handler = RetryHandler(max_retries=3)  # FAILS!
```

---

## 🎯 AgentCapability Reference

### Standard Capabilities
```python
from backend.agents.registry.api_agent_registry import AgentCapability

# Core
AgentCapability.QUERY_PROCESSING              # ✅ Standard
AgentCapability.DATA_ANALYSIS                 # ✅ Standard

# Context & Analysis
AgentCapability.GEO_CONTEXT_RESOLUTION       # Geographic context
AgentCapability.TEMPORAL_ANALYSIS            # Time-based analysis
AgentCapability.DOMAIN_CLASSIFICATION        # Domain detection
AgentCapability.JURISDICTION_MAPPING         # Legal jurisdiction

# Legal & Regulatory
AgentCapability.LEGAL_FRAMEWORK_ANALYSIS     # ✅ Legal agents
AgentCapability.COMPLIANCE_CHECKING          # Compliance checks
AgentCapability.PROCESS_GUIDANCE             # Process guidance

# Domain-Specific
AgentCapability.ENVIRONMENTAL_DATA_PROCESSING  # ✅ Environmental
AgentCapability.BUILDING_PERMIT_PROCESSING     # ✅ Construction
AgentCapability.WEATHER_DATA                   # ✅ Weather
AgentCapability.EXTERNAL_API                   # ✅ API integration
AgentCapability.REAL_TIME_PROCESSING           # ✅ Real-time data
```

### ❌ Common Mistakes
```python
# WRONG - These don't exist:
AgentCapability.LEGAL_FRAMEWORK              # ❌ Use LEGAL_FRAMEWORK_ANALYSIS
AgentCapability.ENVIRONMENTAL_DATA           # ❌ Use ENVIRONMENTAL_DATA_PROCESSING
AgentCapability.DOMAIN_SPECIFIC_PROCESSING   # ❌ Use specific domain capability
```

---

## 📝 Registration Template

### Create Registration Function
```python
from backend.agents.registry.api_agent_registry import (
    get_agent_registry,
    AgentCapability,
    AgentLifecycleType
)

def register_my_agent():
    """Register MyAgent in VERITAS Registry"""
    try:
        registry = get_agent_registry()
        registry.register_agent(
            agent_type="my_agent",
            agent_class=MyAgent,
            capabilities=[
                AgentCapability.QUERY_PROCESSING,
                AgentCapability.DOMAIN_CLASSIFICATION
            ],
            lifecycle_type=AgentLifecycleType.ON_DEMAND,
            max_concurrent_instances=2,
            priority=1,
            description="My custom agent description"
        )
        logger.info("✅ MyAgent registered successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to register MyAgent: {e}")
        return False
```

### Add to domain_agent_registration.py
```python
def register_phase1_agents(registry: AgentRegistry) -> Dict[str, bool]:
    """Register Phase 1 Agents"""
    results = {}

    # ... existing agents ...

    # Your new agent
    try:
        from backend.agents.domain.my_domain.my_agent import MyAgent
        registry.register_agent(
            agent_type="my_agent",
            agent_class=MyAgent,
            capabilities=[AgentCapability.QUERY_PROCESSING],
            lifecycle_type=AgentLifecycleType.ON_DEMAND,
            max_concurrent_instances=2,
            priority=1,
            description="My agent"
        )
        results["my_agent"] = True
    except Exception as e:
        logger.error(f"Failed to register my_agent: {e}")
        results["my_agent"] = False

    return results
```

---

## 🧪 Testing Template

### Unit Tests
```python
import pytest
import asyncio
from unittest.mock import Mock

# Import your agent
from backend.agents.domain.my_domain.my_agent import MyAgent

@pytest.fixture
def agent_instance():
    """Create agent instance for testing"""
    return MyAgent(agent_id="test_my_agent_001")

class TestMyAgentInitialization:
    def test_agent_initialization(self, agent_instance):
        """Test agent initializes correctly"""
        assert agent_instance is not None
        assert agent_instance.agent_id == "test_my_agent_001"

    def test_agent_type(self, agent_instance):
        """Test agent type"""
        assert agent_instance.get_agent_type() == "my_agent"

    def test_agent_capabilities(self, agent_instance):
        """Test agent capabilities"""
        capabilities = agent_instance.get_capabilities()
        assert len(capabilities) > 0
        assert AgentCapability.QUERY_PROCESSING in capabilities

class TestMyAgentAsyncProcessing:
    @pytest.mark.asyncio
    async def test_async_process_query(self, agent_instance):
        """Test async query processing"""
        result = await agent_instance.process_query("test query")
        assert "success" in result
        assert "results" in result
        assert "confidence" in result
```

### Benchmarks
```python
import pytest
import time
import asyncio

class TestMyAgentBenchmarks:
    def test_single_query_execution_time(self, agent_instance):
        """Benchmark single query execution"""
        start = time.time()
        result = asyncio.run(agent_instance.process_query("test"))
        duration = time.time() - start

        assert duration < 0.1  # < 100ms
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_concurrent_queries_10(self, agent_instance):
        """Benchmark 10 concurrent queries"""
        queries = ["test query"] * 10

        start = time.time()
        results = await asyncio.gather(*[
            agent_instance.process_query(q) for q in queries
        ])
        duration = time.time() - start

        assert duration < 0.5  # < 500ms
        assert all(r["success"] for r in results)
```

---

## 🐛 Common Issues & Solutions

### Issue 1: QualityGate initialization fails
```
TypeError: QualityGate.__init__() got unexpected keyword argument 'min_confidence'
```

**Solution:**
```python
# ❌ WRONG
self.quality_gate = QualityGate(min_confidence=0.6)

# ✅ CORRECT
policy = QualityPolicy(min_quality=0.6, target_quality=0.8)
self.quality_gate = QualityGate(policy)
```

### Issue 2: RetryHandler initialization fails
```
TypeError: RetryHandler.__init__() got unexpected keyword argument 'max_retries'
```

**Solution:**
```python
# ❌ WRONG
self.retry_handler = RetryHandler(max_retries=3)

# ✅ CORRECT
retry_config = RetryConfig(max_retries=3)
self.retry_handler = RetryHandler(retry_config)
```

### Issue 3: AgentCapability doesn't exist
```
AttributeError: type object 'AgentCapability' has no attribute 'LEGAL_FRAMEWORK'
```

**Solution:**
```python
# ❌ WRONG
AgentCapability.LEGAL_FRAMEWORK
AgentCapability.ENVIRONMENTAL_DATA

# ✅ CORRECT
AgentCapability.LEGAL_FRAMEWORK_ANALYSIS
AgentCapability.ENVIRONMENTAL_DATA_PROCESSING
```

### Issue 4: AsyncIO Event Loop error
```
RuntimeError: asyncio.run() cannot be called from a running event loop
```

**Solution:**
```python
# In execute_step() for sync context:
result = asyncio.run(self.process_query(query))

# In tests, use @pytest.mark.asyncio:
@pytest.mark.asyncio
async def test_method(self):
    result = await agent.process_query(query)
```

### Issue 5: Abstract method not implemented
```
TypeError: Can't instantiate abstract class MyAgent without implementation
for abstract method 'execute_step'
```

**Solution:**
```python
def execute_step(self, step_data: dict) -> dict:
    """REQUIRED: Implement this method"""
    query = step_data.get("query", "")
    if not query:
        return {"success": False, "error": "No query"}
    result = asyncio.run(self.process_query(query))
    return result
```

---

## 📚 Reference Files

### Documentation
- `PHASE1_MIGRATION_COMPLETE.md` - Complete migration report
- `PHASE1_EXECUTIVE_SUMMARY.md` - Executive summary
- `AGENT_MIGRATION_PHASE1_STATUS.md` - Detailed status
- `PHASE1_TEST_INFRASTRUCTURE_COMPLETE.md` - Test infrastructure

### Example Agents
- `backend/agents/domain/construction/genehmigung_agent.py` - Legal agent
- `backend/agents/domain/weather/dwd_weather_agent_v3_framework.py` - Weather agent
- `backend/agents/domain/construction/construction_agent_v2_framework.py` - Construction
- `backend/agents/domain/environmental/environmental_agent_v2_framework.py` - Environmental

### Tools
- `resolve_all_conflicts.py` - Auto-fix merge conflicts
- `fix_agent_frameworks.py` - Fix framework parameters
- `fix_monitor_calls.py` - Fix monitor method calls

---

## ✅ Pre-commit Checklist

Before committing your new agent:

- [ ] All required methods implemented
- [ ] Framework components initialized correctly
- [ ] Agent registered in registry
- [ ] Unit tests written (min. 10 tests)
- [ ] Benchmarks created (min. 3 benchmarks)
- [ ] Documentation updated
- [ ] All tests passing
- [ ] Code formatted & linted
- [ ] Type hints added
- [ ] Docstrings complete

---

## 🚀 Performance Targets

| Metric | Target | Critical |
|--------|--------|----------|
| Single Query | < 100ms | < 500ms |
| 10 Concurrent | < 500ms | < 2s |
| 50 Concurrent | < 2s | < 5s |
| Memory Baseline | < 30MB | < 100MB |
| Memory Under Load | < 50MB | < 200MB |

---

**Quick Reference v2.0 | BaseAgent Framework**
**Last Updated:** 4. Dezember 2025
**Maintainer:** VERITAS Development Team
