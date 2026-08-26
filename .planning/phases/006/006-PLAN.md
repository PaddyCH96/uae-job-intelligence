# Phase 6: Automated Job Intelligence & Career Assistant (ZERO COST)

## Overview

Transform the UAE Job Intelligence Platform from a passive analytics tool into an **active career assistant** that automatically scrapes jobs daily, ranks the top 10 opportunities, provides ATS-friendly keywords for each listing, and enriches contacts for hiring managers.

**Duration:** 2-3 weeks  
**Priority:** High  
**Dependencies:** Phase 1-5 Complete  
**Monthly Cost:** $0 (completely free)

---

## Zero-Cost Architecture

| Component | Solution | Cost |
|-----------|----------|------|
| **Job Scraping** | RapidAPI free tier (Fantastic Jobs) + TheirStack + Lix rotated | $0 |
| **Contact Enrichment** | DIY pattern detection + website scraping | $0 |
| **Scheduling** | System cron + APScheduler (Python) | $0 |
| **ATS Keywords** | Ollama + Qwen (local LLM) | $0 |
| **Recommendations** | Local computation | $0 |
| **Database** | PostgreSQL (local Docker) | $0 |

---

## Success Criteria

| Metric | Target | Measurement |
|--------|--------|-------------|
| Daily scrape completion | 100% success rate | Cron logs |
| Jobs scraped per day | ≥ 25 new jobs | Database count |
| Top 10 recommendations | Generated daily by 7 AM UAE time | Dashboard display |
| ATS keywords extracted | ≥ 90% of job listings | `ats_keywords IS NOT NULL` |
| Contact enrichment | ≥ 20% of companies have contacts | `company_contacts` table |
| Dashboard refresh | Real-time updates | < 5 second latency |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    DAILY AUTOMATION FLOW                         │
│                                                                 │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│  │ 6 AM     │───▶│ Scrape   │───▶│ Enrich   │───▶│ Rank     │  │
│  │ Cron     │    │ Jobs     │    │ Contacts │    │ Top 10   │  │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘  │
│       │              │               │               │          │
│       ▼              ▼               ▼               ▼          │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│  │ APSched  │    │ RapidAPI │    │ DIY      │    │ Local    │  │
│  │ + Cron   │    │ + Web    │    │ Pattern  │    │ Compute  │  │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Task Breakdown

### Wave 1: Infrastructure & Scheduling (Days 1-3)

#### Task 1.1: Create RapidAPI LinkedIn Scraper
**Files:** `src/ingestion/sources/rapidapi_linkedin.py`

```python
import httpx
from typing import Optional

class RapidAPILinkedInScraper:
    """Scrape LinkedIn jobs via RapidAPI free tier."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://linkedin-data-api.p.rapidapi.com"
        self.headers = {
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": "linkedin-data-api.p.rapidapi.com"
        }
    
    async def search_jobs(
        self, 
        keywords: str = "data engineer",
        location: str = "Dubai, UAE",
        limit: int = 25
    ) -> list[dict]:
        """Search LinkedIn jobs via RapidAPI."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/search-jobs",
                headers=self.headers,
                params={
                    "keywords": keywords,
                    "location": location,
                    "limit": limit
                }
            )
            return response.json().get("jobs", [])
```

**Free Tier Limits:**
- Fantastic Jobs API: 250 jobs/month, 25 requests/month
- Workaround: Rotate keywords, cache aggressively

**Acceptance Criteria:**
- [ ] Connects to RapidAPI LinkedIn endpoint
- [ ] Extracts: title, company, salary, description, requirements
- [ ] Handles pagination
- [ ] Respects rate limits

---

#### Task 1.2: Create Multi-Source Scraper Rotator
**Files:** `src/ingestion/sources/scraper_rotator.py`

