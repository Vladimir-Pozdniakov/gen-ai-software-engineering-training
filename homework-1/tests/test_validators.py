from decimal import Decimal

import pytest

from src.validators import ISO_4217_CODES, parse_amount, validate_account, validate_currency


def test_parse_amount_valid():
    assert parse_amount(100.5) == Decimal("100.5")
    assert parse_amount(3) == Decimal(3)
    assert parse_amount(Decimal("0.01")) == Decimal("0.01")
    assert parse_amount(1.10) == Decimal("1.1")


@pytest.mark.parametrize("bad", [0, -1, float("nan"), float("inf"), "5", None, True])
def test_parse_amount_rejects(bad):
    with pytest.raises(ValueError, match="positive"):
        parse_amount(bad)


def test_parse_amount_decimal_places():
    with pytest.raises(ValueError, match="2 decimal"):
        parse_amount(1.001)


def test_validate_account():
    assert validate_account("ACC-ab12Z") == "ACC-ab12Z"
    for bad in ("ACC-1234", "ACC-123456", "ACC_12345", "ACC-1234 ", "ACC-12345\n"):
        with pytest.raises(ValueError, match="ACC-XXXXX"):
            validate_account(bad)


def test_currency_list():
    assert {"USD", "EUR", "GBP", "JPY"} <= ISO_4217_CODES
    assert "XXX" not in ISO_4217_CODES
    assert validate_currency("CHF") == "CHF"
    with pytest.raises(ValueError, match="Invalid currency"):
        validate_currency("ABC")


def test_currency_rejects_non_strings():
    for bad in (5, None, ["USD"]):
        with pytest.raises(ValueError, match="Invalid currency"):
            validate_currency(bad)
