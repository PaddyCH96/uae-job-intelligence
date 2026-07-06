# Session Log — UAE Job Intelligence Platform

Running log of work sessions, phase by phase. Each entry records what was done, what was found, and what comes next.

---

## Session 001 — Phase 1 Validation

**Date:** 2026-07-03  
**Goal:** Validate Phase 1 as a stable foundation for Phase 2 development.  
**Duration:** ~1 session  
**Outcome:** ❌ NO-GO as-is → ✅ Conditional GO after 3 critical fixes

### What Was Done

1. **Runtime environment assessment**
   - Docker daemon not running; used local Postgres 18.3 (Postgres.app) directly.
   - Python 3.14 in use (project targets 3.11 in Docker).
   - `requirements.txt` is **not installable as pinned**: `uvicorn==0.30.1` conflicts with `prefect==2.19.4`. Discovered and logged as Major-2.
   - Installed a working dependency subset (without prefect) to enable test execution.

2. **Full static code review** — all files in `src/`, `migrations/`, `docs/`, config
   - Catalogued 3 CRITICAL bugs, 4 Major bugs, 5 Minor bugs, 3 Future Improvements.
   - Key finding: `process_unprocessed_jobs` loads ORM objects in one session, then marks them processed in a different inner session — the flag never persists, causing unbounded duplicate fact rows on every re-run.

3. **Migration validation**
   - Clean-database run: ✅ migration succeeds (`migrations/001_init_schema.sql`).
   - Re-run test: ❌ migration is **not idempotent** (fails with `relation already exists`). No rollback path.
   - All 11 tables present with correct indexes; seed data verified (4 currencies, 7 cities, 7 experience levels).
   - Constraint `check_duplicate_reference` verified to enforce `is_duplicate/duplicate_of_id` consistency.

4. **Test suite created from scratch** (`tests/` was empty)
   - `tests/conftest.py` — shared fixtures, DB availability gate, session-scoped cleanup.
   - `tests/test_text_utils.py` — 14 pure-logic tests for normalize/clean/hash/salary/contact utils.
   - `tests/test_ingestion.py` — 10 tests covering MockSource, validation, and resilience.
   - `tests/test_deduplication.py` — 8 tests for similarity scoring (no DB).
   - `tests/test_migration_schema.py` — 7 DB-backed schema/constraint/seed tests.
   - `tests/test_integration_pipeline.py` — 3 end-to-end pipeline integration tests.
   - `tests/test_api.py` — 10 API endpoint tests via FastAPI TestClient.
   - `pytest.ini` — configured.

5. **Test execution results**
   ```
   59 passed, 4 failed, 2 xfailed  (71% coverage)
   ```

   | Failure | Root cause |
   |---------|-----------|
   | `test_reingest_does_not_double_process_raw` | Session isolation bug in processor (CRITICAL-1) |
   | `test_search_route_is_shadowed_bug` | `/jobs/search` declared after `/{job_id}` (CRITICAL-2) |
   | `test_bad_uuid_returns_error` | No UUID validation on path param (Major-1) |
   | `test_removes_special_chars` | Double-space in `normalize_text` after regex strip (Minor-1) |

   XFails (bugs documented, not blockers):
   - Salary regex doesn't match comma-free numbers (`AED 5000 - 9000`)
   - Salary regex doesn't match single-value patterns (`AED 20,000 per month`)

### Decisions Made

- Validation report lives at `phase1_validation_report.md` (project root).
- Session log lives at `docs/SESSION_LOG.md` (this file).
- No Phase 2 code written — validation only, per task scope.

### Bugs Found (summary)

| ID | Severity | File | Description |
|----|----------|------|-------------|
| CRITICAL-1 | Critical | `src/ingestion/processor.py:161` | Session isolation — `raw_job.processed` never persists → duplicate facts on every re-run |
| CRITICAL-2 | Critical | `src/api/main.py:136` | `/jobs/search` shadowed by `/{job_id}` — search returns 500 |
| CRITICAL-3 | Critical | `src/database/config.py:102` | `db.execute("SELECT 1")` raw string crashes on SQLAlchemy 2.0 — ingestion cannot start |
| Major-1 | Major | `src/api/main.py:111` | No UUID validation on `job_id` — bad input returns 500 not 422 |
| Major-2 | Major | `requirements.txt` | `uvicorn==0.30.1` conflicts with `prefect==2.19.4` — fresh install fails |
| Major-3 | Major | `migrations/` | No Alembic config — no versioning, no rollback, re-run fails |
| Major-4 | Major | multiple | `datetime.utcnow()` deprecated in Python 3.12+, removed in future |
| Minor-1 | Minor | `src/utils/text.py:28` | Double space after regex strip in `normalize_text` |
| Minor-2 | Minor | `src/utils/text.py:93` | Salary regex misses comma-free and single-value patterns |
| Minor-3 | Minor | `src/ingestion/processor.py` | `fact_job_posting_snapshot` table never written |
| Minor-4 | Minor | `src/api/schemas.py` | `JobPostingResponse` missing `company_name` and `city` |
| Minor-5 | Minor | `src/database/config.py:30` | Pydantic v2 deprecated `Config` class style |

### Go / No-Go

**❌ NO-GO as-is. ✅ Conditional GO after fixing CRITICAL-1, CRITICAL-2, CRITICAL-3, Major-2.**

Estimated fix time: ~1 hour. After fixes, run `pytest` and confirm 63/63 pass before beginning Phase 2.

### Next Steps for Phase 2 (after fixes)

1. Fix the 3 critical bugs + requirements conflict.
2. Re-run `pytest` — expect 63 pass, 0 fail.
3. Initialize Alembic for migration versioning.
4. Replace `datetime.utcnow()` globally.
5. Add `company_name`/`city` to `JobPostingResponse`.
6. Begin Phase 2: real data sources (LinkedIn/Indeed/Bayt scraper).

---

*Add new sessions below this line, following the same format.*
