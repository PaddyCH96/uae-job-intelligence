# Phase 4 Plan: Version 2 — Predictive Capabilities

**phase:** 4
**mode:** mvp (vertical feature slices)
**status:** in_progress
**start-date:** 2026-08-26
**derived-from-research:** PLAN_PHASE4.md (Phase 4 spec)
**prerequisite-phase:** 3

---

## 1. Phase Overview

**Objective:** Build predictive intelligence capabilities that forecast future skill demands and salary trends, and enable basic user personalization.

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

---

## 2. Task Plan (Vertical MVP Slices)

### Slice 1: Predictive Models & Forecasting
| Task | Status | Deliverable |
|------|--------|-------------|
| T1.1 Train skill demand forecasting model | 📋 Planned | scikit-learn model: future skill demand (3-month) |
| T1.2 Train salary prediction model | 📋 Planned | scikit-learn model: salary given skills/level/tech |
| T1.3 Create forecast SQL views | 📋 Planned | `v_skill_forecast`, `v_salary_prediction` views |
| T1.4 Model evaluation & holdout test | 📋 Planned | R², MAE, RMSE reported per model |

**Definition of Done:** Both models trained; SQL views created; evaluation metrics computed.

### Slice 2: User Profile System (Opt-In)
| Task | Status | Deliverable |
|------|--------|-------------|
| T2.1 Design user profile schema | 📋 Planned | `user_profiles` table (opt-in only) |
| T2.2 Profile CRUD API | 📋 Planned | `POST /profile`, `GET /profile` endpoints |
| T2.3 Personalized skill gap analysis | 📋 Planned | "You are missing: Python, AWS" |
| T2.4 Privacy & opt-out mechanism | 📋 Planned | User can delete profile, data anonymized |

**Definition of Done:** Schema designed; profile CRUD API; gap analysis working; opt-out verified.

### Slice 3: Sentiment & Industry Classification
| Task | Status | Deliverable |
|------|--------|-------------|
| T3.1 Sentiment analysis model (LLM) | 📋 Planned | `sentiment_score` (-1 to 1) per job |
| T3.2 Industry classification | 📋 Planned | `industry` field: tech, finance, etc. |
| T3.3 Automate classification for all jobs | 📋 Planned | `UPDATE fact_job_posting SET industry = ...` |
| T3.4 Dashboard: Sentiment & Industry filters | 📋 Planned | Filter jobs by sentiment/industry |

**Definition of Done:** Sentiment scores populated; industry classifications assigned; dashboard filters working.

### Slice 4: Advanced Reporting & Performance
| Task | Status | Deliverable |
|------|--------|-------------|
| T4.1 Custom report generation framework | 📋 Planned | API: `POST /reports` with filter params; returns PDF/CSV |
| T4.2 Dashboard performance optimization | 📋 Planned | Lazy loading, query caching, CDN for charts |
| T4.3 Model versioning baseline | 📋 Planned | Track model artifacts, retraining triggers |
| T4.4 Data drift detection (simple) | 📋 Planned | Monthly: compare feature distributions, alert if shift > 10% |

**Definition of Done:** Custom reports working; dashboard < 3s load; versioning tracked; drift detection in place.

### Slice 5: Orchestration & MLOps Basics
| Task | Status | Deliverable |
|------|--------|-------------|
| T5.1 Prefect flow for monthly model retraining | 📋 Planned | Scheduled flow: 1st of month, retrain, compare to baseline |
| T5.2 Model artifact storage | 📋 Planned | `models/` directory with version tags |
| T5.3 Data drift detection flow | 📋 Planned | Monthly comparison, email alert if drift detected |
| T5.4 Full-stack error handling | 📋 Planned | Graceful degradation if models unavailable |

**Definition of Done:** Monthly retraining flow; model artifacts; drift detection; error handling.

---

## 3. Verification Commands

```bash
# Run Phase 4 verification tests
python -m pytest tests/ -k "phase4 or prediction or sentiment or industry or profile" -v

# Verify predictive models
docker exec uae-jobs-postgres psql -U jobs_admin -d uae_jobs -c "
SELECT * FROM analytics.v_skill_forecast LIMIT 5;
SELECT * FROM analytics.v_salary_prediction LIMIT 5;
"

# Verify sentiment & industry
docker exec uae-jobs-postgres psql -U jobs_admin -d uae_jobs -c "
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
```

---

## 4. Success Metrics

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Skill demand forecast accuracy | MAE < 15% | Not trained | 📋 Planned |
| Salary prediction MAE | AED 3,000 or 10% | Not trained | 📋 Planned |
| User profile adoption | ≥ 10% opt-in | 0% | 📋 Planned |
| Sentiment analysis accuracy | > 80% | Not implemented | 📋 Planned |
| Industry classification coverage | ≥ 80% | 0% | 📋 Planned |
| Dashboard load time | < 3s | ~5s (estimated) | 📋 Planned |
| Model drift detection | Alert if > 10% | Not implemented | 📋 Planned |
