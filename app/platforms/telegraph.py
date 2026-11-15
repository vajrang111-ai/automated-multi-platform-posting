"""
app/platforms/telegraph.py
Telegraph Website integration.

Flow:
  1. POST https://api.telegra.ph/createAccount  -> get access_token
  2. POST https://api.telegra.ph/createPage     -> get live page URL

No pre-configured keys required — creates an anonymous account per request.
"""
import httpx
from datetime import datetime, timezone

from app.platforms.base import BasePlatform
from app.schemas import PlatformResult

_TIMEOUT = httpx.Timeout(10.0)
_CREATE_ACCOUNT_URL = "https://api.telegra.ph/createAccount"
_CREATE_PAGE_URL = "https://api.telegra.ph/createPage"


class TelegraphPlatform(BasePlatform):
    @property
    def platform_name(self) -> str:
        return "Telegraph"

    async def post(self, message: str) -> PlatformResult:
        now = datetime.now(timezone.utc)
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")

        try:
            async with httpx.AsyncClient(
                timeout=_TIMEOUT,
                verify=False,  # noqa: S501 — env SSL chain issue workaround
            ) as client:
                # Step 1: Create an anonymous account (no keys required)
                account_resp = await client.post(
                    _CREATE_ACCOUNT_URL,
                    data={
                        "short_name": "AutoPoster",
                        "author_name": "Automated Posting System",
                    },
                )
                account_resp.raise_for_status()
                account_data = account_resp.json()

                if not account_data.get("ok"):
                    raise ValueError(
                        f"Telegraph createAccount failed: {account_data.get('error', 'Unknown error')}"
                    )

                access_token = account_data["result"]["access_token"]

                # Step 2: Create a public page
                page_content = [{"tag": "p", "children": [message]}]
                page_resp = await client.post(
                    _CREATE_PAGE_URL,
                    json={
                        "access_token": access_token,
                        "title": "Automated Post",
                        "content": page_content,
                        "return_content": False,
                    },
                )
                page_resp.raise_for_status()
                page_data = page_resp.json()

                if not page_data.get("ok"):
                    raise ValueError(
                        f"Telegraph createPage failed: {page_data.get('error', 'Unknown error')}"
                    )

                page_url = "https://telegra.ph/" + page_data["result"]["path"]

                return PlatformResult(
                    platform=self.platform_name,
                    status="success",
                    posted_url=page_url,
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
                error=str(exc) or type(exc).__name__,
            )
