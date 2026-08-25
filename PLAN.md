# Phase 2 Plan: AI-Enhanced Intelligence Generation

**phase:** 2
**mode:** mvp (vertical feature slices)
**status:** planned
**start-date:** 2026-08-26
**derived-from-research:** RESEARCH.md

---

## 1. Phase Overview

**Objective:** Transform the UAE Job Intelligence Platform from a data collection engine into an AI-powered intelligence platform by integrating LLMs via Ollama for skill and technology extraction, enabling trend analysis, and enhancing the dashboard with AI-generated insights.

**Success Criteria (Phase 2):**
- Ollama + Qwen 3 8B integrated, responding within 10s per request
- ≥ 500 job postings enriched with `extracted_skills` and `extracted_technologies`
- Top 10 technologies identified with trend indicators (growing/established/declining)
- Dashboard shows skill growth charts with < 5s load time
- Prefect flows complete with error rate < 5%
- No database schema migrations required (existing columns reused)

**Non-Goals (Phase 2):**
- ❌ Full predictive salary models (Phase 3)
- ❌ Real-time data processing (batch only)
- ❌ User authentication or accounts
- ❌ Global job market expansion (UAE-only scope)
- ❌ LLM-as-a-service costs (committed to local Ollama)

---

## 2. Success Metrics (Derived from RESEARCH.md)

| Metric | Target | Measurement |
|--------|--------|-------------|
| LLM response time | < 10s per request | `ollama generate` latency |
| Skill extraction accuracy | > 85% vs manual baseline | Spot-check 50 jobs |
| Jobs enriched | ≥ 500 | `fact_job_posting.extracted_skills IS NOT NULL` |
| Top technologies identified | ≥ 10 | `SELECT COUNT(*) FROM dim_technology` |
| Dashboard load time | < 5s | Streamlit `load_state` timing |
| Prefect flow error rate | < 5% | Flow run monitoring |
| Schema migrations | 0 | `alembic heads` comparison |

---

## 3. Task Plan (Vertical MVP Slices)

### Slice 1: Foundation & LLM Integration
| Task | Owner | Dependencies | Deliverable |
|------|-------|--------------|-------------|
| T1.1 Set up Ollama and pull Qwen 3 8B model | Infra | Docker available | `ollama pull qwen3:8b` verified |
| T1.2 Create `src/utils/llm.py` utility module | backend | T1.1 | `extract_with_llm(prompt) -> str` function |
| T1.3 Create skill extraction prompt template | backend | RESEARCH.md | JSON-array prompt for skill extraction |
| T1.4 Create technology extraction prompt template | backend | RESEARCH.md | JSON-array prompt for tech extraction |
| T1.5 Test LLM extraction on 5 mock jobs | backend | T1.2, T1.3 | JSON output parsed, validated |

**Definition of Done:** LLM can extract skills and technologies from job descriptions with valid JSON output.

---

### Slice 2: Pipeline Integration
| Task | Owner | Dependencies | Deliverable |
|------|-------|--------------|-------------|
| T2.1 Add LLM enrichment task to Prefect flows | backend | T1.1, flows.py | `llm_enrichment_flow()` defined |
| T2.2 Integrate LLM call into processor.normalize_and_store_job | backend | T1.2, T1.4, database models | `extracted_skills` and `extracted_technologies` populated |
| T2.3 Add GIN indexes for JSONB query performance | database | T2.2 | `CREATE INDEX` on `extracted_skills`, `extracted_technologies` |
| T2.4 Batch processing logic (5 jobs per LLM request) | backend | T1.2, T2.2 | Reduced LLM calls, managed latency |

**Definition of Done:** Jobs flowing through the pipeline have `extracted_skills` and `extracted_technologies` populated in the database.

---

### Slice 3: Trend Analysis & Database
| Task | Owner | Dependencies | Deliverable |
|------|-------|--------------|-------------|
| T3.1 Write SQL queries for technology trend analysis | backend | T2.3, database models | Query returns top N technologies with growth rate |
| T3.2 Create database view `v_tech_trends` | database | T3.1 | Pre-joined view for dashboard consumption |
| T3.3 Add salary correlation basic analysis | backend | T2.2, test_data | Correlation coefficients between tech skills and salary |

**Definition of Done:** Analytics queries work on enriched data, views created, basic correlations computed.

---

