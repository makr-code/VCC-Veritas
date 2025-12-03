"""
VERITAS Agent Communication Protocol - Enhanced Message Broker with Multi-Worker Pattern

Erweiterung des AgentMessageBrokers mit Multi-Worker-Architecture für höheren Durchsatz.

Features:
- Multi-Worker-Pattern (3-5 parallele Worker)
- Message-Batching (10-50 Messages pro Batch)
- Worker-Health-Monitoring mit Auto-Restart
- Konfigurierbare Performance-Parameter
- Backward-Kompatibel mit Single-Worker-Modus

Version: 1.1 (Throughput-Optimierung)
Author: VERITAS Development Team
Date: 6. Oktober 2025
"""

import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class BrokerConfiguration:
    """
    Konfiguration für AgentMessageBroker Performance-Tuning
    
    Attributes:
        num_workers: Anzahl paralleler Message-Worker (1-10)
        enable_batching: Batch-Processing aktivieren
        batch_size: Max Messages pro Batch
        batch_timeout_ms: Max Wartezeit für Batch-Completion (ms)
        max_queue_size: Maximale Queue-Größe
        queue_warning_threshold: Warn bei Queue-Auslastung (0.0-1.0)
        worker_restart_on_failure: Automatischer Worker-Restart bei Fehlern
        worker_health_check_interval_sec: Intervall für Worker-Health-Checks
        delivery_parallelism: Max parallele Deliveries pro Worker
        retry_max_attempts: Max Retry-Versuche bei Delivery-Failures
        retry_backoff_ms: Backoff zwischen Retries (ms)
    
    Example:
        >>> # High-Throughput Configuration
        >>> config = BrokerConfiguration(
        ...     num_workers=5,
        ...     enable_batching=True,
        ...     batch_size=20
        ... )
        >>> broker = AgentMessageBroker(config=config)
    """
    # Worker Pool
    num_workers: int = 5
    enable_batching: bool = True
    worker_restart_on_failure: bool = True
    worker_health_check_interval_sec: float = 30.0
    
    # Message Batching
    batch_size: int = 20  # Messages pro Batch
    batch_timeout_ms: int = 100  # Max wait time
    
    # Queue Settings
    max_queue_size: int = 10000
    queue_warning_threshold: float = 0.8  # Warn at 80% full
    
    # Performance Tuning
    delivery_parallelism: int = 10  # Max parallel deliveries pro Worker
    retry_max_attempts: int = 3
    retry_backoff_ms: int = 100
    
    def __post_init__(self):
        """Validierung"""
        if not 1 <= self.num_workers <= 10:
            raise ValueError("num_workers must be 1-10")
        if not 1 <= self.batch_size <= 100:
            raise ValueError("batch_size must be 1-100")
        if not 10 <= self.batch_timeout_ms <= 1000:
            raise ValueError("batch_timeout_ms must be 10-1000")


