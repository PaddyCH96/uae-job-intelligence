"""Job data processor - handles storage and normalization."""

from typing import List, Dict, Any, Optional
from datetime import datetime, UTC
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from src.database import (
    get_db_context,
    RawJobPosting,
    DimCompany,
    DimLocation,
    DimSource,
    FactJobPosting,
    FactJobPostingSnapshot,
)
from src.utils.logger import logger
from src.utils.text import normalize_text, clean_html, compute_content_hash, extract_salary_range
from src.utils.llm import extract_skills, extract_technologies, check_ollama_health


class JobProcessor:
    """Process and store job postings."""

    def __init__(self):
        """Initialize the processor."""
        self.logger = logger.bind(component="processor")

    def store_raw_jobs(self, jobs: List[Dict[str, Any]]) -> int:
        """
        Store raw job postings in database.

        Args:
            jobs: List of job dictionaries

        Returns:
            Number of jobs stored successfully
        """
        stored_count = 0

        with get_db_context() as db:
            for job in jobs:
                try:
                    raw_job = RawJobPosting(
                        source_id=job["source_id"],
                        source_name=job["source_name"],
                        raw_data=job["raw_data"],
                        ingested_at=datetime.fromisoformat(job["ingested_at"]),
                    )
                    db.add(raw_job)
                    db.commit()
                    stored_count += 1

                except IntegrityError as e:
                    db.rollback()
                    self.logger.warning(
                        "duplicate_raw_job",
                        source_id=job["source_id"],
                        error=str(e)
                    )
                except Exception as e:
                    db.rollback()
                    self.logger.error(
                        "storage_error",
                        source_id=job["source_id"],
                        error=str(e)
                    )

        self.logger.info("raw_jobs_stored", count=stored_count, total=len(jobs))
        return stored_count

    def get_or_create_company(self, db: Session, company_name: str) -> UUID:
        """
        Get existing company or create new one.

        Args:
            db: Database session
            company_name: Company name

        Returns:
            Company UUID
        """
        normalized_name = normalize_text(company_name)

        company = db.query(DimCompany).filter(
            DimCompany.company_name_normalized == normalized_name
        ).first()

        if company:
            return company.company_id

        # Create new company
        company = DimCompany(
            company_name=company_name,
            company_name_normalized=normalized_name
        )
        db.add(company)
        db.flush()

        return company.company_id

    def get_or_create_location(self, db: Session, city: str, country: str = "UAE") -> UUID:
        """
        Get existing location or create new one.

        Args:
            db: Database session
            city: City name
            country: Country name

        Returns:
            Location UUID
        """
        location = db.query(DimLocation).filter(
            DimLocation.city == city,
            DimLocation.country == country
        ).first()

        if location:
            return location.location_id

        # Create new location
        location = DimLocation(
            city=city,
            country=country
        )
        db.add(location)
        db.flush()

        return location.location_id

    def get_or_create_source(self, db: Session, source_name: str, source_type: str = "API") -> UUID:
        """
        Get existing source or create new one.

        Args:
            db: Database session
            source_name: Source name
            source_type: Source type

        Returns:
            Source UUID
        """
        source = db.query(DimSource).filter(
            DimSource.source_name == source_name
        ).first()

        if source:
            return source.source_id

        # Create new source
        source = DimSource(
            source_name=source_name,
            source_type=source_type
        )
        db.add(source)
        db.flush()

        return source.source_id

    def normalize_and_store_job(self, db: Session, raw_job: RawJobPosting) -> Optional[UUID]:
        """
        Normalize raw job and store in fact table.

        Args:
            db: Database session (shared with caller so processed flag persists)
            raw_job: Raw job posting record

        Returns:
            Job posting UUID if successful, None otherwise
        """
        try:
            raw_data = raw_job.raw_data

            # Extract and clean fields
            title = raw_data.get("job_title") or raw_data.get("title", "")
            description = clean_html(raw_data.get("description", ""))
            company_name = raw_data.get("company", "Unknown")
            city = raw_data.get("location", "Dubai")

            # Get or create dimension records
            company_id = self.get_or_create_company(db, company_name)
            location_id = self.get_or_create_location(db, city)
            source_id = self.get_or_create_source(db, raw_job.source_name)

            # Extract salary
            salary_text = raw_data.get("salary_range", "")
            salary_min, salary_max, currency = extract_salary_range(salary_text)

            # Compute content hash for deduplication
            content_for_hash = f"{title}|{company_name}|{description[:500]}"
            content_hash = compute_content_hash(content_for_hash)

            # Skip if duplicate content already stored
            existing = db.query(FactJobPosting).filter(
                FactJobPosting.content_hash == content_hash
            ).first()
            if existing:
                raw_job.processed = True
                db.commit()
                return existing.job_posting_id

            # Create fact record
            job_posting = FactJobPosting(
                raw_job_id=raw_job.id,
                job_title=title,
                job_description=description,
                posted_date=datetime.now(UTC).date(),
                salary_min=salary_min,
                salary_max=salary_max,
                company_id=company_id,
                location_id=location_id,
                source_id=source_id,
                content_hash=content_hash,
                remote_allowed=raw_data.get("remote_allowed", False),
                visa_sponsorship=raw_data.get("visa_sponsorship", False),
            )

            db.add(job_posting)
            db.flush()  # populate job_posting.job_posting_id before snapshot

            snapshot = FactJobPostingSnapshot(
                job_posting_id=job_posting.job_posting_id,
                snapshot_date=datetime.now(UTC).date(),
                status="active",
            )
            db.add(snapshot)

            raw_job.processed = True
            db.commit()

            return job_posting.job_posting_id

        except Exception as e:
            db.rollback()
            self.logger.error(
                "normalization_error",
                raw_job_id=str(raw_job.id),
                error=str(e)
            )

            raw_job.processed = True
            raw_job.processing_errors = str(e)
            db.commit()

            return None

    def process_unprocessed_jobs(self, limit: int = 100) -> int:
        """
        Process unprocessed raw jobs.

        Args:
            limit: Maximum number of jobs to process

        Returns:
            Number of jobs processed successfully
        """
        processed_count = 0

        with get_db_context() as db:
            unprocessed_jobs = db.query(RawJobPosting).filter(
                RawJobPosting.processed == False
            ).limit(limit).all()

            self.logger.info("processing_jobs", count=len(unprocessed_jobs))

            for raw_job in unprocessed_jobs:
                job_id = self.normalize_and_store_job(db, raw_job)
                if job_id:
                    processed_count += 1

        self.logger.info("processing_completed", success=processed_count, total=len(unprocessed_jobs))
        return processed_count

    def enrich_job_with_llm(self, db: Session, job: FactJobPosting) -> bool:
        """
        Enrich a job posting with LLM-extracted skills and technologies.

        Args:
            db: Database session
            job: FactJobPosting instance

        Returns:
            True if enrichment successful, False otherwise
        """
        if not check_ollama_health():
            self.logger.warning("ollama_not_available")
            return False

        description = job.job_description or ""
        if not description:
            return False

        try:
            # Extract skills
            skills = extract_skills(description)
            job.extracted_skills = skills

            # Extract technologies
            technologies = extract_technologies(description)
            job.extracted_technologies = technologies

            job.updated_at = datetime.utcnow()
            db.commit()

            self.logger.info(
                "job_enriched",
                job_id=str(job.job_posting_id),
                skills_count=len(skills),
                tech_count=len(technologies),
            )
            return True

        except Exception as e:
            db.rollback()
            self.logger.error(
                "enrichment_failed",
                job_id=str(job.job_posting_id),
                error=str(e),
            )
            return False

    def enrich_unprocessed_jobs(self, limit: int = 50) -> int:
        """
        Enrich jobs that don't have extracted skills/technologies.

        Args:
            limit: Maximum number of jobs to enrich

        Returns:
            Number of jobs enriched successfully
        """
        enriched_count = 0

        with get_db_context() as db:
            unenriched_jobs = (
                db.query(FactJobPosting)
                .filter(
                    FactJobPosting.extracted_skills.is_(None),
                    FactJobPosting.is_active == True,
                )
                .limit(limit)
                .all()
            )

            self.logger.info("enriching_jobs", count=len(unenriched_jobs))

            for job in unenriched_jobs:
                success = self.enrich_job_with_llm(db, job)
                if success:
                    enriched_count += 1

        self.logger.info("enrichment_completed", success=enriched_count, total=len(unenriched_jobs))
        return enriched_count
