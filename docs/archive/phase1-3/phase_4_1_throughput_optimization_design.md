# Phase 4.1: Throughput-Optimierung - Design Document

**Version:** 1.0  
**Datum:** 6. Oktober 2025  
**Status:** 🔄 **IN PROGRESS**  
**Ziel:** Message-Broker Throughput von 23.5 msg/s auf **500+ msg/s** steigern

---

## 📋 Problem-Analyse

### Aktueller Status (Phase 4 Baseline)

**Performance-Metriken:**
- **Throughput:** 23.5 messages/sec
- **Avg Latency:** 42.5ms
- **Peak Latency:** ~800ms (Request/Response)
- **Queue-Processing:** Sequential (Single Worker)
- **Messages Delivered:** 248 / 175 sent (100% Success Rate)

**Bottleneck-Identifikation:**

```python
# Aktueller Code (agent_message_broker.py):
async def _message_worker(self):
    """Background worker für Message-Delivery (SEQUENTIAL)"""
    while self._running:
        try:
            priority, msg_id, message = await self._message_queue.get()
            
            # BOTTLENECK: Sequential Processing
            await self._deliver_message(message)  # ← Blocks next message
            
        except Exception as e:
            logger.error(f"Worker error: {e}")
```

**Problem:**
- ✅ Latency akzeptabel (42.5ms < 50ms Ziel)
- ❌ **Throughput zu niedrig** (23.5 msg/s vs 500+ msg/s Ziel)
- ❌ **Single Worker** kann nur 1 Message gleichzeitig verarbeiten
- ❌ **Kein Batching** - jede Message einzeln verarbeitet
- ❌ **Context-Switching-Overhead** pro Message

---

## 🎯 Optimierungs-Ziele

### Performance-Targets

| Metrik | Aktuell | Ziel | Faktor |
|--------|---------|------|--------|
| **Throughput** | 23.5 msg/s | 500+ msg/s | **21x** |
| **Avg Latency** | 42.5ms | < 50ms | ✅ (halten) |
| **P95 Latency** | ~250ms | < 200ms | **1.25x besser** |
| **P99 Latency** | ~800ms | < 500ms | **1.6x besser** |
| **CPU-Usage** | ~5% | < 30% | Acceptable |
| **Memory** | ~5MB | < 50MB | Acceptable |

### Architektur-Ziele

1. ✅ **Multi-Worker-Pattern** (3-5 parallele Worker)
2. ✅ **Message-Batching** (10-50 Messages pro Batch)
3. ✅ **Load-Balancing** (Round-Robin oder Priority-basiert)
4. ✅ **Worker-Health-Monitoring**
5. ✅ **Backward-Kompatibilität** (keine API-Änderungen)

---

## 🏗️ Architektur-Design

### Komponenten-Übersicht