```python
class ScraperRotator:
    """Rotate between free API providers to maximize quota."""
    
    def __init__(self):
        self.providers = [
            RapidAPILinkedInScraper(),  # 250/mo
            TheirStackScraper(),        # 200 credits/7 days
            LixScraper(),               # 1000 exports/mo
        ]
        self.current_provider = 0
    
    async def scrape_next_batch(self, keywords: list[str]) -> list[dict]:
        """Scrape using next available provider."""
        provider = self.providers[self.current_provider]
        
        try:
            jobs = await provider.search_jobs(keywords)
            return jobs
        except RateLimitError:
            # Rotate to next provider
            self.current_provider = (self.current_provider + 1) % len(self.providers)
            return await self.scrape_next_batch(keywords)
```

**Acceptance Criteria:**
- [ ] Rotates between 3+ free providers
- [ ] Handles rate limits gracefully
- [ ] Maximizes monthly job quota

---

#### Task 1.3: Set Up System Cron for Scheduling
**Files:** `scripts/daily_scrape.sh`

```bash
#!/bin/bash
# Daily job scraping script

cd /opt/uae-jobs

# Run Python scraper
python3 -m src.ingestion.main --source rapidapi --keywords "data engineer, data analyst, machine learning"

# Log completion
echo "$(date): Daily scrape completed" >> /var/log/uae-jobs.log
```

**Cron Entry:**
```bash
# /etc/cron.d/uae-jobs
0 6 * * * root /opt/uae-jobs/scripts/daily_scrape.sh
```

**Acceptance Criteria:**
- [ ] Runs at 6 AM UAE time daily
- [ ] Logs to file for debugging
- [ ] Sends notification on failure

---

#### Task 1.4: Create APScheduler Wrapper
**Files:** `src/orchestration/scheduler.py`

```python
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

class DailyScheduler:
    """APScheduler wrapper for daily automation."""
    
    def __init__(self):
        self.scheduler = BlockingScheduler(timezone=pytz.timezone('Asia/Dubai'))
    
    def setup_jobs(self):
        """Configure daily jobs."""
        # Daily scrape at 6 AM
        self.scheduler.add_job(
            self.scrape_jobs,
            CronTrigger(hour=6, minute=0),
            id='daily_scrape'
        )
        
        # Contact enrichment at 9 AM
        self.scheduler.add_job(
            self.enrich_contacts,
            CronTrigger(hour=9, minute=0),
            id='contact_enrichment'
        )
        
        # Recommendations at 10 AM
        self.scheduler.add_job(
            self.generate_recommendations,
            CronTrigger(hour=10, minute=0),
            id='recommendations'
        )
    
    def start(self):
        """Start the scheduler."""
        self.setup_jobs()
        self.scheduler.start()
```

**Acceptance Criteria:**
- [ ] Cron expressions work correctly
- [ ] Timezone set to Asia/Dubai
- [ ] Retry logic on failure

---

### Wave 2: ATS Keyword Extraction (Days 4-7)

#### Task 2.1: Create ATS Keywords Database Table
**Files:** `migrations/006_ats_keywords.sql`

```sql
CREATE TABLE analytics.fact_job_ats_keywords (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_posting_id UUID REFERENCES analytics.fact_job_posting(job_posting_id),
    hard_skills JSONB DEFAULT '[]',
    soft_skills JSONB DEFAULT '[]',
    action_verbs JSONB DEFAULT '[]',
    certifications JSONB DEFAULT '[]',
    industry_terms JSONB DEFAULT '[]',
    keywords_by_category JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_ats_keywords_job ON analytics.fact_job_ats_keywords(job_posting_id);
```

**Acceptance Criteria:**
- [ ] Table created with proper schema
- [ ] Foreign key to fact_job_posting
- [ ] Indexes for fast queries

---

#### Task 2.2: Build LLM ATS Extraction Prompt
**Files:** `src/intelligence/llm/ats_extractor.py`

