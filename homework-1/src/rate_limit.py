"""Per-IP sliding-window rate limiting (in-memory, single process)."""

import math
import time
from collections import deque
from threading import Lock

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from src.errors import error_response

_MAX_TRACKED_CLIENTS = 10_000


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Allow at most ``limit`` requests per ``window`` seconds per client IP, else 429."""

    def __init__(self, app: ASGIApp, limit: int = 100, window: float = 60.0) -> None:
        super().__init__(app)
        self.limit = limit
        self.window = window
        self._hits: dict[str, deque[float]] = {}
        self._lock = Lock()

    def _check(self, client: str) -> float | None:
        """Record a hit; return seconds until retry is allowed if over the limit."""
        now = time.monotonic()
        cutoff = now - self.window
        with self._lock:
            if len(self._hits) > _MAX_TRACKED_CLIENTS:
                self._hits = {k: v for k, v in self._hits.items() if v and v[-1] > cutoff}
            hits = self._hits.setdefault(client, deque())
            while hits and hits[0] <= cutoff:
                hits.popleft()
            if len(hits) >= self.limit:
                return hits[0] + self.window - now
            hits.append(now)
            return None

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        client = request.client.host if request.client else "unknown"
        retry_after = self._check(client)
        if retry_after is not None:
            response = error_response(429, "Too many requests")
            response.headers["Retry-After"] = str(max(1, math.ceil(retry_after)))
            return response
        return await call_next(request)