```
┌────────────────────────────────────────────────────────────────┐
│              AgentMessageBroker (Enhanced)                     │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌──────────────────────────────────────────────────────┐     │
│  │  Configuration                                       │     │
│  │  - num_workers: int = 5                              │     │
│  │  - batch_size: int = 20                              │     │
│  │  - batch_timeout_ms: int = 100                       │     │
│  │  - max_queue_size: int = 10000                       │     │
│  └──────────────────────────────────────────────────────┘     │
│                                                                │
│  ┌──────────────────────────────────────────────────────┐     │
│  │  Message Queue (asyncio.PriorityQueue)               │     │
│  │  - Priority-based                                    │     │
│  │  - Max 10000 messages                                │     │
│  └───────────────────┬──────────────────────────────────┘     │
│                      │                                         │
│                      ▼                                         │
│  ┌──────────────────────────────────────────────────────┐     │
│  │  Worker Pool Manager                                 │     │
│  │  - Spawns N workers (default 5)                      │     │
│  │  - Health monitoring                                 │     │
│  │  - Auto-restart on failure                           │     │
│  └───────────────────┬──────────────────────────────────┘     │
│                      │                                         │
│         ┌────────────┴────────────┬───────────┬──────────┐    │
│         ▼            ▼            ▼           ▼          ▼    │
│   ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ...   │
│   │Worker 1 │  │Worker 2 │  │Worker 3 │  │Worker 4 │        │
│   │         │  │         │  │         │  │         │        │
│   │ Batch   │  │ Batch   │  │ Batch   │  │ Batch   │        │
│   │ Process │  │ Process │  │ Process │  │ Process │        │
│   └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘        │
│        │            │            │            │               │
│        └────────────┴────────────┴────────────┘               │
│                      │                                         │
│                      ▼                                         │
│  ┌──────────────────────────────────────────────────────┐     │
│  │  Delivery Layer                                      │     │
│  │  - Parallel message delivery                         │     │
│  │  - Error handling & retries                          │     │
│  │  - Dead-letter-queue                                 │     │
│  └──────────────────────────────────────────────────────┘     │
│                                                                │
│  ┌──────────────────────────────────────────────────────┐     │
│  │  Statistics & Monitoring                             │     │
│  │  - Per-worker stats                                  │     │
│  │  - Batch processing metrics                          │     │
│  │  - Throughput/Latency histograms                     │     │
│  └──────────────────────────────────────────────────────┘     │
└────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Design-Details

### 1. Multi-Worker-Pattern

#### Worker-Pool-Configuration

```python
@dataclass
class BrokerConfiguration:
    """Broker Performance Configuration"""
    
    # Worker Pool
    num_workers: int = 5
    worker_restart_on_failure: bool = True
    worker_health_check_interval_sec: float = 30.0
    
    # Message Batching
    enable_batching: bool = True
    batch_size: int = 20  # Messages pro Batch
    batch_timeout_ms: int = 100  # Max wait time für Batch-Completion
    
    # Queue Settings
    max_queue_size: int = 10000
    queue_warning_threshold: float = 0.8  # Warn at 80% full
    
    # Performance Tuning
    delivery_parallelism: int = 10  # Max parallel deliveries pro Worker
    retry_max_attempts: int = 3
    retry_backoff_ms: int = 100
