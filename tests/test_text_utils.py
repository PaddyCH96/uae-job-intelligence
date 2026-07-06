"""Unit tests for src/utils/text.py — pure logic, no DB required."""

import pytest

from src.utils.text import (
    normalize_text,
    clean_html,
    compute_content_hash,
    extract_salary_range,
    truncate_text,
    extract_email,
    extract_phone,
)


class TestNormalizeText:
    def test_lowercases_and_strips(self):
        assert normalize_text("  Data ENGINEER ") == "data engineer"

    def test_removes_special_chars(self):
        assert normalize_text("C++ / Python, SQL!") == "c python sql"

    def test_collapses_whitespace(self):
        assert normalize_text("a   b\t c\n d") == "a b c d"

    def test_empty_and_none_safe(self):
        assert normalize_text("") == ""
        assert normalize_text(None) == ""

    def test_unicode_stripped_currently(self):
        # Documents current behavior: non-ascii is stripped (potential i18n debt).
        assert normalize_text("Café") == "caf"


class TestCleanHtml:
    def test_strips_tags(self):
        assert clean_html("<p>Hello <b>World</b></p>") == "Hello World"

    def test_decodes_common_entities(self):
        assert clean_html("A&nbsp;&amp;&lt;B&gt;") == "A &<B>"

    def test_empty_safe(self):
        assert clean_html("") == ""
        assert clean_html(None) == ""


class TestContentHash:
    def test_deterministic(self):
        assert compute_content_hash("Data Engineer") == compute_content_hash("data   engineer")

    def test_length_64(self):
        assert len(compute_content_hash("anything")) == 64

    def test_empty_returns_empty(self):
        # Current behavior: empty input -> empty string (NOT a 64-char hash).
        assert compute_content_hash("") == ""


class TestExtractSalary:
    def test_aed_prefixed_with_commas(self):
        assert extract_salary_range("AED 15,000 - 25,000") == (15000.0, 25000.0, "AED")

    def test_aed_suffixed(self):
        assert extract_salary_range("15,000 - 25,000 AED") == (15000.0, 25000.0, "AED")

    def test_usd_dollar_sign(self):
        assert extract_salary_range("$3,000 - $5,000") == (3000.0, 5000.0, "USD")

    def test_no_salary(self):
        assert extract_salary_range("Competitive salary") == (None, None, None)

    def test_empty_safe(self):
        assert extract_salary_range("") == (None, None, None)

    def test_salary_without_comma_grouping(self):
        assert extract_salary_range("AED 5000 - 9000") == (5000.0, 9000.0, "AED")

    def test_single_value_salary(self):
        mn, mx, cur = extract_salary_range("AED 20,000 per month")
        assert mn == 20000.0 and cur == "AED"


class TestTruncate:
    def test_no_truncate_when_short(self):
        assert truncate_text("short", 100) == "short"

    def test_truncates_with_suffix(self):
        out = truncate_text("x" * 50, max_length=10)
        assert out.endswith("...") and len(out) <= 10


class TestExtractContact:
    def test_email(self):
        assert extract_email("reach me at a.b+c@example.co") == "a.b+c@example.co"

    def test_email_none(self):
        assert extract_email("no address here") is None

    def test_phone_international(self):
        assert extract_phone("Call +971 50 1234567 today") == "+971 50 1234567"

    def test_phone_none(self):
        assert extract_phone("no phone") is None
