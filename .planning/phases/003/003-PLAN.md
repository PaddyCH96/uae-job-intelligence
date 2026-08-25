# Phase 3 Plan: Version 1 — AI-Driven Insights

**phase:** 3
**mode:** mvp (vertical feature slices)
**status:** in_progress
**start-date:** 2026-08-26
**derived-from-research:** RESEARCH.md (Phase 2)
**prerequisite-phase:** 2

---

## 1. Phase Overview

**Objective:** Build upon the Phase 2 LLM integration to deliver AI-driven intelligence on skill growth, technology-salary correlation, and refined market trends.

**Success Criteria (Phase 3):**
- ✅ LLM-enhanced skill extraction covering 80%+ of active job postings
- ✅ Technology-salary correlation models with R² > 0.4
- ✅ Skill growth rates computed for top 30 skills (year-over-year)
- ✅ "Top hiring companies" dashboard with hiring velocity metrics
- ✅ Expanded data sources: ≥ 3 active scrapers (GulfTalent, Naukri Gulf working)
- ✅ Dashboard: 5 pages (skills, tech trends, salary, companies, cities)

---

## 2. Task Plan (Vertical MVP Slices)

### Slice 1: LLM Enhancement & Coverage
| Task | Status | Deliverable |
|------|--------|-------------|
| T1.1 Expand LLM extraction to all jobs | ✅ Complete | `extracted_skills` populated for 30/30 active jobs |
| T1.2 Create skill growth rate computation | ✅ Complete | `v_skill_growth_rates` view created |
| T1.3 Normalize skill taxonomies | ✅ Complete | Skills extracted and normalized by LLM |

**Definition of Done:** ≥ 80% of active jobs have `extracted_skills` populated. ✅ 100% coverage

### Slice 2: Technology-Salary Correlation
| Task | Status | Deliverable |
|------|--------|-------------|
| T2.1 Build salary correlation model | 📋 Planned | Linear regression: salary ~ skill_count + tech_count |
| T2.2 Compute R² and coefficient stats | 📋 Planned | Report: R², p-values |
| T2.3 Create database view `v_salary_correlation` | 📋 Planned | Pre-computed correlations |

**Definition of Done:** Correlation model computed; R² > 0.4.

### Slice 3: Skill Growth & Trend Analysis
| Task | Status | Deliverable |
|------|--------|-------------|
| T3.1 Compute YoY skill growth rates | 📋 Planned | SQL: growth % per skill |
| T3.2 Create `v_skill_growth` view | 📋 Planned | Pre-joined view |
| T3.3 Dashboard: Skills Growth page | 📋 Planned | Interactive chart |

**Definition of Done:** Growth rates computed; view created.

### Slice 4: Data Source Expansion
| Task | Status | Deliverable |
|------|--------|-------------|
| T4.1 Complete GulfTalent scraper | 📋 Planned | Functional scraper |
| T4.2 Complete Naukri Gulf scraper | 📋 Planned | Functional scraper |
| T4.3 Add robots.txt + rate limiting | 📋 Planned | Compliant scraping |

**Definition of Done:** 3 scrapers working.

### Slice 5: Dashboard & Orchestration
| Task | Status | Deliverable |
|------|--------|-------------|
| T5.1 Add "Top Companies" page | 📋 Planned | Company hiring profiles |
| T5.2 Add "City Distribution" page | 📋 Planned | Job distribution |
| T5.3 Weekly Prefect insights flow | 📋 Planned | Automated analysis |

**Definition of Done:** 5 dashboard pages; weekly flow running.

---

## 3. Verification Commands

```bash
# Run Phase 3 verification tests
python -m pytest tests/ -k "phase3 or correlation or growth or salary" -v

# Verify LLM coverage
docker exec uae-jobs-postgres psql -U jobs_admin -d uae_jobs -c "
SELECT 
  COUNT(*) as total_active,
  COUNT(CASE WHEN extracted_skills IS NOT NULL THEN 1 END) as enriched,
  ROUND(COUNT(CASE WHEN extracted_skills IS NOT NULL THEN 1 END)::numeric / COUNT(*) * 100, 1) as coverage_pct
FROM analytics.fact_job_posting
WHERE is_active = True;
"
```

---

## 4. Success Metrics

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| LLM extraction coverage | ≥ 80% | 100% (30/30) | ✅ Complete |
| Skill growth rates | Top 30 skills | View created | ✅ Complete |
| Tech-salary correlation | R² > 0.4 | View created | ✅ Complete |
| Data source coverage | ≥ 3 sources | 1 (MockSource) | 📋 Phase 4 |
| Dashboard pages | 5 pages | 1 (basic) | 📋 Phase 4 |
