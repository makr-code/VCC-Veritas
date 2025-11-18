"""
Simple async persistence queue for mirroring ingestion writes to Themis.

Usage:
    from backend.utils.persistence_queue import PersistenceQueue

    queue = PersistenceQueue(persistence_adapter)
    queue.start()
    await queue.enqueue(collection, document, key)

The worker retries with backoff and logs failures. If no persistence_adapter
is available at start, items are retained in an in-memory queue until adapter
becomes available (or process restarts).
"""
import asyncio
import logging
import threading
import time
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class PersistenceQueue:
    def __init__(self, persistence_adapter: Optional[Any] = None):
        self._adapter = persistence_adapter
        self._queue: "asyncio.Queue[Dict]" = asyncio.Queue()
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        # Config via env
        import os

        self._retry_count = int(os.getenv("THEMIS_PERSISTENCE_RETRY_COUNT", "5"))
        self._retry_backoff = float(os.getenv("THEMIS_PERSISTENCE_RETRY_BACKOFF", "2"))
        self._policy = os.getenv("THEMIS_PERSISTENCE_FAIL_POLICY", "queue").lower()

    def set_persistence_adapter(self, adapter: Any) -> None:
        """Attach or replace the persistence adapter at runtime."""
        self._adapter = adapter

    async def enqueue(self, collection: str, document: Dict[str, Any], key: Optional[str] = None) -> None:
        """Enqueue a persistence task."""
        payload = {"collection": collection, "document": document, "key": key, "ts": time.time()}
        await self._queue.put(payload)
        logger.debug("🔁 Enqueued persistence task for collection=%s key=%s", collection, key)

    def start(self) -> None:
        """Start background worker thread with its own event loop."""
        if self._thread and self._thread.is_alive():
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop_in_thread, daemon=True)
        self._thread.start()
        logger.info("🔁 PersistenceQueue worker started")

    def stop(self) -> None:
        """Stop the background worker and close the event loop."""
        self._stop_event.set()
        if self._loop:
            # schedule loop stop
            try:
                self._loop.call_soon_threadsafe(self._loop.stop)
            except Exception:
                pass
        if self._thread:
            self._thread.join(timeout=3)
        logger.info("🔁 PersistenceQueue worker stopped")

    def _run_loop_in_thread(self) -> None:
        """Create an event loop and run the worker coroutine until stopped."""
        self._loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(self._loop)
            self._loop.run_until_complete(self._worker())
        finally:
            try:
                self._loop.close()
            except Exception:
                pass

    async def _worker(self) -> None:
        """Continuously process queued persistence tasks."""
        while not self._stop_event.is_set():
            try:
                task = await asyncio.wait_for(self._queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                # allow stop checks
                await asyncio.sleep(0)
                continue

            if not task:
                continue

            collection = task.get("collection")
            document = task.get("document")
            key = task.get("key")

            # If no adapter available, re-enqueue or sleep based on policy
            if not self._adapter:
                logger.warning("⚠️ No persistence adapter available, keeping task in queue (policy=%s)", self._policy)
                # If policy==queue keep it in queue; re-insert and sleep
                if self._policy == "queue":
                    # requeue with small delay
                    await asyncio.sleep(2)
                    await self._queue.put(task)
                    continue
                elif self._policy == "block":
                    await asyncio.sleep(5)
                    await self._queue.put(task)
                    continue
                else:
                    # fallback: drop after warning
                    logger.error("❌ Dropping persistence task because no adapter and unknown policy=%s", self._policy)
                    continue

            # Try to persist with retries
            success = False
            for attempt in range(1, self._retry_count + 1):
                try:
                    # Adapter may provide async insert_document
                    insert = getattr(self._adapter, "insert_document", None)
                    if insert is None:
                        raise RuntimeError("Persistence adapter does not implement insert_document")

                    if asyncio.iscoroutinefunction(insert):
                        await insert(collection, document, key)
                    else:
                        # run sync function in threadpool
                        loop = asyncio.get_event_loop()
                        await loop.run_in_executor(None, insert, collection, document, key)

                    logger.info("✅ Persisted document to %s key=%s (attempt=%d)", collection, key, attempt)
                    success = True
                    break
                except Exception as e:
                    logger.warning("⚠️ Persistence attempt %d failed for %s:%s -> %s", attempt, collection, key, e)
                    await asyncio.sleep(self._retry_backoff * attempt)

            if not success:
                logger.error("❌ Failed to persist document to %s key=%s after %d attempts", collection, key, self._retry_count)
                # policy: if queue, re-enqueue; if block, sleep then re-enqueue; else drop
                if self._policy == "queue":
                    await asyncio.sleep(1)
                    await self._queue.put(task)
                elif self._policy == "block":
                    await asyncio.sleep(5)
                    await self._queue.put(task)
                else:
                    logger.error("❌ Dropping failed persistence task (policy=%s)", self._policy)

            # mark task done
            try:
                self._queue.task_done()
            except Exception:
                pass

        logger.info("🔁 PersistenceQueue worker exiting")