```python
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
    """Extract ATS-friendly keywords using local LLM (free)."""
    
    def __init__(self):
        self.llm_client = OllamaClient()  # Local, free
    
    async def extract(self, job: dict) -> dict:
        """Extract keywords from job description."""
        prompt = ATS_KEYWORDS_PROMPT.format(**job)
        response = await self.llm_client.generate(prompt)
        return json.loads(response)
```

**Acceptance Criteria:**
- [ ] Uses local Ollama + Qwen (free)
- [ ] Extracts 5+ hard skills per job
- [ ] Returns valid JSON

---

#### Task 2.3: Build spaCy Fallback Extractor
**Files:** `src/intelligence/nlp/keyword_extractor.py`

```python
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer

class SpacyKeywordExtractor:
    """NLP-based keyword extraction as LLM fallback (free)."""
    
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")
    
    def extract(self, text: str) -> dict:
        """Extract keywords using NLP."""
        doc = self.nlp(text)
        
        # Named entities (skills, tools)
        entities = [ent.text for ent in doc.ents]
        
        # Noun phrases (potential skills)
        noun_phrases = [chunk.text for chunk in doc.noun_chunks]
        
        # TF-IDF keywords
        tfidf = TfidfVectorizer(max_features=20)
        tfidf.fit_transform([text])
        keywords = tfidf.get_feature_names_out()
        
        return {
            "hard_skills": entities,
            "soft_skills": noun_phraces,
            "keywords": list(keywords)
        }
```

**Acceptance Criteria:**
- [ ] Works without LLM (offline mode)
- [ ] Free open-source libraries
- [ ] Extracts entities and noun phrases

---

#### Task 2.4: Integrate ATS Extraction into Pipeline
**Files:** `src/intelligence/pipeline.py`

```python
async def enrich_with_ats_keywords(jobs: list[dict]) -> list[dict]:
    """Add ATS keywords to job listings."""
    extractor = ATSKeywordExtractor()
    fallback = SpacyKeywordExtractor()
    
    for job in jobs:
        try:
            # Primary: LLM extraction (free)
            keywords = await extractor.extract(job)
        except Exception:
            # Fallback: spaCy NLP (free)
            keywords = fallback.extract(job["description"])
        
        job["ats_keywords"] = keywords
    
    return jobs
```

**Acceptance Criteria:**
- [ ] Falls back to spaCy on LLM failure
- [ ] Stores keywords in database
- [ ] Pipeline processes ≥ 50 jobs/hour

---

### Wave 3: Contact Enrichment (Days 8-12)

#### Task 3.1: Create Company Contacts Table
**Files:** `migrations/007_company_contacts.sql`

```sql
CREATE TABLE analytics.dim_company_contacts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES analytics.dim_company(company_id),
    contact_name VARCHAR(255),
    email VARCHAR(255),
    email_confidence DECIMAL(3,2),
    linkedin_url VARCHAR(500),
    position VARCHAR(255),
    source VARCHAR(50),  -- 'website', 'github', 'pattern'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_company_contacts_company ON analytics.dim_company_contacts(company_id);
```

**Acceptance Criteria:**
- [ ] Table with company relationship
- [ ] Email confidence score
- [ ] Source tracking

---

#### Task 3.2: Build DIY Email Pattern Finder
**Files:** `src/intelligence/enrichment/email_finder.py`

