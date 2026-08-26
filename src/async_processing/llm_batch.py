"""Async batch processing for LLM requests with concurrency control."""

from __future__ import annotations

import asyncio
import time
from typing import List, Callable, Any, Dict, Optional
from dataclasses import dataclass

from src.utils.logger import logger
from src.utils.llm import extract_skills, extract_technologies
from src.metrics import get_metrics, track_llm_request


@dataclass
class LLMBatchResult:
    """Result from batch LLM processing."""
    success_count: int
    error_count: int
    total_duration: float
    results: List[Dict[str, Any]]
    errors: List[Dict[str, Any]]


class AsyncLLMBatcher:
    """Async batch processor for LLM requests with concurrency control."""

    def __init__(
        self,
        max_concurrent: int = 3,
        batch_size: int = 10,
        rate_limit_delay: float = 0.5
    ):
        """Initialize async LLM batcher.
        
        Args:
            max_concurrent: Maximum concurrent LLM requests
            batch_size: Jobs per batch
            rate_limit_delay: Delay between requests (seconds)
        """
        self.max_concurrent = max_concurrent
        self.batch_size = batch_size
        self.rate_limit_delay = rate_limit_delay
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.logger = logger.bind(component="async_llm_batcher")

    async def _process_with_semaphore(
        self,
        job_id: str,
        description: str,
        task_type: str
    ) -> Dict[str, Any]:
        """Process single job with semaphore for concurrency control."""
        async with self.semaphore:
            try:
                await asyncio.sleep(self.rate_limit_delay)  # Rate limiting
                
                start = time.time()
                
                if task_type == "skills":
                    result = extract_skills(description)
                    extraction_type = "skills"
                elif task_type == "technologies":
                    result = extract_technologies(description)
                    extraction_type = "technologies"
                else:
                    raise ValueError(f"Unknown task type: {task_type}")
                
                duration = time.time() - start
                
                get_metrics().record_llm_request(
                    model="qwen2.5-coder:7b",
                    task_type=extraction_type,
                    duration=duration,
                    status="success"
                )
                get_metrics().jobs_enriched_total.labels(
                    enrichment_type=extraction_type
                ).inc()
                
                return {
                    "job_id": job_id,
                    "status": "success",
                    "result": result,
                    "duration": duration
                }
            
            except Exception as e:
                self.logger.error(
                    "batch_processing_error",
                    job_id=job_id,
                    error=str(e)
                )
                get_metrics().record_llm_request(
                    model="qwen2.5-coder:7b",
                    task_type=task_type,
                    duration=0,
                    status="error"
                )
                return {
                    "job_id": job_id,
                    "status": "error",
                    "error": str(e)
                }

    async def process_batch(
        self,
        jobs: List[Dict[str, str]],
        task_type: str = "skills"
    ) -> LLMBatchResult:
        """Process batch of jobs concurrently.
        
        Args:
            jobs: List of {job_id, description} dicts
            task_type: Type of extraction (skills, technologies)
            
        Returns:
            LLMBatchResult with results and statistics
        """
        start_time = time.time()
        
        self.logger.info(
            "batch_processing_started",
            job_count=len(jobs),
            task_type=task_type,
            max_concurrent=self.max_concurrent
        )
        
        # Create tasks
        tasks = [
            self._process_with_semaphore(
                job["job_id"],
                job["description"],
                task_type
            )
            for job in jobs
        ]
        
        # Process all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=False)
        
        # Separate successes and errors
        successes = [r for r in results if r["status"] == "success"]
        errors = [r for r in results if r["status"] == "error"]
        
        total_duration = time.time() - start_time
        
        batch_result = LLMBatchResult(
            success_count=len(successes),
            error_count=len(errors),
            total_duration=total_duration,
            results=successes,
            errors=errors
        )
        
        self.logger.info(
            "batch_processing_completed",
            success=len(successes),
            errors=len(errors),
            duration=total_duration,
            throughput=len(jobs) / total_duration if total_duration > 0 else 0
        )
        
        return batch_result

    async def process_batches(
        self,
        all_jobs: List[Dict[str, str]],
        task_type: str = "skills"
    ) -> LLMBatchResult:
        """Process jobs in multiple batches.
        
        Args:
            all_jobs: All jobs to process
            task_type: Type of extraction
            
        Returns:
            Combined results from all batches
        """
        all_successes = []
        all_errors = []
        total_duration = 0
        
        # Process in batches
        for i in range(0, len(all_jobs), self.batch_size):
            batch = all_jobs[i:i + self.batch_size]
            result = await self.process_batch(batch, task_type)
            
            all_successes.extend(result.results)
            all_errors.extend(result.errors)
            total_duration += result.total_duration
        
        return LLMBatchResult(
            success_count=len(all_successes),
            error_count=len(all_errors),
            total_duration=total_duration,
            results=all_successes,
            errors=all_errors
        )

    def run(
        self,
        jobs: List[Dict[str, str]],
        task_type: str = "skills"
    ) -> LLMBatchResult:
        """Synchronous wrapper for async processing.
        
        Args:
            jobs: Jobs to process
            task_type: Type of extraction
            
        Returns:
            Batch processing results
        """
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.process_batches(jobs, task_type))
