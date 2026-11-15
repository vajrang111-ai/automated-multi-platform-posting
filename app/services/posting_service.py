"""
app/services/posting_service.py
Executes all 5 platform integrations concurrently and independently
using asyncio.gather with return_exceptions=False.
Any individual platform exception is caught inside each platform's post()
method so gather never raises and all platforms run to completion.
"""
import asyncio
from typing import List

from app.platforms.telegraph import TelegraphPlatform
from app.platforms.dpaste import DpastePlatform
from app.platforms.ntfy_sh import NtfyPlatform
from app.platforms.github_gist import GitHubGistPlatform
from app.platforms.huggingface_llm import HuggingFacePlatform
from app.schemas import PlatformResult


# Instantiate all platform adapters (stateless singletons)
_PLATFORMS = [
    TelegraphPlatform(),
    DpastePlatform(),
    NtfyPlatform(),
    GitHubGistPlatform(),
    HuggingFacePlatform(),
]


async def post_to_all_platforms(message: str) -> List[PlatformResult]:
    """
    Concurrently posts `message` to all 5 platforms.

    Uses asyncio.gather with return_exceptions=False. Each platform's
    post() method handles its own exceptions internally, so this gather
    never raises — all platforms always return a PlatformResult.
    """
    tasks = [platform.post(message) for platform in _PLATFORMS]
    results: List[PlatformResult] = await asyncio.gather(*tasks, return_exceptions=False)
    return list(results)
