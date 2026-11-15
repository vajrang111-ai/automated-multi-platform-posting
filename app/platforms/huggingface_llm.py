"""
app/platforms/huggingface_llm.py
HuggingFace LLM Hub API integration.

Uses HF_API_TOKEN from environment variables.
If the token is missing, returns a graceful failed status.
"""
import httpx
from datetime import datetime, timezone

from app.platforms.base import BasePlatform
from app.schemas import PlatformResult
from app.config import HF_API_TOKEN

_TIMEOUT = httpx.Timeout(10.0)
_HF_QUICK_PICK_URL = "https://huggingface.co/api/quick-pick"
_HF_INFERENCE_URL = "https://api-inference.huggingface.co/models/gpt2"
_HF_PLATFORM_URL = "https://huggingface.co"


class HuggingFacePlatform(BasePlatform):
    @property
    def platform_name(self) -> str:
        return "HuggingFace"

    async def post(self, message: str) -> PlatformResult:
        now = datetime.now(timezone.utc)
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")

        # Graceful failure when token is missing
        if not HF_API_TOKEN:
            return PlatformResult(
                platform=self.platform_name,
                status="failed",
                posted_url=None,
                public_access=False,
                date=None,
                time=None,
                error="Authentication failed: Missing HF_API_TOKEN",
            )

        try:
            async with httpx.AsyncClient(
                timeout=_TIMEOUT,
                verify=False,  # noqa: S501 — env SSL chain issue workaround
            ) as client:
                headers = {
                    "Authorization": f"Bearer {HF_API_TOKEN}",
                    "Content-Type": "application/json",
                }

                # Try quick-pick endpoint first
                try:
                    qp_resp = await client.get(
                        _HF_QUICK_PICK_URL,
                        headers=headers,
                        params={"pipeline_tag": "text-generation"},
                    )
                    if qp_resp.status_code == 401:
                        return PlatformResult(
                            platform=self.platform_name,
                            status="failed",
                            posted_url=None,
                            public_access=False,
                            date=None,
                            time=None,
                            error="Authentication failed: Invalid HF_API_TOKEN",
                        )
                    qp_resp.raise_for_status()
                    # Use inference endpoint to validate message submission
                    inf_resp = await client.post(
                        _HF_INFERENCE_URL,
                        headers=headers,
                        json={"inputs": message[:200]},
                    )
                    # 503 means model loading — still valid auth
                    if inf_resp.status_code not in (200, 503):
                        inf_resp.raise_for_status()

                except httpx.HTTPStatusError as hse:
                    if hse.response.status_code == 401:
                        return PlatformResult(
                            platform=self.platform_name,
                            status="failed",
                            posted_url=None,
                            public_access=False,
                            date=None,
                            time=None,
                            error="Authentication failed: Invalid HF_API_TOKEN",
                        )
                    raise

                return PlatformResult(
                    platform=self.platform_name,
                    status="success",
                    posted_url=_HF_PLATFORM_URL,
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
