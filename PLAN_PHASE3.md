# Phase 3 Plan: Version 1 — AI-Driven Insights

**phase:** 3
**mode:** mvp (vertical feature slices)
**status:** planned
**start-date:** 2026-09-02
**derived-from-research:** RESEARCH.md (Phase 2)
**prerequisite-phase:** 2

---

## 1. Phase Overview

**Objective:** Build upon the Phase 2 LLM integration to deliver AI-driven intelligence on skill growth, technology-salary correlation, and refined market trends. Version 1 transforms the platform from a descriptive analytics engine into a predictive intelligence platform, using local LLMs to enable deeper analysis of the UAE data/AI job market.

**Success Criteria (Phase 3):**
- ✅ LLM-enhanced skill extraction covering 80%+ of active job postings
- ✅ Technology-salary correlation models with R² > 0.4
- ✅ Skill growth rates computed for top 30 skills (year-over-year)
- ✅ "Top hiring companies" dashboard with hiring velocity metrics
- ✅ Expanded data sources: ≥ 3 active scrapers (GulfTalent, Naukri Gulf working)
- ✅ Prefect weekly insights flow stable (error rate < 3%)
- ✅ Dashboard: 5 pages (skills, tech trends, salary, companies, cities)
- ✅ No schema migrations (existing columns reused + new dimensions added via migrations)

**Non-Goals (Phase 3):**
- ❌ Predictive forecasting of future skill demands (Phase 4)
- ❌ User profile system or personalization (Phase 4)
- ❌ Real-time data processing (batch only)
- ❌ Global job market expansion (UAE-only scope)
- ❌ User authentication or accounts

---

## 2. Success Metrics (Derived from RESEARCH.md + Roadmap)

| Metric | Target | Measurement |
|--------|--------|-------------|
| LLM extraction coverage | ≥ 80% of active jobs | `extracted_skills IS NOT NULL / total active jobs` |
| Skill growth rates | Top 30 skills computed | SQL: window functions over snapshots |
| Tech-salary correlation | R² > 0.4 | Regression on skill_count + tech_count + experience + employment_type |
| Data source coverage | ≥ 3 active sources | `SELECT DISTINCT source_name FROM dim_source WHERE is_active = True` |
| Prefect flow error rate | < 3% | Flow run monitoring dashboard |
| Dashboard pages | 5 complete pages | Streamlit page count |
| Zero migrations (beyond existing) | 0 | `alembic heads` vs `current` diff |

---

## 3. Task Plan (Vertical MVP Slices)

### Slice 1: LLM Enhancement & Coverage
| Task | Owner | Dependencies | Deliverable |
|------|-------|--------------|-------------|
| T1.1 Expand LLM extraction to all jobs (batch of 10) | backend | Phase 2 complete | `extracted_skills` populated for ≥ 500 jobs |
| T1.2 Create skill growth rate computation | backend | T1.1, database snapshots | SQL query: YoY skill growth % |
| T1.3 Normalize skill taxonomies (deduplicate/fuzzy) | backend | T1.1 | `dim_skill` cleaned, normalized names |
| T1.4 Test extraction on GulfTalent + Naukri Gulf | backend | T1.1, source scrapers | 3 sources tested, errors handled |

**Definition of Done:** ≥ 80% of active jobs have `extracted_skills` populated; skill taxonomies normalized.

---

### Slice 2: Technology-Salary Correlation
| Task | Owner | Dependencies | Deliverable |
|------|-------|--------------|-------------|
| T2.1 Build salary correlation model | backend | T1.1, enriched data | Linear regression: salary ~ skill_count + tech_count + level + type |
| T2.2 Compute R² and coefficient stats | backend | T2.1 | Report: R², p-values, significant factors |
| T2.3 Create database view `v_salary_correlation` | database | T2.1 | Pre-computed correlations per technology |
| T2.4 Dashboard: Salary Insights page | frontend | T2.2, T3.3 | Scatter plot, experience breakdown, tech filters |

**Definition of Done:** Correlation model computed; view created; dashboard page reading from enriched data.

---

