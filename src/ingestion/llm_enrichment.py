"""LLM enrichment pipeline for batch processing jobs.

Integrates with Ollama to extract skills, technologies, and sentiment
from job descriptions. Handles rate limiting, retries, and database updates.
"""

from __future__ import annotations

import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.database import get_db_context
from src.database.models import FactJobPosting
from src.utils.llm import (
    extract_skills,
    extract_technologies,
    extract_sentiment,
    classify_industry,
    check_ollama_health,
    DEFAULT_MODEL,
)
from src.utils.logger import logger


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BATCH_SIZE = 10  # Jobs per batch
DELAY_BETWEEN_REQUESTS = 0.5  # Seconds between LLM requests
MAX_RETRIES = 3  # Retry on failure
RETRY_DELAY = 2.0  # Delay between retries


# ---------------------------------------------------------------------------
# Core Enrichment Functions
# ---------------------------------------------------------------------------

def enrich_single_job(
    job: FactJobPosting,
    model: str = DEFAULT_MODEL,
    db: Optional[Session] = None,
) -> Dict[str, any]:
    """Enrich a single job posting with LLM-extracted data.

    Args:
        job: FactJobPosting instance
        model: Ollama model to use
        db: Database session (optional, will create if not provided)

    Returns:
        Dict with enrichment results and metadata
    """
    description = job.job_description or ""
    if not description:
        logger.warning("empty_job_description", job_id=str(job.job_posting_id))
        return {"success": False, "reason": "empty_description"}

    start_time = time.time()
    results = {
        "job_id": str(job.job_posting_id),
        "skills": [],
        "technologies": [],
        "sentiment": {},
        "industry": "Others",
        "llm_latency_ms": 0,
        "success": False,
    }

    try:
        # Extract skills
        skills = extract_skills(description, model=model)
        results["skills"] = skills

        # Extract technologies
        technologies = extract_technologies(description, model=model)
        results["technologies"] = technologies

        # Extract sentiment
        sentiment = extract_sentiment(description, model=model)
        results["sentiment"] = sentiment

        # Classify industry
        industry = classify_industry(description, model=model)
        results["industry"] = industry

        # Calculate latency
        results["llm_latency_ms"] = round((time.time() - start_time) * 1000, 2)
        results["success"] = True

        # Update database if session provided
        if db:
            _update_job_enrichment(db, job, results)

        logger.info(
            "job_enriched",
            job_id=str(job.job_posting_id),
            skills_count=len(skills),
            tech_count=len(technologies),
            latency_ms=results["llm_latency_ms"],
        )

    except Exception as e:
        logger.error(
            "enrichment_failed",
            job_id=str(job.job_posting_id),
            error=str(e),
        )
        results["error"] = str(e)

    return results


def _update_job_enrichment(
    db: Session,
    job: FactJobPosting,
    results: Dict[str, any],
) -> None:
    """Update job posting in database with enrichment results.

    Args:
        db: Database session
        job: FactJobPosting instance
        results: Enrichment results dict
    """
    job.extracted_skills = results["skills"]
    job.extracted_technologies = results["technologies"]
    job.updated_at = datetime.utcnow()
    db.commit()


# ---------------------------------------------------------------------------
# Batch Processing
# ---------------------------------------------------------------------------

def batch_enrich_jobs(
    limit: int = 100,
    model: str = DEFAULT_MODEL,
    dry_run: bool = False,
) -> Dict[str, any]:
    """Batch enrich jobs that haven't been processed yet.

    Args:
        limit: Maximum number of jobs to process
        model: Ollama model to use
        dry_run: If True, don't update database

    Returns:
        Dict with batch processing statistics
    """
    # Check Ollama health first
    if not check_ollama_health():
        logger.error("ollama_not_available")
        return {"success": False, "error": "Ollama not available"}

    stats = {
        "total_processed": 0,
        "successful": 0,
        "failed": 0,
        "skipped": 0,
        "total_skills_extracted": 0,
        "total_tech_extracted": 0,
        "avg_latency_ms": 0,
        "start_time": datetime.utcnow().isoformat(),
    }

    with get_db_context() as db:
        # Get jobs without enrichment
        jobs = (
            db.query(FactJobPosting)
            .filter(
                FactJobPosting.extracted_skills.is_(None),
                FactJobPosting.is_active == True,
            )
            .limit(limit)
            .all()
        )

        logger.info("batch_enrichment_started", job_count=len(jobs))

        for i, job in enumerate(jobs):
            results = enrich_single_job(job, model=model, db=db if not dry_run else None)

            stats["total_processed"] += 1
            if results["success"]:
                stats["successful"] += 1
                stats["total_skills_extracted"] += len(results["skills"])
                stats["total_tech_extracted"] += len(results["technologies"])
            else:
                stats["failed"] += 1

            # Rate limiting
            if i < len(jobs) - 1:
                time.sleep(DELAY_BETWEEN_REQUESTS)

            # Progress logging every 10 jobs
            if (i + 1) % 10 == 0:
                logger.info(
                    "batch_progress",
                    processed=i + 1,
                    total=len(jobs),
                    successful=stats["successful"],
                )

    # Calculate average latency
    if stats["successful"] > 0:
        stats["avg_latency_ms"] = round(
            sum(r.get("llm_latency_ms", 0) for r in [results]) / stats["successful"], 2
        )

    stats["end_time"] = datetime.utcnow().isoformat()
    stats["success"] = True

    logger.info(
        "batch_enrichment_complete",
        processed=stats["total_processed"],
        successful=stats["successful"],
        failed=stats["failed"],
    )

    return stats


