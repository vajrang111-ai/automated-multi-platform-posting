"""
app/platforms/github_gist.py
GitHub Gist Portal integration.

Publishes a public gist using GITHUB_TOKEN from environment variables.
If the token is missing, returns a graceful failed status.
"""
import httpx
from datetime import datetime, timezone

from app.platforms.base import BasePlatform
from app.schemas import PlatformResult
from app.config import GITHUB_TOKEN

_TIMEOUT = httpx.Timeout(10.0)
_GIST_API_URL = "https://api.github.com/gists"


class GitHubGistPlatform(BasePlatform):
    @property
    def platform_name(self) -> str:
        return "GitHub Gist"

    async def post(self, message: str) -> PlatformResult:
        now = datetime.now(timezone.utc)
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")

        # Graceful failure when token is missing
        if not GITHUB_TOKEN:
            return PlatformResult(
                platform=self.platform_name,
                status="failed",
                posted_url=None,
                public_access=False,
                date=None,
                time=None,
                error="Authentication failed: Missing GITHUB_TOKEN",
            )

        try:
            async with httpx.AsyncClient(
                timeout=_TIMEOUT,
                verify=False,  # noqa: S501 — env SSL chain issue workaround
            ) as client:
                resp = await client.post(
                    _GIST_API_URL,
                    json={
                        "description": "Automated Post via Automated Multi-Platform Posting System",
                        "public": True,
                        "files": {
                            "post.md": {
                                "content": message,
                            }
                        },
                    },
                    headers={
                        "Authorization": f"Bearer {GITHUB_TOKEN}",
                        "Accept": "application/vnd.github+json",
                        "X-GitHub-Api-Version": "2022-11-28",
                        "User-Agent": "AutomatedPostingSystem/1.0",
                    },
                )

                if resp.status_code == 401:
                    return PlatformResult(
                        platform=self.platform_name,
                        status="failed",
                        posted_url=None,
                        public_access=False,
                        date=None,
                        time=None,
                        error="Authentication failed: Invalid GITHUB_TOKEN",
                    )

                resp.raise_for_status()
                data = resp.json()
                gist_url = data.get("html_url", "")

                return PlatformResult(
                    platform=self.platform_name,
                    status="success",
                    posted_url=gist_url,
                    public_access=True,
                    date=date_str,
                    time=time_str,
                    error=None,
                )

        except Exception as exc:
            return PlatformResult(
                platform=self.platform_name,
                status="failed",
                posted_url=None,
                public_access=False,
                date=None,
                time=None,
                error=str(exc),
            )
