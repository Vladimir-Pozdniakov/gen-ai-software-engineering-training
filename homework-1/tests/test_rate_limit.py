from fastapi.testclient import TestClient

from src.main import create_app
from src.rate_limit import RateLimitMiddleware


def test_returns_429_after_limit():
    client = TestClient(create_app(rate_limit=3))
    codes = [client.get("/transactions").status_code for _ in range(5)]
    assert codes == [200, 200, 200, 429, 429]
    r = client.get("/transactions")
    assert r.json() == {"error": "Too many requests"}
    assert int(r.headers["retry-after"]) >= 1


def test_default_limit_is_100_per_minute(monkeypatch):
    monkeypatch.delenv("RATE_LIMIT_PER_MINUTE", raising=False)
    client = TestClient(create_app())
    codes = [client.get("/transactions").status_code for _ in range(101)]
    assert codes.count(200) == 100
    assert codes[-1] == 429


def test_limit_from_env(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_PER_MINUTE", "2")
    client = TestClient(create_app())
    assert [client.get("/transactions").status_code for _ in range(3)] == [200, 200, 429]


def test_window_slides(monkeypatch):
    now = [1000.0]
    monkeypatch.setattr("src.rate_limit.time.monotonic", lambda: now[0])
    client = TestClient(create_app(rate_limit=2))
    assert [client.get("/transactions").status_code for _ in range(3)] == [200, 200, 429]
    now[0] += 61
    assert client.get("/transactions").status_code == 200


def test_limit_is_per_client():
    mw = RateLimitMiddleware(app=None, limit=1, window=60)  # type: ignore[arg-type]
    assert mw._check("1.1.1.1") is None
    assert mw._check("1.1.1.1") is not None
    assert mw._check("2.2.2.2") is None


def test_errors_also_count(monkeypatch):
    client = TestClient(create_app(rate_limit=2))
    assert [client.get("/nope").status_code for _ in range(3)] == [404, 404, 429]


def test_stale_clients_are_pruned(monkeypatch):
    monkeypatch.setattr("src.rate_limit._MAX_TRACKED_CLIENTS", 2)
    now = [0.0]
    monkeypatch.setattr("src.rate_limit.time.monotonic", lambda: now[0])
    mw = RateLimitMiddleware(app=None, limit=5, window=10)  # type: ignore[arg-type]
    for ip in ("a", "b", "c"):
        mw._check(ip)
    now[0] = 100.0
    mw._check("d")
    assert set(mw._hits) == {"d"}
