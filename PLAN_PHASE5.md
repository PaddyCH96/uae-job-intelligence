# Phase 5 Plan: Stretch Goals

**phase:** 5
**mode:** experimental (modular, not MVP — these are aspirational)
**status:** planned
**start-date:** 2027-01-15
**derived-from-research:** RESEARCH.md (Phase 2), PLAN_PHASE3.md (Phase 3), PLAN_PHASE4.md (Phase 4)
**prerequisite-phase:** 4
**mvp-mode:** false (stretch goals are optional, not core MVP path)

---

## 1. Phase Overview

**Objective:** Explore aspirational features that extend the platform's capabilities beyond the core MVP path. These goals depend on available resources, project evolution, and stakeholder alignment with open-source principles. Phase 5 represents the "moonshot" phase — features that could significantly enhance the platform but are not required for core functionality.

**Success Criteria (Phase 5 - Stretch):**
- ✅ Real-time data processing pipeline prototype (critical data points only)
- ✅ Job postings analysis in Arabic and English (UAE official languages)
- ✅ Granular geospatial insights at district/metro level (Dubai Marina, Abu Dhabi Al Nahyan, etc.)
- ✅ Community features: insight sharing, bookmarking, saved searches (opt-in only)
- ✅ MLOps practices: model versioning, CI/CD baseline, monitoring dashboards
- ✅ Multi-language job description processing (Arabic English code-switching)
- ✅ Positive user feedback on new features (qualitative surveys)

**Non-Goals (Phase 5 - explicitly optional):**
- ❌ Real-time data processing at full pipeline scale (only critical data points)
- ❌ Paid API integrations (government labor stats, educational course data — deferred)
- ❌ Full community social network (simple sharing/booking only)
- ❌ Mobile application (responsive web only)
- ❌ 100% model accuracy (MLOps baseline + continuous improvement mindset)

---

## 2. Success Metrics (Derived from Roadmap Stretch Goals)

| Metric | Target | Measurement |
|--------|--------|-------------|
| Real-time pipeline critical data | < 5s latency for top 10 critical metrics | `docker stats` monitoring; Prometheus alerts |
| Multi-language coverage | ≥ 50% of new postings in Arabic/English | `SELECT COUNT(*) FROM raw_data.job_postings WHERE language IN ('ar','en')` |
| Geospatial precision | District-level job distribution | `SELECT district, COUNT(*) FROM analytics.v_geo_distribution` |
| Community feature adoption | ≥ 10% of active users opt-in (if community enabled) | User opt-in tracking (if community feature flag enabled) |
| MLOps maturity | Model versioning + CI/CD baseline established | `mlflow experiments` count; GitHub Actions for model testing |
| Multi-language processing | Accurate skill extraction ≥ 70% in Arabic | Manual benchmark vs automated extraction |
| User satisfaction | ≥ 80% positive on new features (survey) | Optional survey after feature release |

---

## 3. Task Plan (Modular / Optional Slices)

Since Phase 5 is experimental/not MVP, tasks are organized as modular slices that can be enabled/disabled via feature flags.

### Slice 1: Real-Time Data Processing (Critical Points Only)
| Task | Owner | Dependencies | Deliverable |
|------|-------|--------------|-------------|
| T1.1 Identify "critical data points" for real-time | product | stakeholder input | List of 5-10 metrics needing real-time updates (e.g., salary spikes, skill shortages) |
| T1.2 Real-time PostgreSQL change detection | database | Phase 4 enriched data | `pg_notify`/`pg_listen` for key table changes; trigger dashboard refresh |
| T1.3 Real-time dashboard widgets | frontend | T1.2 | Streamlit: "Skill Shortage Alert", "Salary Spike" widget with < 5s latency |
| T1.4 Real-time Prefect flow | orchestration | T1.2 | Daily flow: check for critical changes, push to dashboard |

**Definition of Done:** Critical data points update in < 5s; real-time widgets functional; Prefect flow operational.