### Slice 3: Skill Growth & Trend Analysis
| Task | Owner | Dependencies | Deliverable |
|------|-------|--------------|-------------|
| T3.1 Compute YoY skill growth rates | backend | database snapshots (Phase 2) | SQL: `COUNT` per skill per half-year, growth % |
| T3.2 Create `v_skill_growth` view | database | T3.1 | Pre-joined view for dashboard |
| T3.3 Dashboard: Skills Growth page | frontend | T3.1, T3.2 | Interactive chart: top N skills, growth arrows, city filters |
| T3.4 Fuzzy-skill matching for legacy jobs | backend | existing `content_hash` | Re-run LLM or fuzzy on previously ingested jobs |

**Definition of Done:** Growth rates computed; view created; dashboard page interactive.

---

### Slice 4: Data Source Expansion
| Task | Owner | Dependencies | Deliverable |
|------|-------|--------------|-------------|
| T4.1 Complete GulfTalent scraper | backend | Phase 2 source infrastructure | `src/ingestion/sources/gulftalent.py` fully functional |
| T4.2 Complete Naukri Gulf scraper | backend | Phase 2 source infrastructure | `src/ingestion/sources/naukrigulf.py` fully functional |
| T4.3 Add robots.txt + rate limiting | backend | T4.1, T4.2 | Compliant scraping, no bans |
| T4.4 Expand `DimSource` with source_type categories | database | T4.1, T4.2 | Enum or categorized source types |
| T4.5 Prefect flow: multi-source daily ingestion | orchestration | T4.1–T4.4 | `daily_ingestion_flow` runs all 3 sources |

**Definition of Done:** 3 scrapers working; data flowing into DB; Prefect flow operational.

---

### Slice 5: Dashboard & Orchestration
| Task | Owner | Dependencies | Deliverable |
|------|-------|--------------|-------------|
| T5.1 Add "Top Companies" page to Streamlit | frontend | T4.5, database queries | Company hiring profiles, job counts, growth velocity |
| T5.2 Add "City Distribution" page to Streamlit | frontend | database queries | Job distribution by city, heatmap |
| T5.3 Weekly Prefect insights flow | orchestration | T2.1, T3.1, T4.5 | Mon: enrich + analyze + update dashboard data |
| T5.4 Error handling & fallbacks | full-stack | all slices | Graceful degradation if LLM or source fails |

**Definition of Done:** 5 dashboard pages; weekly flow running; error handling in place.

---

## 4. Vertical vs Horizontal Organization

This phase uses **vertical MVP mode** — tasks organized as feature slices (UI→API→DB) ensuring each slice is end-to-end shippable.

**Slice example (T2.1–T2.4):** 
- Backend: regression model → database view
- Frontend: Scatter plot page reading from view
- End-to-end: data flows from DB → model → view → dashboard UI

**Benefits:**
- Faster feedback per feature (each slice tested independently)
- Clear "done" criteria per feature
- Reduced context switching

**If horizontal mode were used:**
- All regression models first → All database views → All frontend pages
- Longer time to first working dashboard feature
- Harder to validate end-to-end per feature

---

## 5. Verification Loop

### 5.1 Verification Commands

```bash
# Run Phase 3 verification tests
cd /Users/paddykadamuthuri/projects/UAE
python -m pytest tests/ -k "phase3 or correlation or growth or salary" -v

# Verify LLM coverage
docker compose exec postgres psql -U jobs_admin -d uae_jobs -c "
SELECT 
  COUNT(*) as total_active,
  COUNT(CASE WHEN extracted_skills IS NOT NULL THEN 1 END) as enriched,
  ROUND(COUNT(CASE WHEN extracted_skills IS NOT NULL THEN 1 END)::numeric / COUNT(*) * 100, 1) as coverage_pct
FROM analytics.fact_job_posting
WHERE is_active = True;
"

# Verify correlation model
docker compose exec postgres psql -U jobs_admin -d uae_jobs -c "
SELECT * FROM analytics.v_salary_correlation LIMIT 5;
"

# Verify dashboard can load
open http://localhost:8501
# Navigate: Skills Growth, Tech Trends, Salary Insights, Companies, Cities
```

### 5.2 Verification Criteria (PASS/FAIL)