```

#### Worker-Lifecycle

```python
class MessageWorker:
    """Individual Message-Processing Worker"""
    
    def __init__(self, worker_id: int, broker: 'AgentMessageBroker'):
        self.worker_id = worker_id
        self.broker = broker
        self.messages_processed = 0
        self.batches_processed = 0
        self.errors = 0
        self.is_healthy = True
        self._running = False
        self._task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start worker task"""
        self._running = True
        self._task = asyncio.create_task(self._run())
        logger.info(f"Worker {self.worker_id} started")
    
    async def stop(self):
        """Graceful shutdown"""
        self._running = False
        if self._task:
            await self._task
        logger.info(f"Worker {self.worker_id} stopped")
    
    async def _run(self):
        """Main worker loop"""
        while self._running:
            try:
                # Batch collection
                batch = await self._collect_batch()
                
                if batch:
                    # Parallel batch processing
                    await self._process_batch(batch)
                    self.batches_processed += 1
                    
            except Exception as e:
                self.errors += 1
                self.is_healthy = False
                logger.error(f"Worker {self.worker_id} error: {e}")
                
                if self.broker.config.worker_restart_on_failure:
                    await asyncio.sleep(1.0)  # Backoff
                    self.is_healthy = True  # Auto-recover
    
    async def _collect_batch(self) -> List[AgentMessage]:
        """Collect messages for batch processing"""
        batch = []
        batch_start = asyncio.get_event_loop().time()
        
        while len(batch) < self.broker.config.batch_size:
            timeout = (self.broker.config.batch_timeout_ms / 1000.0)
            elapsed = asyncio.get_event_loop().time() - batch_start
            remaining = max(0, timeout - elapsed)
            
            if remaining == 0 and batch:
                break  # Batch timeout reached
            
            try:
                # Non-blocking queue get with timeout
                priority, msg_id, message = await asyncio.wait_for(
                    self.broker._message_queue.get(),
                    timeout=remaining
                )
                batch.append(message)
                
            except asyncio.TimeoutError:
                break  # Timeout, process partial batch
        
        return batch
    
    async def _process_batch(self, batch: List[AgentMessage]):
        """Process batch of messages in parallel"""
        tasks = []
        
        for message in batch:
            task = asyncio.create_task(self.broker._deliver_message(message))
            tasks.append(task)
            
            # Limit parallelism
            if len(tasks) >= self.broker.config.delivery_parallelism:
                await asyncio.gather(*tasks, return_exceptions=True)
                tasks = []
        
        # Process remaining
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        self.messages_processed += len(batch)
```

---

### 2. Worker-Pool-Manager

```python
class WorkerPoolManager:
    """Manages pool of message workers"""
    
    def __init__(self, broker: 'AgentMessageBroker'):
        self.broker = broker
        self.workers: List[MessageWorker] = []
        self._health_check_task: Optional[asyncio.Task] = None
    
    async def start(self, num_workers: int):
        """Start worker pool"""
        for i in range(num_workers):
            worker = MessageWorker(worker_id=i, broker=self.broker)
            await worker.start()
            self.workers.append(worker)
        
        # Start health monitoring
        self._health_check_task = asyncio.create_task(self._health_monitor())
        
        logger.info(f"Worker pool started with {num_workers} workers")
    
    async def stop(self):
        """Stop all workers"""
        if self._health_check_task:
            self._health_check_task.cancel()
        
        for worker in self.workers:
            await worker.stop()
        
        self.workers = []
        logger.info("Worker pool stopped")
    
    async def _health_monitor(self):
        """Monitor worker health and restart failed workers"""
        interval = self.broker.config.worker_health_check_interval_sec
        
        while True:
            await asyncio.sleep(interval)
            
            for worker in self.workers:
                if not worker.is_healthy:
                    logger.warning(f"Worker {worker.worker_id} unhealthy, restarting...")
                    
                    await worker.stop()
                    new_worker = MessageWorker(worker.worker_id, self.broker)
                    await new_worker.start()
                    
                    # Replace in list
                    idx = self.workers.index(worker)
                    self.workers[idx] = new_worker
    
    def get_stats(self) -> Dict[str, Any]:
        """Aggregate worker statistics"""
        total_processed = sum(w.messages_processed for w in self.workers)
        total_batches = sum(w.batches_processed for w in self.workers)
        total_errors = sum(w.errors for w in self.workers)
        healthy_workers = sum(1 for w in self.workers if w.is_healthy)
        
        return {
            "total_workers": len(self.workers),
            "healthy_workers": healthy_workers,
            "total_messages_processed": total_processed,
            "total_batches_processed": total_batches,
            "total_worker_errors": total_errors,
            "avg_messages_per_worker": total_processed / len(self.workers) if self.workers else 0,
            "worker_details": [
                {
                    "worker_id": w.worker_id,
                    "messages_processed": w.messages_processed,
                    "batches_processed": w.batches_processed,
                    "errors": w.errors,
                    "is_healthy": w.is_healthy
                }
                for w in self.workers
            ]
        }
```

---

### 3. Enhanced AgentMessageBroker

```python
class AgentMessageBroker:
    """Enhanced Message Broker with Multi-Worker Pattern"""
    
    def __init__(self, config: Optional[BrokerConfiguration] = None):
        self.config = config or BrokerConfiguration()
        
        # Existing components
        self._agents: Dict[str, AgentIdentity] = {}
        self._handlers: Dict[str, Callable] = {}
        self._subscriptions: Dict[str, Set[str]] = {}
        self._message_queue = asyncio.PriorityQueue(
            maxsize=self.config.max_queue_size
        )
        self._pending_requests: Dict[str, asyncio.Future] = {}
        self._dead_letters: List[Tuple[AgentMessage, str]] = []
        
        # NEW: Worker Pool
        self._worker_pool = WorkerPoolManager(self)
        
        # Statistics
        self._stats = {
            "messages_sent": 0,
            "messages_delivered": 0,
            "messages_failed": 0,
            "messages_expired": 0,
            "requests_timeout": 0,
            "agents_registered": 0,
            "batches_processed": 0,  # NEW
            "avg_batch_size": 0.0,   # NEW
        }
        
        self._running = False
        self._start_time: Optional[float] = None
    
    async def start(self):
        """Start broker with worker pool"""
        if self._running:
            return
        
        self._running = True
        self._start_time = asyncio.get_event_loop().time()
        
        # Start worker pool
        await self._worker_pool.start(self.config.num_workers)
        
        logger.info(f"AgentMessageBroker started with {self.config.num_workers} workers")
    
    async def stop(self):
        """Graceful shutdown"""
        if not self._running:
            return
        
        self._running = False
        
        # Stop worker pool
        await self._worker_pool.stop()
        
        # Cancel pending requests
        for future in self._pending_requests.values():
            if not future.done():
                future.cancel()
        
        logger.info("AgentMessageBroker stopped")
    
    # Existing methods (unchanged)...
    # register_agent(), send_message(), send_request(), publish_event(), etc.
    
    def get_stats(self) -> Dict[str, Any]:
        """Enhanced statistics with worker pool info"""
        base_stats = {
            "messages_sent": self._stats["messages_sent"],
            "messages_delivered": self._stats["messages_delivered"],
            "messages_failed": self._stats["messages_failed"],
            "messages_expired": self._stats["messages_expired"],
            "requests_timeout": self._stats["requests_timeout"],
            "agents_registered": self._stats["agents_registered"],
            "batches_processed": self._stats["batches_processed"],
            "avg_batch_size": self._stats["avg_batch_size"],
            "queue_size": self._message_queue.qsize(),
            "queue_utilization": self._message_queue.qsize() / self.config.max_queue_size,
            "pending_requests": len(self._pending_requests),
            "dead_letters": len(self._dead_letters),
        }
        
        # Add worker pool stats
        worker_stats = self._worker_pool.get_stats()
        
        # Calculate uptime
        if self._start_time:
            uptime = asyncio.get_event_loop().time() - self._start_time
            base_stats["broker_uptime_seconds"] = uptime
        
        return {**base_stats, "worker_pool": worker_stats}
```

---

## 📊 Performance-Modellierung

### Theoretische Analyse

**Single-Worker Throughput:**
```
Latency per message: 42.5ms
Throughput = 1000ms / 42.5ms = 23.5 msg/s  ✅ (matches baseline)
```

**Multi-Worker Throughput (5 Workers, No Batching):**
```
Throughput = 23.5 msg/s × 5 workers = 117.5 msg/s
```

**Multi-Worker + Batching (5 Workers, Batch=20):**
```
Batch processing overhead reduction: ~50% (context switching)
Effective latency per message: 42.5ms × 0.5 = 21.25ms

Throughput per worker = 1000ms / 21.25ms = 47 msg/s
Total throughput = 47 msg/s × 5 workers = 235 msg/s
```

**Optimistic Target (5 Workers, Batch=20, Parallel Delivery=10):**
```
Parallel delivery within batch: 10x speedup
Effective latency: 21.25ms / 10 = 2.125ms

Throughput per worker = 1000ms / 2.125ms = 470 msg/s
Total throughput = 470 msg/s × 5 workers = 2350 msg/s  🎯 (exceeds 500+ target)
```

**Realistic Target:**
```
Accounting for coordination overhead, lock contention, etc.
Estimated throughput: 500-1000 msg/s  ✅
```

---

## 🧪 Testing-Strategie

### Performance-Benchmarks

```python
class ThroughputBenchmark:
    """Comprehensive throughput benchmarking"""
    
    async def test_baseline_vs_optimized(self):
        """Compare baseline (1 worker) vs optimized (5 workers)"""
        
        # Test 1: Baseline (1 worker, no batching)
        broker_baseline = AgentMessageBroker(
            config=BrokerConfiguration(num_workers=1, enable_batching=False)
        )
        baseline_throughput = await self.measure_throughput(broker_baseline, 1000)
        
        # Test 2: Multi-worker (5 workers, no batching)
        broker_multi = AgentMessageBroker(
            config=BrokerConfiguration(num_workers=5, enable_batching=False)
        )
        multi_throughput = await self.measure_throughput(broker_multi, 1000)
        
        # Test 3: Multi-worker + Batching (5 workers, batch=20)
        broker_optimized = AgentMessageBroker(
            config=BrokerConfiguration(num_workers=5, enable_batching=True, batch_size=20)
        )
        optimized_throughput = await self.measure_throughput(broker_optimized, 1000)
        
        print(f"Baseline:   {baseline_throughput:.1f} msg/s")
        print(f"Multi:      {multi_throughput:.1f} msg/s ({multi_throughput/baseline_throughput:.1f}x)")
        print(f"Optimized:  {optimized_throughput:.1f} msg/s ({optimized_throughput/baseline_throughput:.1f}x)")
    
    async def measure_throughput(self, broker: AgentMessageBroker, num_messages: int) -> float:
        """Measure messages/sec for given configuration"""
        await broker.start()
        
        # Setup test agents
        agent_a = create_test_agent("agent-a", broker)
        agent_b = create_test_agent("agent-b", broker)
        
        start_time = asyncio.get_event_loop().time()
        
        # Send messages
        for i in range(num_messages):
            await broker.send_message(
                create_request_message(agent_a.identity, agent_b.identity, {"data": i})
            )
        
        # Wait for all deliveries
        while broker._message_queue.qsize() > 0:
            await asyncio.sleep(0.01)
        
        await asyncio.sleep(0.5)  # Buffer for final deliveries
        
        elapsed = asyncio.get_event_loop().time() - start_time
        throughput = num_messages / elapsed
        
        await broker.stop()
        
        return throughput
```

### Test-Scenarios

1. **Throughput-Scaling-Test**
   - 1, 3, 5, 10 workers
   - 1000 messages each
   - Measure linear scaling

2. **Batch-Size-Optimization**
   - Batch sizes: 1, 5, 10, 20, 50, 100
   - Find optimal batch size

3. **Latency-Under-Load**
   - 100-1000 messages/sec load
   - Measure P50, P95, P99 latency

4. **Worker-Failure-Recovery**
   - Simulate worker crashes
   - Measure recovery time
   - Validate no message loss

---

## 📈 Success-Kriterien

### Must-Have

- ✅ **Throughput ≥ 500 msg/s** (1000 messages in ≤ 2 sec)
- ✅ **Avg Latency ≤ 50ms** (keine Verschlechterung)
- ✅ **Success Rate = 100%** (keine Message-Loss)
- ✅ **Backward-Kompatibilität** (alle bestehenden Tests PASS)

### Should-Have

- ✅ **Linear Scaling** (5 workers → 4-5x Throughput)
- ✅ **Worker-Health-Monitoring** (Auto-restart auf Failure)
- ✅ **Konfigurierbar** (num_workers, batch_size via Config)

### Nice-to-Have

- 🔄 **Adaptive Batching** (dynamische Batch-Size basierend auf Load)
- 🔄 **Load-Balancing-Strategies** (Round-Robin, Least-Loaded, Priority-based)

---

## 🔄 Implementation-Roadmap

### Phase 1: Worker-Infrastructure (1h)

1. ✅ BrokerConfiguration Dataclass
2. ✅ MessageWorker Klasse
3. ✅ WorkerPoolManager Klasse
4. ✅ Unit-Tests für Worker-Lifecycle

### Phase 2: Batch-Processing (30min)

1. ✅ `_collect_batch()` Implementierung
2. ✅ `_process_batch()` mit Parallelisierung
3. ✅ Batch-Statistics

### Phase 3: Integration (30min)

1. ✅ AgentMessageBroker erweitern
2. ✅ start()/stop() mit Worker-Pool
3. ✅ Backward-Kompatibilität prüfen

### Phase 4: Testing & Tuning (1h)

1. ✅ Performance-Benchmarks
2. ✅ Latency-Tests
3. ✅ Configuration-Tuning
4. ✅ Integration-Tests re-run

### Phase 5: Documentation (30min)

1. ✅ Implementation-Report
2. ✅ Performance-Comparison
3. ✅ Tuning-Guide

---

## 📚 References

- Phase 4 Implementation Report (Baseline-Performance)
- Python asyncio Documentation
- Message-Queue-Design-Patterns
- Load-Balancing-Strategies

---

**Status:** 🔄 **DESIGN COMPLETE - READY FOR IMPLEMENTATION**

**Next Step:** Implementiere MessageWorker Klasse

