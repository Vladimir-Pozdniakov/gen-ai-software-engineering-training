from datetime import UTC, datetime

import pytest


def ts(day: int, hour: int = 12) -> datetime:
    return datetime(2024, 1, day, hour, tzinfo=UTC)


@pytest.fixture
def seeded(make_tx):
    """t1: transfer 12345->67890 Jan 10 | t2: deposit ->12345 Jan 20 | t3: withdrawal 99999 Jan 31 23:59"""
    return {
        "t1": make_tx(at=ts(10)),
        "t2": make_tx(at=ts(20), type="deposit", fromAccount=None, toAccount="ACC-12345"),
        "t3": make_tx(at=ts(31, 23), type="withdrawal", fromAccount="ACC-99999", toAccount=None),
    }


def ids(client, **params) -> list[str]:
    r = client.get("/transactions", params=params)
    assert r.status_code == 200, r.text
    return [t["id"] for t in r.json()]


def test_filter_by_account_matches_sender_or_receiver(client, seeded):
    assert ids(client, accountId="ACC-12345") == [seeded["t1"]["id"], seeded["t2"]["id"]]
    assert ids(client, accountId="ACC-67890") == [seeded["t1"]["id"]]
    assert ids(client, accountId="ACC-00000") == []


def test_filter_by_type(client, seeded):
    assert ids(client, type="deposit") == [seeded["t2"]["id"]]
    assert ids(client, type="transfer") == [seeded["t1"]["id"]]


def test_filter_by_date_range_is_inclusive(client, seeded):
    t = {k: v["id"] for k, v in seeded.items()}
    assert ids(client, **{"from": "2024-01-10", "to": "2024-01-10"}) == [t["t1"]]
    assert ids(client, **{"from": "2024-01-11"}) == [t["t2"], t["t3"]]
    assert ids(client, to="2024-01-19") == [t["t1"]]
    # 'to' covers the whole day: Jan 31 23:00 is included
    assert ids(client, **{"from": "2024-01-01", "to": "2024-01-31"}) == list(t.values())
    assert ids(client, **{"from": "2024-02-01"}) == []


def test_combined_filters(client, seeded):
    t = {k: v["id"] for k, v in seeded.items()}
    assert ids(client, accountId="ACC-12345", type="deposit") == [t["t2"]]
    assert ids(client, accountId="ACC-12345", **{"from": "2024-01-15"}) == [t["t2"]]
    assert ids(client, accountId="ACC-12345", type="transfer", to="2024-01-05") == []
    assert ids(
        client, accountId="ACC-12345", type="deposit", **{"from": "2024-01-01", "to": "2024-01-31"}
    ) == [t["t2"]]


@pytest.mark.parametrize(
    ("params", "field"),
    [
        ({"accountId": "bad"}, "accountId"),
        ({"type": "gift"}, "type"),
        ({"from": "2024-13-01"}, "from"),
        ({"to": "yesterday"}, "to"),
        ({"from": "2024-02-01", "to": "2024-01-01"}, "to"),
    ],
)
def test_invalid_filters_400(client, params, field):
    r = client.get("/transactions", params=params)
    assert r.status_code == 400
    assert r.json()["error"] == "Validation failed"
    assert [d["field"] for d in r.json()["details"]] == [field]