### Slice 4: Dashboard Enhancements (Streamlit)
| Task | Owner | Dependencies | Deliverable |
|------|-------|--------------|-------------|
| T4.1 Add "Skills Dashboard" page to Streamlit | frontend | T2.3, T3.1 | Interactive skill growth charts, filters |
| T4.2 Add "Technology Trends" page to Streamlit | frontend | T3.1, T3.2 | Tech adoption trends, emerging tech highlights |
| T4.3 Add "Salary Insights" page to Streamlit | frontend | T3.3 | Scatter plots, experience level breakdowns |
| T4.4 Connect dashboard to enriched data (not mock) | frontend | T2.3, T4.1 | Dashboard reads from real DB, not seed data |

**Definition of Done:** Streamlit dashboard has 3 new pages reading from the enriched analytics layer.

---

### Slice 5: Orchestration & Verification
| Task | Owner | Dependencies | Deliverable |
|------|-------|--------------|-------------|
| T5.1 Create Prefect flow `weekly_insights_flow` | backend | T2.1, T3.1 | Weekly: enrich + analyze + trigger update |
| T5.2 Write verification tests (pytest) | QA | T2.2, T3.3, T4.1, T4.2 | Test suite: enrichment, trends, dashboard |
| T5.2 Set up verification loop (gsd-plan-checker) | orchestration | All slices | Pass/fail criteria documented |

**Definition of Done:** Automated tests validate Phase 2 deliverables; verification loop ready.

---

## 4. Vertical vs Horizontal Organization

This phase uses **vertical MVP mode** — tasks are organized as feature slices (UI→API→DB) rather than horizontal layers. This means:

- **Slice 1** end-to-end: LLM integration from API to database
- **Slice 2** end-to-end: Pipeline integration from ingestion to enrichment
- **Slice 3** end-to-end: Analytics from database to queries
- **Slice 4** end-to-end: Dashboard from frontend to enriched data
- **Slice 5** end-to-end: Orchestration and verification

**Benefits:**
- Faster end-to-end feedback (each slice is shippable)
- Clearer "done" criteria per feature
- Reduced context switching (focus on one user journey at a time)

**If horizontal mode were used:**
- All API endpoints first → All database migrations → All frontend pages
- Longer time to first working feature
- Harder to validate end-to-end

---

## 5. Verification Loop

### 5.1 Verification Commands

```bash
# Run all Phase 2 verification tests
cd /Users/paddykadamuthuri/projects/UAE
python -m pytest tests/ -k "phase2 or llm or enrichment or trend" -v

# Verify LLM integration
docker compose run --rm api python -c "
from src.utils.llm import extract_with_llm
result = extract_with_llm('Extract skills from: Python SQL AWS')
print('LLM result:', result)
'

# Verify database enrichment
docker compose exec postgres psql -U jobs_admin -d uae_jobs -c "
SELECT COUNT(*) as enriched_count FROM analytics.fact_job_posting 
WHERE extracted_skills IS NOT NULL;
"

# Verify dashboard can load
open http://localhost:8501
```

### 5.2 Verification Criteria (PASS/FAIL)

| Check | Pass Condition | Fail Action |
|-------|---------------|-------------|
| LLM connectivity | `extract_with_llm()` returns non-empty JSON | Retry model load; check Ollama status |
| Enrichment count | ≥ 50 jobs have `extracted_skills IS NOT NULL` | Increase batch size; check LLM output format |
| Trend query | Returns ≥ 10 technologies | Check GIN indexes; verify JSONB format |
| Dashboard load | Streamlit page loads in < 5s | Optimize queries; add caching |
| Prefect flow | `daily_ingestion_flow` completes without error | Debug source scraper; check rate limits |
| Zero migrations | `alembic upgrade head` runs without schema changes | Re-review model mapping |

---

## 6. Dependencies

### 6.1 Python Dependencies (requirements.txt)

Add to existing requirements:
```text
# LLM (optional, documented)
# ollama >= 0.1.0  # Local LLM runtime via Ollama

# Analysis
pandas >= 2.2.0
numpy >= 1.24.0

# Already installed (verified)
plotly >= 5.1.0
structlog >= 23.1.0
```

### 6.2 Infrastructure

- Ollama installed and running (`docker compose up -d` includes ollama service, or separate install)
- Qwen 3 8B model pulled (`ollama pull qwen3:8b`)
- PostgreSQL running with analytics schema migrated (existing, no new migrations)
- Streamlit dashboard accessible at `localhost:8501`

### 6.3 External Services (None - all local)

- ✅ Ollama local — no API keys required
- ✅ PostgreSQL local — no external dependencies
- ✅ No LLM API costs (free, local inference)

---

