# Phase 5 Plan: Stretch Goals (Experimental / Optional)

**phase:** 5
**mode:** experimental (modular, not MVP)
**status:** in_progress
**start-date:** 2026-08-26
**derived-from-research:** PLAN_PHASE5.md (Phase 5 spec)
**prerequisite-phase:** 4

---

## 1. Phase Overview

**Objective:** Explore aspirational features that extend the platform's capabilities beyond the core MVP path. These goals depend on available resources, project evolution, and stakeholder alignment with open-source principles.

**Success Criteria (Phase 5 - Stretch):**
- ✅ Real-time data processing pipeline prototype (critical data points only)
- ✅ Job postings analysis in Arabic and English (UAE official languages)
- ✅ Granular geospatial insights at district/metro level
- ✅ Community features: insight sharing, bookmarking, saved searches (opt-in only)
- ✅ MLOps practices: model versioning, CI/CD baseline, monitoring dashboards
- ✅ Multi-language job description processing (Arabic English code-switching)

---

## 2. Task Plan (Modular / Optional Slices)

### Slice 1: Real-Time Data Processing (Critical Points Only)
| Task | Status | Deliverable |
|------|--------|-------------|
| T1.1 Identify critical data points | 📋 Planned | List of 5-10 metrics needing real-time updates |
| T1.2 PostgreSQL change detection | 📋 Planned | pg_notify/pg_listen for key table changes |
| T1.3 Real-time dashboard widgets | 📋 Planned | Streamlit widgets with < 5s latency |
| T1.4 Real-time Prefect flow | 📋 Planned | Daily flow for critical changes |

**Definition of Done:** Critical data points update in < 5s; real-time widgets functional.

### Slice 2: Multi-Language Support (Arabic/English)
| Task | Status | Deliverable |
|------|--------|-------------|
| T2.1 Language detection | 📋 Planned | `language` column on raw_data.job_postings |
| T2.2 Arabic skill extraction | 📋 Planned | LLM extraction for Arabic/English code-switched |
| T2.3 Bilingual skill taxonomy | 📋 Planned | dim_skill entries in both languages |
| T2.4 Dashboard language filter | 📋 Planned | Filter jobs by language |

**Definition of Done:** Language detection working; Arabic skill extraction functional.

### Slice 3: Geospatial Insights (District-Level)
| Task | Status | Deliverable |
|------|--------|-------------|
| T3.1 Extract UAE districts | 📋 Planned | List of 20+ UAE districts/areas |
| T3.2 Geo-distribution SQL view | 📋 Planned | analytics.v_geo_distribution |
| T3.3 Interactive geo-map widget | 📋 Planned | Folium/Plotly choropleth map |
| T3.4 District-level trend analysis | 📋 Planned | Growth rate per district YoY |

**Definition of Done:** District list populated; geo view created; map widget functional.

### Slice 4: Community Features (Opt-In, Minimal)
| Task | Status | Deliverable |
|------|--------|-------------|
| T4.1 Save/Share job insights | 📋 Planned | POST /insights/share (opt-in) |
| T4.2 Saved searches | 📋 Planned | POST /searches/save |
| T4.3 Insight browsing | 📋 Planned | Streamlit page for saved insights |
| T4.4 Privacy & data deletion | 📋 Planned | User can delete all shared insights |

**Definition of Done:** Share/search API working; opt-in gated; deletion verified.

### Slice 5: MLOps Baseline & Monitoring
| Task | Status | Deliverable |
|------|--------|-------------|
| T5.1 Model versioning with MLflow | 📋 Planned | mlflow ui accessible; models tagged |
| T5.2 GitHub Actions for model testing | 📋 Planned | CI pipeline for model testing |
| T5.3 Model monitoring dashboard | 📋 Planned | Grafana/Prometheus metrics |
| T5.4 Retraining scheduler | 📋 Planned | Prefect flow for monthly retraining |

**Definition of Done:** MLflow accessible; CI pipeline passing; dashboard showing model health.

---

## 3. Verification Commands

```bash
# Check feature flags
grep -E "FEATURE_FLAG_" .env

# Run verification for enabled slices
python -m pytest tests/ -k "phase5 or multi_lang or geo or community or mlops" -v

# Check real-time latency
docker exec uae-jobs-postgres psql -U jobs_admin -d uae_jobs -c "
SELECT * FROM analytics.v_critical_data LIMIT 5;
"

# Check multi-language coverage
docker exec uae-jobs-postgres psql -U jobs_admin -d uae_jobs -c "
SELECT language, COUNT(*) as count
FROM raw_data.job_postings
WHERE is_active = True
GROUP BY language;
"

# Check geospatial data
docker exec uae-jobs-postgres psql -U jobs_admin -d uae_jobs -c "
SELECT * FROM analytics.v_geo_distribution LIMIT 10;
"
```

---

## 4. Success Metrics

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Real-time pipeline critical data | < 5s latency | Not implemented | 📋 Planned |
| Multi-language coverage | ≥ 50% Arabic/English | 0% | 📋 Planned |
| Geospatial precision | District-level view | Not implemented | 📋 Planned |
| Community feature adoption | ≥ 10% opt-in | 0% | 📋 Planned |
| MLOps maturity | MLflow + CI baseline | Not implemented | 📋 Planned |

---

## 5. Feature Flags

All slices can be enabled/disabled via feature flags in `.env`:

```
FEATURE_FLAG_real_time_critical=true
FEATURE_FLAG_multi_language=true
FEATURE_FLAG_geospatial=true
FEATURE_FLAG_community_sharing=true
FEATURE_FLAG_mlops_baseline=true
```

Any slice can be disabled without affecting others or the core platform.
