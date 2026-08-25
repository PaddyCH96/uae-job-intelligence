# Phase 2 Research: AI-Enhanced Job Intelligence

## research-date: 2026-08-26
## phase: 2 — Intelligence Generation
## status: complete

---

## 1. Executive Summary

Phase 2 transforms the UAE Job Intelligence Platform from a **data collection engine** into an **AI-powered intelligence platform**. The core objective is to integrate Large Language Models (LLMs) via Ollama to extract structured insights from unstructured job descriptions, enabling trend analysis, skill growth tracking, and salary correlation.

Key deliverables:
- Ollama integration with Qwen 3 8B or Gemma 2B for skill/technology extraction
- Automated enrichment of `fact_job_posting.extracted_skills` and `extracted_technologies`
- Predictive salary insights (basic correlation models)
- Technology adoption trend analysis over time
- Enhanced Streamlit dashboard with AI-generated visualizations
- Prefect orchestration for model-enhanced pipeline runs

---

## 2. LLM Integration Strategy

### 2.1 Model Selection

| Option | Model | Size | VRAM | Pros | Cons |
|--------|-------|------|------|------|------|
| **A** | Qwen 3 8B | 8B | ~5GB | Best Arabic/English support, strong coding, active development | Larger VRAM footprint |
| **B** | Gemma 2B | 2B | ~1.5GB | Lightweight, Google-quality, easy deployment | Weaker reasoning than Qwen 3 |
| **C** | Qwen 2.5 7B Q4 | 7B Q4 | ~4.5GB | Good balance of size/capability, quantized support | Still requires GPU or large RAM |

**Recommendation**: **Qwen 3 8B** (Option A) — The UAE job market requires strong English language processing and technical skill identification. Qwen 3 8B offers the best balance of capability and deployability via Ollama.

### 2.2 Ollama Setup

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull the model
ollama pull qwen3:8b

# Verify
ollama run qwen3:8b "Extract skills from: 'Looking for a Data Engineer with Python, SQL, and AWS experience.'"
```

### 2.3 API Integration

The platform will use `ollama.py` utility module:

```python
import requests
import json
import time
from src.utils.logger import logger

OLLAMA_BASE = "http://localhost:11434"
MODEL = "qwen3:8b"

def extract_with_llm(prompt: str, timeout: int = 30) -> str:
    """Send a prompt to Ollama and return the response."""
    try:
        resp = requests.post(
            f"{OLLAMA_BASE}/api/generate",
            json={"model": MODEL, "prompt": prompt, "stream": False},
            timeout=timeout,
        )
        resp.raise_for_status()
        result = resp.json()
        return result.get("response", "")
    except Exception as e:
        logger.error("llm_request_failed", error=str(e))
        return ""
```

### 2.4 Prompt Templates

#### Skill Extraction Prompt

```text
Extract the technical skills and tools mentioned in this job description.
Return ONLY a JSON array of skill names. No prose, no explanations.

Job Description:
{description}

Skills (JSON array):
```

#### Technology Extraction Prompt

```text
Extract the technologies, platforms, and cloud services mentioned in this job description.
Return ONLY a JSON array of technology names. No prose, no explanations.

Job Description:
{description}

Technologies (JSON array):
```

#### Salary Analysis Prompt

```text
Given this job salary range and description, provide a salary analysis.
Return a JSON with: "predicted_min", "predicted_max", "confidence" (0-1), "factors" (array of strings).

Job Description:
{description}

Salary Range: {salary_range}

Analysis (JSON):
```

---

## 3. Data Source Enhancements

### 3.1 Current Sources Status

| Source | Status | Coverage | Notes |
|--------|--------|----------|-------|
| **Bayt** | ✅ Implemented | UAE general | Working scraper, rate-limited |
| **GulfTalent** | ⚠️ Partial | UAE/GCC | Scraper exists, needs validation |
| **Naukri Gulf** | ⚠️ Partial | India/UAE | Scraper exists, needs validation |
| **Mock** | ✅ Always available | Testing | Used for development |

### 3.2 Recommended Enhancements

1. **Complete GulfTalent scraper** (`src/ingestion/sources/gulftalent.py`) - Add pagination, error handling, and deduplication
2. **Complete Naukri Gulf scraper** (`src/ingestion/sources/naukrigulf.py`) - Add headers, robots.txt compliance
3. **LinkedIn Jobs scraper** (Phase 2+) - Would require authentication; deferred to Phase 3
4. **Company career pages** - ADNOC, Emirates, Etisalat career pages; manual API or structured scraping

### 3.3 Mock Source Enhancement

The `MockSource` in `base.py` should be enhanced to generate realistic job descriptions with embedded skills for LLM testing:

```python
# In src/ingestion/base.py
class MockSource(BaseSource):
    def fetch_and_transform(self, max_pages: int = 3) -> List[Dict]:
        """Generate mock jobs with realistic descriptions for LLM testing."""
        jobs = []
        for i in range(5):
            job = {
                "job_title": f"Data Engineer {i}",
                "company": f"Company {i}",
                "location": ["Dubai", "Abu Dhabi", "Sharjah"][i % 3],
                "description": fake.text(max_nb_chars=500),
                "salary_range": f"AED {20000 + i*2000} - {AED {35000 + i*3000}}",
                "remote_allowed": i % 2 == 0,
                "visa_sponsorship": i % 3 != 0,
                "experience_level": ["Entry Level", "Mid Level", "Senior Level"][i % 3],
            }
            jobs.append(job)
        return jobs
