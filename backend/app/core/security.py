"""Reusable request authentication dependencies."""

import secrets
from typing import Annotated

from fastapi import Header

from app.core.config import settings


class APIKeyAuthenticationError(Exception):
    """Authentication failure with the message returned by the API."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


async def verify_api_key(
    api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> None:
    """Require a valid Edge AI API key using a constant-time comparison."""
    if api_key is None:
        raise APIKeyAuthenticationError("Missing API key")

    configured_key = settings.edge_api_key
    if not configured_key or not secrets.compare_digest(
        api_key.encode("utf-8"), configured_key.encode("utf-8")
    ):
        raise APIKeyAuthenticationError("Invalid API key")