---

### Slice 2: Multi-Language Support (Arabic/English)
| Task | Owner | Dependencies | Deliverable |
|------|-------|--------------|-------------|
| T2.1 Language detection on ingested jobs | backend | Phase 2 ingestion | `language` column on `raw_data.job_postings`; `detect()` from langdetect or similar |
| T2.2 Arabic skill extraction via LLM | backend | Phase 2 LLM, T2.1 | `extract_with_llm()` speaking Arabic/English code-switched; JSON skills output |
| T2.3 Bilingual skill taxonomy | data-science | T2.2 | `dim_skill` entries in both Arabic and English; mapping table |
| T2.4 Dashboard: Language filter | frontend | T2.2, T3.1 | Filter jobs by language: Arabic, English, Both |

**Definition of Done:** Language detection working; Arabic skill extraction functional; dashboard filter working.

---

### Slice 3: Geospatial Insights (District-Level)
| Task | Owner | Dependencies | Deliverable |
|------|-------|--------------|-------------|
| T3.1 Extract UAE districts from job locations | backend | Phase 3 enriched data | List of 20+ UAE districts/areas (Dubai Marina, Abu Dhabi Al Jimi, etc.) |
| T3.2 Geo-distribution SQL view | database | T3.1 | `analytics.v_geo_distribution`: jobs by district, city, count, trends |
| T3.3 Interactive geo-map widget | frontend | T3.2 | Streamlit: Folium/Plotly choropleth map of UAE job distribution |
| T3.4 District-level trend analysis | backend | T3.1, Phase 3 snapshots | SQL: growth rate per district YoY |

**Definition of Done:** District list populated; geo view created; map widget functional; trends computed.

---

### Slice 4: Community Features (Opt-In, Minimal)
| Task | Owner | Dependencies | Deliverable |
|------|-------|--------------|-------------|
| T4.1 Save/Share job insights (opt-in) | backend | open-source principles | `POST /insights/share` (requires opt-in); stores user_id + selected job IDs + notes |
| T4.2 Saved searches (opt-in) | backend | T4.1 | `POST /searches/save`; user-defined search criteria, email digest opt-in |
| T4.3 Insight browsing (opt-in only) | frontend | T4.1, T4.2 | Streamlit page: "Your saved insights", "Shared from community" (opt-in gated) |
| T4.4 Privacy & data deletion | backend | T4.1, T4.2 | User can delete all their shared insights; anonymized aggregate data only |

**Definition of Done:** Share/search API working; opt-in gated; deletion verified; no data stored without consent.

---

### Slice 5: MLOps Baseline & Monitoring
| Task | Owner | Dependencies | Deliverable |
|------|-------|--------------|-------------|
| T5.1 Model versioning with MLflow | data-science | Phase 4 models | `mlflow ui` accessible; models tagged v1.0, v2.0, etc. |
| T5.2 GitHub Actions for model testing | DevOps | T1.1, T1.2 (Phase 4) | CI pipeline: on PR, train model, compute R²/MAE, fail if regression |
| T5.3 Model monitoring dashboard | data-science | T5.1 | Grafana/Prometheus: model prediction drift, feature distribution over time |
| T5.4 Retraining scheduler | orchestration | T5.1, T5.2 | Prefect flow: 1st of month, retrain, compare to baseline, alert if drift > 10% |

**Definition of Done:** MLflow accessible; CI pipeline passing; dashboard showing model health; scheduler operational.

---

## 4. Modular Organization (Not MVP Mode)

Unlike Phases 1-4, Phase 5 uses **modular organization** — tasks are independent slices that can be enabled/disabled via feature flags. This is because:

- These are **aspirational**, not core to the platform's mission
- Resources are limited; features may not all be ready simultaneously
- Different stakeholders may prioritize different goals
- Opt-in/opt-out model respects user autonomy and open-source principles

