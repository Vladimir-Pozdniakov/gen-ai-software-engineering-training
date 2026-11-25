import pytest

BASE = {
    "fromAccount": "ACC-12345",
    "toAccount": "ACC-67890",
    "amount": 10,
    "currency": "USD",
    "type": "transfer",
}


def post(client, **overrides):
    body = {k: v for k, v in (BASE | overrides).items() if v is not ...}
    return client.post("/transactions", json=body)


def details(response):
    assert response.status_code == 400
    body = response.json()
    assert body["error"] == "Validation failed"
    return {d["field"]: d["message"] for d in body["details"]}


@pytest.mark.parametrize("amount", [-5, 0, "10", True, None, [1]])
def test_amount_must_be_positive_number(client, amount):
    assert details(post(client, amount=amount))["amount"] == "Amount must be a positive number"


@pytest.mark.parametrize("amount", [1.234, 0.001, 10.999])
def test_amount_max_two_decimals(client, amount):
    assert details(post(client, amount=amount))["amount"] == (
        "Amount must have at most 2 decimal places"
    )


@pytest.mark.parametrize("field", ["fromAccount", "toAccount"])
@pytest.mark.parametrize("value", ["ACC-1234", "ACC-123456", "acc-12345", "ACC-12!45", "12345", ""])
def test_bad_account_format(client, field, value):
    assert "ACC-XXXXX" in details(post(client, **{field: value}))[field]


def test_alphanumeric_accounts_accepted(client):
    assert post(client, fromAccount="ACC-aB3d9", toAccount="ACC-ZZ999").status_code == 201


@pytest.mark.parametrize("currency", ["XXX", "usd", "US", "DOLLAR", "", 5])
def test_bad_currency(client, currency):
    assert details(post(client, currency=currency))["currency"] == "Invalid currency code"


@pytest.mark.parametrize("currency", ["USD", "EUR", "GBP", "JPY"])
def test_valid_currencies(client, currency):
    assert post(client, currency=currency).status_code == 201


def test_bad_type(client):
    assert "deposit" in details(post(client, type="gift"))["type"]


def test_missing_required_fields(client):
    r = client.post("/transactions", json={})
    assert details(r) == {
        "amount": "Field is required",
        "currency": "Field is required",
        "type": "Field is required",
    }


def test_multiple_errors_reported_together(client):
    r = post(client, amount=-5, currency="XXX")
    assert details(r) == {
        "amount": "Amount must be a positive number",
        "currency": "Invalid currency code",
    }
    assert [d["field"] for d in r.json()["details"]] == ["amount", "currency"]


def test_deposit_requires_to_account(client):
    assert details(post(client, type="deposit", fromAccount=..., toAccount=...)) == {
        "toAccount": "toAccount is required for deposit"
    }


def test_withdrawal_requires_from_account(client):
    assert details(post(client, type="withdrawal", toAccount=..., fromAccount=...)) == {
        "fromAccount": "fromAccount is required for withdrawal"
    }


@pytest.mark.parametrize("missing", ["fromAccount", "toAccount"])
def test_transfer_requires_both_accounts(client, missing):
    assert missing in details(post(client, **{missing: ...}))


def test_transfer_accounts_must_differ(client):
    assert details(post(client, toAccount="ACC-12345")) == {
        "toAccount": "toAccount must differ from fromAccount"
    }


def test_invalid_json(client):
    r = client.post("/transactions", content="{oops", headers={"content-type": "application/json"})
    assert details(r) == {"body": "Request body must be valid JSON"}


def test_missing_body(client):
    assert details(client.post("/transactions")) == {"body": "Field is required"}


def test_invalid_request_is_not_stored(client):
    post(client, amount=-1)
    assert client.get("/transactions").json() == []


def test_deposit_rejects_from_account(client):
    assert details(post(client, type="deposit")) == {
        "fromAccount": "fromAccount must not be set for deposit"
    }


def test_withdrawal_rejects_to_account(client):
    assert details(post(client, type="withdrawal")) == {
        "toAccount": "toAccount must not be set for withdrawal"
    }


def test_deposit_does_not_debit_other_account(client):
    """Regression: a deposit naming a source account used to be accepted and debit it."""
    assert post(client, type="deposit", amount=50).status_code == 400
    assert client.get("/accounts/ACC-12345/balance").json()["balances"] == {}
