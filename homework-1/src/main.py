import os

from fastapi import FastAPI

from src.errors import register_exception_handlers
from src.rate_limit import RateLimitMiddleware
from src.routes import accounts, transactions

DEFAULT_RATE_LIMIT = 100  # requests per minute per IP


def _rate_limit_from_env() -> int:
    """Read $RATE_LIMIT_PER_MINUTE; fail with a clear message if it isn't an integer >= 1."""
    raw = os.environ.get("RATE_LIMIT_PER_MINUTE")
    if raw is None:
        return DEFAULT_RATE_LIMIT
    try:
        value = int(raw)
    except ValueError:
        value = 0
    if value < 1:
        msg = f"RATE_LIMIT_PER_MINUTE must be an integer >= 1, got {raw!r}"
        raise RuntimeError(msg)
    return value


def create_app(rate_limit: int | None = None) -> FastAPI:
    """Build the app. ``rate_limit`` falls back to $RATE_LIMIT_PER_MINUTE, then 100."""
    if rate_limit is None:
        rate_limit = _rate_limit_from_env()
    app = FastAPI(title="Banking Transactions API", version="0.1.0")
    register_exception_handlers(app)
    app.add_middleware(RateLimitMiddleware, limit=rate_limit, window=60.0)
    app.include_router(transactions.router)
    app.include_router(accounts.router)
    return app


app = create_app()
