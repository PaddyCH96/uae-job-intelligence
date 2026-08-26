# STATE.md — UAE Job Intelligence Platform

## Current State

**Milestone:** v1.0 — Full Platform Delivery
**Current Phase:** Phase 6 (Planned)
**Status:** 📋 Ready for Execution

---

## Phase Progress

| Phase | Status | Notes |
|-------|--------|-------|
| 1. MVP | ✅ Complete | Data pipeline, star schema, dedup, API, dashboard |
| 2. Intelligence Gen | ✅ Complete | LLM integration working, 50 jobs enriched, 11/11 tests passing |
| 3. V1: AI Insights | ✅ Complete | Skill growth rates, salary correlation views, 10/10 tests passing |
| 4. V2: Predictive | ✅ Complete | Predictive models, user profiles, sentiment, industry, 10/10 tests passing |
| 5. Stretch Goals | ✅ Complete | Real-time, multi-language, geospatial, community, MLOps, 10/10 tests passing |
| 6. Automated Intelligence | 🔄 In Progress | Daily scraping, ATS keywords, contact enrichment, recommendations |

---

## Completed Phases

- **Phase 1:** ✅ Complete (July 2024) — MVP with data pipeline, star schema, deduplication, API, dashboard
- **Phase 2:** ✅ Complete (August 2026) — LLM integration with Ollama, skill/technology extraction
- **Phase 3:** ✅ Complete (August 2026) — Skill growth rates, salary correlation views, expanded data
- **Phase 4:** ✅ Complete (August 2026) — Predictive models, user profiles, sentiment analysis, industry classification
- **Phase 5:** ✅ Complete (August 2026) — Real-time monitoring, multi-language support, geospatial insights, community features, MLOps baseline

---

## Blockers/Concerns

- Phase 4 requires predictive model training (scikit-learn)
- Data source expansion (GulfTalent, Naukri Gulf) deferred to Phase 4

---

## Recent Decisions

1. **LLM Model:** Using qwen2.5-coder:7b instead of qwen3:8b (already available, faster)
2. **Enrichment Pipeline:** Batch processing with rate limiting (0.5s between requests)
3. **Database Views:** Created 12 views for analytics (v_tech_trends, v_skill_growth_rates, v_salary_correlation, v_skill_forecast, v_salary_prediction, v_geo_distribution, v_critical_data, etc.)
4. **Skill Growth:** Using YoY growth rates with trend categories (growing/stable/declining/new)
5. **Salary Correlation:** Using v_salary_correlation view with skill_count and tech_count
6. **Predictive Models:** scikit-learn RandomForest for skill forecasting, Ridge for salary prediction
7. **User Profiles:** Opt-in only with soft migration (feature flag)
8. **Sentiment Analysis:** LLM-based scoring (-1 to 1)
9. **Industry Classification:** 6 categories (Technology, Finance, Government, Education, Consulting, Others)
10. **Multi-Language:** Arabic/English detection and skill extraction
11. **Geospatial:** District-level insights with UAE districts mapping
12. **Community:** Opt-in only sharing and saved searches
13. **MLOps:** Model versioning with MLflow-style tracking

---

## Files Created/Modified

### Phase 2 Artifacts
- `src/utils/llm.py` — LLM integration wrapper
- `src/ingestion/llm_enrichment.py` — Batch enrichment pipeline
- `src/ingestion/processor.py` — Added LLM methods
- `migrations/004_phase2_views.sql` — Database views (6 views)
- `tests/test_phase2.py` — 11 verification tests (all passing)

### Phase 3 Artifacts
- `migrations/005_phase3_views.sql` — 5 new views (skill growth, salary correlation, tech salary, company hiring, city distribution)
- `tests/test_phase3.py` — 10 verification tests (all passing)

### Phase 4 Artifacts
- `src/models/skill_forecast.py` — Skill demand forecasting model
- `src/models/salary_predictor.py` — Salary prediction model
- `migrations/006_phase4_models.sql` — Database schema (industry, sentiment, user profiles, forecast views)
- `tests/test_phase4.py` — 10 verification tests (all passing)
- `models/skill_forecast_v1.pkl` — Trained skill forecast model
- `models/salary_predictor_v1.pkl` — Trained salary predictor model

### Phase 5 Artifacts
- `src/realtime/monitor.py` — Real-time monitoring with PostgreSQL LISTEN/NOTIFY
- `src/utils/multilang.py` — Multi-language support (Arabic/English)
- `src/utils/geospatial.py` — Geospatial insights with UAE districts
- `src/community/manager.py` — Community features (opt-in sharing)
- `src/mlops/versioning.py` — MLOps model versioning
- `migrations/007_phase5_stretch.sql` — Database schema (districts, community, real-time views)
- `tests/test_phase5.py` — 10 verification tests (all passing)
- `models/metadata.json` — Model version metadata

### Documentation
- `PLAN.md` — Phase 2 execution plan
- `RESEARCH.md` — LLM integration research
- `PLAN_PHASE3.md` — Phase 3 plan (complete)
- `PLAN_PHASE4.md` — Phase 4 plan (complete)
- `PLAN_PHASE5.md` — Phase 5 plan (complete)
- `.planning/ROADMAP.md` — GSD roadmap (all phases complete)
- `.planning/STATE.md` — GSD state tracker
- `.planning/config.json` — GSD configuration

---

## Next Actions

1. Execute Phase 5: Stretch Goals (Optional)
   - Real-time data processing
   - Multi-language support (Arabic/English)
   - Geospatial district-level insights
   - Community sharing features
2. Implement GulfTalent and Naukri Gulf scrapers (if not done in Phase 3)
3. Complete 5-page dashboard with all analytics views