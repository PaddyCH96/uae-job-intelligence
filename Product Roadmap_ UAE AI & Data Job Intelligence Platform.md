# Product Roadmap: UAE AI & Data Job Intelligence Platform

## 1. Introduction

This document outlines the strategic product roadmap for the UAE AI & Data Job Intelligence Platform. It details the planned evolution of the platform across different versions, providing a high-level overview of key features and initiatives. This roadmap serves to guide our development efforts and communicate the future direction to all stakeholders. It is a living document, and we expect it to be updated as the project progresses and new insights emerge.

## 2. Audience

This roadmap is a vital resource for several groups. **Human developers** will use it to understand the long-term vision and prioritize their development tasks effectively. **AI coding agents** will find it useful for understanding the phased delivery of features, allowing them to align their development efforts with the project's strategic goals. Ultimately, it fosters a shared understanding of the project's future direction and key milestones for everyone involved.

## 3. Phase Structure

The platform evolves across 5 phases, each building upon the previous one. Phases 1-4 are **MVP mode** (vertical feature slices, guaranteed delivery). Phase 5 is **modular/stretch** (optional features via feature flags).

### Phase 1: Minimum Viable Intelligence Engine (Complete)
- **Status:** ✅ Complete (July 2024)
- **Focus:** Data collection pipeline, star schema database, deduplication, basic API, dashboard
- **Deliverables:** Mock data ingestion, deduplication engine (85% threshold), PostgreSQL raw+analytics, FastAPI 10+ endpoints, Streamlit dashboard, Docker Compose
- **Reference:** PROJECT.md, CONTEXT.md, BUILD.md

### Phase 2: Intelligence Generation (Planned)
- **Status:** 📋 Planned, ready for execution (August 2026)
- **Focus:** Ollama + Qwen 3 8B LLM integration, skill/technology extraction, trend analysis, dashboard enhancements
- **Deliverables:** RESEARCH.md + PLAN.md created; 11 verification tests written; Ollama integration; LLM enrichment pipeline; 5 new dashboard pages; Prefect weekly insights flow
- **Reference:** RESEARCH.md, PLAN.md, tests/test_phase2.py

### Phase 3: Version 1 — AI-Driven Insights (Planned)
- **Status:** 📋 Planned (September 2026)
- **Focus:** Skill growth rates, technology-salary correlation, expanded data sources (GulfTalent, Naukri Gulf), 5-page dashboard
- **Deliverables:** PLAN_PHASE3.md created; LLM coverage ≥ 80% of jobs; skill growth rates YoY; correlation R² > 0.4; 3 new scraper functional; dashboard: Skills Growth, Salary Insights, Tech Trends
- **Reference:** PLAN_PHASE3.md

### Phase 4: Version 2 — Predictive Capabilities (Planned)
- **Status:** 📋 Planned (October 2026)
- **Focus:** Predictive models (skill demand forecasting, salary prediction), user profiles (opt-in), sentiment analysis, industry classification, advanced reporting, MLOps basics
- **Deliverables:** PLAN_PHASE4.md created; skill demand + salary models trained; R²/MAE reported; user profile opt-in API; sentiment scores ≥ 80% accuracy; industry classification ≥ 80% coverage; dashboard < 3s load; monthly retraining Prefect flow; custom report API
- **Reference:** PLAN_PHASE4.md

### Phase 5: Stretch Goals (Experimental / Optional)
- **Status:** 📋 Planned (January 2027) — dependent on resources
- **Focus:** Real-time critical data points, multi-language (Arabic/English) support, geospatial district-level insights, community sharing (opt-in), MLOps maturity baseline
- **Deliverables:** PLAN_PHASE5.md created; feature flags in .env; real-time widgets (< 5s latency); language detection ≥ 50% Arabic/English; geospatial district view; opt-in share/save API; MLflow model versioning; CI pipeline for model testing
- **Reference:** PLAN_PHASE5.md

---

## 4. Product Evolution

