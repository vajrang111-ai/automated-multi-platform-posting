"""
app/schemas.py
Pydantic v2 request/response schemas with strict validation.
"""
import re
from urllib.parse import urlparse
from pydantic import BaseModel, field_validator
from typing import Optional, List


# Regex to find all http/https links in a string
_URL_PATTERN = re.compile(r"https?://[^\s\)\]\"\'>]+")

# Trailing punctuation characters to strip from extracted URLs
_TRAILING_PUNCT = ".,!?;:"

# Minimum valid TLD check: host must end with dot + 2+ alpha chars
_TLD_PATTERN = re.compile(r"\.[a-zA-Z]{2,}$")


def _extract_urls(text: str) -> List[str]:
    """
    Extract all http/https URLs from text, stripping trailing punctuation
    (., , ! ? ; :) so that sentences like "Visit http://example.org now."
    yield the clean URL "http://example.org".
    """
    raw_urls = _URL_PATTERN.findall(text)
    return [url.rstrip(_TRAILING_PUNCT) for url in raw_urls]


def _validate_url(url: str) -> bool:
    """Validate that a URL has a proper scheme, netloc, and TLD."""
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
        netloc = parsed.netloc
        if not netloc:
            return False
        # Strip port if present
        host = netloc.split(":")[0]
        if not host:
            return False
        # Must have a valid TLD (at least one dot followed by 2+ alpha chars)
        if not _TLD_PATTERN.search(host):
            return False
        return True
    except Exception:
        return False


class PostingRequest(BaseModel):
    message: str

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        # Rule 1: non-empty
        if not v or not v.strip():
            raise ValueError("message must be a non-empty string.")

        # Rule 1: max 200 characters
        if len(v) > 200:
            raise ValueError(
                f"message must not exceed 200 characters (received {len(v)} characters)."
            )

        # Rule 2: exactly one CTA link (after stripping trailing punctuation)
        urls = _extract_urls(v)
        if len(urls) == 0:
            raise ValueError(
                "message must contain exactly one CTA link (http:// or https://). "
                "Zero links found."
            )
        if len(urls) > 1:
            raise ValueError(
                f"message must contain exactly one CTA link (http:// or https://). "
                f"{len(urls)} links found."
            )

        # Rule 3: validate the extracted (cleaned) URL
        url = urls[0]
        if not _validate_url(url):
            raise ValueError(
                f"The CTA URL '{url}' is invalid. "
                "It must have a valid scheme (http/https), domain, and TLD."
            )

        return v

    @property
    def cta_url(self) -> str:
        """Return the single validated CTA URL (trailing punctuation stripped)."""
        return _extract_urls(self.message)[0]


class PlatformResult(BaseModel):
    platform: str
    status: str                     # "success" | "failed"
    posted_url: Optional[str]       # null when failed
    public_access: bool             # false when failed
    date: Optional[str]             # "YYYY-MM-DD", null when failed
    time: Optional[str]             # "HH:MM:SS", null when failed
    error: Optional[str]            # null when success


class PostingResponse(BaseModel):
    success: bool
    results: List[PlatformResult]
