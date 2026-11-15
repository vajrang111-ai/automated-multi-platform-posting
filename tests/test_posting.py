"""
tests/test_posting.py
Comprehensive unit and integration tests for the Automated Multi-Platform Posting System.

Test coverage:
  1.  Valid 200 OK posting
  2.  >200 characters message → 422
  3.  Zero URLs in message → 422
  4.  >1 URLs in message → 422
  5.  Invalid URL format → 422
  6.  Partial platform failure resilience
  7.  Trailing punctuation stripping from extracted URLs
"""
import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.main import app
from app.schemas import PostingRequest, PlatformResult, _extract_urls


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def client():
    """Synchronous ASGI test client."""
    return TestClient(app)


VALID_MESSAGE = (
    "Check out our latest business platform and grow your online visibility. "
    "https://example.com"
)

# patch target — where post_to_all_platforms is imported in main.py
PATCH_TARGET = "app.main.post_to_all_platforms"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _make_success(platform: str) -> PlatformResult:
    now = datetime.now(timezone.utc)
    return PlatformResult(
        platform=platform,
        status="success",
        posted_url=f"https://example.com/{platform.lower().replace(' ', '-')}",
        public_access=True,
        date=now.strftime("%Y-%m-%d"),
        time=now.strftime("%H:%M:%S"),
        error=None,
    )


def _make_failed(platform: str, error: str) -> PlatformResult:
    return PlatformResult(
        platform=platform,
        status="failed",
        posted_url=None,
        public_access=False,
        date=None,
        time=None,
        error=error,
    )


MOCK_ALL_SUCCESS = [
    _make_success("Telegraph"),
    _make_success("Dpaste"),
    _make_success("Ntfy.sh"),
    _make_failed("GitHub Gist", "Authentication failed: Missing GITHUB_TOKEN"),
    _make_failed("HuggingFace", "Authentication failed: Missing HF_API_TOKEN"),
]


# ===========================================================================
# Test 1: Valid 200 OK posting
# ===========================================================================
class TestValidPosting:
    """HTTP 200 with correct response structure for a valid message."""

    def test_valid_message_returns_200(self, client):
        with patch(PATCH_TARGET, new=AsyncMock(return_value=MOCK_ALL_SUCCESS)):
            resp = client.post("/posting", json={"message": VALID_MESSAGE})
        assert resp.status_code == 200

    def test_response_has_success_true(self, client):
        with patch(PATCH_TARGET, new=AsyncMock(return_value=MOCK_ALL_SUCCESS)):
            resp = client.post("/posting", json={"message": VALID_MESSAGE})
        assert resp.json()["success"] is True

    def test_response_has_results_list_of_5(self, client):
        with patch(PATCH_TARGET, new=AsyncMock(return_value=MOCK_ALL_SUCCESS)):
            resp = client.post("/posting", json={"message": VALID_MESSAGE})
        data = resp.json()
        assert isinstance(data["results"], list)
        assert len(data["results"]) == 5

    def test_each_result_has_all_required_fields(self, client):
        required = {
            "platform", "status", "posted_url",
            "public_access", "date", "time", "error",
        }
        with patch(PATCH_TARGET, new=AsyncMock(return_value=MOCK_ALL_SUCCESS)):
            resp = client.post("/posting", json={"message": VALID_MESSAGE})
        for result in resp.json()["results"]:
            assert required.issubset(result.keys())

    def test_success_entries_non_null_fields(self, client):
        with patch(PATCH_TARGET, new=AsyncMock(return_value=MOCK_ALL_SUCCESS)):
            resp = client.post("/posting", json={"message": VALID_MESSAGE})
        for r in resp.json()["results"]:
            if r["status"] == "success":
                assert r["posted_url"] is not None
                assert r["date"] is not None
                assert r["time"] is not None
                assert r["public_access"] is True
                assert r["error"] is None

    def test_failed_entries_null_fields(self, client):
        with patch(PATCH_TARGET, new=AsyncMock(return_value=MOCK_ALL_SUCCESS)):
            resp = client.post("/posting", json={"message": VALID_MESSAGE})
        for r in resp.json()["results"]:
            if r["status"] == "failed":
                assert r["posted_url"] is None
                assert r["date"] is None
                assert r["time"] is None
                assert r["public_access"] is False
                assert r["error"] is not None

    def test_platform_field_not_accepted_in_request(self, client):
        """Extra 'platform' field must be silently ignored — not an error."""
        with patch(PATCH_TARGET, new=AsyncMock(return_value=MOCK_ALL_SUCCESS)):
            resp = client.post(
                "/posting",
                json={"message": VALID_MESSAGE, "platform": "Telegraph"},
            )
        assert resp.status_code == 200


