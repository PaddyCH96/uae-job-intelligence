"""Unit tests for the deduplication scoring logic (no DB required).

compute_similarity() only reads attributes off the two objects, so we use
lightweight stand-ins rather than real ORM rows.
"""

from types import SimpleNamespace

from src.deduplication.engine import DeduplicationEngine


def make_job(title, company_id, location_id, description, content_hash="h"):
    return SimpleNamespace(
        job_title=title,
        company_id=company_id,
        location_id=location_id,
        job_description=description,
        content_hash=content_hash,
        job_posting_id="id-" + title,
    )


class TestComputeSimilarity:
    def setup_method(self):
        self.engine = DeduplicationEngine(similarity_threshold=0.85)

    def test_exact_hash_match_is_one(self):
        a = make_job("Data Engineer", 1, 1, "desc", content_hash="SAME")
        b = make_job("Totally Different", 1, 2, "other", content_hash="SAME")
        assert self.engine.compute_similarity(a, b) == 1.0

    def test_different_company_is_zero(self):
        a = make_job("Data Engineer", 1, 1, "desc", content_hash="A")
        b = make_job("Data Engineer", 2, 1, "desc", content_hash="B")
        assert self.engine.compute_similarity(a, b) == 0.0

    def test_identical_posting_scores_high(self):
        a = make_job("Data Engineer", 1, 1, "Build data pipelines with python and sql", "A")
        b = make_job("Data Engineer", 1, 1, "Build data pipelines with python and sql", "B")
        score = self.engine.compute_similarity(a, b)
        assert score >= 0.85

    def test_same_company_different_role_scores_low(self):
        a = make_job("Data Engineer", 1, 1, "pipelines etl warehouse", "A")
        b = make_job("Marketing Manager", 1, 2, "brand campaigns social media", "B")
        score = self.engine.compute_similarity(a, b)
        assert score < 0.85

    def test_none_description_is_safe(self):
        a = make_job("Data Engineer", 1, 1, None, "A")
        b = make_job("Data Engineer", 1, 1, None, "B")
        # Should not raise; title+location carry the score.
        score = self.engine.compute_similarity(a, b)
        assert 0.0 <= score <= 1.0


class TestWeighting:
    def test_weights_sum_to_one(self):
        # Guards against silent reweighting that would shift the threshold meaning.
        engine = DeduplicationEngine()
        a = make_job("X", 1, 1, "same text here", "A")
        b = make_job("X", 1, 1, "same text here", "B")
        # identical title(1.0)+location(1.0)+desc(~1.0) -> ~1.0 total
        assert engine.compute_similarity(a, b) > 0.98
