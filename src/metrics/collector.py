"""Prometheus metrics collector for monitoring platform performance."""

from __future__ import annotations

from typing import Optional, Dict, Any
import time
from contextlib import contextmanager
from functools import wraps

try:
    from prometheus_client import Counter, Histogram, Gauge, Info
except ImportError:
    # Graceful fallback if prometheus_client not installed
    class Counter:
        def __init__(self, *args, **kwargs): pass
        def inc(self, *args, **kwargs): pass
        def labels(self, *args, **kwargs): return self
    
    class Histogram:
        def __init__(self, *args, **kwargs): pass
        def observe(self, *args): pass
        def time(self, *args): pass
        def labels(self, *args, **kwargs): return self
    
    class Gauge:
        def __init__(self, *args, **kwargs): pass
        def set(self, *args): pass
        def inc(self, *args): pass
        def dec(self, *args): pass
        def labels(self, *args, **kwargs): return self
    
    class Info:
        def __init__(self, *args, **kwargs): pass
        def info(self, *args, **kwargs): pass

from src.utils.logger import logger


class MetricsCollector:
    """Collects and exposes Prometheus metrics."""

    def __init__(self):
        """Initialize metrics collector with all tracked metrics."""
        # HTTP Metrics
        self.http_requests_total = Counter(
            'http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status']
        )
        self.http_request_duration = Histogram(
            'http_request_duration_seconds',
            'HTTP request duration',
            ['method', 'endpoint'],
            buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0)
        )
        self.http_request_size = Histogram(
            'http_request_size_bytes',
            'HTTP request size',
            ['method', 'endpoint']
        )
        self.http_response_size = Histogram(
            'http_response_size_bytes',
            'HTTP response size',
            ['method', 'endpoint']
        )

        # Database Metrics
        self.db_query_duration = Histogram(
            'db_query_duration_seconds',
            'Database query duration',
            ['query_type', 'table'],
            buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 5.0)
        )
        self.db_queries_total = Counter(
            'db_queries_total',
            'Total database queries',
            ['query_type', 'status']
        )
        self.db_connection_pool = Gauge(
            'db_connection_pool_size',
            'Database connection pool size'
        )
        self.db_connection_active = Gauge(
            'db_connection_active',
            'Active database connections'
        )

        # Cache Metrics
        self.cache_hits_total = Counter(
            'cache_hits_total',
            'Total cache hits',
            ['cache_key']
        )
        self.cache_misses_total = Counter(
            'cache_misses_total',
            'Total cache misses',
            ['cache_key']
        )
        self.cache_evictions_total = Counter(
            'cache_evictions_total',
            'Total cache evictions',
            ['cache_key']
        )

        # LLM Metrics
        self.llm_requests_total = Counter(
            'llm_requests_total',
            'Total LLM requests',
            ['model', 'task_type', 'status']
        )
        self.llm_request_duration = Histogram(
            'llm_request_duration_seconds',
            'LLM request duration',
            ['model', 'task_type'],
            buckets=(1.0, 5.0, 10.0, 30.0, 60.0)
        )
        self.llm_tokens_used = Counter(
            'llm_tokens_used_total',
            'Total LLM tokens used',
            ['model', 'token_type']
        )

        # Job Processing Metrics
        self.jobs_ingested_total = Counter(
            'jobs_ingested_total',
            'Total jobs ingested',
            ['source']
        )
        self.jobs_deduplicated_total = Counter(
            'jobs_deduplicated_total',
            'Total jobs marked as duplicate'
        )
        self.jobs_enriched_total = Counter(
            'jobs_enriched_total',
            'Total jobs enriched with LLM',
            ['enrichment_type']
        )
        self.ingestion_duration = Histogram(
            'ingestion_duration_seconds',
            'Job ingestion duration',
            ['source']
        )

        # Model Metrics
        self.model_predictions_total = Counter(
            'model_predictions_total',
            'Total model predictions',
            ['model_name', 'prediction_type']
        )
        self.model_accuracy = Gauge(
            'model_accuracy',
            'Model accuracy score',
            ['model_name']
        )
        self.model_inference_duration = Histogram(
            'model_inference_duration_seconds',
            'Model inference duration',
            ['model_name']
        )

        # System Metrics
        self.app_info = Info(
            'uae_jobs_app',
            'UAE Job Intelligence Platform'
        )
        self.jobs_in_database = Gauge(
            'jobs_in_database_total',
            'Total jobs in database'
        )
        self.companies_in_database = Gauge(
            'companies_in_database_total',
            'Total unique companies'
        )

        logger.info("metrics_collector_initialized")

    def record_http_request(
        self,
        method: str,
        endpoint: str,
        status_code: int,
        duration: float,
        request_size: int = 0,
        response_size: int = 0
    ) -> None:
        """Record HTTP request metrics."""
        try:
            self.http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status=status_code
            ).inc()
            self.http_request_duration.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
            if request_size > 0:
                self.http_request_size.labels(
                    method=method,
                    endpoint=endpoint
                ).observe(request_size)
            if response_size > 0:
                self.http_response_size.labels(
                    method=method,
                    endpoint=endpoint
                ).observe(response_size)
        except Exception as e:
            logger.warning(f"failed_to_record_http_metrics: {str(e)}")

    def record_db_query(
        self,
        query_type: str,
        table: str,
        duration: float,
        status: str = "success"
    ) -> None:
        """Record database query metrics."""
        try:
            self.db_query_duration.labels(
                query_type=query_type,
                table=table
            ).observe(duration)
            self.db_queries_total.labels(
                query_type=query_type,
                status=status
            ).inc()
        except Exception as e:
            logger.warning(f"failed_to_record_db_metrics: {str(e)}")

    def record_llm_request(
        self,
        model: str,
        task_type: str,
        duration: float,
        status: str = "success",
        tokens_used: int = 0
    ) -> None:
        """Record LLM request metrics."""
        try:
            self.llm_requests_total.labels(
                model=model,
                task_type=task_type,
                status=status
            ).inc()
            self.llm_request_duration.labels(
                model=model,
                task_type=task_type
            ).observe(duration)
            if tokens_used > 0:
                self.llm_tokens_used.labels(
                    model=model,
                    token_type="total"
                ).inc(tokens_used)
        except Exception as e:
            logger.warning(f"failed_to_record_llm_metrics: {str(e)}")

    def record_job_ingestion(
        self,
        source: str,
        count: int,
        duration: float
    ) -> None:
        """Record job ingestion metrics."""
        try:
            self.jobs_ingested_total.labels(source=source).inc(count)
            self.ingestion_duration.labels(source=source).observe(duration)
        except Exception as e:
            logger.warning(f"failed_to_record_ingestion_metrics: {str(e)}")

    def set_database_stats(self, total_jobs: int, total_companies: int) -> None:
        """Update database statistics."""
        try:
            self.jobs_in_database.set(total_jobs)
            self.companies_in_database.set(total_companies)
        except Exception as e:
            logger.warning(f"failed_to_update_db_stats: {str(e)}")

    @contextmanager
    def track_duration(self, metric_name: str, labels: Dict[str, str]):
        """Context manager for tracking operation duration."""
        start = time.time()
        try:
            yield
        finally:
            duration = time.time() - start
            logger.debug(f"operation_completed", metric=metric_name, duration=duration)


