"""Prefect flows for scheduled UAE jobs ingestion."""

from prefect import flow, task
from src.utils.logger import logger
from src.database import test_connection
from src.ingestion.processor import JobProcessor


@task(retries=3, retry_delay_seconds=60, name="ingest-source")
def ingest_source(source_name: str, max_pages: int = 3) -> dict:
    """
    Prefect task that ingests a single source.

    Imports are done lazily inside the task so that missing source
    modules don't crash at module load time.

    Args:
        source_name: One of bayt | gulftalent | naukrigulf | mock
        max_pages: Maximum pages to fetch

    Returns:
        Dict with keys fetched, stored, processed (and optionally error/skipped)
    """
    logger.info("task_started", source=source_name, max_pages=max_pages)

    if not test_connection():
        raise RuntimeError("Database connection failed — cannot ingest source")

    processor = JobProcessor()

    # Import source classes (lazy to tolerate missing optional deps)
    try:
        if source_name == "bayt":
            from src.ingestion.sources.bayt import BaytSource as BaytSource
            source = BaytSource()
        elif source_name == "gulftalent":
            from src.ingestion.sources.gulftalent import GulfTalentSource
            source = GulfTalentSource()
        elif source_name == "naukrigulf":
            from src.ingestion.sources.naukrigulf import NaukriGulfSource
            source = NaukriGulfSource()
        elif source_name == "mock":
            from src.ingestion.base import MockSource
            source = MockSource()
        else:
            raise ValueError(f"Unknown source: {source_name}")
    except ImportError as exc:
        logger.warning("source_module_missing", source=source_name, error=str(exc))
        return {"fetched": 0, "stored": 0, "processed": 0, "skipped": True}

    jobs = source.fetch_and_transform(max_pages=max_pages)

    if not jobs:
        logger.warning("no_jobs_fetched", source=source_name)
        return {"fetched": 0, "stored": 0, "processed": 0}

    stored_count = processor.store_raw_jobs(jobs)
    processed_count = processor.process_unprocessed_jobs(limit=stored_count)

    result = {
        "fetched": len(jobs),
        "stored": stored_count,
        "processed": processed_count,
    }
    logger.info("task_completed", source=source_name, **result)
    return result


@flow(name="uae-jobs-daily-ingestion", log_prints=True)
def daily_ingestion_flow(
    sources: list = ["bayt", "gulftalent", "naukrigulf"],
    max_pages: int = 3,
) -> dict:
    """
    Daily ingestion flow — runs each configured source as a separate Prefect task.

    Args:
        sources: List of source names to run. Defaults to all three real scrapers.
        max_pages: Maximum pages to fetch per source.

    Returns:
        Summary dict mapping source name to {fetched, stored, processed}.
    """
    print(f"Starting daily ingestion for sources: {sources} (max_pages={max_pages})")

    summary = {}
    for source_name in sources:
        print(f"Submitting task for source: {source_name}")
        result = ingest_source(source_name=source_name, max_pages=max_pages)
        summary[source_name] = result
        print(f"Source {source_name} done: {result}")

    total_fetched = sum(v.get("fetched", 0) for v in summary.values())
    total_stored = sum(v.get("stored", 0) for v in summary.values())
    total_processed = sum(v.get("processed", 0) for v in summary.values())
    print(
        f"Daily ingestion complete — "
        f"fetched={total_fetched}, stored={total_stored}, processed={total_processed}"
    )

    return summary


if __name__ == "__main__":
    daily_ingestion_flow()
