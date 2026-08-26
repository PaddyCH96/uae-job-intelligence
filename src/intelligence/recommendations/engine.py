"""Recommendation Engine - Rank jobs based on user profile and job attributes."""

import numpy as np
from datetime import datetime, timedelta
from typing import Optional
from src.utils.logger import logger


class RecommendationEngine:
    """Rank jobs based on user profile and job attributes (free)."""
    
    def __init__(self):
        self.weights = {
            "skills_match": 0.35,
            "salary_fit": 0.25,
            "recency": 0.15,
            "location_fit": 0.15,
            "experience_fit": 0.10
        }
    
    def rank_jobs(self, jobs: list[dict], user_profile: Optional[dict] = None) -> list[dict]:
        """
        Rank jobs by score.
        
        Args:
            jobs: List of job dictionaries
            user_profile: User profile with skills, salary expectations, etc.
            
        Returns:
            Top 10 ranked jobs
        """
        if not user_profile:
            user_profile = self._default_profile()
        
        for job in jobs:
            job["score"] = self._calculate_score(job, user_profile)
        
        # Sort by score descending
        ranked = sorted(jobs, key=lambda x: x["score"], reverse=True)
        
        # Return top 10
        return ranked[:10]
    
    def _calculate_score(self, job: dict, user: dict) -> float:
        """Calculate multi-factor score."""
        scores = {
            "skills_match": self._skills_score(job, user),
            "salary_fit": self._salary_score(job, user),
            "recency": self._recency_score(job),
            "location_fit": self._location_score(job, user),
            "experience_fit": self._experience_score(job, user)
        }
        
        return sum(scores[k] * self.weights[k] for k in scores)
    
    def _skills_score(self, job: dict, user: dict) -> float:
        """Cosine similarity between skill vectors."""
        job_skills = set(job.get("extracted_skills", []))
        user_skills = set(user.get("skills", []))
        
        if not job_skills or not user_skills:
            return 0.0
        
        intersection = job_skills & user_skills
        return len(intersection) / max(len(job_skills), len(user_skills))
    
    def _salary_score(self, job: dict, user: dict) -> float:
        """Score based on salary fit."""
        job_salary = job.get("salary_avg")
        user_min = user.get("expected_salary_min", 0)
        user_max = user.get("expected_salary_max", float('inf'))
        
        if not job_salary or not user_min:
            return 0.5  # Neutral if no salary info
        
        if user_min <= job_salary <= user_max:
            return 1.0  # Perfect fit
        elif job_salary < user_min:
            # Below expectations
            ratio = job_salary / user_min if user_min > 0 else 0
            return max(0.3, ratio)
        else:
            # Above expectations (still good)
            return 0.8
    
    def _recency_score(self, job: dict) -> float:
        """Exponential decay from posting date."""
        posted = job.get("posted_date")
        
        if not posted:
            return 0.5  # Neutral if no date
        
        if isinstance(posted, str):
            try:
                posted = datetime.fromisoformat(posted.replace("Z", "+00:00"))
            except Exception:
                return 0.5
        
        days_old = (datetime.now(posted.tzinfo) - posted).days
        return np.exp(-0.1 * days_old)  # Decay factor
    
    def _location_score(self, job: dict, user: dict) -> float:
        """Score based on location preference."""
        job_location = job.get("location", "").lower()
        preferred_cities = [c.lower() for c in user.get("preferred_cities", [])]
        
        if not preferred_cities:
            return 0.7  # Neutral if no preference
        
        for city in preferred_cities:
            if city in job_location:
                return 1.0
        
        return 0.3
    
    def _experience_score(self, job: dict, user: dict) -> float:
        """Score based on experience level fit."""
        job_level = job.get("experience_level", "").lower()
        user_years = user.get("experience_years", 0)
        
        # Map levels to years
        level_years = {
            "entry": (0, 2),
            "junior": (1, 3),
            "mid": (3, 5),
            "senior": (5, 10),
            "lead": (7, 15),
            "principal": (10, 20)
        }
        
        for level, (min_years, max_years) in level_years.items():
            if level in job_level:
                if min_years <= user_years <= max_years:
                    return 1.0
                elif user_years < min_years:
                    return 0.6
                else:
                    return 0.8
        
        return 0.5  # Neutral if can't determine
    
    def _default_profile(self) -> dict:
        """Default user profile for recommendations."""
        return {
            "skills": ["Python", "SQL", "Data Analysis", "Machine Learning"],
            "experience_years": 3,
            "expected_salary_min": 15000,
            "expected_salary_max": 30000,
            "preferred_cities": ["Dubai", "Abu Dhabi", "UAE"],
            "preferred_industries": ["Technology", "Finance"]
        }
