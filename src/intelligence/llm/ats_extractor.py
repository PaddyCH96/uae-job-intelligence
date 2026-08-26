"""ATS Keyword Extractor - Extract ATS-friendly keywords from job descriptions."""

import json
import re
from typing import Optional
from src.utils.logger import logger


ATS_KEYWORDS_PROMPT = """
Extract ATS-optimization keywords from this job description.
Return JSON with:
- hard_skills: Exact technical skills mentioned (e.g., "Python", "SQL", "TensorFlow")
- soft_skills: Behavioral attributes (e.g., "leadership", "communication")
- action_verbs: Strong verbs used (e.g., "architected", "deployed", "optimized")
- certifications: Required/preferred certs (e.g., "AWS Solutions Architect", "PMP")
- industry_terms: Domain-specific jargon (e.g., "MLOps", "ETL pipelines")
- keywords_by_category: Organized by technical, behavioral, tools

Job Title: {title}
Company: {company}
Description: {description}
"""


class ATSKeywordExtractor:
    """Extract ATS-friendly keywords using LLM."""
    
    def __init__(self):
        self.llm_client = None
        self._init_llm()
    
    def _init_llm(self):
        """Initialize LLM client."""
        try:
            from src.utils.llm import LLMClient
            self.llm_client = LLMClient()
        except Exception as e:
            logger.warning(f"Failed to initialize LLM client: {e}")
    
    async def extract(self, job: dict) -> dict:
        """
        Extract keywords from job description.
        
        Args:
            job: Job dictionary with title, company_name, description
            
        Returns:
            Dictionary with ATS keywords
        """
        if not self.llm_client:
            return self._fallback_extraction(job.get("description", ""))
        
        try:
            prompt = ATS_KEYWORDS_PROMPT.format(
                title=job.get("title", ""),
                company=job.get("company_name", ""),
                description=job.get("description", "")[:2000]  # Limit length
            )
            
            response = await self.llm_client.generate(prompt)
            
            # Parse JSON response
            keywords = self._parse_json_response(response)
            
            logger.info(f"Extracted {len(keywords.get('hard_skills', []))} hard skills for {job.get('title', 'Unknown')}")
            return keywords
            
        except Exception as e:
            logger.warning(f"LLM extraction failed, using fallback: {e}")
            return self._fallback_extraction(job.get("description", ""))
    
    def _parse_json_response(self, response: str) -> dict:
        """Parse JSON response from LLM."""
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
        
        # Default structure
        return {
            "hard_skills": [],
            "soft_skills": [],
            "action_verbs": [],
            "certifications": [],
            "industry_terms": [],
            "keywords_by_category": {}
        }
    
    def _fallback_extraction(self, description: str) -> dict:
        """Fallback extraction using regex patterns."""
        if not description:
            return self._empty_keywords()
        
        # Common technical skills
        tech_skills = [
            "Python", "SQL", "Java", "JavaScript", "TypeScript", "C++", "C#",
            "TensorFlow", "PyTorch", "Scikit-learn", "Pandas", "NumPy",
            "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Git",
            "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch",
            "Spark", "Hadoop", "Airflow", "Prefect", "dbt",
            "Tableau", "Power BI", "Looker", "Excel",
            "Machine Learning", "Deep Learning", "NLP", "Computer Vision",
            "Data Engineering", "Data Analysis", "ETL", "ELT",
            "REST API", "GraphQL", "Microservices", "CI/CD"
        ]
        
        # Common soft skills
        soft_skills = [
            "leadership", "communication", "collaboration", "problem-solving",
            "analytical", "critical thinking", "team player", "self-motivated",
            "attention to detail", "time management", "adaptability"
        ]
        
        # Common action verbs
        action_verbs = [
            "architected", "deployed", "implemented", "optimized", "designed",
            "developed", "built", "created", "maintained", "improved",
            "led", "managed", "coordinated", "mentored", "trained"
        ]
        
        found_skills = []
        found_soft = []
        found_verbs = []
        
        desc_lower = description.lower()
        
        # Find technical skills
        for skill in tech_skills:
            if skill.lower() in desc_lower:
                found_skills.append(skill)
        
        # Find soft skills
        for skill in soft_skills:
            if skill.lower() in desc_lower:
                found_soft.append(skill)
        
        # Find action verbs
        for verb in action_verbs:
            if verb.lower() in desc_lower:
                found_verbs.append(verb)
        
        return {
            "hard_skills": found_skills[:10],  # Limit to top 10
            "soft_skills": found_soft[:5],
            "action_verbs": found_verbs[:5],
            "certifications": [],
            "industry_terms": [],
            "keywords_by_category": {
                "technical": found_skills[:5],
                "behavioral": found_soft[:3]
            }
        }
    
    def _empty_keywords(self) -> dict:
        """Return empty keywords structure."""
        return {
            "hard_skills": [],
            "soft_skills": [],
            "action_verbs": [],
            "certifications": [],
            "industry_terms": [],
            "keywords_by_category": {}
        }


class SpacyKeywordExtractor:
    """NLP-based keyword extraction as LLM fallback (free)."""
    
    def __init__(self):
        self.nlp = None
        self._init_spacy()
    
    def _init_spacy(self):
        """Initialize spaCy model."""
        try:
            import spacy
            self.nlp = spacy.load("en_core_web_sm")
        except Exception as e:
            logger.warning(f"Failed to load spaCy model: {e}")
    
    def extract(self, text: str) -> dict:
        """
        Extract keywords using NLP.
        
        Args:
            text: Job description text
            
        Returns:
            Dictionary with extracted keywords
        """
        if not self.nlp or not text:
            return self._simple_extraction(text)
        
        try:
            doc = self.nlp(text)
            
            # Named entities (skills, tools)
            entities = [ent.text for ent in doc.ents if ent.label_ in ["ORG", "PRODUCT", "TECH"]]
            
            # Noun phrases (potential skills)
            noun_phrases = [chunk.text for chunk in doc.noun_chunks]
            
            return {
                "hard_skills": list(set(entities))[:10],
                "soft_skills": noun_phrases[:5],
                "action_verbs": [],
                "certifications": [],
                "industry_terms": [],
                "keywords_by_category": {
                    "technical": entities[:5],
                    "tools": noun_phrases[:3]
                }
            }
            
        except Exception as e:
            logger.warning(f"spaCy extraction failed: {e}")
            return self._simple_extraction(text)
    
    def _simple_extraction(self, text: str) -> dict:
        """Simple keyword extraction without NLP."""
        if not text:
            return {"hard_skills": [], "soft_skills": [], "action_verbs": []}
        
        # Basic word frequency
        words = re.findall(r'\b\w+\b', text.lower())
        word_freq = {}
        for word in words:
            if len(word) > 3:  # Skip short words
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Get most common words
        common_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:20]
        
        return {
            "hard_skills": [w for w, _ in common_words[:10]],
            "soft_skills": [],
            "action_verbs": [],
            "certifications": [],
            "industry_terms": [],
            "keywords_by_category": {}
        }