class MessageWorker:
    """
    Individual Message-Processing Worker für Multi-Worker-Pattern
    
    Holt Messages aus der Broker-Queue und verarbeitet sie (optional in Batches).
    Kann automatisch neu gestartet werden bei Fehlern.
    
    Attributes:
        worker_id: Eindeutige Worker-ID
        broker: Referenz zum AgentMessageBroker
        messages_processed: Anzahl verarbeiteter Messages
        batches_processed: Anzahl verarbeiteter Batches
        errors: Anzahl aufgetretener Fehler
        is_healthy: Worker-Health-Status
    
    Example:
        >>> worker = MessageWorker(worker_id=0, broker=broker)
        >>> await worker.start()
        >>> # ... worker läuft im Hintergrund ...
        >>> await worker.stop()
    """
    
    def __init__(self, worker_id: int, broker: 'AgentMessageBroker'):
        self.worker_id = worker_id
        self.broker = broker
        self.messages_processed = 0
        self.batches_processed = 0
        self.errors = 0
        self.is_healthy = True
        self._running = False
        self._task: Optional[asyncio.Task] = None
        
        logger.debug(f"Worker-{worker_id} erstellt")
    
    async def start(self):
        """Startet Worker-Task"""
        if self._running:
            logger.warning(f"Worker-{self.worker_id} läuft bereits")
            return
        
        self._running = True
        self._task = asyncio.create_task(self._run())
        logger.info(f"✅ Worker-{self.worker_id} gestartet")
    
    async def stop(self):
        """Graceful Shutdown"""
        if not self._running:
            return
        
        logger.info(f"🛑 Stoppe Worker-{self.worker_id}...")
        self._running = False
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        logger.info(f"✅ Worker-{self.worker_id} gestoppt (Processed: {self.messages_processed}, Errors: {self.errors})")
    
    async def _run(self):
        """Main Worker Loop"""
        logger.debug(f"Worker-{self.worker_id} Loop gestartet")
        
        while self._running:
            try:
                if self.broker.config.enable_batching:
                    # Batch-Modus
                    batch = await self._collect_batch()
                    
                    if batch:
                        await self._process_batch(batch)
                        self.batches_processed += 1
                else:
                    # Single-Message-Modus (für Backward-Kompatibilität)
                    await self._process_single_message()
                    
            except asyncio.CancelledError:
                logger.debug(f"Worker-{self.worker_id} cancelled")
                break
                
            except Exception as e:
                self.errors += 1
                self.is_healthy = False
                logger.error(f"❌ Worker-{self.worker_id} Error: {e}", exc_info=True)
                
                # Auto-Recovery
                if self.broker.config.worker_restart_on_failure:
                    await asyncio.sleep(1.0)  # Backoff
                    self.is_healthy = True
                    logger.info(f"🔄 Worker-{self.worker_id} Auto-Recovery")
                else:
                    break  # Stop worker bei Fehler
        
        logger.debug(f"Worker-{self.worker_id} Loop beendet")
    
    async def _process_single_message(self):
        """Verarbeitet einzelne Message (Non-Batching Mode)"""
        try:
            priority, msg_id, message = await asyncio.wait_for(
                self.broker._message_queue.get(),
                timeout=1.0
            )
            
            await self.broker._deliver_message(message)
            self.messages_processed += 1
            
        except asyncio.TimeoutError:
            # Keine Messages, weiter warten
            pass
    
    async def _collect_batch(self) -> List:
        """
        Sammelt Messages für Batch-Processing
        
        Returns:
            Liste von (priority, msg_id, message) Tuples
        """
        batch = []
        batch_start = asyncio.get_event_loop().time()
        timeout_sec = self.broker.config.batch_timeout_ms / 1000.0
        
        while len(batch) < self.broker.config.batch_size:
            elapsed = asyncio.get_event_loop().time() - batch_start
            remaining = max(0, timeout_sec - elapsed)
            
            # Batch-Timeout erreicht?
            if remaining == 0 and batch:
                break
            
            try:
                # Non-blocking Queue-Get mit Timeout
                item = await asyncio.wait_for(
                    self.broker._message_queue.get(),
                    timeout=remaining if remaining > 0 else 0.1
                )
                batch.append(item)
                
            except asyncio.TimeoutError:
                # Timeout, verarbeite partial batch
                break
        
        return batch
    
    async def _process_batch(self, batch: List):
        """
        Verarbeitet Batch von Messages parallel
        
        Args:
            batch: Liste von (priority, msg_id, message) Tuples
        """
        if not batch:
            return
        
        tasks = []
        messages_in_batch = []
        
        # Tasks erstellen
        for priority, msg_id, message in batch:
            messages_in_batch.append(message)
            task = asyncio.create_task(self.broker._deliver_message(message))
            tasks.append(task)
            
            # Parallelismus begrenzen
            if len(tasks) >= self.broker.config.delivery_parallelism:
                # Warte auf aktuellen Task-Chunk
                await asyncio.gather(*tasks, return_exceptions=True)
                self.messages_processed += len(tasks)
                tasks = []
        
        # Verbleibende Tasks verarbeiten
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
            self.messages_processed += len(tasks)
        
        logger.debug(f"Worker-{self.worker_id} verarbeitete Batch: {len(batch)} Messages")
    
    def get_stats(self) -> Dict[str, Any]:
        """Worker-Statistiken"""
        return {
            "worker_id": self.worker_id,
            "messages_processed": self.messages_processed,
            "batches_processed": self.batches_processed,
            "errors": self.errors,
            "is_healthy": self.is_healthy,
            "is_running": self._running
        }


