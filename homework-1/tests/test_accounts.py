import pytest


def balance(client, account="ACC-12345"):
    r = client.get(f"/accounts/{account}/balance")
    assert r.status_code == 200
    return r.json()


def test_balance_unknown_account_is_empty(client):
    assert balance(client, "ACC-00000") == {"accountId": "ACC-00000", "balances": {}}


def test_balance_math_across_types(client, make_tx):
    make_tx(type="deposit", fromAccount=None, toAccount="ACC-12345", amount=200)
    make_tx(type="withdrawal", fromAccount="ACC-12345", toAccount=None, amount=50.25)
    make_tx(fromAccount="ACC-12345", toAccount="ACC-67890", amount=30)  # out
    make_tx(fromAccount="ACC-67890", toAccount="ACC-12345", amount=10.10)  # in
    assert balance(client)["balances"] == {"USD": pytest.approx(129.85)}
    assert balance(client, "ACC-67890")["balances"] == {"USD": pytest.approx(19.90)}


def test_balance_is_exact_with_decimals(client, make_tx):
    for _ in range(10):
        make_tx(type="deposit", fromAccount=None, toAccount="ACC-12345", amount=0.1)
    assert balance(client)["balances"] == {"USD": 1.0}


def test_balance_keeps_currencies_separate(client, make_tx):
    make_tx(type="deposit", fromAccount=None, toAccount="ACC-12345", amount=10, currency="USD")
    make_tx(type="deposit", fromAccount=None, toAccount="ACC-12345", amount=7, currency="EUR")
    assert balance(client)["balances"] == {"USD": 10, "EUR": 7}


def test_balance_ignores_non_completed(client, make_tx, store):
    tx = make_tx(type="deposit", fromAccount=None, toAccount="ACC-12345", amount=10)
    make_tx(type="deposit", fromAccount=None, toAccount="ACC-12345", amount=5)
    store.get(tx["id"]).status = "failed"
    assert balance(client)["balances"] == {"USD": 5}


def test_account_endpoints_reject_bad_ids(client):
    for path in ("balance", "summary"):
        r = client.get(f"/accounts/bad/{path}")
        assert r.status_code == 400
        assert r.json()["details"][0]["field"] == "accountId"


def test_summary_empty_account(client):
    assert client.get("/accounts/ACC-00000/summary").json() == {
        "accountId": "ACC-00000",
        "totalDeposits": {},
        "totalWithdrawals": {},
        "transactionCount": 0,
        "mostRecentTransaction": None,
    }


def test_summary(client, make_tx):
    make_tx(type="deposit", fromAccount=None, amount=100, toAccount="ACC-12345")
    make_tx(type="deposit", fromAccount=None, amount=5.5, toAccount="ACC-12345")
    make_tx(type="deposit", fromAccount=None, amount=3, toAccount="ACC-12345", currency="EUR")
    make_tx(type="withdrawal", toAccount=None, amount=20, fromAccount="ACC-12345")
    make_tx(fromAccount="ACC-12345", toAccount="ACC-67890", amount=1)  # transfer: count only
    last = make_tx(type="deposit", fromAccount=None, toAccount="ACC-99999")  # other account
    s = client.get("/accounts/ACC-12345/summary").json()
    assert s["totalDeposits"] == {"USD": 105.5, "EUR": 3}
    assert s["totalWithdrawals"] == {"USD": 20}
    assert s["transactionCount"] == 5
    assert s["mostRecentTransaction"] < last["timestamp"]
    assert s["mostRecentTransaction"].endswith("Z")


def test_summary_ignores_non_completed_amounts(client, make_tx, store):
    tx = make_tx(type="deposit", fromAccount=None, toAccount="ACC-12345", amount=10)
    store.get(tx["id"]).status = "pending"
    s = client.get("/accounts/ACC-12345/summary").json()
    assert s["totalDeposits"] == {}
    assert s["transactionCount"] == 1
