"""
VQB Frontend - Async Worker Service

Manages background tasks using threading and queues for non-blocking UI.
"""

import threading
import logging
from queue import Queue, Empty
from typing import Callable, Optional, Any, Dict
from dataclasses import dataclass
from abc import ABC, abstractmethod
import uuid

logger = logging.getLogger(__name__)


@dataclass
class TaskResult:
    """Result of an async task"""
    task_id: str
    success: bool
    result: Any = None
    error: Optional[str] = None


class Task(ABC):
    """
    Abstract base class for async tasks
    
    Subclass this to create specific tasks.
    """
    
    def __init__(self, task_id: Optional[str] = None):
        """
        Initialize task
        
        Args:
            task_id: Optional task ID (auto-generated if not provided)
        """
        self.task_id = task_id or str(uuid.uuid4())
        self.callback: Optional[Callable] = None
    
    @abstractmethod
    def execute(self) -> Any:
        """
        Execute the task (runs in worker thread)
        
        Returns:
            Task result
        """
        pass


class AsyncWorker:
    """
    Manages asynchronous tasks in background threads
    
    Features:
    - Thread pool for concurrent task execution
    - Task queue with FIFO ordering
    - Result queue for callbacks
    - Error handling and logging
    
    Usage:
        worker = AsyncWorker(num_threads=4)
        worker.submit_task(my_task, callback=on_complete)
        # In main thread, periodically call:
        worker.process_results()
    """
    
    def __init__(self, num_threads: int = 4):
        """
        Initialize async worker
        
        Args:
            num_threads: Number of worker threads to create
        """
        self.num_threads = num_threads
        self.task_queue: Queue = Queue()
        self.result_queue: Queue = Queue()
        self.threads: list[threading.Thread] = []
        self.running = True
        
        # Start worker threads
        self._start_workers()
        
        logger.info(f"AsyncWorker initialized with {num_threads} threads")
    
    def _start_workers(self):
        """Start worker threads"""
        for i in range(self.num_threads):
            thread = threading.Thread(
                target=self._worker,
                name=f"AsyncWorker-{i}",
                daemon=True
            )
            thread.start()
            self.threads.append(thread)
    
    def _worker(self):
        """
        Worker thread loop
        
        Continuously processes tasks from the queue.
        """
        thread_name = threading.current_thread().name
        logger.debug(f"{thread_name} started")
        
        while self.running:
            try:
                # Get task from queue (blocking with timeout)
                task = self.task_queue.get(timeout=1.0)
                
                logger.debug(f"{thread_name} executing task {task.task_id}")
                
                try:
                    # Execute task
                    result = task.execute()
                    
                    # Put success result in result queue
                    task_result = TaskResult(
                        task_id=task.task_id,
                        success=True,
                        result=result
                    )
                    self.result_queue.put((task, task_result))
                    
                    logger.debug(f"{thread_name} task {task.task_id} completed successfully")
                    
                except Exception as e:
                    # Put error result in result queue
                    logger.error(f"{thread_name} task {task.task_id} failed: {e}", exc_info=True)
                    
                    task_result = TaskResult(
                        task_id=task.task_id,
                        success=False,
                        error=str(e)
                    )
                    self.result_queue.put((task, task_result))
                
                finally:
                    self.task_queue.task_done()
                    
            except Empty:
                # No task available, continue loop
                continue
            except Exception as e:
                logger.error(f"{thread_name} unexpected error: {e}", exc_info=True)
        
        logger.debug(f"{thread_name} stopped")
    
    def submit_task(self, task: Task, callback: Optional[Callable] = None):
        """
        Submit a task for async execution
        
        Args:
            task: Task to execute
            callback: Optional callback function (called with TaskResult)
        """
        task.callback = callback
        self.task_queue.put(task)
        logger.debug(f"Task {task.task_id} submitted")
    
    def process_results(self):
        """
        Process results from result queue
        
        This should be called periodically from the main thread
        to handle task results and execute callbacks.
        """
        processed = 0
        
        while not self.result_queue.empty():
            try:
                task, result = self.result_queue.get_nowait()
                
                # Call callback if present
                if task.callback:
                    try:
                        task.callback(result)
                    except Exception as e:
                        logger.error(f"Error in callback for task {task.task_id}: {e}", exc_info=True)
                
                processed += 1
                
            except Empty:
                break
            except Exception as e:
                logger.error(f"Error processing result: {e}", exc_info=True)
        
        if processed > 0:
            logger.debug(f"Processed {processed} task results")
        
        return processed
    
    def shutdown(self):
        """Shutdown worker threads gracefully"""
        logger.info("Shutting down AsyncWorker...")
        self.running = False
        
        # Wait for threads to finish
        for thread in self.threads:
            thread.join(timeout=2.0)
        
        logger.info("AsyncWorker shut down")
    
    def get_pending_count(self) -> int:
        """Get number of pending tasks"""
        return self.task_queue.qsize()
    
    def get_result_count(self) -> int:
        """Get number of pending results"""
        return self.result_queue.qsize()


# Singleton instance
_worker_instance: Optional[AsyncWorker] = None


def get_async_worker(num_threads: int = 4) -> AsyncWorker:
    """
    Get singleton AsyncWorker instance
    
    Args:
        num_threads: Number of threads (only used on first call)
    
    Returns:
        AsyncWorker instance
    """
    global _worker_instance
    
    if _worker_instance is None:
        _worker_instance = AsyncWorker(num_threads=num_threads)
    
    return _worker_instance