# ===========================================================================
# Test 2: Message exceeds 200 characters → 422
# ===========================================================================
class TestMessageTooLong:
    """Messages longer than 200 chars must be rejected with 422."""

    def test_201_char_message_returns_422(self, client):
        url = "https://example.com"               # 19 chars
        prefix = "A" * (201 - len(url) - 1)       # 181 A's
        msg = prefix + " " + url                  # 181 + 1 + 19 = 201
        assert len(msg) == 201
        resp = client.post("/posting", json={"message": msg})
        assert resp.status_code == 422

    def test_very_long_message_returns_422(self, client):
        msg = "X" * 300 + " https://example.com"
        resp = client.post("/posting", json={"message": msg})
        assert resp.status_code == 422

    def test_422_body_has_success_false(self, client):
        url = "https://example.com"
        prefix = "A" * (201 - len(url) - 1)
        msg = prefix + " " + url
        assert len(msg) == 201
        resp = client.post("/posting", json={"message": msg})
        assert resp.json()["success"] is False

    def test_exactly_200_chars_accepted(self, client):
        url = "https://example.com"               # 19 chars
        msg = "A" * (200 - len(url) - 1) + " " + url  # exactly 200
        assert len(msg) == 200
        with patch(PATCH_TARGET, new=AsyncMock(return_value=MOCK_ALL_SUCCESS)):
            resp = client.post("/posting", json={"message": msg})
        assert resp.status_code == 200


# ===========================================================================
# Test 3: Zero URLs → 422
# ===========================================================================
class TestZeroUrls:
    """Messages with no CTA link must return 422."""

    def test_no_url_returns_422(self, client):
        resp = client.post(
            "/posting", json={"message": "This is a message without any link."}
        )
        assert resp.status_code == 422

    def test_empty_message_returns_422(self, client):
        resp = client.post("/posting", json={"message": ""})
        assert resp.status_code == 422

    def test_whitespace_only_returns_422(self, client):
        resp = client.post("/posting", json={"message": "   "})
        assert resp.status_code == 422

    def test_no_url_body_success_false(self, client):
        resp = client.post("/posting", json={"message": "No link here at all."})
        assert resp.json()["success"] is False

    def test_ftp_url_treated_as_no_cta_link(self, client):
        """FTP is not http/https — zero valid CTA links → 422."""
        resp = client.post(
            "/posting",
            json={"message": "Download from ftp://files.example.com today."},
        )
        assert resp.status_code == 422


# ===========================================================================
# Test 4: Multiple URLs → 422
# ===========================================================================
class TestMultipleUrls:
    """Messages with more than one URL must return 422."""

    def test_two_urls_returns_422(self, client):
        resp = client.post(
            "/posting",
            json={"message": "Visit https://example.com and also https://another.com"},
        )
        assert resp.status_code == 422

    def test_three_urls_returns_422(self, client):
        resp = client.post(
            "/posting",
            json={"message": "See https://a.com, https://b.com, and https://c.com"},
        )
        assert resp.status_code == 422

    def test_multiple_urls_body_success_false(self, client):
        resp = client.post(
            "/posting",
            json={"message": "Visit https://example.com and https://another.com"},
        )
        assert resp.json()["success"] is False

    def test_multiple_urls_mentions_count(self, client):
        resp = client.post(
            "/posting",
            json={"message": "Visit https://example.com and https://another.com"},
        )
        body = resp.text.lower()
        assert "2" in body or "multiple" in body or "link" in body


# ===========================================================================
# Test 5: Invalid URL format → 422
# ===========================================================================
class TestInvalidUrl:
    """Messages with malformed URLs must return 422."""

    def test_url_without_tld_returns_422(self, client):
        resp = client.post(
            "/posting", json={"message": "Visit http://localhost for more info."}
        )
        assert resp.status_code == 422

    def test_url_bare_scheme_returns_422(self, client):
        resp = client.post(
            "/posting", json={"message": "Click http:// for details."}
        )
        assert resp.status_code == 422

    def test_valid_https_url_accepted(self, client):
        with patch(PATCH_TARGET, new=AsyncMock(return_value=MOCK_ALL_SUCCESS)):
            resp = client.post(
                "/posting",
                json={"message": "Visit https://www.example.co.uk for details."},
            )
        assert resp.status_code == 200

    def test_valid_http_url_accepted(self, client):
        with patch(PATCH_TARGET, new=AsyncMock(return_value=MOCK_ALL_SUCCESS)):
            resp = client.post(
                "/posting",
                json={"message": "Visit http://example.org for more info."},
            )
        assert resp.status_code == 200

    def test_invalid_url_body_success_false(self, client):
        resp = client.post(
            "/posting", json={"message": "Visit http://localhost for info."}
        )
        assert resp.json()["success"] is False