```python
import re
import httpx
from bs4 import BeautifulSoup

class EmailPatternFinder:
    """Find company emails from public sources (free)."""
    
    async def find_emails_from_website(self, domain: str) -> list[dict]:
        """Scrape company website for emails."""
        emails = []
        
        # Check common pages
        pages = ["/contact", "/about", "/team", "/careers"]
        
        async with httpx.AsyncClient() as client:
            for page in pages:
                try:
                    url = f"https://{domain}{page}"
                    response = await client.get(url, timeout=10)
                    
                    if response.status_code == 200:
                        found = self._extract_emails(response.text, domain)
                        emails.extend(found)
                except Exception:
                    continue
        
        return emails
    
    def _extract_emails(self, html: str, domain: str) -> list[dict]:
        """Extract emails from HTML."""
        emails = []
        
        # Regex for emails
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        found_emails = re.findall(email_pattern, html)
        
        for email in found_emails:
            if domain in email:  # Only company emails
                emails.append({
                    "email": email,
                    "confidence": 0.8,
                    "source": "website"
                })
        
        return emails
    
    async def find_email_pattern(self, domain: str) -> str:
        """Detect email pattern from known emails."""
        emails = await self.find_emails_from_website(domain)
        
        if not emails:
            return None
        
        # Analyze pattern
        patterns = []
        for email_data in emails:
            email = email_data["email"].split("@")[0]
            
            if "." in email:
                patterns.append("first.last")
            elif len(email) <= 2:
                patterns.append("flast")
            else:
                patterns.append("first")
        
        # Return most common pattern
        from collections import Counter
        return Counter(patterns).most_common(1)[0][0]
```

**Acceptance Criteria:**
- [ ] Scrapes company websites
- [ ] Extracts emails from HTML
- [ ] Detects email patterns
- [ ] Completely free, no API keys

---

#### Task 3.3: Build GitHub Email Finder
**Files:** `src/intelligence/enrichment/github_finder.py`

```python
import httpx

class GitHubEmailFinder:
    """Find company emails from public GitHub commits (free)."""
    
    def __init__(self):
        self.base_url = "https://api.github.com"
    
    async def find_company_emails(self, company_name: str) -> list[dict]:
        """Find emails from company's GitHub commits."""
        emails = []
        
        # Search for company repos
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/search/repositories",
                params={"q": company_name, "per_page": 5}
            )
            
            repos = response.json().get("items", [])
            
            for repo in repos[:3]:  # Check top 3 repos
                # Get recent commits
                commits_response = await client.get(
                    f"{self.base_url}/repos/{repo['full_name']}/commits",
                    params={"per_page": 10}
                )
                
                commits = commits_response.json()
                
                for commit in commits:
                    author = commit.get("author", {})
                    if author and author.get("email"):
                        emails.append({
                            "email": author["email"],
                            "name": author.get("login", ""),
                            "confidence": 0.6,
                            "source": "github"
                        })
        
        return emails
```

**Acceptance Criteria:**
- [ ] Finds emails from GitHub commits
- [ ] Uses GitHub API (free, no auth needed for public repos)
- [ ] Returns author information

---

#### Task 3.4: Build LinkedIn Profile Finder
**Files:** `src/intelligence/enrichment/linkedin_finder.py`

```python
class LinkedInFinder:
    """Find public LinkedIn profiles (ethical approach)."""
    
    async def find_company_linkedin(self, company_name: str) -> Optional[str]:
        """Find company LinkedIn URL from job posting."""
        # Extract from job posting if available
        # Never scrape private profiles
        pass
    
    async def find_recruiter_profiles(self, company_domain: str) -> list[dict]:
        """Find public recruiter profiles via Google search."""
        # Use Google search with site:linkedin.com/in
        # Only collect publicly available data
        pass
```

**Ethical Guidelines:**
- ✅ Store LinkedIn URLs from job postings (if listed)
- ✅ Find public company pages
- ✅ Use Google search for public profiles
- ❌ Never scrape private profiles
- ❌ Never bypass LinkedIn authentication
- ❌ Never store private data

**Acceptance Criteria:**
- [ ] Finds public LinkedIn URLs
- [ ] Respects robots.txt
- [ ] Only stores publicly available data

---

#### Task 3.5: Integrate Contact Enrichment into Pipeline
**Files:** `src/intelligence/pipeline.py`

