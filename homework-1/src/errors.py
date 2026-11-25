"""Uniform JSON error responses.

* Validation failures -> 400 ``{"error": "Validation failed", "details": [{"field", "message"}]}``
* HTTP errors (404, 405, ...) -> ``{"error": "<message>"}``
* Unexpected exceptions -> 500 ``{"error": "Internal server error"}``
"""

import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)

_PYDANTIC_VALUE_ERROR_PREFIX = "Value error, "


def _field_name(loc: tuple[Any, ...]) -> str:
    """('body', 'amount') -> 'amount'; ('query', 'from') -> 'from'; ('body',) -> 'body'."""
    parts = [p for p in loc[1:] if isinstance(p, str)]
    return parts[-1] if parts else str(loc[0])


def _message(error: dict[str, Any]) -> str:
    kind = error["type"]
    if kind == "missing":
        return "Field is required"
    if kind == "json_invalid":
        return "Request body must be valid JSON"
    return error["msg"].removeprefix(_PYDANTIC_VALUE_ERROR_PREFIX)


def error_response(status_code: int, error: str, details: list[dict[str, str]] | None = None):
    content: dict[str, Any] = {"error": error}
    if details is not None:
        content["details"] = details
    return JSONResponse(status_code=status_code, content=content)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        details = [
            {"field": _field_name(tuple(e["loc"])), "message": _message(e)} for e in exc.errors()
        ]
        return error_response(status.HTTP_400_BAD_REQUEST, "Validation failed", details)

    @app.exception_handler(StarletteHTTPException)
    async def _http(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        response = error_response(exc.status_code, str(exc.detail))
        if exc.headers:
            response.headers.update(exc.headers)
        return response

    @app.exception_handler(Exception)
    async def _unexpected(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error", exc_info=exc)
        return error_response(status.HTTP_500_INTERNAL_SERVER_ERROR, "Internal server error")