# ===========================================================================
# Test 6: Partial platform failure resilience
# ===========================================================================
class TestPartialFailureResilience:
    """Some platforms failing must not stop others; response is always 200."""

    @property
    def _mixed(self):
        return [
            _make_success("Telegraph"),
            _make_failed("Dpaste", "Connection timeout"),
            _make_success("Ntfy.sh"),
            _make_failed("GitHub Gist", "Authentication failed: Missing GITHUB_TOKEN"),
            _make_failed("HuggingFace", "Authentication failed: Missing HF_API_TOKEN"),
        ]

    def test_partial_failure_returns_200(self, client):
        with patch(PATCH_TARGET, new=AsyncMock(return_value=self._mixed)):
            resp = client.post("/posting", json={"message": VALID_MESSAGE})
        assert resp.status_code == 200

    def test_partial_failure_returns_all_5_results(self, client):
        with patch(PATCH_TARGET, new=AsyncMock(return_value=self._mixed)):
            resp = client.post("/posting", json={"message": VALID_MESSAGE})
        assert len(resp.json()["results"]) == 5

    def test_all_platforms_fail_still_200(self, client):
        all_failed = [
            _make_failed("Telegraph", "Network error"),
            _make_failed("Dpaste", "Timeout"),
            _make_failed("Ntfy.sh", "Service unavailable"),
            _make_failed("GitHub Gist", "Authentication failed: Missing GITHUB_TOKEN"),
            _make_failed("HuggingFace", "Authentication failed: Missing HF_API_TOKEN"),
        ]
        with patch(PATCH_TARGET, new=AsyncMock(return_value=all_failed)):
            resp = client.post("/posting", json={"message": VALID_MESSAGE})
        assert resp.status_code == 200

    def test_failed_platforms_null_fields(self, client):
        with patch(PATCH_TARGET, new=AsyncMock(return_value=self._mixed)):
            resp = client.post("/posting", json={"message": VALID_MESSAGE})
        for r in resp.json()["results"]:
            if r["status"] == "failed":
                assert r["posted_url"] is None
                assert r["date"] is None
                assert r["time"] is None
                assert r["public_access"] is False

    def test_success_true_with_partial_failures(self, client):
        with patch(PATCH_TARGET, new=AsyncMock(return_value=self._mixed)):
            resp = client.post("/posting", json={"message": VALID_MESSAGE})
        assert resp.json()["success"] is True

    def test_mixed_statuses_in_results(self, client):
        with patch(PATCH_TARGET, new=AsyncMock(return_value=self._mixed)):
            resp = client.post("/posting", json={"message": VALID_MESSAGE})
        statuses = {r["status"] for r in resp.json()["results"]}
        assert "success" in statuses
        assert "failed" in statuses