**Feature flag examples (to be added to `.env`):**
```
FEATURE_FLAG_real_time_critical=true
FEATURE_FLAG_multi_language=true
FEATURE_FLAG_geospatial=true
FEATURE_FLAG_community_sharing=true
FEATURE_FLAG_mlops_baseline=true
```

Any slice can be disabled without affecting others or the core platform.

---

## 5. Verification Loop

### 5.1 Verification Commands (Modular — run only enabled slices)

```bash
# Check feature flags
cd /Users/paddykadamuthuri/projects/UAE
grep -E "FEATURE_FLAG_" .env

# Run verification for enabled slices only
# Example: if multi-language enabled:
python -m pytest tests/ -k "phase5 or multi_lang or geo or community or mlops" -v

# Check real-time latency
docker compose exec postgres psql -U jobs_admin -d uae_jobs -c "
SELECT * FROM analytics.v_critical_data LIMIT 5;
"

# Check multi-language coverage
docker compose exec postgres psql -U jobs_admin -d uae_jobs -c "
SELECT 
  language,
  COUNT(*) as count
FROM raw_data.job_postings
WHERE is_active = True
GROUP BY language;
"

# Check geospatial data
docker compose exec postgres psql -U jobs_admin -d uae_jobs -c "
SELECT * FROM analytics.v_geo_distribution LIMIT 10;
"

# Check MLOps status
docker compose exec postgres psql -U jobs_admin -d uae_jobs -c "
SELECT * FROM analytics.models_status LIMIT 5;
"
```

### 5.2 Verification Criteria (Per-Feature)

| Feature | Pass Condition | Fail Action |
|---------|---------------|-------------|
| Real-time critical data | < 5s latency for critical metrics widgets | Optimize queries; reduce data scope; add caching |
| Multi-language coverage | ≥ 50% of new postings detected as Arabic/English | Improve language detection; add Arabic preprocessing |
| Geospatial precision | District-level view returns data for ≥ 10 districts | Expand district list; improve location parsing |
| Community sharing | Opt-in gated; no data without consent | Review API; add opt-in validation; verify deletion |
| MLOps baseline | MLflow accessible; CI pipeline passing | Check MLflow config; fix CI pipeline; add model tests |

---

## 6. Dependencies

### 6.1 Python Dependencies (requirements.txt)

Add to existing requirements (optional, feature-gated):
```text
# Multi-language
langdetect >= 1.0.0  # language detection (optional, FEATURE_FLAG_multi_language)

# Geospatial
folium >= 0.15.0  # interactive maps (optional, FEATURE_FLAG_geospatial)
plotly >= 5.1.0  # already installed

# MLOps / Model monitoring
mlflow >= 2.5.0  # model versioning (optional, FEATURE_FLAG_mlops_baseline)
grafana_client >= 1.5.0  # dashboard optional

# Community / sharing (optional)
# No new deps — uses existing auth opt-in mechanism
```

### 6.2 Infrastructure

- Feature flags in `.env` (opt-in/opt-out per slice)
- PostgreSQL with additional columns/ tables (conditional on flags)
- Optional: Redis for real-time pub/sub (critical data points)
- Optional: MLflow server (for model versioning slice)
- Optional: Grafana/Prometheus (for monitoring slice)

### 6.3 New Database Structures (Conditional on Flags)

Conditional migrations (only applied if feature flag enabled):

```sql
-- Multi-language: language column
ALTER TABLE raw_data.job_postings ADD COLUMN language VARCHAR(2) DEFAULT 'en';

-- Geospatial: district column + geo view
ALTER TABLE raw_data.job_postings ADD COLUMN district VARCHAR(100) DEFAULT NULL;
-- Create analytics.v_geo_distribution view

-- Community: user insights table (only if FEATURE_FLAG_community_sharing)
-- CREATE TABLE user_shared_insights (
--   id UUID PRIMARY KEY,
--   user_id UUID,
--   job_id UUID,
--   notes TEXT,
--   shared BOOLEAN DEFAULT FALSE,
--   created_at TIMESTAMP DEFAULT NOW()
-- );

-- MLOps: models tracking table
-- CREATE TABLE mlflow.experiments (already in MLflow)
```