```python
async def enrich_contacts(jobs: list[dict]) -> list[dict]:
    """Enrich jobs with company contacts (free)."""
    email_finder = EmailPatternFinder()
    github_finder = GitHubEmailFinder()
    linkedin_finder = LinkedInFinder()
    
    # Group by company to avoid duplicate lookups
    companies = {}
    for job in jobs:
        company = job["company_name"]
        if company not in companies:
            companies[company] = job
    
    for company_name, job in companies.items():
        domain = self._get_company_domain(company_name)
        
        # Website email scraping (free)
        website_emails = await email_finder.find_emails_from_website(domain)
        
        # GitHub email finding (free)
        github_emails = await github_finder.find_company_emails(company_name)
        
        # LinkedIn URL (free)
        linkedin_url = await linkedin_finder.find_company_linkedin(company_name)
        
        # Combine and store
        all_contacts = website_emails + github_emails
        store_company_contacts(job["company_id"], all_contacts, linkedin_url)
    
    return jobs
```

**Acceptance Criteria:**
- [ ] Enriches ≥ 20% of companies
- [ ] Uses only free sources
- [ ] Caches results to avoid re-querying

---

### Wave 4: Job Recommendations (Days 13-16)

#### Task 4.1: Create User Profile Table
**Files:** `migrations/008_user_profiles.sql`

```sql
CREATE TABLE analytics.dim_user_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(100) UNIQUE NOT NULL,
    skills JSONB DEFAULT '[]',
    experience_years INTEGER,
    expected_salary_min DECIMAL(10,2),
    expected_salary_max DECIMAL(10,2),
    preferred_cities JSONB DEFAULT '[]',
    preferred_industries JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Acceptance Criteria:**
- [ ] Opt-in user profiles (no default data)
- [ ] Skills and preferences storage
- [ ] Privacy-respecting design

---

#### Task 4.2: Build Recommendation Engine
**Files:** `src/intelligence/recommendations/engine.py`

```python
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

class RecommendationEngine:
    """Rank jobs based on user profile and job attributes (free)."""
    
    def __init__(self):
        self.weights = {
            "skills_match": 0.35,
            "salary_fit": 0.25,
            "company_reputation": 0.15,
            "recency": 0.15,
            "experience_fit": 0.10
        }
    
    def rank_jobs(self, jobs: list[dict], user_profile: dict) -> list[dict]:
        """Rank jobs by score."""
        for job in jobs:
            job["score"] = self._calculate_score(job, user_profile)
        
        return sorted(jobs, key=lambda x: x["score"], reverse=True)[:10]
    
    def _calculate_score(self, job: dict, user: dict) -> float:
        """Calculate multi-factor score."""
        scores = {
            "skills_match": self._skills_score(job, user),
            "salary_fit": self._salary_score(job, user),
            "company_reputation": self._reputation_score(job),
            "recency": self._recency_score(job),
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
```

**Acceptance Criteria:**
- [ ] Multi-factor scoring
- [ ] Returns top 10 jobs
- [ ] Local computation (free)

---

#### Task 4.3: Create Recommendations Table
**Files:** `migrations/009_job_recommendations.sql`

```sql
CREATE TABLE analytics.job_recommendations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(100),
    job_posting_id UUID REFERENCES analytics.fact_job_posting(job_posting_id),
    score DECIMAL(5,4),
    rank INTEGER,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP DEFAULT (CURRENT_TIMESTAMP + INTERVAL '1 day')
);

CREATE INDEX idx_recommendations_user ON analytics.job_recommendations(user_id);
CREATE INDEX idx_recommendations_score ON analytics.job_recommendations(score DESC);
```

**Acceptance Criteria:**
- [ ] Daily recommendations stored
- [ ] Expiration after 24 hours
- [ ] Indexed for fast retrieval

---

#### Task 4.4: Build Daily Recommendation Flow
**Files:** `src/orchestration/recommendation_flow.py`

```python
async def generate_daily_recommendations():
    """Generate daily top 10 recommendations (free)."""
    engine = RecommendationEngine()
    
    # Get all active jobs from last 7 days
    jobs = get_recent_jobs(days=7)
    
    # Get user profiles (opt-in only)
    users = get_opt_in_users()
    
    for user in users:
        # Rank jobs for this user
        top_10 = engine.rank_jobs(jobs, user)
        
        # Store recommendations
        store_recommendations(user["user_id"], top_10)
    
    # Generate default recommendations (no user profile)
    default_top_10 = engine.rank_jobs(jobs, DEFAULT_PROFILE)
    store_recommendations("default", default_top_10)
