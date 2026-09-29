"""Common response envelopes.

SuccessResponse, ErrorResponse, and Paginated wrappers matching the API contract.
"""

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class SuccessResponse(BaseModel, Generic[T]):
    """Standard success envelope: { success, message, data }."""

    success: bool = True
    message: str = "Request completed successfully"
    data: T


class ErrorResponse(BaseModel):
    """Standard error envelope: { success, message, error_code }."""

    success: bool = False
    message: str
    error_code: str


class Paginated(BaseModel, Generic[T]):
    """Paginated data wrapper: { total, page, size, items }."""

    total: int
    page: int
    size: int
    items: list[T]
