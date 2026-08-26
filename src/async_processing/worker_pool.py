"""Generic worker pool for parallel task processing."""

from __future__ import annotations

import asyncio
import time
from typing import List, Callable, Any, Dict, Optional, Coroutine
from dataclasses import dataclass

from src.utils.logger import logger


@dataclass
class WorkerResult:
    """Result from worker processing."""
    task_id: str
    status: str  # 'success' or 'error'
    result: Any
    error: Optional[str] = None
    duration: float = 0.0


class WorkerPool:
    """Async worker pool for processing tasks concurrently."""

    def __init__(self, max_workers: int = 5, timeout: Optional[float] = None):
        """Initialize worker pool.
        
        Args:
            max_workers: Maximum concurrent workers
            timeout: Task timeout in seconds
        """
        self.max_workers = max_workers
        self.timeout = timeout
        self.semaphore = asyncio.Semaphore(max_workers)
        self.logger = logger.bind(component="worker_pool")
        self.active_tasks = 0

    async def _execute_task(
        self,
        task_id: str,
        task_func: Callable,
        *args,
        **kwargs
    ) -> WorkerResult:
        """Execute single task with semaphore."""
        async with self.semaphore:
            self.active_tasks += 1
            start = time.time()
            
            try:
                # Execute task (handle both async and sync functions)
                if asyncio.iscoroutinefunction(task_func):
                    result = await asyncio.wait_for(
                        task_func(*args, **kwargs),
                        timeout=self.timeout
                    )
                else:
                    result = await asyncio.wait_for(
                        asyncio.to_thread(task_func, *args, **kwargs),
                        timeout=self.timeout
                    )
                
                duration = time.time() - start
                
                return WorkerResult(
                    task_id=task_id,
                    status="success",
                    result=result,
                    duration=duration
                )
            
            except asyncio.TimeoutError:
                self.logger.warning(f"task_timeout: {task_id}")
                return WorkerResult(
                    task_id=task_id,
                    status="error",
                    result=None,
                    error="Task timeout",
                    duration=time.time() - start
                )
            
            except Exception as e:
                self.logger.error(f"task_error: {task_id}", error=str(e))
                return WorkerResult(
                    task_id=task_id,
                    status="error",
                    result=None,
                    error=str(e),
                    duration=time.time() - start
                )
            
            finally:
                self.active_tasks -= 1

    async def process_tasks(
        self,
        tasks: List[Dict[str, Any]]
    ) -> List[WorkerResult]:
        """Process multiple tasks concurrently.
        
        Args:
            tasks: List of {task_id, task_func, args, kwargs}
            
        Returns:
            List of WorkerResult objects
        """
        self.logger.info(
            "worker_pool_started",
            task_count=len(tasks),
            max_workers=self.max_workers
        )
        
        start = time.time()
        
        # Create tasks
        coroutines = [
            self._execute_task(
                task["task_id"],
                task["task_func"],
                *task.get("args", []),
                **task.get("kwargs", {})
            )
            for task in tasks
        ]
        
        # Execute all tasks
        results = await asyncio.gather(*coroutines)
        
        # Statistics
        successes = [r for r in results if r.status == "success"]
        errors = [r for r in results if r.status == "error"]
        total_duration = time.time() - start
        avg_duration = sum(r.duration for r in results) / len(results) if results else 0
        
        self.logger.info(
            "worker_pool_completed",
            success=len(successes),
            errors=len(errors),
            total_duration=total_duration,
            avg_duration=avg_duration
        )
        
        return results

    def run(
        self,
        tasks: List[Dict[str, Any]]
    ) -> List[WorkerResult]:
        """Synchronous wrapper for async task processing."""
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.process_tasks(tasks))

    def get_status(self) -> Dict[str, Any]:
        """Get worker pool status."""
        return {
            "max_workers": self.max_workers,
            "active_tasks": self.active_tasks,
            "available_slots": self.max_workers - self.active_tasks
        }
