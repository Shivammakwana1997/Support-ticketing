from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    status_code: int = 500
    detail: str = "Internal server error"
    error_code: str = "INTERNAL_ERROR"

    def __init__(self, detail: str | None = None, **kwargs: Any) -> None:
        self.detail = detail or self.__class__.detail
        self.extra = kwargs
        super().__init__(self.detail)


class NotFoundError(AppError):
    status_code = 404
    detail = "Resource not found"
    error_code = "NOT_FOUND"


class UnauthorizedError(AppError):
    status_code = 401
    detail = "Not authenticated"
    error_code = "UNAUTHORIZED"


class ForbiddenError(AppError):
    status_code = 403
    detail = "Permission denied"
    error_code = "FORBIDDEN"


class ValidationError(AppError):
    status_code = 422
    detail = "Validation error"
    error_code = "VALIDATION_ERROR"


class ConflictError(AppError):
    status_code = 409
    detail = "Resource conflict"
    error_code = "CONFLICT"


class RateLimitError(AppError):
    status_code = 429
    detail = "Rate limit exceeded"
    error_code = "RATE_LIMIT_EXCEEDED"


def _error_response(exc: AppError) -> JSONResponse:
    body: dict[str, Any] = {
        "error": {
            "code": exc.error_code,
            "message": exc.detail,
        }
    }
    if exc.extra:
        body["error"]["details"] = exc.extra
    return JSONResponse(status_code=exc.status_code, content=body)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
        return _error_response(exc)

    @app.exception_handler(404)
    async def not_found_handler(_request: Request, _exc: Exception) -> JSONResponse:
        return _error_response(NotFoundError())

    @app.exception_handler(500)
    async def internal_error_handler(_request: Request, _exc: Exception) -> JSONResponse:
        return _error_response(AppError())