### 3.1 Minimum Viable Product (MVP) — Phase 1
Our MVP focuses on establishing the core data pipeline and delivering foundational job market insights. The primary goal is to demonstrate end-to-end data ingestion, transformation, and basic visualization of UAE job market data.

**Key Features:**
- Automated job data collection from multiple sources
- Smart duplicate detection (85% similarity threshold)
- Normalized data storage with historical snapshots
- REST API for data access
- Interactive admin dashboard

### 3.2 Version 1 (V1) — Phase 2
Builds upon the MVP by introducing AI-driven insights and enhancing data coverage. Goal: actionable intelligence on skill growth, technology-salary impact, refined market trends, powered by local LLMs.

**Key Features:**
- Ollama + Qwen 3 8B integration for LLM-powered extraction
- LLM-powered extraction and standardization of skills and technologies
- Skill growth rates over time analysis
- Technology-salary correlation models
- Enhanced dashboard with interactive charts
- Expanded data sources (GulfTalent, Naukri Gulf)
- Improved data quality checks within Prefect flows

### 3.3 Version 2 (V2) — Phase 3
Shifts focus towards predictive capabilities, user personalization, and further refinement of intelligence. Goal: predictive insights into future job market trends and personalized career development.

**Key Features:**
- Predictive models for forecasting future skill demands and salary trends
- Basic user profile system (opt-in only, open-source compatible)
- Personalized skill recommendations based on career goals
- Additional data sources (government labor stats, educational course data — Phase 5)
- Advanced AI models for sentiment analysis, industry classification
- Custom report generation
- Performance optimizations for large-scale data processing

### 3.4 Stretch Goals — Phase 5
Aspirational features that depend on available resources and project evolution.

**Key Features:**
- Real-time data processing for critical data points only
- Multi-language job posting analysis (Arabic/English)
- Granular geospatial insights at district/neighborhood level
- Community features: insight sharing, bookmarking, saved searches (opt-in)
- MLOps practices: model versioning, CI/CD baseline, monitoring dashboards

---

## 5. Phase Transition Summary

| From Phase | To Phase | Key Enabler |
|------------|----------|-------------|
| 1 (MVP) | 2 (Intelligence Gen) | LLM integration (Ollama + Qwen 3 8B) |
| 2 | 3 (V1: AI Insights) | LLM enrichment coverage ≥ 80% of jobs |
| 3 | 4 (V2: Predictive) | Predictive models trained; R²/MAE computed |
| 4 | 5 (Stretch Goals) | All Phase 4 success criteria met; resources available |

---

## 6. Development Principles (Across All Phases)

1. **No Breaking Changes** — Always migrate, never destroy
2. **Environment Variables** — Zero hardcoded config; feature flags for optional features
3. **Structured Logging** — Every event is queryable via structlog
4. **Docker First** — No "works on my machine"; all services via `docker compose up`
5. **Documentation** — Every decision is recorded in markdown
6. **Feature Flags** — Optional features (Phase 5) controlled via `.env` flags
7. **Local-First Development** — Everything runs via Docker; no external APIs required (Phase 2-4)
8. **Open Source Stack** — No paid APIs or proprietary dependencies (core mission)

---

## 7. Key Decisions & Rationale

**Why PostgreSQL over MongoDB?**
- Need for ACID transactions
- Rich querying with JSONB support
- Better for analytical workloads

**Why FastAPI over Flask?**
- Async support for scalability
- Auto-generated API documentation
- Type safety with Pydantic

**Why Streamlit over React?**
- Rapid development for internal tools
- Python-native (no context switching)
- Easy deployment

**Why Fuzzy Matching over ML (Phase 1)?**
- Phase 1 focuses on reliability over sophistication
- Fuzzy matching is deterministic and debuggable
- ML deduplication planned for Phase 2

**Why Local LLMs (Phases 2-5)?**
- No API costs (free, local Ollama)
- Data never leaves infrastructure (privacy)
- UAE context: Arabic/English code-switching supported
- Full control over model versioning and deployment

