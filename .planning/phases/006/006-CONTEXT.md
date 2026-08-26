# Phase 6: Automated Job Intelligence & Career Assistant - Context

**Gathered:** August 26, 2026
**Status:** Ready for planning
**Mode:** Zero-cost implementation

<domain>
## Phase Boundary

Transform the UAE Job Intelligence Platform from a passive analytics tool into an **active career assistant** that automatically scrapes jobs daily, ranks the top 10 opportunities, provides ATS-friendly keywords for each listing, and enriches contacts for hiring managers. This phase focuses on **zero-cost implementation** using free APIs, local computation, and open-source tools.

</domain>

<decisions>
## Implementation Decisions

### Zero-Cost Architecture
All implementation choices prioritize zero monthly cost:
1. **Job Scraping:** RapidAPI free tier (Fantastic Jobs) + TheirStack + Lix rotated
2. **Contact Enrichment:** DIY website scraping + GitHub commits + pattern detection
3. **Scheduling:** System cron + APScheduler (Python)
4. **ATS Keywords:** Ollama + Qwen (local LLM)
5. **Recommendations:** Local computation with scikit-learn
6. **Database:** PostgreSQL (local Docker)

### Key Decisions:
1. **Mode:** Zero-cost implementation (no paid APIs)
2. **Scraping:** Rotate between 3 free RapidAPI providers (750 jobs/month total)
3. **Contact Enrichment:** DIY pattern detection + website scraping (unlimited)
4. **Scheduling:** System cron + APScheduler (no external service)
5. **ATS Keywords:** LLM-first with spaCy fallback (free)
6. **Recommendations:** Multi-factor scoring with local computation
7. **Dashboard:** Streamlit enhancements (free)

</decisions>

<code_context>
## Existing Code Insights

### Phase 1-5 Completed:
- Data pipeline with mock source
- Star schema database (12 tables)
- Deduplication engine (fuzzy matching)
- FastAPI backend with 10+ endpoints
- Streamlit admin dashboard
- LLM integration (Ollama + Qwen)
- Skill/technology extraction
- Predictive models (skill forecasting, salary prediction)
- User profiles (opt-in only)
- Sentiment analysis
- Industry classification
- Real-time monitoring
- Multi-language support
- Geospatial insights
- Community features
- MLOps baseline

### Key Files:
- src/ingestion/sources/ - Existing scrapers (Bayt, GulfTalent, NaukriGulf)
- src/intelligence/llm/ - LLM integration
- src/intelligence/pipeline.py - Intelligence pipeline
- src/api/main.py - FastAPI backend
- src/dashboard/main.py - Streamlit dashboard
- docker-compose.yml - Service orchestration
- .env - Environment variables

### Free API Providers:
1. **Fantastic Jobs (RapidAPI):** 250 jobs/month, 25 requests/month
2. **TheirStack:** 200 credits/7 days
3. **Lix:** 1000 exports/month

</code_context>

<constraints>
## Constraints

### Technical:
- Must use only free APIs and open-source tools
- No paid subscriptions or services
- Must work within Docker environment
- Must be production-ready and reliable

### Business:
- Zero monthly cost requirement
- Must comply with website terms of service
- Must respect user privacy (opt-in only)
- Must be maintainable by a single developer

### Timeline:
- 3 weeks implementation
- Week 1: Infrastructure + Scraping
- Week 2: ATS Keywords + Contact Enrichment
- Week 3: Recommendations + Dashboard

</constraints>

<success_criteria>
## Success Criteria

| Metric | Target | Measurement |
|--------|--------|-------------|
| Daily scrape completion | 100% success rate | Cron logs |
| Jobs scraped per day | ≥ 25 new jobs | Database count |
| Top 10 recommendations | Generated daily by 7 AM UAE time | Dashboard display |
| ATS keywords extracted | ≥ 90% of job listings | `ats_keywords IS NOT NULL` |
| Contact enrichment | ≥ 20% of companies have contacts | `company_contacts` table |
| Dashboard refresh | Real-time updates | < 5 second latency |
| Monthly cost | $0 | All free APIs and tools |

</success_criteria>

<risks>
## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| RapidAPI quota exceeded | Rotate between 3 free providers |
| Website blocks scraping | Rate limiting, rotating user agents |
| LLM extraction fails | spaCy fallback, retry logic |
| Data quality issues | Validation, deduplication, manual review |
| Free tier limits change | Monitor usage, have backup providers |

</risks>
