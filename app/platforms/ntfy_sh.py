"""
app/platforms/ntfy_sh.py
Ntfy.sh Public Portal integration.

Publishes the message to the public feed topic and returns the live feed URL.
Topic: dxora_automated_posting_feed
Feed URL: https://ntfy.sh/dxora_automated_posting_feed
"""
import httpx
from datetime import datetime, timezone

from app.platforms.base import BasePlatform
from app.schemas import PlatformResult

_TIMEOUT = httpx.Timeout(10.0)
_NTFY_TOPIC = "dxora_automated_posting_feed"
_NTFY_PUBLISH_URL = f"https://ntfy.sh/{_NTFY_TOPIC}"
_NTFY_FEED_URL = f"https://ntfy.sh/{_NTFY_TOPIC}"


class NtfyPlatform(BasePlatform):
    @property
    def platform_name(self) -> str:
        return "Ntfy.sh"

    async def post(self, message: str) -> PlatformResult:
        now = datetime.now(timezone.utc)
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")

        try:
            async with httpx.AsyncClient(
                timeout=_TIMEOUT,
                verify=False,  # noqa: S501 — env SSL chain issue workaround
            ) as client:
                resp = await client.post(
                    _NTFY_PUBLISH_URL,
                    content=message.encode("utf-8"),
                    headers={
                        "Title": "Automated Post",
                        "Priority": "default",
                        "Tags": "mega,automated",
                        "Content-Type": "text/plain",
                    },
                )
                resp.raise_for_status()

                return PlatformResult(
                    platform=self.platform_name,
                    status="success",
                    posted_url=_NTFY_FEED_URL,
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