**Why Vertical MVP Mode (Phases 1-4)?**
- Faster end-to-end feedback per feature
- Clearer "done" criteria per feature
- Reduced context switching between layers

**Why Modular Mode (Phase 5)?**
- Aspirational features not core to mission
- Resources limited; features may not all be ready simultaneously
- Different stakeholders prioritize differently
- Opt-in/out respects user autonomy

---

## 8. Environment Variables

See `.env.example` for all configuration options.

**Critical Settings:**
- `POSTGRES_*` — Database connection
- `DEDUP_SIMILARITY_THRESHOLD` — Duplicate detection (default: 0.85)
- `LOG_LEVEL` — Logging verbosity
- `API_PORT` / `DASHBOARD_PORT` — Service ports
- `FEATURE_FLAG_*` — Phase 5 optional features (real-time, multi-language, geospatial, community, MLOps)

**Phase 5 Feature Flags (add to `.env`):**
```
FEATURE_FLAG_real_time_critical=false
FEATURE_FLAG_multi_language=false
FEATURE_FLAG_geospatial=false
FEATURE_FLAG_community_sharing=false
FEATURE_FLAG_mlops_baseline=false
```

---

## 9. Testing Strategy

### Phase 1:
- Manual testing via dashboard
- API smoke tests with curl
- Mock data for development

### Phase 2:
- pytest for unit tests (11 Phase 2 tests written)
- Integration tests for pipelines
- Mock data for LLM development

### Phase 3+
- pytest test suites per phase
- Model evaluation (R², MAE, RMSE)
- Holdout test sets for predictive models
- User acceptance testing (opt-in features)
- Performance load testing (dashboard response times)

### Phase 5:
- Feature flag gate testing (each slice enabled/disabled)
- Multi-language benchmark (Arabic vs English accuracy)
- Geospatial data validation (district counts vs known UAE areas)
- Community sharing opt-in/out verification
- MLOps CI pipeline passing

---

## 10. Known Limitations (Across All Phases)

1. **Single Source (Phase 1)** — Only mock data initially; real sources added in Phase 2+
2. **No Authentication (Phases 1-3)** — API open; authentication Phase 4+
3. **Synchronous Processing (Phases 1-3)** — Batch processing only; real-time Phase 5 optional
4. **Limited Search (Phases 1-3)** — Basic SQL LIKE matching; full-text search enhancements Phase 4+
5. **No Caching (Phases 1-3)** — Direct database queries; caching Phase 4+ (Redis, CDN)
6. **UAE-Only Scope** — All phases maintain UAE focus; no global expansion

---

## 11. Success Metrics (Overall Project)

| Milestone | Phase | Metric | Target |
|-----------|-------|--------|--------|
| Phase 1 Complete | 1 | All services start with `docker compose up` | ✅ Complete |
| Phase 2 Complete | 2 | LLM integration, ≥ 50 jobs enriched | 📋 Planned |
| Phase 3 Complete | 3 | Skill growth rates, correlation R² > 0.4 | 📋 Planned |
| Phase 4 Complete | 4 | Predictive models, user profiles, sentiment ≥ 80% | 📋 Planned |
| Phase 5 Complete | 5 | Real-time, multi-language, geospatial (optional) | 📋 Planned |

---

## 12. Roadmap Visualization

```
UAE Job Intelligence Platform Evolution
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Phase 1:     MVP                          [Complete] July 2024
           │
           ▼
Phase 2:   Intelligence Generation        [Planned]  August 2026
           │
           ▼
Phase 3:   Version 1 — AI Insights        [Planned]  September 2026
           │
           ▼
Phase 4:   Version 2 — Predictive         [Planned]  October 2026
           │
           ▼
Phase 5:   Stretch Goals (Experimental)   [Planned]  January 2027
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 13. Contact & Support

This is an internal project. For questions:
- Review existing `.md` documentation files
- Check `docs/` directory for detailed guides
- Consult phase-specific PLAN.md files for implementation details
- Feature flags controlled via `.env`; consult Project Lead for enabling/disabling

---

*Last Updated: August 26, 2026*