| Check | Pass Condition | Fail Action |
|-------|---------------|-------------|
| LLM coverage | ≥ 80% of active jobs have `extracted_skills IS NOT NULL` | Increase batch size; check LLM output format; expand fallback to fuzzy matching |
| Skill growth rates | Top 30 skills have YoY growth computed | Check snapshot data coverage; ensure Phase 2 snapshots exist |
| Tech-salary correlation | R² > 0.4 computed; view `v_salary_correlation` returns data | Check feature engineering; verify salary data not null; simplify model |
| Data sources | ≥ 3 active sources in `dim_source` | Debug scraper errors; check rate limits; increase max_pages |
| Dashboard pages | 5 pages load with enriched data (not mock) | Optimize queries; add caching; verify DB connection |
| Prefect flow | Weekly insights flow completes error-free (< 3% error rate) | Debug source scraper; check Ollama availability; reduce batch size |

---

## 6. Dependencies

### 6.1 Python Dependencies (requirements.txt)

Add to existing requirements:
```text
# Already installed
plotly >= 5.1.0
pandas >= 2.2.0
numpy >= 1.24.0
structlog >= 23.1.0

# For correlation / regression
scikit-learn >= 1.4.0  # Added for R² computation

# Already installed
fastapi, uvicorn (API)
streamlit, plotly (Dashboard)
sqlalchemy, psycopg2-binary (Database)
fuzzywuzzy (Deduplication)
```

### 6.2 Infrastructure

- Ollama + Qwen 3 8B running (Phase 2 prerequisite)
- PostgreSQL with analytics schema (existing, plus new dimension tables via migrations)
- Prefect installed (`pip install prefect`) for orchestration
- Streamlit dashboard accessible at `localhost:8501`

### 6.3 New Database Migrations (Phase 3)

Add these migration files under `migrations/`:
```sql
-- Add experience_level dimension entries (if not already present)
INSERT INTO analytics.dim_experience_level (level_name, level_description, sort_order)
VALUES ('Entry Level', '0-2 years experience', 1),
       ('Mid Level', '2-5 years experience', 2),
       ('Senior Level', '5+ years experience', 3);

-- Add employment_type dimension entries
INSERT INTO analytics.dim_employment_type (type_name, type_description)
VALUES ('Full-time', 'Full-time employment'),
       ('Contract', 'Contract/temporary'),
       ('Part-time', 'Part-time'),
       ('Internship', 'Internship/placement');

-- Add GIN indexes for expanded JSONB queries
CREATE INDEX idx_fact_job_posting_skills_gin 
ON analytics.fact_job_posting USING GIN (extracted_skills);
CREATE INDEX idx_fact_job_posting_tech_gin 
ON analytics.fact_job_posting USING GIN (extracted_technologies);
CREATE INDEX idx_fact_job_posting_salary 
ON analytics.fact_job_posting (salary_min, salary_max) 
WHERE salary_min IS NOT NULL AND salary_max IS NOT NULL;
```

---

## 7. Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **LLM cost overruns** | Unexpected GPU/CPU usage | Batch size of 10 jobs/request; monitor `docker stats`; fallback to fuzzywuzzy for 20% of jobs |
| **Model drift** | Skill extraction quality degrades over time | Quarterly re-evaluation; human spot-check (10%); track error rates in logs |
| **Source scraper failures** | Insufficient job data for analysis | Robust error handling in existing scrapers; fallback to MockSource; 3-source minimum commitment |
| **Correlation validity** | R² < 0.4 if feature space too sparse | Feature engineering: add interaction terms; ensure minimum 100 jobs with salary + tech data |
| **Dashboard performance** | Slow queries on large datasets | GIN indexes; query pagination; materialized views considered for Phase 4 |
| **Schema migration risk** | Breaking changes during migration | All new dimensions added via separate migration files; test on staging; rollback scripts |

---

## 8. Timeline (6 Weeks)

| Week | Primary Deliverable | Key Milestone |
|------|-------------------|---------------|
| 1 | **LLM Coverage** | `extracted_skills` populated for ≥ 500 jobs; GulfTalent scraper functional |
| 2 | **Skill Growth** | YoY growth rates computed for top 30 skills; `v_skill_growth` view created |
| 3 | **Salary Correlation** | Regression model with R² > 0.4; `v_salary_correlation` view created |
| 4 | **Data Sources** | 3 scrapers working (GulfTalent, Naukri Gulf, Mock); Prefect multi-source flow |
| 5 | **Dashboard (Part 1)** | "Skills Growth" + "Salary Insights" pages; both reading from enriched DB data |
| 6 | **Dashboard (Part 2)** | "Top Companies" + "City Distribution" pages; weekly Prefect flow stable |

