# Phase 4 Plan: Version 2 — Predictive Capabilities

**phase:** 4
**mode:** mvp (vertical feature slices)
**status:** planned
**start-date:** 2026-10-14
**derived-from-research:** RESEARCH.md (Phase 2), PLAN_PHASE3.md (Phase 3)
**prerequisite-phase:** 3

---

## 1. Phase Overview

**Objective:** Build predictive intelligence capabilities that forecast future skill demands and salary trends, and enable basic user personalization. Version 2 shifts the platform from descriptive analytics ("what is happening") to predictive analytics ("what will happen"), while exploring a basic user profile system aligned with open-source principles.

**Success Criteria (Phase 4):**
- ✅ Predictive models for skill demand forecasting (3-month horizon)
- ✅ Salary trend predictions with confidence intervals
- ✅ Basic user profile system (open-source compatible, opt-in only)
- ✅ Personalized skill gap analysis for registered users
- ✅ Sentiment analysis on job descriptions (positive/negative indicators)
- ✅ Industry classification automation (Categorize into tech, finance, gov, etc.)
- ✅ Advanced reporting: custom report generation
- ✅ Performance optimizations: dashboard load < 3s, query caching
- ✅ MLOps basics: model versioning baseline, data drift detection

**Non-Goals (Phase 4):**
- ❌ Real-time predictive models (batch retraining monthly)
- ❌ Paid API integrations (government data deferred to Phase 5)
- ❌ Community features (profiles, sharing — Phase 5)
- ❌ Full MLOps pipeline (CI/CD for models — Phase 5)
- ❌ Mobile application responsiveness

---

## 2. Success Metrics (Derived from RESEARCH.md + Roadmap)

| Metric | Target | Measurement |
|--------|--------|-------------|
| Skill demand forecast accuracy | MAE < 15% (vs actual future data) | Compare model predictions to actual hiring data at 3-month interval |
| Salary prediction MAE | AED 3,000 or 10% (whichever lower) | Mean absolute error on holdout test set |
| User profile adoption | ≥ 10% of active users opt-in | `SELECT COUNT(*) FROM user_profiles WHERE opt_in = True / total_active_users` |
| Sentiment analysis accuracy | > 80% vs manual baseline | Spot-check 100 job descriptions |
| Industry classification coverage | ≥ 80% of jobs classified | `industry IS NOT NULL / total active jobs` |
| Dashboard load time | < 3s (cached) | `Streamlit load_time` monitoring |
| Model drift detection | Alert if > 10% feature shift | Monthly retraining trigger |

---

## 3. Task Plan (Vertical MVP Slices)

### Slice 1: Predictive Models & Forecasting
| Task | Owner | Dependencies | Deliverable |
|------|-------|--------------|-------------|
| T1.1 Train skill demand forecasting model | data-science | Phase 3 enriched data, skill growth rates | PyCaret/PMML model: future skill demand (3-month) |
| T1.2 Train salary prediction model | data-science | Phase 3 correlation model | PyCaret model: salary given skills/level/tech |
| T1.3 3-month forward forecast SQL | database | T1.1, T1.2 | `SELECT skill, predicted_demand, confidence FROM v_skill_forecast` |
| T1.4 Model evaluation & holdout test | data-science | T1.1, T1.2 | R², MAE, RMSE reported per model |

**Definition of Done:** Both models trained; SQL view created; evaluation metrics computed.

---

### Slice 2: User Profile System (Opt-In, Open-Source Compatible)
| Task | Owner | Dependencies | Deliverable |
|------|-------|--------------|-------------|
| T2.1 Design user profile schema (opt-in only) | backend | open-source principles | `user_profiles` table (optional schema, no mandatory columns) |
| T2.2 Profile: save/load user preferences | backend | T2.1 | API: `POST /profile`, `GET /profile` (opt-in only) |
| T2.3 Personalized skill gap analysis | frontend + backend | T1.2, T2.1 | "You are missing: Python, AWS vs current skills" |
| T2.3 Privacy & opt-out mechanism | backend | T2.1, legal review | User can delete profile, data anonymized |

**Definition of Done:** Schema designed; profile CRUD API; gap analysis working; opt-out verified.

---

