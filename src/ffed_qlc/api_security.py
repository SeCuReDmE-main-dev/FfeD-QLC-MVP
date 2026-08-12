"""HTTP boundary controls shared by all API routers."""

from __future__ import annotations

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse, Response


MAX_REQUEST_BYTES = 1_000_000


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        raw_length = request.headers.get("content-length")
        if raw_length is not None:
            try:
                length = int(raw_length, 10)
            except ValueError:
                return _error(400, "INVALID_CONTENT_LENGTH", "Content-Length must be a non-negative integer")
            if length < 0:
                return _error(400, "INVALID_CONTENT_LENGTH", "Content-Length must be a non-negative integer")
            if length > MAX_REQUEST_BYTES:
                return _error(413, "REQUEST_TOO_LARGE", f"request exceeds {MAX_REQUEST_BYTES} bytes")
        return await call_next(request)


def _error(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"detail": {"code": code, "message": message}, "secret_values_exposed": False},
    )