# Global metrics instance
_metrics_instance: Optional[MetricsCollector] = None


def get_metrics() -> MetricsCollector:
    """Get or create global metrics collector instance."""
    global _metrics_instance
    if _metrics_instance is None:
        _metrics_instance = MetricsCollector()
    return _metrics_instance


def track_request(method: str, endpoint: str):
    """Decorator for tracking HTTP request metrics."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                status = getattr(result, 'status_code', 200)
                duration = time.time() - start
                get_metrics().record_http_request(method, endpoint, status, duration)
                return result
            except Exception as e:
                duration = time.time() - start
                get_metrics().record_http_request(method, endpoint, 500, duration)
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                status = getattr(result, 'status_code', 200)
                duration = time.time() - start
                get_metrics().record_http_request(method, endpoint, status, duration)
                return result
            except Exception as e:
                duration = time.time() - start
                get_metrics().record_http_request(method, endpoint, 500, duration)
                raise
        
        return async_wrapper if hasattr(func, '__await__') else sync_wrapper
    return decorator


def track_db_query(query_type: str, table: str):
    """Decorator for tracking database query metrics."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start
                get_metrics().record_db_query(query_type, table, duration, "success")
                return result
            except Exception as e:
                duration = time.time() - start
                get_metrics().record_db_query(query_type, table, duration, "error")
                raise
        return wrapper
    return decorator


def track_llm_request(model: str, task_type: str):
    """Decorator for tracking LLM request metrics."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start
                get_metrics().record_llm_request(model, task_type, duration, "success")
                return result
            except Exception as e:
                duration = time.time() - start
                get_metrics().record_llm_request(model, task_type, duration, "error")
                raise
        return wrapper
    return decorator
