from datetime import datetime


def test_create_transfer(client):
    body = {
        "fromAccount": "ACC-12345",
        "toAccount": "ACC-67890",
        "amount": 100.50,
        "currency": "USD",
        "type": "transfer",
    }
    r = client.post("/transactions", json=body)
    assert r.status_code == 201
    data = r.json()
    assert data["id"]
    assert data | {"id": None, "timestamp": None} == body | {
        "id": None,
        "timestamp": None,
        "status": "completed",
    }
    assert data["timestamp"].endswith("Z")
    datetime.fromisoformat(data["timestamp"])


def test_create_deposit_and_withdrawal(make_tx):
    dep = make_tx(type="deposit", fromAccount=None)
    wd = make_tx(type="withdrawal", toAccount=None)
    assert dep["fromAccount"] is None
    assert wd["toAccount"] is None


def test_ids_are_unique(make_tx):
    assert make_tx()["id"] != make_tx()["id"]


def test_list_empty(client):
    r = client.get("/transactions")
    assert r.status_code == 200
    assert r.json() == []


def test_list_returns_all_in_creation_order(client, make_tx):
    ids = [make_tx(amount=a)["id"] for a in (1, 2, 3)]
    assert [t["id"] for t in client.get("/transactions").json()] == ids


def test_get_by_id(client, make_tx):
    tx = make_tx()
    r = client.get(f"/transactions/{tx['id']}")
    assert r.status_code == 200
    assert r.json() == tx


def test_get_unknown_id_404(client):
    r = client.get("/transactions/does-not-exist")
    assert r.status_code == 404
    assert r.json() == {"error": "Transaction not found"}


def test_unknown_route_and_method(client):
    assert client.get("/nope").json() == {"error": "Not Found"}
    r = client.delete("/transactions")
    assert r.status_code == 405
    assert "error" in r.json()


def test_accepts_integer_and_two_decimal_amounts(make_tx):
    assert make_tx(amount=5)["amount"] == 5
    assert make_tx(amount=0.01)["amount"] == 0.01
    assert make_tx(amount=19.99)["amount"] == 19.99


def test_unexpected_error_returns_500_json():
    from fastapi.testclient import TestClient

    from src.main import create_app
    from src.storage import get_store

    def boom():
        raise RuntimeError("kaput")

    app = create_app(rate_limit=100)
    app.dependency_overrides[get_store] = boom
    r = TestClient(app, raise_server_exceptions=False).get("/transactions")
    assert r.status_code == 500
    assert r.json() == {"error": "Internal server error"}


def test_store_clear(store, make_tx):
    make_tx()
    store.clear()
    assert store.list() == []
