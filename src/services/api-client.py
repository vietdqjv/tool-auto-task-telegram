# src/services/api-client.py
"""External API client wrapper (stub - not used in MVP)."""
from typing import Any


class APIClient:
    """Async HTTP client for external APIs (stub implementation).

    Note: External API integration not needed for MVP.
    This is a placeholder for future implementation.
    """

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: int = 30
    ):
        self.base_url = base_url or ""
        self.api_key = api_key or ""
        self.timeout = timeout

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def get(self, endpoint: str, params: dict | None = None) -> Any:
        """GET request stub."""
        raise NotImplementedError("API client not implemented for MVP")

    async def post(self, endpoint: str, data: dict | None = None) -> Any:
        """POST request stub."""
        raise NotImplementedError("API client not implemented for MVP")
