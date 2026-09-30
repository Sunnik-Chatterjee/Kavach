"""Application exception hierarchy.

Defines AppError subclasses mapped to the API contract error_code values.
"""

from typing import Any


class AppError(Exception):
    """Base application error carrying an HTTP status and error code."""

    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"

    def __init__(self, message: str, *, details: Any = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class NotFoundError(AppError):
    """Raised when a requested resource does not exist."""

    status_code = 404
    error_code = "NOT_FOUND"


class ConflictError(AppError):
    """Raised when an operation conflicts with the current state."""

    status_code = 409
    error_code = "CONFLICT"


class ValidationError(AppError):
    """Raised when request data fails business validation."""

    status_code = 400
    error_code = "VALIDATION_ERROR"


class UnauthorizedError(AppError):
    """Raised when authentication is required but missing/invalid."""

    status_code = 401
    error_code = "UNAUTHORIZED"
