"""Main ingestion service entry point."""

import sys
from typing import List

from src.ingestion.base import MockSource
from src.ingestion.processor import JobProcessor
from src.database import test_connection
from src.utils.logger import logger


def run_ingestion(source_name: str = "mock", batch_size: int = 50):
    """
    Run the ingestion pipeline.

    Args:
        source_name: Name of data source to ingest from
        batch_size: Number of jobs to process per batch
    """
    logger.info("ingestion_started", source=source_name)

    # Test database connection
    if not test_connection():
        logger.error("database_connection_failed")
        sys.exit(1)

    # Initialize components
    processor = JobProcessor()

    # Get appropriate data source
    if source_name == "mock":
        source = MockSource()
    else:
        logger.error("unknown_source", source=source_name)
        sys.exit(1)

    try:
        # Fetch and transform jobs
        jobs = source.fetch_and_transform(count=batch_size)

        if not jobs:
            logger.warning("no_jobs_fetched")
            return

        # Store raw jobs
        stored_count = processor.store_raw_jobs(jobs)

        # Process and normalize jobs
        processed_count = processor.process_unprocessed_jobs(limit=stored_count)

        logger.info(
            "ingestion_completed",
            fetched=len(jobs),
            stored=stored_count,
            processed=processed_count
        )

    except Exception as e:
        logger.error("ingestion_failed", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    run_ingestion()