```

---

## 4. Skill & Technology Extraction Pipeline

### 4.1 Workflow

```text
Raw Job Description
      ↓
LLM Extraction (Qwen 3 8B via Ollama)
      ↓
Parse JSON output → normalized skill/technology lists
      ↓
Upsert into dim_skill / dim_technology tables
      ↓
Populate fact_job_posting.extracted_skills / extracted_technologies (JSONB)
      ↓
Aggregate for dashboards (top skills, emerging technologies, salary correlation)
```

### 4.2 Processing Steps

1. **Fetch jobs** from ingestion sources (existing pipeline)
2. **Send to LLM** in batches (to manage API costs and latency)
3. **Parse JSON** from LLM response (validate schema)
4. **Normalize skills** (lowercase, trim, deduplicate)
5. **Upsert into dim_skill** and dim_technology
6. **Store JSONB** in fact_job_posting
7. **Trigger dashboard update** (Streamlit auto-refresh)

### 4.3 Batch Processing Strategy

To manage costs and latency:

- **Batch size**: 5-10 jobs per LLM request
- **Rate limiting**: 1 request per 2 seconds (Ollama local)
- **Cost**: Free (local Ollama), but GPU RAM constrained
- **Fallback**: If LLM fails, use fuzzywuzzy-based extraction (existing deduplication logic)

---

## 5. Technology Trend Analysis

### 5.1 SQL for Trend Analysis

```sql
-- Top technologies by growth rate (year-over-year)
SELECT 
    dt.technology_name,
    COUNT(DISTINCT fjp.job_posting_id) AS job_count,
    COUNT(DISTINCT fjp.snapshot_id) AS snapshot_count,
    -- Simple growth: compare first half vs second half of year
    CASE 
        WHEN MIN(fjp.posted_date) < DATE '2024-07-01' 
        THEN 'Growing' 
        ELSE 'Established' 
    END as trend
FROM analytics.fact_job_posting fjp
JOIN analytics.dim_technology dt ON dt.technology_name = ANY(fjp.extracted_technologies::text[])
GROUP BY dt.technology_name
ORDER BY job_count DESC
LIMIT 20;
```

### 5.2 Key Metrics

| Metric | Description |
|--------|-------------|
| **Technology Adoption Rate** | % of new postings mentioning technology X in last 30 days |
| **Skill Decay** | Skills that appear in < 5% of new postings (year-over-year) |
| **Emerging Tech** | Technologies with > 50% year-over-year growth |
| **Salary Premium** | Avg salary for roles requiring technology X vs overall avg |

---

## 6. Salary Prediction Model (Basic)

### 6.1 Correlation Analysis

Simple linear regression on extracted features:

```python
import numpy as np
import pandas as pd
from sqlalchemy import text

# Query job data with features
query = text("""
SELECT 
    fjp.salary_min,
    fjp.salary_max,
    ARRAY_LENGTH(fjp.extracted_skills, 1) AS skill_count,
    ARRAY_LENGTH(fjp.extracted_technologies, 1) AS tech_count,
    dim.level_name AS experience_level,
    dim.type_name AS employment_type
FROM analytics.fact_job_posting fjp
JOIN analytics.dim_experience_level dim ON fjp.experience_level_id = dim.experience_level_id
JOIN analytics.dim_employment_type dim ON fjp.employment_type_id = dim.employment_type_id
WHERE fjp.salary_min IS NOT NULL AND fjp.salary_max IS NOT NULL
""")

df = db.session.execute(query).mappings().fetchall()
# Run regression: salary ~ skill_count + tech_count + experience_level + employment_type
```

### 6.2 Features

| Feature | Type | Expected Correlation |
|---------|------|---------------------|
| skill_count | Integer | Positive (more skills → higher salary) |
| tech_count | Integer | Positive (rare tech → premium) |
| experience_level | Categorical | Positive (senior > mid > entry) |
| employment_type | Categorical | Full-time > contract > internship |

---

## 7. Prefect Orchestration Enhancements

### 7.1 Current Flow

The `daily_ingestion_flow` in `flows.py` already handles:
- Source ingestion (bayt, gulftalent, naukrigulf)
- Raw job storage
- Deduplication/processing

### 7.2 Phase 2 Additions

Add a new Prefect flow for LLM-enhanced processing:

```python
@flow(name="uae-jobs-llm-enrichment", log_prints=True)
def llm_enrichment_flow(
    job_ids: List[uuid.UUID] = None,
    batch_size: int = 5,
) -> dict:
    """
    Enrich job postings with LLM-extracted skills and technologies.
    
    Args:
        job_ids: Specific job IDs to enrich (None = all unprocessed)
        batch_size: Jobs per LLM request
    
    Returns:
        Summary of enrichment results
    """
    # ... implementation
