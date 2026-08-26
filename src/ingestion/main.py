"""Main ingestion service entry point."""

import sys
import argparse
from typing import List, Optional

from src.ingestion.base import MockSource
from src.ingestion.processor import JobProcessor
from src.database import test_connection
from src.utils.logger import logger

# Lazy imports for scrapers that may not exist yet
try:
    from src.ingestion.sources.bayt import BaytSource
    _BAYT_AVAILABLE = True
except ImportError:
    _BAYT_AVAILABLE = False

try:
    from src.ingestion.sources.gulftalent import GulfTalentSource
    _GULFTALENT_AVAILABLE = True
except ImportError:
    _GULFTALENT_AVAILABLE = False

try:
    from src.ingestion.sources.naukrigulf import NaukriGulfSource
    _NAUKRIGULF_AVAILABLE = True
except ImportError:
    _NAUKRIGULF_AVAILABLE = False

try:
    from src.ingestion.sources.rapidapi_linkedin import RapidAPILinkedInScraper
    _RAPIDAPI_AVAILABLE = True
except ImportError:
    _RAPIDAPI_AVAILABLE = False


def _make_source(name: str):
    """Instantiate a source by name. Returns None if source is unavailable."""
    if name == "mock":
        return MockSource()
    if name == "bayt":
        if not _BAYT_AVAILABLE:
            logger.warning("bayt_source_unavailable", reason="module not found")
            return None
        return BaytSource()
    if name == "gulftalent":
        if not _GULFTALENT_AVAILABLE:
            logger.warning("gulftalent_source_unavailable", reason="module not found")
            return None
        return GulfTalentSource()
    if name == "naukrigulf":
        if not _NAUKRIGULF_AVAILABLE:
            logger.warning("naukrigulf_source_unavailable", reason="module not found")
            return None
        return NaukriGulfSource()
    if name == "rapidapi":
        if not _RAPIDAPI_AVAILABLE:
            logger.warning("rapidapi_source_unavailable", reason="module not found")
            return None
        return RapidAPILinkedInScraper()
    return None


AVAILABLE_SOURCES = {
    "mock": lambda: MockSource(),
    "bayt": lambda: _make_source("bayt"),
    "gulftalent": lambda: _make_source("gulftalent"),
    "naukrigulf": lambda: _make_source("naukrigulf"),
    "rapidapi": lambda: _make_source("rapidapi"),
    "all": None,  # special: run all real sources
}

REAL_SOURCES = ["bayt", "gulftalent", "naukrigulf", "rapidapi"]


def run_ingestion(
    source_name: str = "mock",
    max_pages: int = 3,
    batch_size: int = 50,
) -> dict:
    """
    Run the ingestion pipeline for one or all sources.

    Args:
        source_name: Name of data source to ingest from, or "all" for all real sources
        max_pages: Maximum number of pages to fetch per source (for paginated scrapers)
        batch_size: Number of jobs to process per batch (used for MockSource)

    Returns:
        Summary dict mapping source name to {fetched, stored, processed}
    """
    logger.info("ingestion_started", source=source_name)

    # Test database connection
    if not test_connection():
        logger.error("database_connection_failed")
        sys.exit(1)

    processor = JobProcessor()

    # Determine which sources to run
    if source_name == "all":
        sources_to_run = REAL_SOURCES
    elif source_name in AVAILABLE_SOURCES:
        sources_to_run = [source_name]
    else:
        logger.error("unknown_source", source=source_name)
        sys.exit(1)

    summary = {}

    for src_name in sources_to_run:
        logger.info("source_starting", source=src_name)

        source = _make_source(src_name)
        if source is None:
            logger.warning("source_skipped", source=src_name)
            summary[src_name] = {"fetched": 0, "stored": 0, "processed": 0, "skipped": True}
            continue

        try:
            # MockSource uses count=batch_size; real scrapers use max_pages
            if src_name == "mock":
                jobs = source.fetch_and_transform(count=batch_size)
            else:
                jobs = source.fetch_and_transform(max_pages=max_pages)

            if not jobs:
                logger.warning("no_jobs_fetched", source=src_name)
                summary[src_name] = {"fetched": 0, "stored": 0, "processed": 0}
                continue

            stored_count = processor.store_raw_jobs(jobs)
            processed_count = processor.process_unprocessed_jobs(limit=stored_count)

            logger.info(
                "source_completed",
                source=src_name,
                fetched=len(jobs),
                stored=stored_count,
                processed=processed_count,
            )
            summary[src_name] = {
                "fetched": len(jobs),
                "stored": stored_count,
                "processed": processed_count,
            }

        except Exception as e:
            logger.error("source_failed", source=src_name, error=str(e))
            summary[src_name] = {"fetched": 0, "stored": 0, "processed": 0, "error": str(e)}

    logger.info("ingestion_completed", summary=summary)
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UAE Jobs Ingestion Pipeline")
    parser.add_argument(
        "--source",
        default="mock",
        choices=list(AVAILABLE_SOURCES.keys()),
        help="Data source to ingest from (default: mock)",
    )
    parser.add_argument(
        "--pages",
        type=int,
        default=3,
        help="Maximum pages to fetch per source (default: 3)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="Batch size for MockSource (default: 50)",
    )
    args = parser.parse_args()
    run_ingestion(source_name=args.source, max_pages=args.pages, batch_size=args.batch_size)
