"""Base classes for data ingestion sources."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime, UTC
import hashlib

from src.utils.logger import logger


class BaseSource(ABC):
    """Abstract base class for all data sources."""

    def __init__(self, source_name: str, source_type: str = "API"):
        """
        Initialize the data source.

        Args:
            source_name: Name of the data source
            source_type: Type of source (API, Scraper, etc.)
        """
        self.source_name = source_name
        self.source_type = source_type
        self.logger = logger.bind(source=source_name)

    @abstractmethod
    def fetch_jobs(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Fetch job postings from the source.

        Args:
            **kwargs: Source-specific parameters

        Returns:
            List of job posting dictionaries

        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError("Subclasses must implement fetch_jobs()")

    def transform_job(self, raw_job: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform raw job data into standardized format.

        Args:
            raw_job: Raw job data from source

        Returns:
            Standardized job dictionary with common fields
        """
        # Default implementation - can be overridden
        return {
            "source_id": self._generate_source_id(raw_job),
            "source_name": self.source_name,
            "raw_data": raw_job,
            "ingested_at": datetime.now(UTC).isoformat(),
        }

    def _generate_source_id(self, raw_job: Dict[str, Any]) -> str:
        """
        Generate unique source ID for a job posting.

        Args:
            raw_job: Raw job data

        Returns:
            Unique identifier string
        """
        # Create hash from key fields to generate consistent ID
        id_string = f"{self.source_name}_{raw_job.get('id', '')}_{raw_job.get('url', '')}"
        return hashlib.md5(id_string.encode()).hexdigest()

    def validate_job(self, job: Dict[str, Any]) -> bool:
        """
        Validate job data meets minimum requirements.

        Args:
            job: Job dictionary

        Returns:
            True if valid, False otherwise
        """
        required_fields = ["source_id", "source_name", "raw_data"]

        for field in required_fields:
            if field not in job or not job[field]:
                self.logger.warning(
                    "validation_failed",
                    field=field,
                    job_id=job.get("source_id")
                )
                return False

        # Check raw_data has minimum content
        raw_data = job.get("raw_data", {})
        if not raw_data.get("title") and not raw_data.get("job_title"):
            self.logger.warning(
                "validation_failed",
                reason="missing_title",
                job_id=job.get("source_id")
            )
            return False

        return True

    def fetch_and_transform(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Fetch jobs from source and transform them to standard format.

        Args:
            **kwargs: Source-specific fetch parameters

        Returns:
            List of transformed job dictionaries
        """
        self.logger.info("fetch_started", source=self.source_name)

        try:
            # Fetch raw jobs
            raw_jobs = self.fetch_jobs(**kwargs)
            self.logger.info("fetch_completed", count=len(raw_jobs))

            # Transform and validate
            transformed_jobs = []
            for raw_job in raw_jobs:
                try:
                    transformed = self.transform_job(raw_job)
                    if self.validate_job(transformed):
                        transformed_jobs.append(transformed)
                except Exception as e:
                    self.logger.error(
                        "transformation_error",
                        error=str(e),
                        job=raw_job
                    )
                    continue

            self.logger.info(
                "transformation_completed",
                total=len(raw_jobs),
                valid=len(transformed_jobs),
                invalid=len(raw_jobs) - len(transformed_jobs)
            )

            return transformed_jobs

        except Exception as e:
            self.logger.error("fetch_error", error=str(e))
            raise


class MockSource(BaseSource):
    """Mock data source for testing and development."""

    def __init__(self):
        super().__init__(source_name="MockJobBoard", source_type="Mock")

    def fetch_jobs(self, count: int = 10) -> List[Dict[str, Any]]:
        """
        Generate mock job postings.

        Args:
            count: Number of mock jobs to generate

        Returns:
            List of mock job dictionaries
        """
        mock_jobs = []

        companies = ["Emirates Group", "ADNOC", "Etisalat", "DP World", "Majid Al Futtaim"]
        cities = ["Dubai", "Abu Dhabi", "Sharjah"]
        titles = [
            "Data Analyst",
            "Data Engineer",
            "BI Analyst",
            "Analytics Engineer",
            "ML Engineer",
            "AI Engineer"
        ]

        for i in range(count):
            job = {
                "id": f"mock_{i+1}",
                "job_title": titles[i % len(titles)],
                "company": companies[i % len(companies)],
                "location": cities[i % len(cities)],
                "description": f"We are looking for an experienced {titles[i % len(titles)]} to join our team. "
                              f"Requirements: Python, SQL, Data Analysis. Salary: AED 15,000 - 25,000.",
                "posted_date": datetime.now(UTC).isoformat(),
                "salary_range": "AED 15,000 - 25,000",
                "employment_type": "Full-time",
                "experience_level": "Mid Level",
                "remote_allowed": i % 3 == 0,
                "url": f"https://mockjobboard.com/job/{i+1}"
            }
            mock_jobs.append(job)

        return mock_jobs