```

### 7.2 scheduled flow

```python
@flow(name="uae-jobs-weekly-insights", log_prints=True, cron="0 2 * * Mon")
def weekly_insights_flow() -> dict:
    """
    Run weekly: LLM enrichment + trend analysis + dashboard update.
    Executes Mondays at 2 AM.
    """
    # 1. Enrich unprocessed jobs with LLM
    # 2. Run trend analysis SQL
    # 3. Update materialized views
    # 4. Trigger Streamlit refresh
    pass
```

---

## 8. Streamlit Dashboard Enhancements

### 8.1 New Pages

| Page | Purpose | Key Components |
|------|---------|----------------|
| **Skills Dashboard** | Interactive skill growth analysis | Bar charts, heatmaps, filters by city/year |
| **Technology Trends** | Tech adoption over time | Line charts, emerging tech highlights |
| **Salary Insights** | Salary correlation models | Scatter plots, experience level breakdowns |
| **LLM Extraction View** | Raw LLM output verification | Expandable sections, JSON viewer |

### 8.2 Example Chart: Top Skills Growth

```python
import plotly.express as px

def top_skills_chart(years: int = 3) -> go.Figure:
    """Plot top N skills growth over specified years."""
    # Query data from analytics layer
    skills = get_skill_growth_data(years=years)
    
    fig = px.bar(
        skills.head(20),
        x="skill_name",
        y="growth_rate",
        title=f"Top 20 Skills Growth Rate (Last {years} Years)",
        labels={"growth_rate": "Growth Rate (%)", "skill_name": "Skill"},
        color="growth_rate",
        color_continuous_scale="RdYlGn",
    )
    fig.update_layout(showlegend=False, height=600)
    return fig
```

---

## 9. Database Schema Considerations

### 9.1 Existing Fields (Ready for Phase 2)

The `fact_job_posting` model already has these columns perfect for Phase 2:

| Column | Type | Phase 2 Use |
|--------|------|-------------|
| `extracted_skills` | JSONB | LLM-extracted skills |
| `extracted_technologies` | JSONB | LLM-extracted technologies |
| `extracted_certifications` | JSONB | (Phase 3) LLM-certification extraction |
| `content_hash` | String(64) | Deduplication fingerprint |

### 9.2 Index Recommendations

Add GIN index for JSONB queries:

```sql
CREATE INDEX idx_fact_job_posting_skills 
ON analytics.fact_job_posting USING GIN (extracted_skills);
CREATE INDEX idx_fact_job_posting_tech 
ON analytics.fact_job_posting USING GIN (extracted_technologies);
```

---

## 10. Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **LLM latency** | Slow pipeline if processing large volumes | Batch processing; configurable batch size; fallback to fuzzy matching |
| **Model hallucination** | Invalid skills/technologies extracted | JSON schema validation; human-in-the-loop review; error rates tracked |
| **VRAM limitations** | Ollama crashes on model load | Use quantized models (Q4); monitor GPU RAM; gracefully degrade |
| **Data privacy** | Job descriptions contain PII | Local-only Ollama; no data leaves infrastructure; anonymize before sending |
| **Source reliability** | Scrapers fail or change structure | Robust error handling; robots.txt compliance; fallback to mock data |

---

## 11. Success Metrics (Phase 2)

- ✅ Ollama + Qwen 3 8B integrated and responding within 10s per request
- ✅ LLM extracts skills with > 85% accuracy (vs manual baseline)
- ✅ ≥ 500 job postings enriched with extracted_skills/technologies
- ✅ Top 10 technologies identified with trend arrows (growing/established/declining)
- ✅ Dashboard shows skill growth charts with < 5s load time
- ✅ Prefect flows complete successfully (error rate < 5%)
- ✅ No schema migrations required (existing columns reused)

---

## 12. Dependencies

Add to `requirements.txt`:
- `ollama` (or keep as optional dependency documented)
- `plotly` (already installed for dashboard)
- `pandas` (for trend analysis)
- `numpy` (for regression models)

Optional GPU acceleration:
- `cufflinks` (if needed for Plotly offline mode)

---

## 13. Timeline Estimate

| Week | Deliverable |
|------|-------------|
| 1 | Ollama setup, model pull, basic API integration |
| 2 | Skill extraction prompt engineering, parsing logic |
| 3 | Pipeline integration (ingest → LLM → store) |
| 4 | Prefect flow for LLM enrichment |
| 5 | Dashboard new pages (skills, tech trends) |
| 6 | Salary correlation analysis, success metric validation |
| 7 | Bug fixes, documentation, handoff |

**Total**: 7 weeks from kickoff.

---

## 14. Open Questions / Decisions Needed

1. **Model choice**: Qwen 3 8B vs Gemma 2B — Awaiting stakeholder input
2. **Batch size**: 5 jobs/request vs 10 — Balance latency vs coverage
3. **LLM cost model**: Free (local) vs hosted API — Committed to local Ollama
4. **LLM concurrency**: Single request at a time vs multi-threaded — Single thread for VRAM safety
5. **Human review**: 100% automated vs sample review vs full audit — Sample review (10%) for quality assurance

---