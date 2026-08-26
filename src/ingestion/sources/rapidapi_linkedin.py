"""RapidAPI LinkedIn Scraper - Zero Cost Job Scraping."""

import os
import httpx
from typing import Optional
from datetime import datetime
from src.utils.logger import logger


class RapidAPILinkedInScraper:
    """Scrape LinkedIn jobs via RapidAPI free tier."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("RAPIDAPI_KEY")
        self.base_url = "https://linkedin-data-api.p.rapidapi.com"
        self.headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": "linkedin-data-api.p.rapidapi.com"
        }
    
    async def search_jobs(
        self, 
        keywords: str = "data engineer",
        location: str = "Dubai, United Arab Emirates",
        limit: int = 25
    ) -> list[dict]:
        """
        Search LinkedIn jobs via RapidAPI.
        
        Args:
            keywords: Job search keywords
            location: Job location
            limit: Maximum number of jobs to return
            
        Returns:
            List of job dictionaries
        """
        if not self.api_key:
            logger.warning("RAPIDAPI_KEY not set, skipping RapidAPI scrape")
            return []
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/search-jobs",
                    headers=self.headers,
                    params={
                        "keywords": keywords,
                        "location": location,
                        "limit": min(limit, 25)  # Free tier limit
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    jobs = data.get("jobs", [])
                    logger.info(f"RapidAPI: Found {len(jobs)} jobs for '{keywords}' in {location}")
                    return self._normalize_jobs(jobs)
                else:
                    logger.error(f"RapidAPI error: {response.status_code} - {response.text}")
                    return []
                    
        except Exception as e:
            logger.error(f"RapidAPI scrape failed: {e}")
            return []
    
    def _normalize_jobs(self, jobs: list[dict]) -> list[dict]:
        """Normalize RapidAPI job data to standard format."""
        normalized = []
        
        for job in jobs:
            try:
                normalized_job = {
                    "title": job.get("title", ""),
                    "company_name": job.get("companyName", ""),
                    "company_id": job.get("companyId", ""),
                    "location": job.get("location", ""),
                    "description": job.get("description", ""),
                    "url": job.get("url", ""),
                    "posted_date": self._parse_date(job.get("listedAt")),
                    "salary_min": self._extract_salary(job.get("salary", "")),
                    "salary_max": None,
                    "employment_type": job.get("employmentType", ""),
                    "experience_level": job.get("seniorityLevel", ""),
                    "remote_allowed": job.get("remoteAllowed", False),
                    "source": "rapidapi_linkedin",
                    "raw_data": job
                }
                normalized.append(normalized_job)
            except Exception as e:
                logger.warning(f"Failed to normalize job: {e}")
                continue
        
        return normalized
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string to datetime."""
        if not date_str:
            return None
        
        try:
            # Try ISO format
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except Exception:
            try:
                # Try timestamp
                return datetime.fromtimestamp(int(date_str))
            except Exception:
                return None
    
    def _extract_salary(self, salary_str: str) -> Optional[float]:
        """Extract salary from string."""
        if not salary_str:
            return None
        
        try:
            # Remove non-numeric characters except dots
            import re
            numbers = re.findall(r'[\d,]+\.?\d*', salary_str.replace(",", ""))
            if numbers:
                return float(numbers[0])
        except Exception:
            pass
        
        return None


class ScraperRotator:
    """Rotate between multiple free API providers."""
    
    def __init__(self):
        self.providers = [
            RapidAPILinkedInScraper(),
        ]
        self.current_provider = 0
    
    async def scrape_next_batch(
        self, 
        keywords: list[str],
        location: str = "Dubai, United Arab Emirates"
    ) -> list[dict]:
        """
        Scrape using next available provider.
        
        Args:
            keywords: List of search keywords
            location: Job location
            
        Returns:
            List of normalized jobs
        """
        all_jobs = []
        
        for keyword in keywords:
            provider = self.providers[self.current_provider % len(self.providers)]
            
            try:
                jobs = await provider.search_jobs(
                    keywords=keyword,
                    location=location,
                    limit=25
                )
                all_jobs.extend(jobs)
                
                # Rotate to next provider after each keyword
                self.current_provider += 1
                
            except Exception as e:
                logger.error(f"Provider {self.current_provider} failed for '{keyword}': {e}")
                # Try next provider
                self.current_provider += 1
                continue
        
        # Deduplicate by title + company
        seen = set()
        unique_jobs = []
        
        for job in all_jobs:
            key = f"{job['title']}_{job['company_name']}"
            if key not in seen:
                seen.add(key)
                unique_jobs.append(job)
        
        logger.info(f"ScraperRotator: {len(unique_jobs)} unique jobs from {len(keywords)} keywords")
        return unique_jobs
