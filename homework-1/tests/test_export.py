import csv
import io


def test_export_csv(client, make_tx):
    a = make_tx(amount=10)
    b = make_tx(type="deposit", fromAccount=None, toAccount="ACC-12345", amount=5.5)
    r = client.get("/transactions/export?format=csv")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/csv")
    assert "attachment" in r.headers["content-disposition"]
    rows = list(csv.DictReader(io.StringIO(r.text)))
    assert list(rows[0]) == [
        "id", "fromAccount", "toAccount", "amount", "currency", "type", "timestamp", "status",
    ]  # fmt: skip
    assert [row["id"] for row in rows] == [a["id"], b["id"]]
    assert rows[0]["amount"] == "10.00"
    assert rows[1]["amount"] == "5.50"
    assert rows[1]["fromAccount"] == ""
    assert rows[1]["timestamp"] == b["timestamp"]


def test_export_empty_is_header_only(client):
    r = client.get("/transactions/export")
    assert r.status_code == 200
    assert r.text.strip().count("\n") == 0


def test_export_not_captured_by_id_route(client):
    assert client.get("/transactions/export").headers["content-type"].startswith("text/csv")


def test_export_unsupported_format(client):
    r = client.get("/transactions/export?format=xml")
    assert r.status_code == 400
    assert r.json()["details"][0]["field"] == "format"
