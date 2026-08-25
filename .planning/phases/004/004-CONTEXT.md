# Phase 4: Version 2 — Predictive Capabilities - Context

**Gathered:** August 26, 2026
**Status:** Ready for planning
**Mode:** Auto-generated from PLAN_PHASE4.md

<domain>
## Phase Boundary

Build predictive intelligence capabilities that forecast future skill demands and salary trends, and enable basic user personalization. Version 2 shifts the platform from descriptive analytics ("what is happening") to predictive analytics ("what will happen"), while exploring a basic user profile system aligned with open-source principles.

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion
All implementation choices are at Claude's discretion — using PLAN_PHASE4.md as the spec. Use Phase 3 completion status, codebase conventions, and success criteria to guide decisions.

### Key Decisions from PLAN_PHASE4.md:
1. **Mode:** Vertical MVP slices (feature-based, not horizontal)
2. **LLM Model:** Continue using qwen2.5-coder:7b (already working)
3. **Predictive Models:** scikit-learn for regression, PyCaret optional
4. **Sentiment Analysis:** LLM-based (qwen2.5-coder:7b)
5. **Industry Classification:** Rule-based + LLM fallback
6. **User Profiles:** Opt-in only, soft migration (feature flag)
7. **Dashboard:** Streamlit with 5+ pages, < 3s load time
8. **Orchestration:** Prefect for monthly retraining
9. **MLOps:** Lightweight model versioning, drift detection

</decisions>

<code_context>
## Existing Code Insights

### Phase 3 Completed:
- 100% LLM enrichment coverage (30/30 jobs)
- Skill growth rates view (v_skill_growth_rates)
- Salary correlation view (v_salary_correlation)
- Tech salary averages view (v_tech_salary_avg)
- Company hiring view (v_company_hiring)
- City distribution view (v_city_distribution)

### Key Files:
- src/utils/llm.py — LLM wrapper (ready for sentiment/classification)
- src/ingestion/llm_enrichment.py — Batch enrichment pipeline
- src/ingestion/processor.py — Job processing with LLM
- migrations/004_phase2_views.sql — Phase 2 views
- migrations/005_phase3_views.sql — Phase 3 views
- tests/test_phase2.py — 11 tests (all passing)
- tests/test_phase3.py — 10 tests (all passing)

</code_context>

<specifics>
## Specific Ideas

### Slice 1: Predictive Models & Forecasting
- Train skill demand forecasting model (3-month horizon)
- Train salary prediction model
- Create v_skill_forecast and v_salary_prediction views
- Compute R², MAE, RMSE metrics

### Slice 2: User Profile System (Opt-In)
- Design user profile schema (opt-in only)
- Profile CRUD API (POST /profile, GET /profile)
- Personalized skill gap analysis
- Privacy & opt-out mechanism

### Slice 3: Sentiment & Industry Classification
- Sentiment analysis using LLM (score -1 to 1)
- Industry classification (tech, finance, gov, education, consulting, others)
- Automate classification for all jobs
- Dashboard filters for sentiment/industry

### Slice 4: Advanced Reporting & Performance
- Custom report generation framework (PDF/CSV)
- Dashboard performance optimization (< 3s load)
- Model versioning baseline
- Data drift detection

### Slice 5: Orchestration & MLOps Basics
- Prefect flow for monthly model retraining
- Model artifact storage
- Data drift detection flow
- Full-stack error handling

</specifics>

<deferred>
## Deferred Ideas

- Real-time predictive models (batch retraining monthly)
- Paid API integrations (government data deferred to Phase 5)
- Community features (profiles, sharing — Phase 5)
- Full MLOps pipeline (CI/CD for models — Phase 5)
- Mobile application responsiveness

</deferred>
