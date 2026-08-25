# Phase 3: Version 1 — AI-Driven Insights - Context

**Gathered:** August 26, 2026
**Status:** Ready for planning
**Mode:** Auto-generated from PLAN_PHASE3.md

<domain>
## Phase Boundary

Build upon the Phase 2 LLM integration to deliver AI-driven intelligence on skill growth, technology-salary correlation, and refined market trends. Version 1 transforms the platform from a descriptive analytics engine into a predictive intelligence platform, using local LLMs to enable deeper analysis of the UAE data/AI job market.

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion
All implementation choices are at Claude's discretion — using PLAN_PHASE3.md as the spec. Use Phase 2 completion status, codebase conventions, and success criteria to guide decisions.

### Key Decisions from PLAN_PHASE3.md:
1. **Mode:** Vertical MVP slices (feature-based, not horizontal)
2. **LLM Model:** Continue using qwen2.5-coder:7b (already working)
3. **Correlation:** Linear regression with scikit-learn
4. **Dashboard:** Streamlit with 5 pages
5. **Orchestration:** Prefect for weekly insights flow

</decisions>

<code_context>
## Existing Code Insights

### Phase 2 Completed:
- LLM integration working (src/utils/llm.py)
- 50 jobs ingested, 10 enriched with skills/technologies
- Database views created (v_tech_trends, v_skill_trends, etc.)
- 11/11 tests passing

### Key Files:
- src/utils/llm.py — LLM wrapper
- src/ingestion/llm_enrichment.py — Batch enrichment
- src/ingestion/processor.py — Job processing
- migrations/004_phase2_views.sql — Database views
- tests/test_phase2.py — Phase 2 tests

</code_context>

<specifics>
## Specific Ideas

### Slice 1: LLM Enhancement & Coverage
- Expand LLM extraction to all 50 jobs (currently 10 enriched)
- Create skill growth rate computation
- Normalize skill taxonomies

### Slice 2: Technology-Salary Correlation
- Build linear regression model
- Compute R² and coefficient stats
- Create v_salary_correlation view

### Slice 3: Skill Growth & Trend Analysis
- Compute YoY skill growth rates
- Create v_skill_growth view
- Dashboard: Skills Growth page

### Slice 4: Data Source Expansion
- Complete GulfTalent scraper
- Complete Naukri Gulf scraper
- Add robots.txt + rate limiting

### Slice 5: Dashboard & Orchestration
- Add "Top Companies" page
- Add "City Distribution" page
- Weekly Prefect insights flow

</specifics>

<deferred>
## Deferred Ideas

- Predictive forecasting (Phase 4)
- User profiles (Phase 4)
- Real-time processing (Phase 5)
- Multi-language support (Phase 5)

</deferred>