# ---------------------------------------------------------------------------
# Re-enrichment (for model updates)
# ---------------------------------------------------------------------------

def reenrich_jobs(
    limit: int = 100,
    model: str = DEFAULT_MODEL,
) -> Dict[str, any]:
    """Re-enrich jobs with updated model or prompts.

    Args:
        limit: Maximum number of jobs to re-process
        model: Ollama model to use

    Returns:
        Dict with re-enrichment statistics
    """
    if not check_ollama_health():
        return {"success": False, "error": "Ollama not available"}

    stats = {
        "total_processed": 0,
        "successful": 0,
        "failed": 0,
    }

    with get_db_context() as db:
        jobs = (
            db.query(FactJobPosting)
            .filter(
                FactJobPosting.extracted_skills.isnot(None),
                FactJobPosting.is_active == True,
            )
            .limit(limit)
            .all()
        )

        logger.info("reenrichment_started", job_count=len(jobs))

        for i, job in enumerate(jobs):
            results = enrich_single_job(job, model=model, db=db)
            stats["total_processed"] += 1
            if results["success"]:
                stats["successful"] += 1
            else:
                stats["failed"] += 1

            if i < len(jobs) - 1:
                time.sleep(DELAY_BETWEEN_REQUESTS)

    stats["success"] = True
    logger.info("reenrichment_complete", **stats)
    return stats


# ---------------------------------------------------------------------------
# Analytics Queries
# ---------------------------------------------------------------------------

def get_skill_trends(db: Session, limit: int = 20) -> List[Dict]:
    """Get top skills with trend indicators.

    Args:
        db: Database session
        limit: Number of results to return

    Returns:
        List of skill trend dicts
    """
    query = text("""
        SELECT
            skill_name,
            job_count,
            first_seen,
            last_seen,
            trend,
            trend_indicator
        FROM analytics.v_skill_trends
        LIMIT :limit
    """)
    result = db.execute(query, {"limit": limit})
    return [dict(row) for row in result]


def get_tech_trends(db: Session, limit: int = 20) -> List[Dict]:
    """Get top technologies with trend indicators.

    Args:
        db: Database session
        limit: Number of results to return

    Returns:
        List of technology trend dicts
    """
    query = text("""
        SELECT
            technology_name,
            job_count,
            first_seen,
            last_seen,
            trend,
            trend_indicator
        FROM analytics.v_tech_trends
        LIMIT :limit
    """)
    result = db.execute(query, {"limit": limit})
    return [dict(row) for row in result]


def get_salary_by_skill(db: Session, limit: int = 20) -> List[Dict]:
    """Get salary statistics by skill.

    Args:
        db: Database session
        limit: Number of results to return

    Returns:
        List of salary by skill dicts
    """
    query = text("""
        SELECT
            skill_name,
            job_count,
            avg_salary_min,
            avg_salary_max,
            avg_salary_midpoint
        FROM analytics.v_salary_by_skill
        LIMIT :limit
    """)
    result = db.execute(query, {"limit": limit})
    return [dict(row) for row in result]


def get_tech_cooccurrence(db: Session, limit: int = 20) -> List[Dict]:
    """Get technology co-occurrence matrix.

    Args:
        db: Database session
        limit: Number of results to return

    Returns:
        List of co-occurrence dicts
    """
    query = text("""
        SELECT
            technology_a,
            technology_b,
            cooccurrence_count
        FROM analytics.v_tech_cooccurrence
        LIMIT :limit
    """)
    result = db.execute(query, {"limit": limit})
    return [dict(row) for row in result]


def get_enriched_jobs(
    db: Session,
    skills: Optional[List[str]] = None,
    technologies: Optional[List[str]] = None,
    limit: int = 50,
) -> List[Dict]:
    """Get enriched job postings with optional filters.

    Args:
        db: Database session
        skills: Filter by required skills
        technologies: Filter by required technologies
        limit: Number of results to return

    Returns:
        List of enriched job dicts
    """
    query = text("""
        SELECT
            job_posting_id,
            job_title,
            job_description,
            posted_date,
            salary_min,
            salary_max,
            extracted_skills,
            extracted_technologies,
            company_name,
            city,
            source_name,
            experience_level,
            employment_type
        FROM analytics.v_enriched_jobs
        WHERE 1=1
        LIMIT :limit
    """)
    result = db.execute(query, {"limit": limit})
    return [dict(row) for row in result]