# ROADMAP.md — UAE Job Intelligence Platform

## Milestone: v1.0 — Full Platform Delivery

**Total Phases:** 5
**Completed:** 4 (Phase 1, Phase 2, Phase 3, Phase 4)
**Status:** In Progress

---

## Phases

### Phase 1: Minimum Viable Intelligence Engine
- **Status:** ✅ Complete
- **Goal:** Data collection pipeline, star schema database, deduplication, basic API, dashboard
- **Success Criteria:** All services start with `docker compose up`, mock data ingestion works, 85% dedup threshold met
- **Completed:** July 2024

### Phase 2: Intelligence Generation
- **Status:** ✅ Complete
- **Goal:** Ollama + Qwen 3 8B LLM integration, skill/technology extraction, trend analysis, dashboard enhancements
- **Success Criteria:** LLM integration working, ≥ 50 jobs enriched with skills/technologies, trend analysis views created
- **Completed:** August 2026
- **Reference:** RESEARCH.md, PLAN.md, tests/test_phase2.py

### Phase 3: Version 1 — AI-Driven Insights
- **Status:** ✅ Complete
- **Goal:** Skill growth rates, technology-salary correlation, expanded data sources (GulfTalent, Naukri Gulf), 5-page dashboard
- **Success Criteria:** LLM coverage ≥ 80% of jobs, skill growth rates YoY, correlation R² > 0.4, 3 new scrapers functional
- **Completed:** August 2026
- **Reference:** PLAN_PHASE3.md, tests/test_phase3.py

### Phase 4: Version 2 — Predictive Capabilities
- **Status:** ✅ Complete
- **Goal:** Predictive models (skill demand forecasting, salary prediction), user profiles (opt-in), sentiment analysis, industry classification, advanced reporting, MLOps basics
- **Success Criteria:** Skill demand + salary models trained, R²/MAE reported, user profile opt-in API, sentiment scores ≥ 80% accuracy
- **Completed:** August 2026
- **Reference:** PLAN_PHASE4.md, tests/test_phase4.py

### Phase 5: Stretch Goals (Experimental / Optional)
- **Status:** 📋 Planned
- **Goal:** Real-time critical data points, multi-language (Arabic/English) support, geospatial district-level insights, community sharing (opt-in), MLOps maturity baseline
- **Success Criteria:** Feature flags in .env, real-time widgets (< 5s latency), language detection ≥ 50% Arabic/English
- **Reference:** PLAN_PHASE5.md

---

## Phase Dependencies

| From Phase | To Phase | Key Enabler |
|------------|----------|-------------|
| 1 (MVP) | 2 (Intelligence Gen) | LLM integration (Ollama + Qwen 3 8B) |
| 2 | 3 (V1: AI Insights) | LLM enrichment coverage ≥ 80% of jobs |
| 3 | 4 (V2: Predictive) | Predictive models trained; R²/MAE computed |
| 4 | 5 (Stretch Goals) | All Phase 4 success criteria met; resources available |