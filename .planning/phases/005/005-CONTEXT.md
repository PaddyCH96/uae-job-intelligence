# Phase 5: Stretch Goals (Experimental / Optional) - Context

**Gathered:** August 26, 2026
**Status:** Ready for planning
**Mode:** Auto-generated from PLAN_PHASE5.md

<domain>
## Phase Boundary

Explore aspirational features that extend the platform's capabilities beyond the core MVP path. These goals depend on available resources, project evolution, and stakeholder alignment with open-source principles. Phase 5 represents the "moonshot" phase — features that could significantly enhance the platform but are not required for core functionality.

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion
All implementation choices are at Claude's discretion — using PLAN_PHASE5.md as the spec. Use Phase 4 completion status, codebase conventions, and success criteria to guide decisions.

### Key Decisions from PLAN_PHASE5.md:
1. **Mode:** Experimental/Modular (not MVP — these are aspirational)
2. **Feature Flags:** All slices can be enabled/disabled via FEATURE_FLAG_* in .env
3. **Multi-Language:** Arabic/English support using langdetect + LLM
4. **Geospatial:** District-level insights using Folium/Plotly
5. **Community:** Opt-in only, minimal features (share/save)
6. **MLOps:** MLflow for model versioning, GitHub Actions for CI
7. **Real-Time:** Critical data points only, < 5s latency

</decisions>

<code_context>
## Existing Code Insights

### Phase 4 Completed:
- Skill demand forecasting model (RandomForest)
- Salary prediction model (Ridge regression)
- Industry classification (6 categories)
- User profile system (opt-in only)
- Sentiment analysis support
- All 31 tests passing

### Key Files:
- src/models/skill_forecast.py — Skill forecasting model
- src/models/salary_predictor.py — Salary prediction model
- src/utils/llm.py — LLM wrapper (ready for Arabic)
- src/ingestion/processor.py — Job processing
- migrations/006_phase4_models.sql — Phase 4 schema
- tests/test_phase4.py — Phase 4 tests

</code_context>

<specifics>
## Specific Ideas

### Slice 1: Real-Time Data Processing
- Identify critical data points (salary spikes, skill shortages)
- PostgreSQL change detection (pg_notify/pg_listen)
- Real-time dashboard widgets (< 5s latency)
- Prefect flow for daily critical changes

### Slice 2: Multi-Language Support (Arabic/English)
- Language detection on ingested jobs
- Arabic skill extraction via LLM
- Bilingual skill taxonomy
- Dashboard language filter

### Slice 3: Geospatial Insights (District-Level)
- Extract UAE districts from job locations
- Geo-distribution SQL view
- Interactive geo-map widget (Folium/Plotly)
- District-level trend analysis

### Slice 4: Community Features (Opt-In, Minimal)
- Save/Share job insights (opt-in)
- Saved searches (opt-in)
- Insight browsing (opt-in only)
- Privacy & data deletion

### Slice 5: MLOps Baseline & Monitoring
- Model versioning with MLflow
- GitHub Actions for model testing
- Model monitoring dashboard
- Retraining scheduler

</specifics>

<deferred>
## Deferred Ideas

- Real-time data processing at full pipeline scale (only critical data points)
- Paid API integrations (government labor stats, educational course data)
- Full community social network (simple sharing/booking only)
- Mobile application (responsive web only)
- 100% model accuracy (MLOps baseline + continuous improvement mindset)

</deferred>