### Slice 3: Sentiment & Industry Classification
| Task | Owner | Dependencies | Deliverable |
|------|-------|--------------|-------------|
| T3.1 Sentiment analysis model (Qwen 3 8B) | data-science / backend | Phase 2 LLM infrastructure | `sentiment_score` (-1 to 1) per job description |
| T3.2 Industry classification (rule-based + LLM) | backend | T3.1, existing job descriptions | `industry` field: tech, finance, government, education, consulting, others |
| T3.3 Automate classification for all jobs | backend | T3.1, T3.2 | `UPDATE fact_job_posting SET industry = ...` |
| T3.4 Dashboard: Sentiment & Industry filters | frontend | T3.2, database views | Filter jobs by sentiment/industry |

**Definition of Done:** Sentiment scores populated; industry classifications assigned; dashboard filters working.

---

### Slice 4: Advanced Reporting & Performance
| Task | Owner | Dependencies | Deliverable |
|------|-------|--------------|-------------|
| T4.1 Custom report generation framework | backend | T3.2, T3.3 | API: `POST /reports` with filter params; returns PDF/CSV |
| T4.2 Dashboard performance optimization | frontend | all slices | Lazy loading, query caching, CDN for charts |
| T4.3 Model versioning baseline | data-science | T1.1, T1.2 | Track model artifacts, retraining triggers |
| T4.4 Data drift detection (simple) | data-science | T1.1, T1.2 | Monthly: compare feature distributions, alert if shift > 10% |

**Definition of Done:** Custom reports working; dashboard < 3s load; versioning tracked; drift detection in place.

---

### Slice 5: Orchestration & MLOps Basics
| Task | Owner | Dependencies | Deliverable |
|------|-------|--------------|-------------|
| T5.1 Prefect flow for monthly model retraining | orchestration | T1.1, T1.2, T3.1 | Scheduled flow: 1st of month, retrain, compare to baseline |
| T5.2 Model artifact storage | data-science | T1.1, T1.2 | `models/` directory with version tags |
| T5.3 Data drift detection flow | orchestration | T5.1 | Monthly comparison, email alert if drift detected |
| T5.4 Full-stack error handling | full-stack | all slices | Graceful degradation if models unavailable |

**Definition of Done:** Monthly retraining flow; model artifacts; drift detection; error handling.

---

## 4. Vertical vs Horizontal Organization

This phase continues **vertical MVP mode** — tasks organized as feature slices ensuring end-to-end delivery per feature.

**Slice example (T1.1–T1.4):**
- Data Science: train two models (skill demand, salary)
- Backend: SQL views for forecasts
- Evaluation: R², MAE computed
- All integrated and tested end-to-end

**Benefits:**
- Each feature delivers tangible value (forecasts, profiles, classifications)
- Clear boundaries between predictive and descriptive features
- Easier to toggle off predictive features if needed

**If horizontal mode were used:**
- All models trained first → All views created → All frontend pages
- Longer time to first predictive feature working
- Harder to validate each predictive feature independently

---

## 5. Verification Loop

### 5.1 Verification Commands

```bash
# Run Phase 4 verification tests
cd /Users/paddykadamuthuri/projects/UAE
python -m pytest tests/ -k "phase4 or prediction or sentiment or industry or profile" -v

# Verify predictive models
docker compose exec postgres psql -U jobs_admin -d uae_jobs -c "
SELECT * FROM analytics.v_skill_forecast LIMIT 5;
SELECT * FROM analytics.v_salary_prediction LIMIT 5;
"

# Verify sentiment & industry
docker compose exec postgres psql -U jobs_admin -d uae_jobs -c "
SELECT 
  industry,
  COUNT(*) as count,
  AVG(sentiment_score) as avg_sentiment
FROM analytics.fact_job_posting
WHERE is_active = True
GROUP BY industry;
"

# Verify dashboard load time
open http://localhost:8501
# Time page loads; should be < 3s with caching

# Verify user profile (opt-in only, no data without consent)
# Check that no user data exists without opt-in
```

### 5.2 Verification Criteria (PASS/FAIL)

| Check | Pass Condition | Fail Action |
|-------|---------------|-------------|
| Skill forecast model | Trained; `v_skill_forecast` view returns data | Check training data coverage; simplify model features |
| Salary prediction model | Trained; `v_salary_prediction` view returns data | Check salary data sufficiency; feature engineer more |
| User profiles | Opt-in only; no data without consent | Verify API doesn't persist without opt-in flag |
| Sentiment accuracy | > 80% vs manual baseline (spot-check) | Re-tune prompts; human-in-the-loop for 20% |
| Industry classification | ≥ 80% of jobs have industry assigned | Check LLM output format; add rule-based fallback |
| Dashboard load | < 3s with caching enabled | Optimize queries; add Streamlit caching (@st.cache_data) |
| Model drift detection | Can compare monthly feature distributions | Implement simple KS-test or distribution comparison |

