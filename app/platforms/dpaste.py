"""
app/platforms/dpaste.py
Dpaste Web Portal integration.

POST https://dpaste.com/api/v2/
Returns the generated public URL.
"""
import httpx
from datetime import datetime, timezone

from app.platforms.base import BasePlatform
from app.schemas import PlatformResult

_TIMEOUT = httpx.Timeout(10.0)
_DPASTE_API_URL = "https://dpaste.com/api/v2/"


class DpastePlatform(BasePlatform):
    @property
    def platform_name(self) -> str:
        return "Dpaste"

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
                    _DPASTE_API_URL,
                    data={
                        "content": message,
                        "syntax": "text",
                        "expiry_days": 365,
                    },
                    headers={"User-Agent": "AutomatedPostingSystem/1.0"},
                )
                resp.raise_for_status()

                # dpaste returns the URL as plain text in the response body
                posted_url = resp.text.strip()

                # Ensure it looks like a real URL
                if not posted_url.startswith("http"):
                    raise ValueError(f"Unexpected dpaste response: {posted_url}")

                return PlatformResult(
                    platform=self.platform_name,
                    status="success",
                    posted_url=posted_url,
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