```

**Acceptance Criteria:**
- [ ] Runs after daily ingestion
- [ ] Generates per-user and default recommendations
- [ ] Stores with 24-hour expiration

---

### Wave 5: Dashboard Enhancements (Days 17-21)

#### Task 5.1: Add Top 10 Recommendations Page
**Files:** `src/dashboard/pages/recommendations.py`

```python
def render_recommendations():
    """Render top 10 job recommendations."""
    st.header("🎯 Today's Top 10 Jobs")
    
    recommendations = fetch_recommendations(limit=10)
    
    for i, rec in enumerate(recommendations, 1):
        with st.expander(f"#{i} - {rec['job_title']} at {rec['company_name']}"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"**Score:** {rec['score']:.1%}")
                st.markdown(f"**Salary:** {rec['salary_range']}")
                st.markdown(f"**Location:** {rec['city']}")
                
                # ATS Keywords
                st.subheader("📝 ATS Keywords to Use")
                keywords = rec.get("ats_keywords", {})
                st.markdown(f"**Skills:** {', '.join(keywords.get('hard_skills', []))}")
                st.markdown(f"**Action Verbs:** {', '.join(keywords.get('action_verbs', []))}")
            
            with col2:
                # Company Contacts
                st.subheader("👤 Hiring Contacts")
                contacts = rec.get("contacts", [])
                for contact in contacts[:3]:
                    st.markdown(f"**{contact['name']}**")
                    st.markdown(f"📧 {contact['email']}")
                    if contact.get('linkedin'):
                        st.markdown(f"🔗 [LinkedIn]({contact['linkedin']})")
```

**Acceptance Criteria:**
- [ ] Shows top 10 ranked jobs
- [ ] Displays ATS keywords
- [ ] Shows company contacts

---

#### Task 5.2: Add ATS Keywords Dashboard Section
**Files:** `src/dashboard/pages/ats_keywords.py`

```python
def render_ats_keywords():
    """Render ATS keyword analysis."""
    st.header("🔑 ATS Keyword Intelligence")
    
    # Keyword frequency chart
    st.subheader("Most In-Demand Skills")
    skills_data = fetch_skill_frequency()
    fig = px.bar(skills_data, x="count", y="skill", orientation="h")
    st.plotly_chart(fig)
    
    # Action verbs by industry
    st.subheader("Action Verbs by Industry")
    industry = st.selectbox("Select Industry", get_industries())
    verbs = fetch_action_verbs(industry)
    st.dataframe(verbs)
    
    # Certification demand
    st.subheader("Top Certifications")
    certs = fetch_certification_demand()
    st.dataframe(certs)
```

**Acceptance Criteria:**
- [ ] Skill frequency visualization
- [ ] Action verbs by industry
- [ ] Certification demand analysis

---

#### Task 5.3: Add Company Contacts Directory
**Files:** `src/dashboard/pages/contacts.py`

```python
def render_contacts():
    """Render company contacts directory."""
    st.header("🏢 Company Contacts")
    
    # Search by company
    company = st.text_input("Search Company")
    if company:
        contacts = search_company_contacts(company)
        st.dataframe(contacts)
    
    # Browse by industry
    st.subheader("Browse by Industry")
    industry = st.selectbox("Industry", get_industries())
    companies = fetch_companies_by_industry(industry)
    
    for company in companies:
        with st.expander(company["name"]):
            contacts = fetch_company_contacts(company["id"])
            for contact in contacts:
                st.markdown(f"**{contact['name']}** - {contact['position']}")
                st.markdown(f"📧 {contact['email']}")
                if contact.get('linkedin'):
                    st.markdown(f"🔗 [LinkedIn]({contact['linkedin']})")
