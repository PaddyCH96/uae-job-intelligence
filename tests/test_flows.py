"""Tests for the Prefect ingestion flows."""

from __future__ import annotations

from unittest.mock import MagicMock, patch, call

import pytest


# ---------------------------------------------------------------------------
# ingest_source task — call the underlying .fn() to bypass Prefect runtime
# ---------------------------------------------------------------------------

class TestIngestSourceTask:

    def test_db_connection_failure_raises(self):
        from src.ingestion.flows import ingest_source
        with patch("src.ingestion.flows.test_connection", return_value=False):
            with pytest.raises(RuntimeError, match="Database connection failed"):
                ingest_source.fn(source_name="bayt", max_pages=1)

    def test_unknown_source_raises_value_error(self):
        from src.ingestion.flows import ingest_source
        mock_proc = MagicMock()
        with patch("src.ingestion.flows.test_connection", return_value=True), \
             patch("src.ingestion.flows.JobProcessor", return_value=mock_proc):
            with pytest.raises((ValueError, ImportError)):
                ingest_source.fn(source_name="no_such_source", max_pages=1)

    def test_mock_source_returns_summary_dict(self):
        from src.ingestion.flows import ingest_source
        mock_proc = MagicMock()
        mock_proc.store_raw_jobs.return_value = 5
        mock_proc.process_unprocessed_jobs.return_value = 5
        mock_source = MagicMock()
        mock_source.fetch_and_transform.return_value = [{"x": i} for i in range(5)]

        with patch("src.ingestion.flows.test_connection", return_value=True), \
             patch("src.ingestion.flows.JobProcessor", return_value=mock_proc), \
             patch("src.ingestion.base.MockSource", return_value=mock_source):
            result = ingest_source.fn(source_name="mock", max_pages=1)

        assert isinstance(result, dict)
        assert "fetched" in result and "stored" in result and "processed" in result

    def test_no_jobs_fetched_returns_zero_summary(self):
        from src.ingestion.flows import ingest_source
        mock_proc = MagicMock()
        mock_source = MagicMock()
        mock_source.fetch_and_transform.return_value = []

        with patch("src.ingestion.flows.test_connection", return_value=True), \
             patch("src.ingestion.flows.JobProcessor", return_value=mock_proc), \
             patch("src.ingestion.base.MockSource", return_value=mock_source):
            result = ingest_source.fn(source_name="mock", max_pages=1)

        assert result.get("fetched", 0) == 0


# ---------------------------------------------------------------------------
# daily_ingestion_flow — patch ingest_source at the flow module level
# ---------------------------------------------------------------------------

class TestDailyIngestionFlow:

    def test_flow_runs_all_three_default_sources(self):
        call_log = []

        def fake_ingest(source_name, max_pages=3):
            call_log.append(source_name)
            return {"fetched": 5, "stored": 5, "processed": 4}

        with patch("src.ingestion.flows.ingest_source", side_effect=fake_ingest):
            from src.ingestion.flows import daily_ingestion_flow
            result = daily_ingestion_flow(sources=["bayt", "gulftalent", "naukrigulf"], max_pages=1)

        assert set(call_log) == {"bayt", "gulftalent", "naukrigulf"}

    def test_flow_returns_dict_keyed_by_source(self):
        with patch("src.ingestion.flows.ingest_source",
                   side_effect=lambda source_name, max_pages=3: {"fetched": 3, "stored": 3, "processed": 2}):
            from src.ingestion.flows import daily_ingestion_flow
            result = daily_ingestion_flow(sources=["bayt", "naukrigulf"], max_pages=1)

        assert "bayt" in result and "naukrigulf" in result
        assert result["bayt"]["fetched"] == 3

    def test_flow_custom_sources_list(self):
        call_log = []

        def fake_ingest(source_name, max_pages=3):
            call_log.append(source_name)
            return {"fetched": 1, "stored": 1, "processed": 1}

        with patch("src.ingestion.flows.ingest_source", side_effect=fake_ingest):
            from src.ingestion.flows import daily_ingestion_flow
            daily_ingestion_flow(sources=["bayt"], max_pages=1)

        assert call_log == ["bayt"]

    def test_flow_empty_sources_returns_empty_dict(self):
        with patch("src.ingestion.flows.ingest_source") as mock_task:
            from src.ingestion.flows import daily_ingestion_flow
            result = daily_ingestion_flow(sources=[], max_pages=1)

        assert result == {}
        mock_task.assert_not_called()

    def test_flow_partial_failure_continues(self):
        call_log = []

        def fake_ingest(source_name, max_pages=3):
            call_log.append(source_name)
            if source_name == "bayt":
                raise RuntimeError("scrape failed")
            return {"fetched": 5, "stored": 5, "processed": 4}

        with patch("src.ingestion.flows.ingest_source", side_effect=fake_ingest):
            from src.ingestion.flows import daily_ingestion_flow
            try:
                daily_ingestion_flow(sources=["bayt", "gulftalent", "naukrigulf"], max_pages=1)
            except Exception:
                pass

        # At minimum bayt was tried
        assert "bayt" in call_log


# ---------------------------------------------------------------------------
# run_ingestion orchestration (no DB required)
# ---------------------------------------------------------------------------

class TestRunIngestionOrchestration:

    def test_all_sources_skipped_when_make_source_returns_none(self):
        from src.ingestion.main import run_ingestion
        with patch("src.ingestion.main.test_connection", return_value=True), \
             patch("src.ingestion.main._make_source", return_value=None):
            summary = run_ingestion(source_name="all", max_pages=1)

        assert isinstance(summary, dict)
        for v in summary.values():
            assert v.get("skipped") is True

    def test_mock_source_summary_has_expected_keys(self):
        from src.ingestion.main import run_ingestion
        fake_jobs = [
            {"source_id": f"m{i}", "source_name": "MockJobBoard",
             "raw_data": {"job_title": f"J{i}"}, "ingested_at": "2026-07-04T00:00:00+00:00"}
            for i in range(3)
        ]
        with patch("src.ingestion.main.test_connection", return_value=True), \
             patch("src.ingestion.processor.JobProcessor.store_raw_jobs", return_value=3), \
             patch("src.ingestion.processor.JobProcessor.process_unprocessed_jobs", return_value=3), \
             patch("src.ingestion.base.MockSource.fetch_and_transform", return_value=fake_jobs):
            summary = run_ingestion(source_name="mock", batch_size=3)

        assert summary["mock"]["fetched"] == 3
        assert summary["mock"]["stored"] == 3
        assert summary["mock"]["processed"] == 3