---

## 7. Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Feature flag sprawl** | Too many flags; complex state management | Document all flags in `.env.example`; group related flags; periodic cleanup |
| **Multi-language quality** | Arabic skill extraction accuracy low | Human baseline; prompt engineering; consider external Arabic NLP model; toggle off if < 70% accuracy |
| **Geospatial inaccuracies** | District misidentification affects filters | Rule-based fallback + LLM; manual review of borderline cases; accuracy threshold before enabling |
| **Community data sparsity** | Few users opt-in; feature feels empty | Opt-in UI is gentle (not modal); aggregate anonymous data still valuable; consider deferred to Phase 6 |
| **MLOps overhead** | Model monitoring adds operational burden | Lightweight baseline only; alert on significant drift only; human-in-the-loop for decisions |
| **Real-time pipeline load** | Change detection triggers too frequent | Throttle: only alert on truly critical changes; debounce notifications; manual review queue |

---

## 8. Timeline (8 Weeks — Modular, Dependent on Resources)

| Week | Primary Deliverable | Key Milestone |
|------|-------------------|---------------|
| 1 | **Feature Flags + Critical Real-Time** | Flags in `.env`; `pg_notify` listening; 1 critical dashboard widget (< 5s) |
| 2 | **Multi-Language Detection** | `language` column populated; `detect()` working on 80% of new jobs |
| 3 | **Arabic Skill Extraction** | LLM extraction functional on Arabic/English code-switched descriptions |
| 4 | **Geospatial District Mapping** | District list (≥ 20) populated; `v_geo_distribution` view created |
| 5 | **Community Share/Save (Opt-In)** | API endpoints; opt-in mechanism; deletion verified |
| 6 | **MLflow Model Versioning** | MLflow accessible; 1 model version tagged; CI pipeline passing |
| 7 | **Monitoring Dashboard** | Grafana/Prometheus: basic model health metrics; drift detection baseline |
| 8 | **Finalization** | All enabled slices verified; documentation; feature flag matrix; handoff |

**Note:** Timeline is flexible — slices can be completed in any order or skipped entirely based on resource availability.

---

## 9. Rollback Plan (Per-Slice)

Since Phase 5 is modular with feature flags, rollback is per-feature:

1. **Disable feature flag** in `.env`; restart services (`docker compose restart`)
2. **Drop conditional structures**: Only drop if flag was enabled; otherwise no-op
3. **Delete feature data**: If table/column created only when flag enabled, drop it; otherwise no-op
4. **API endpoints**: Disabled at code level (flag check); existing code unaffected

**Example rollback (real-time critical data):**
```bash
# 1. Disable flag
sed -i 's/FEATURE_FLAG_real_time_critical=true/FEATURE_FLAG_real_time_critical=false/' .env

# 2. Restart services
docker compose restart api dashboard

# 3. Drop real-time structures (if they were created)
docker compose exec postgres psql -U jobs_admin -d uae_jobs -c "
DROP VIEW IF EXISTS analytics.v_critical_data;
DROP TABLE IF EXISTS critical_data_log;
"
```

---

## 10. Stakeholder Alignment

**When to pursue Phase 5:**
- ✅ Phase 4 success criteria all met (≥ 80% of metrics)
- ✅ Stakeholder budget/time available for experimental features
- ✅ Community interest expressed in sharing/insights
- ✅ i18n (internationalization) requirements from UAE government/education stakeholders
- ✅ Data science team capacity for MLOps experimentation

**When to defer Phase 5:**
- ❌ Phase 4 metrics below threshold
- ❌ Critical security or compliance constraints
- ❌ Resource reallocation needed for Phase 4 maintenance
- ❌ Stakeholder priority shifts to immediate-market features

---