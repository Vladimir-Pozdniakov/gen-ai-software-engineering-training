from collections.abc import Callable
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from src.main import create_app
from src.storage import TransactionStore, get_store


@pytest.fixture
def store() -> TransactionStore:
    return TransactionStore()


@pytest.fixture
def client(store: TransactionStore) -> TestClient:
    """Fresh app + fresh store per test; rate limit effectively off."""
    app = create_app(rate_limit=100_000)
    app.dependency_overrides[get_store] = lambda: store
    return TestClient(app)


@pytest.fixture
def make_tx(client: TestClient, store: TransactionStore) -> Callable[..., dict]:
    """Create a transaction via the API; optionally backdate it with ``at``."""

    def _make(at: datetime | None = None, **overrides) -> dict:
        body = {
            "fromAccount": "ACC-12345",
            "toAccount": "ACC-67890",
            "amount": 100.50,
            "currency": "USD",
            "type": "transfer",
        } | overrides
        body = {k: v for k, v in body.items() if v is not None}
        response = client.post("/transactions", json=body)
        assert response.status_code == 201, response.text
        data = response.json()
        if at is not None:
            store.get(data["id"]).timestamp = at
        return data

    return _make