---

## 6. Dependencies

### 6.1 Python Dependencies (requirements.txt)

Add to existing requirements:
```text
# Data science & ML
scikit-learn >= 1.4.0  # regression, model evaluation
pycaret >= 3.0.0  # simplified model training/experimentation
mlflow >= 2.5.0  # model versioning baseline (lightweight)

# Sentiment & classification
nltk >= 3.8.0  # text preprocessing
spacy >= 3.7.0  # NLP if needed (optional, can use Ollama directly)

# Already installed
plotly >= 5.1.0
pandas >= 2.2.0
numpy >= 1.24.0
```

### 6.2 Infrastructure

- Ollama + Qwen 3 8B running (Phase 2 prerequisite, for sentiment/classification)
- PyCaret installed (`pip install pycaret`)
- MLflow tracking URI configured (optional, lightweight local)
- PostgreSQL with additional columns: `sentiment_score`, `industry` (added via migration)
- Optional: Redis for drift detection cache

### 6.3 New Database Migrations (Phase 4)

Add these migration files under `migrations/`:
```sql
-- Add industry dimension
INSERT INTO analytics.dim_industry (industry_name, industry_description)
VALUES ('Technology', 'IT, software, data, AI roles'),
       ('Finance', 'Banking, insurance, financial services'),
       ('Government', 'Public sector, regulatory, policy'),
       ('Education', 'Academic, training, edTech roles'),
       ('Consulting', 'Consulting, advisory, services'),
       ('Others', 'Other industries');

-- Add sentiment and industry to fact table (nullable, default NULL)
ALTER TABLE analytics.fact_job_posting 
ADD COLUMN sentiment_score NUMERIC(3, 2) DEFAULT NULL;

ALTER TABLE analytics.fact_job_posting 
ADD COLUMN industry_id INTEGER 
REFERENCES analytics.dim_industry(industry_id) DEFAULT NULL;

-- Add user profiles table (optional, created only if opt-in enabled)
-- This is a "soft" migration — table only created if feature flag enabled
-- CREATE TABLE user_profiles (
--   user_id UUID PRIMARY KEY,
--   opt_in BOOLEAN DEFAULT False,
--   created_at TIMESTAMP DEFAULT NOW(),
--   skills_interests TEXT[],
--   salary_expectation_min NUMERIC,
--   salary_expectation_max NUMERIC
-- );
```

---

## 7. Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Model quality too low** | MAE too high for practical use | Feature engineering; ensure minimum 500 jobs with complete features; consider simpler statistical models (ARIMA) alongside ML |
| **User privacy concerns** | Opt-in adoption low; legal issues | Explicit opt-in UI; one-click opt-out; no data without consent; anonymized storage only |
| **Sentiment model bias** | Consistent positive/negative misclassification | Human baseline evaluation (100 jobs); prompt engineering; toggle off if accuracy < 70% |
| **Industry classification errors** | Mis-categorized jobs affecting filters | Rule-based fallback + LLM; manual review of borderline cases; toggle classification off if accuracy < 75% |
| **Drift detection false positives** | Unnecessary monthly retraining wastes resources | Threshold configurable; require > 10% shift across multiple features; human review before triggering |
| **Dashboard performance** | 3s target not met with additional data | Lazy loading; query caching (@st.cache_data); CDN for chart assets; pagination |

---

## 8. Timeline (7 Weeks)

| Week | Primary Deliverable | Key Milestone |
|------|-------------------|---------------|
| 1 | **Predictive Models** | Skill demand + salary models trained; R²/MAE reported; holdout test complete |
| 2 | **Forecast SQL** | `v_skill_forecast` and `v_salary_prediction` views created; 3-month ahead predictions |
| 3 | **User Profiles** | Schema designed; opt-in API; CRUD working; opt-out verified; no data without consent |
| 4 | **Sentiment & Industry** | LLM sentiment scores populated; industry classifications assigned; > 80% coverage |
| 5 | **Reporting & Performance** | Custom report API working; dashboard < 3s with caching; model versioning baseline |
| 6 | **Orchestration** | Monthly retraining Prefect flow; drift detection; model artifact storage |
| 7 | **Finalization** | Bug fixes; documentation; all success criteria validated; handoff complete |

**Buffer:** 1 week built-in for unexpected integration and model evaluation issues.

---

## 9. Execution Strategy

### 9.1 Week 1: Predictive Models