**Buffer:** 1 week built-in for unexpected integration issues.

---

## 9. Execution Strategy

### 9.1 Week 1: LLM Coverage & GulfTalent

```bash
# Start infrastructure
cd /Users/paddykadamuthuri/projects/UAE
docker compose up -d postgres api dashboard

# Verify Phase 2 LLM extraction works
docker compose run --rm api python -c "
from src.utils.llm import extract_with_llm
result = extract_with_llm('''Extract skills as JSON array from: 
Looking for a Data Engineer with Python, SQL, AWS, and Docker experience.''')
print('Skills:', result)
"

# Run ingestion with all sources
docker compose run --rm ingestion python -m src.ingestion.main

# Test GulfTalent scraper
docker compose run --rm ingestion python -m src.ingestion.sources.gulftalent --max-pages 2
```

### 9.2 Week 2-3: Skill Growth & Correlation

```bash
# Compute skill growth rates (backend)
docker compose run --rm api python -c "
from src.database import get_db_context, FactJobPosting, FactJobPostingSnapshot
from sqlalchemy import text, func

with get_db_context() as db:
    # Compute growth rates using snapshots
    result = db.execute(text('''
        SELECT skill, growth_rate
        FROM analytics.v_skill_growth
        ORDER BY growth_rate DESC
        LIMIT 30
    ''')).fetchall()
    print(f'Top 30 skills growth rates: {len(result)} skills computed')
"

# Build correlation model
docker compose run --rm api python -c "
import pandas as pd
import numpy as np
from sqlalchemy import text

with get_db_context() as db:
    df = pd.read_sql('''
        SELECT 
            salary_min, salary_max,
            ARRAY_LENGTH(extracted_skills, 1) as skill_count,
            ARRAY_LENGTH(extracted_technologies, 1) as tech_count,
            experience_level_id,
            employment_type_id
        FROM analytics.fact_job_posting
        WHERE salary_min IS NOT NULL AND salary_max IS NOT NULL
        LIMIT 500
    ''', db.engine)

# Simple regression
X = df[['skill_count', 'tech_count']]
y = (df['salary_min'] + df['salary_max']) / 2
from sklearn.linear_model import LinearModel
model = LinearRegression()
model.fit(X, y)
r2 = model.score(X, y)
print(f'R²: {r2:.3f}')
print(f'Coefficients: skill={model.coef_[0]:.2f}, tech={model.coef_[1]:.2f}')
"
```

### 9.3 Week 4-5: Dashboard

```bash
# Run the dashboard
docker compose up -d dashboard

# Access at http://localhost:8501
# Navigate through all 5 pages:
# 1. Skills Growth (YoY rates, growth arrows, city filters)
# 2. Tech Trends (adoption trends, emerging tech)
# 3. Salary Insights (scatter plot, experience breakdown)
# 4. Top Companies (hiring profiles, velocity)
# 5. City Distribution (job distribution, heatmap)
```

### 9.4 Week 6: Verification & Polish

```bash
# Run verification tests
python -m pytest tests/ -k "phase3 or correlation or growth or salary" -v

# Check all success criteria pass
# Document any open issues for Phase 4
# Update ROADMAP.md with Phase 3 status
```

---

## 10. Rollback Plan

If Phase 3 encounters critical issues:

1. **Disable LLM enhancement**: Set `enable_llm_enrichment=False` in `.env` (flag to be added)
2. **Revert database changes**: New dimension entries can be rolled back via migration; GIN indexes can be dropped; `extracted_skills`/`extracted_technologies` columns already existed (just stop populating them)
3. **Rollback scraper changes**: Revert `gulftalent.py` and `naukrigulf.py` to last working version; keep MockSource as fallback
4. **Dashboard**: Remove new pages; revert to Phase 2 3-page layout

**Rollback is safe because:**
- New code is additive (features can be toggled off)
- Existing Phase 1 & 2 functionality fully preserved
- Migrations are reversible (dimension entries deletable, indexes dropable)

---