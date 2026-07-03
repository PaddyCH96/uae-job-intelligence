"""Deduplication engine for identifying duplicate job postings."""

from typing import List, Tuple, Optional
from uuid import UUID
import os

from sqlalchemy import and_
from sqlalchemy.orm import Session
from fuzzywuzzy import fuzz

from src.database import get_db_context, FactJobPosting
from src.utils.logger import logger
from src.utils.text import normalize_text


class DeduplicationEngine:
    """Engine for detecting and marking duplicate job postings."""

    def __init__(
        self,
        similarity_threshold: float = 0.85,
        batch_size: int = 1000
    ):
        """
        Initialize deduplication engine.

        Args:
            similarity_threshold: Minimum similarity score (0-1) to mark as duplicate
            batch_size: Number of jobs to process per batch
        """
        self.similarity_threshold = similarity_threshold
        self.batch_size = batch_size
        self.logger = logger.bind(component="deduplication")

    def compute_similarity(
        self,
        job1: FactJobPosting,
        job2: FactJobPosting
    ) -> float:
        """
        Compute similarity score between two job postings.

        Args:
            job1: First job posting
            job2: Second job posting

        Returns:
            Similarity score between 0 and 1
        """
        # First check: exact content hash match
        if job1.content_hash == job2.content_hash:
            return 1.0

        # Title similarity (weighted heavily)
        title_similarity = fuzz.ratio(
            normalize_text(job1.job_title),
            normalize_text(job2.job_title)
        ) / 100.0

        # Company must match exactly (normalized)
        if job1.company_id != job2.company_id:
            return 0.0

        # Location similarity
        location_match = 1.0 if job1.location_id == job2.location_id else 0.5

        # Description similarity (first 500 chars)
        desc1 = normalize_text(job1.job_description or "")[:500]
        desc2 = normalize_text(job2.job_description or "")[:500]
        desc_similarity = fuzz.partial_ratio(desc1, desc2) / 100.0

        # Weighted average
        weights = {
            "title": 0.4,
            "location": 0.2,
            "description": 0.4
        }

        similarity = (
            weights["title"] * title_similarity +
            weights["location"] * location_match +
            weights["description"] * desc_similarity
        )

        return similarity

    def find_duplicate_of(
        self,
        job: FactJobPosting,
        db: Session
    ) -> Optional[UUID]:
        """
        Find if a job posting is a duplicate of an existing one.

        Args:
            job: Job posting to check
            db: Database session

        Returns:
            UUID of original job if duplicate found, None otherwise
        """
        # Find potential duplicates by same company, similar posted date
        potential_duplicates = db.query(FactJobPosting).filter(
            and_(
                FactJobPosting.company_id == job.company_id,
                FactJobPosting.job_posting_id != job.job_posting_id,
                FactJobPosting.is_duplicate == False,
                FactJobPosting.is_active == True,
            )
        ).all()

        best_match = None
        best_similarity = 0.0

        for candidate in potential_duplicates:
            similarity = self.compute_similarity(job, candidate)

            if similarity > best_similarity:
                best_similarity = similarity
                best_match = candidate

        # Mark as duplicate if above threshold
        if best_similarity >= self.similarity_threshold:
            self.logger.info(
                "duplicate_found",
                job_id=str(job.job_posting_id),
                original_id=str(best_match.job_posting_id),
                similarity=best_similarity
            )
            return best_match.job_posting_id

        return None

    def deduplicate_jobs(self, limit: Optional[int] = None) -> Tuple[int, int]:
        """
        Run deduplication on unprocessed jobs.

        Args:
            limit: Maximum number of jobs to check

        Returns:
            Tuple of (checked_count, duplicates_found)
        """
        checked_count = 0
        duplicates_found = 0

        with get_db_context() as db:
            # Get jobs that haven't been checked for duplicates yet
            query = db.query(FactJobPosting).filter(
                FactJobPosting.is_duplicate == False,
                FactJobPosting.is_active == True
            )

            if limit:
                query = query.limit(limit)

            jobs_to_check = query.all()

            self.logger.info("deduplication_started", count=len(jobs_to_check))

            for job in jobs_to_check:
                try:
                    duplicate_of_id = self.find_duplicate_of(job, db)

                    if duplicate_of_id:
                        job.is_duplicate = True
                        job.duplicate_of_id = duplicate_of_id
                        job.is_active = False
                        db.commit()
                        duplicates_found += 1

                    checked_count += 1

                except Exception as e:
                    self.logger.error(
                        "deduplication_error",
                        job_id=str(job.job_posting_id),
                        error=str(e)
                    )
                    db.rollback()

        self.logger.info(
            "deduplication_completed",
            checked=checked_count,
            duplicates=duplicates_found
        )

        return checked_count, duplicates_found

    def get_deduplication_stats(self) -> dict:
        """
        Get deduplication statistics.

        Returns:
            Dictionary with deduplication metrics
        """
        with get_db_context() as db:
            total_jobs = db.query(FactJobPosting).count()
            active_jobs = db.query(FactJobPosting).filter(
                FactJobPosting.is_active == True,
                FactJobPosting.is_duplicate == False
            ).count()
            duplicate_jobs = db.query(FactJobPosting).filter(
                FactJobPosting.is_duplicate == True
            ).count()

            return {
                "total_jobs": total_jobs,
                "active_jobs": active_jobs,
                "duplicate_jobs": duplicate_jobs,
                "deduplication_rate": duplicate_jobs / total_jobs if total_jobs > 0 else 0
            }


def run_deduplication():
    """Run deduplication from command line."""
    threshold = float(os.getenv("DEDUP_SIMILARITY_THRESHOLD", "0.85"))
    batch_size = int(os.getenv("DEDUP_BATCH_SIZE", "1000"))

    engine = DeduplicationEngine(
        similarity_threshold=threshold,
        batch_size=batch_size
    )

    checked, duplicates = engine.deduplicate_jobs()
    stats = engine.get_deduplication_stats()

    logger.info("deduplication_summary", stats=stats)


if __name__ == "__main__":
    run_deduplication()