class WorkerPoolManager:
    """
    Manages Pool of MessageWorkers mit Health-Monitoring
    
    Verwaltet mehrere MessageWorker-Instanzen, überwacht deren Health-Status
    und startet fehlerhafte Worker automatisch neu.
    
    Attributes:
        broker: Referenz zum AgentMessageBroker
        workers: Liste aller aktiven Worker
    
    Example:
        >>> pool = WorkerPoolManager(broker=broker)
        >>> await pool.start(num_workers=5)
        >>> stats = pool.get_stats()
        >>> await pool.stop()
    """
    
    def __init__(self, broker: 'AgentMessageBroker'):
        self.broker = broker
        self.workers: List[MessageWorker] = []
        self._health_check_task: Optional[asyncio.Task] = None
        
        logger.debug("WorkerPoolManager erstellt")
    
    async def start(self, num_workers: int):
        """
        Startet Worker-Pool
        
        Args:
            num_workers: Anzahl zu startender Worker
        """
        logger.info(f"🚀 Starte Worker-Pool mit {num_workers} Workern...")
        
        for i in range(num_workers):
            worker = MessageWorker(worker_id=i, broker=self.broker)
            await worker.start()
            self.workers.append(worker)
        
        # Health-Monitoring starten
        if self.broker.config.worker_restart_on_failure:
            self._health_check_task = asyncio.create_task(self._health_monitor())
        
        logger.info(f"✅ Worker-Pool gestartet ({num_workers} Worker aktiv)")
    
    async def stop(self):
        """Stoppt alle Worker"""
        logger.info("🛑 Stoppe Worker-Pool...")
        
        # Health-Monitor stoppen
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        
        # Alle Worker stoppen
        for worker in self.workers:
            await worker.stop()
        
        self.workers = []
        logger.info("✅ Worker-Pool gestoppt")
    
    async def _health_monitor(self):
        """Überwacht Worker-Health und startet fehlerhafte Worker neu"""
        interval = self.broker.config.worker_health_check_interval_sec
        
        logger.info(f"🏥 Health-Monitor gestartet (Interval: {interval}s)")
        
        while True:
            try:
                await asyncio.sleep(interval)
                
                for i, worker in enumerate(self.workers):
                    if not worker.is_healthy:
                        logger.warning(
                            f"⚠️ Worker-{worker.worker_id} unhealthy "
                            f"(Errors: {worker.errors}), restarting..."
                        )
                        
                        # Worker stoppen
                        await worker.stop()
                        
                        # Neuen Worker erstellen
                        new_worker = MessageWorker(worker.worker_id, self.broker)
                        await new_worker.start()
                        
                        # Ersetzen in Liste
                        self.workers[i] = new_worker
                        
                        logger.info(f"✅ Worker-{worker.worker_id} neu gestartet")
                        
            except asyncio.CancelledError:
                logger.debug("Health-Monitor cancelled")
                break
                
            except Exception as e:
                logger.error(f"❌ Health-Monitor Error: {e}", exc_info=True)
    
    def get_stats(self) -> Dict[str, Any]:
        """Aggregierte Worker-Pool-Statistiken"""
        total_processed = sum(w.messages_processed for w in self.workers)
        total_batches = sum(w.batches_processed for w in self.workers)
        total_errors = sum(w.errors for w in self.workers)
        healthy_workers = sum(1 for w in self.workers if w.is_healthy)
        
        return {
            "total_workers": len(self.workers),
            "healthy_workers": healthy_workers,
            "unhealthy_workers": len(self.workers) - healthy_workers,
            "total_messages_processed": total_processed,
            "total_batches_processed": total_batches,
            "total_worker_errors": total_errors,
            "avg_messages_per_worker": total_processed / len(self.workers) if self.workers else 0,
            "worker_details": [w.get_stats() for w in self.workers]
        }


# Für Backward-Kompatibilität: Default Config
DEFAULT_CONFIG = BrokerConfiguration()