```bash
# Train skill demand forecast model (PyCaret)
docker compose run --rm api python -c "
import pycaret
from src.database import get_db_context, FactJobPosting
import pandas as pd

with get_db_context() as db:
    df = pd.read_sql('''
        SELECT 
            extracted_skills,
            ARRAY_LENGTH(extracted_skills, 1) as skill_count,
            experience_level_id,
            employment_type_id,
            salary_min, salary_max
        FROM analytics.fact_job_posting
        WHERE is_active = True AND salary_min IS NOT NULL
        LIMIT 1000
    ''', db.engine)

# PyCaret setup
s = setup(data=df, target='salary_min', session_id=123)
print('PyCaret setup complete')

# Create model
lr = create_model('ridge')
print(lr)
"

# Train salary prediction model similarly
```

### 9.2 Week 2-3: User Profiles

```bash
# Create user profiles table (soft migration - only if flag enabled)
# In alembic upgrade head, check for FEATURE_FLAG_user_profiles

# Test opt-in API
docker compose run --rm api python -c "
from fastapi.testclient import TestClient
from src.api.main import app
client = TestClient(app)

# Opt-in (should create profile if not exists)
resp = client.post('/profile', json={'opt_in': True})
print('Opt-in status:', resp.status_code, resp.json())

# Get profile (should return opt-in status)
resp = client.get('/profile')
print('Profile status:', resp.status_code, resp.json())
"
```

### 9.3 Week 4-5: Sentiment & Industry

```bash
# Run LLM sentiment analysis on job descriptions
docker compose run --rm api python -c "
from src.utils.llm import extract_with_llm
import json

# Sentiment prompt
prompt = '''Analyze the job description below and return a JSON with:
- \"sentiment_score\": number between -1 (very negative) and 1 (very positive)
- \"sentiment_label\": \"positive\" | \"negative\" | \"neutral\"
- \"factors\": array of 1-3 strings explaining the sentiment

Job Description:
{description}

Return ONLY valid JSON, no prose.'''

# Test on a sample
result = extract_with_llm(prompt.format(description='''We are a fast-growing startup looking for a Rockstar Data Engineer who will change the world. Great salary, equity, and unlimited PTO. Must have Python and AWS experience.'''))
print('Sentiment result:', result)
"

# Run industry classification
docker compose run --rm api python -c "
from src.utils.llm import extract_with_llm

prompt = '''Classify this job into exactly ONE of these industries:
- Technology: IT, software, data, AI, engineering roles
- Finance: Banking, insurance, financial services, accounting  
- Government: Public sector, regulatory, policy, defense
- Education: Academic, training, edTech, teaching roles
- Consulting: Consulting, advisory, services, outsourcing
- Others: Everything else

Job Description:
{description}

Return ONLY the industry name, no prose, no explanations.'''

result = extract_with_llm(prompt.format(description='''Looking for a Data Engineer with Python, SQL, and AWS experience. Company in the fintech sector.'''))
print('Industry result:', result)
"
```

### 9.3 Week 6-7: Reporting & Orchestration

```bash
# Run custom report
docker compose run --rm api python -c "
from fastapi.testclient import TestClient
from src.api.main import app
client = TestClient(app)

resp = client.post('/reports', params={
    'filters': 'industry:Technology,salary_min:30000',
    'format': 'csv'
})
print('Report status:', resp.status_code)
print('Report preview:', resp.text[:200])
"

# Verify monthly retraining flow
docker compose up -d prefect
# Trigger manual run or wait for scheduled
```

### 9.4 Week 7: Verification & Polish

```bash
# Run verification tests
python -m pytest tests/ -k "phase4 or prediction or sentiment or industry or profile" -v

# Check all success criteria
# Document open issues for Phase 5
# Update ROADMAP.md with Phase 4 status
```

---

## 10. Rollback Plan

If Phase 4 encounters critical issues:

1. **Disable predictive models**: Set `enable_predictive_models=False` in `.env` (flag to be added)
2. **Revert database changes**: `sentiment_score`, `industry_id` columns nullable — just stop populating; drop if needed
3. **Rollback user profiles**: Table is "soft" — only created if feature flag enabled; drop table if created; all API endpoints check flag first
4. **Sentiment/industry**: Stop LLM calls; keep existing data; toggle filters off in dashboard
5. **Reporting**: Disable `FEATURE_FLAG_custom_reports`; revert to dashboard default view

**Rollback is safe because:**
- All new features are additive (feature flags control enablement)
- Existing Phase 1-3 functionality fully preserved
- No breaking schema changes (columns nullable, tables optional)

---