```

**Acceptance Criteria:**
- [ ] Search by company name
- [ ] Browse by industry
- [ ] Contact details with email/LinkedIn

---

#### Task 5.4: Create Daily Email Digest (Optional - Free)
**Files:** `src/notifications/email_digest.py`

```python
import smtplib
from email.mime.text import MIMEText

class EmailDigest:
    """Send daily job recommendations via email (free with Gmail)."""
    
    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
    
    async def send_daily_digest(self, user_email: str, recommendations: list):
        """Send top 10 jobs email."""
        html = self._build_email_html(recommendations)
        
        msg = MIMEText(html, 'html')
        msg['Subject'] = f"🎯 Your Daily Job Recommendations"
        msg['From'] = os.getenv("SMTP_EMAIL")
        msg['To'] = user_email
        
        with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
            server.starttls()
            server.login(os.getenv("SMTP_EMAIL"), os.getenv("SMTP_PASSWORD"))
            server.send_message(msg)
    
    def _build_email_html(self, recommendations: list) -> str:
        """Build HTML email with recommendations."""
        # Template with top 10 jobs, ATS keywords, contacts
        pass
```

**Acceptance Criteria:**
- [ ] Opt-in email notifications
- [ ] HTML email with job cards
- [ ] Uses Gmail SMTP (free)

---

## Dependencies to Add

```txt
# requirements.txt additions
httpx==0.27.0           # HTTP client (free)
beautifulsoup4==4.12.3  # HTML parsing (free)
spacy==3.8.0            # NLP (free)
scikit-learn==1.6.0     # TF-IDF, cosine similarity (free)
apscheduler==3.10.4     # Scheduling (free)
jinja2==3.1.4           # Email templates (free)
```

**Note:** All dependencies are free and open-source.

---

## Environment Variables

```bash
# .env additions
RAPIDAPI_KEY=your_rapidapi_key  # Free tier
SMTP_EMAIL=your_email@gmail.com  # Free Gmail SMTP
SMTP_PASSWORD=your_app_password  # Free Gmail app password
DAILY_SCRAPER_ENABLED=true
RECOMMENDATIONS_ENABLED=true
```

---

## Database Migrations

1. `006_ats_keywords.sql` - ATS keywords table
2. `007_company_contacts.sql` - Company contacts table
3. `008_user_profiles.sql` - User profiles table
4. `009_job_recommendations.sql` - Recommendations table

---

## Testing Strategy

### Unit Tests
- `tests/test_ats_extractor.py` - ATS keyword extraction
- `tests/test_contact_enricher.py` - Contact enrichment
- `tests/test_recommendation_engine.py` - Job ranking

### Integration Tests
- `tests/test_daily_pipeline.py` - End-to-end daily flow
- `tests/test_rapidapi_scraper.py` - RapidAPI scraping

### Manual Testing
- Run daily pipeline manually
- Verify top 10 recommendations on dashboard
- Check ATS keywords for sample jobs
- Verify company contacts

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| RapidAPI quota exceeded | Rotate between 3 free providers |
| Website blocks scraping | Rate limiting, rotating user agents |
| LLM extraction fails | spaCy fallback, retry logic |
| Data quality issues | Validation, deduplication, manual review |

---

## Rollout Plan

1. **Week 1:** RapidAPI scraper + Cron scheduling
2. **Week 2:** ATS keywords + Contact enrichment
3. **Week 3:** Recommendations + Dashboard

---

## Definition of Done

- [ ] Daily pipeline runs at 6 AM UAE time
- [ ] Top 10 recommendations generated daily
- [ ] ATS keywords extracted for ≥ 90% of jobs
- [ ] Contact enrichment for ≥ 20% of companies
- [ ] Dashboard displays all new features
- [ ] All tests passing
- [ ] Documentation updated
- [ ] **Total monthly cost: $0**