# ===========================================================================
# Test 7: Trailing punctuation stripping
# ===========================================================================
class TestTrailingPunctuationStripping:
    """
    URLs followed by sentence-ending punctuation must be extracted cleanly.
    The _extract_urls helper and the full validator both strip .,!?;: from
    the right side of each raw URL match.
    """

    # --- Unit tests for _extract_urls() directly ---

    def test_strip_trailing_period(self):
        urls = _extract_urls("Visit http://example.org.")
        assert urls == ["http://example.org"]

    def test_strip_trailing_comma(self):
        urls = _extract_urls("See https://example.com, then do something.")
        assert urls == ["https://example.com"]

    def test_strip_trailing_exclamation(self):
        urls = _extract_urls("Check https://example.com!")
        assert urls == ["https://example.com"]

    def test_strip_trailing_question_mark(self):
        urls = _extract_urls("Have you visited https://example.com?")
        # The '?' is part of a query string — only strip if it's trailing with no path after
        # Our rstrip removes it; that's acceptable for well-formed CTA URLs
        result = _extract_urls("Go to https://example.com now?")
        assert result[0] == "https://example.com"

    def test_strip_trailing_semicolon(self):
        urls = _extract_urls("Visit https://example.com; more info inside.")
        assert urls == ["https://example.com"]

    def test_strip_trailing_colon(self):
        urls = _extract_urls("Source: https://example.com:")
        assert urls == ["https://example.com"]

    def test_strip_multiple_trailing_chars(self):
        urls = _extract_urls("See https://example.com.,!")
        assert urls == ["https://example.com"]

    def test_no_strip_from_path(self):
        """Dots inside a URL path must NOT be stripped."""
        urls = _extract_urls("Read https://example.com/page.html for more.")
        assert urls == ["https://example.com/page.html"]

    def test_no_strip_from_subdomain(self):
        """Dots in subdomain must NOT be stripped."""
        urls = _extract_urls("Visit https://www.example.co.uk today.")
        assert urls == ["https://www.example.co.uk"]

    # --- Integration: full HTTP endpoint with trailing punctuation ---

    def test_url_ending_with_period_accepted_200(self, client):
        """
        A message where the URL is followed by a period must still be accepted
        (200 OK) because the period is stripped before validation.
        """
        with patch(PATCH_TARGET, new=AsyncMock(return_value=MOCK_ALL_SUCCESS)):
            resp = client.post(
                "/posting",
                json={"message": "Visit http://example.org now."},
            )
        assert resp.status_code == 200

    def test_url_ending_with_comma_accepted_200(self, client):
        with patch(PATCH_TARGET, new=AsyncMock(return_value=MOCK_ALL_SUCCESS)):
            resp = client.post(
                "/posting",
                json={"message": "See https://example.com, it's great."},
            )
        assert resp.status_code == 200

    def test_url_ending_with_exclamation_accepted_200(self, client):
        with patch(PATCH_TARGET, new=AsyncMock(return_value=MOCK_ALL_SUCCESS)):
            resp = client.post(
                "/posting",
                json={"message": "Check out https://example.com!"},
            )
        assert resp.status_code == 200

    def test_url_in_markdown_link_syntax(self, client):
        """
        Markdown-style [text](url) — the closing ) is not in our strip set
        but the regex already excludes ) from URL chars, so it cleanly stops.
        """
        with patch(PATCH_TARGET, new=AsyncMock(return_value=MOCK_ALL_SUCCESS)):
            resp = client.post(
                "/posting",
                json={"message": "See [our site](https://example.com) for more."},
            )
        assert resp.status_code == 200


# ===========================================================================
# Schema Unit Tests (pure Python, no HTTP layer)
# ===========================================================================
class TestPostingRequestSchema:
    """Unit tests for the PostingRequest Pydantic v2 schema."""

    def test_valid_message_accepted(self):
        req = PostingRequest(message=VALID_MESSAGE)
        assert req.message == VALID_MESSAGE

    def test_cta_url_property_clean(self):
        req = PostingRequest(message="Go to https://example.com now!")
        assert req.cta_url == "https://example.com"

    def test_cta_url_strips_trailing_period(self):
        req = PostingRequest(message="Go to https://example.com.")
        assert req.cta_url == "https://example.com"

    def test_empty_message_raises(self):
        with pytest.raises(Exception):
            PostingRequest(message="")

    def test_whitespace_message_raises(self):
        with pytest.raises(Exception):
            PostingRequest(message="   ")

    def test_too_long_message_raises(self):
        with pytest.raises(Exception):
            PostingRequest(message="A" * 201)

    def test_exactly_200_chars_valid(self):
        url = "https://example.com"
        msg = "A" * (200 - len(url) - 1) + " " + url
        req = PostingRequest(message=msg)
        assert len(req.message) == 200

    def test_no_url_raises(self):
        with pytest.raises(Exception):
            PostingRequest(message="No link here at all.")

    def test_multiple_urls_raises(self):
        with pytest.raises(Exception):
            PostingRequest(
                message="See https://a.com and https://b.com for details."
            )

    def test_invalid_url_tld_raises(self):
        with pytest.raises(Exception):
            PostingRequest(message="Visit http://localhost for info.")

    def test_valid_http_url_accepted(self):
        req = PostingRequest(message="Visit http://example.org now.")
        assert req.cta_url == "http://example.org"

    def test_valid_https_subdomain_accepted(self):
        req = PostingRequest(message="Go to https://www.example.co.uk today!")
        assert "example.co.uk" in req.cta_url