## 7. Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **LLM latency** | Pipeline slowdown if processing large volumes | Batch size of 5 jobs per request; configurable; fallback to fuzzywuzzy deduplication logic already in codebase |
| **Model hallucination** | Invalid skills/technologies extracted | JSON schema validation on LLM output; human-in-the-loop spot-check (10% of jobs); error rates tracked in logs |
| **VRAM limitations** | Ollama crashes on model load | Use Qwen 3 8B Q4 quantized version; monitor `docker stats` GPU RAM; gracefully degrade to fallback extraction |
| **Source scraper failures** | Insufficient job data for LLM processing | Robust error handling in existing scrapers (bayt, gulftalent, naukrigulf); fallback to MockSource; rate limiting respected |
| **JSONB query performance** | Slow trend analysis on large datasets | GIN indexes on `extracted_skills` and `extracted_technologies`; pagination on dashboard queries; materialized views considered for Phase 3 |
| **Human review bandwidth** | Quality assurance bottleneck | Sample-based review (10% of enriched jobs); automated validation of JSON format; track error rates |

---

## 8. Timeline (7 Weeks)

| Week | Primary Deliverable | Key Milestone |
|------|-------------------|---------------|
| 1 | **Foundation** | Ollama + Qwen 3 8B running; `src/utils/llm.py` created and tested on 5 mock jobs |
| 2 | **Pipeline Integration** | LLM enrichment integrated into `normalize_and_store_job`; GIN indexes created; 50+ jobs enriched |
| 3 | **Trend Analysis** | SQL queries working; `v_tech_trends` view created; basic salary correlation computed |
| 4 | **Dashboard (Part 1)** | "Skills Dashboard" page in Streamlit; interactive charts with filters; loads in < 5s |
| 5 | **Dashboard (Part 2)** | "Technology Trends" page; "Salary Insights" page; both reading from enriched DB data |
| 6 | **Orchestration** | `weekly_insights_prefect` flow created; pytest test suite written (≥ 10 tests); verification loop documented |
| 7 | **Finalization** | Bug fixes; documentation updated; success metrics validated; hand-off complete |

**Buffer**: 1 week built-in for unexpected integration issues.

---

## 9. Execution Strategy

### 9.1 Week 1: Foundation

```bash
# Start infrastructure
cd /Users/paddykadamuthuri/projects/UAE
docker compose up -d postgres api dashboard

# Install Ollama and pull model
# (Follow RESEARCH.md section 2.2)
ollama pull qwen3:8b

# Verify
ollama run qwen3:8b "Extract skills from: Python SQL AWS"

# Create llm.py utility
# Implement extract_with_llm() function

# Test on mock data
docker compose run --rm api python -c "
from src.utils.llm import extract_with_llm
result = extract_with_llm('''Extract skills as JSON array from: 
Looking for a Data Engineer with Python, SQL, AWS, and Docker experience.''')
print('Skills:', result)
"
```

### 9.2 Week 2-3: Pipeline & Analytics

```bash
# Run ingestion to get jobs in the pipeline
docker compose run --rm ingestion python -m src.ingestion.main

# Run deduplication
docker compose run --rm ingestion python -m src.deduplication.engine

# Test LLM enrichment on a subset
docker compose run --rm api python -c "
from src.utils.llm import extract_with_llm
from src.database import get_db_context, FactJobPosting, RawJobPosting
from sqlalchemy import select

with get_db_context() as db:
    # Get 3 unprocessed jobs
    jobs = db.query(RawJobPosting).filter(RawJobPosting.processed == False).limit(3).all()
    for job in jobs:
        result = extract_with_llm(job.raw_data.get('description', '')[:500])
        print(f'Job {job.id}: {result[:100]}')
"
```

### 9.3 Week 4-5: Dashboard

```bash
# Run the dashboard
docker compose up -d dashboard

# Access at http://localhost:8501
# Navigate to new pages: Skills, Tech Trends, Salary Insights

# Verify data is from enriched source, not mock
# Check sidebar for page selection
```

### 9.4 Week 6-7: Verification & Polish

```bash
# Run verification tests
python -m pytest tests/ -k "phase2 or llm or enrichment or trend" -v

# Check all success criteria pass
# Document any open issues for Phase 3
# Update ROADMAP.md with Phase 2 status
```

---

## 10. Rollback Plan

If Phase 2 encounters critical issues:

1. **Disable LLM enrichment**: Set `enable_llm_enrichment=False` in `.env` (flag to be added)
2. **Revert database changes**: GIN indexes can be dropped; `extracted_skills`/`extracted_technologies` columns already exist (no migration needed — just stop populating them)
3. **Rollback Prefect flows**: Comment out `weekly_insights_flow`; revert to `daily_ingestion_flow` only
4. **Dashboard**: Remove new pages; revert to original 3-page layout

**Rollback is safe because:**
- No schema migrations required (existing columns reused)
- All new code is additive (features can be toggled off)
- Existing Phase 1 functionality fully preserved

---