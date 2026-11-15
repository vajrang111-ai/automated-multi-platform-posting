"""
app/platforms/base.py
Abstract base class for all platform integrations.
"""
from abc import ABC, abstractmethod
from app.schemas import PlatformResult


class BasePlatform(ABC):
    """
    Abstract base class every platform adapter must extend.
    Each subclass implements `post(message)` as an async method.
    """

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Human-readable name shown in API responses."""
        ...

    @abstractmethod
    async def post(self, message: str) -> PlatformResult:
        """
        Publish `message` to the platform and return a PlatformResult.
        Must never raise – all errors must be caught and returned as a
        failed PlatformResult.
        """
        ...
