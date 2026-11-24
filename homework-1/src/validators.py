"""Pure validation helpers (no dependency on the models, so no import cycles).

Each ``validate_*``/``parse_*`` function returns the normalized value or raises
``ValueError`` with the user-facing message returned in the API's error ``details``.
"""

import re
from decimal import Decimal

ACCOUNT_RE = re.compile(r"^ACC-[A-Za-z0-9]{5}$")

AMOUNT_POSITIVE_MSG = "Amount must be a positive number"
AMOUNT_DECIMALS_MSG = "Amount must have at most 2 decimal places"
ACCOUNT_FORMAT_MSG = "Account must follow format ACC-XXXXX (X is alphanumeric)"
CURRENCY_MSG = "Invalid currency code"

# Active ISO 4217 alphabetic codes.
ISO_4217_CODES: frozenset[str] = frozenset(
    """
    AED AFN ALL AMD ANG AOA ARS AUD AWG AZN BAM BBD BDT BGN BHD BIF BMD BND BOB BRL
    BSD BTN BWP BYN BZD CAD CDF CHF CLP CNY COP CRC CUP CVE CZK DJF DKK DOP DZD EGP
    ERN ETB EUR FJD FKP GBP GEL GHS GIP GMD GNF GTQ GYD HKD HNL HTG HUF IDR ILS INR
    IQD IRR ISK JMD JOD JPY KES KGS KHR KMF KPW KRW KWD KYD KZT LAK LBP LKR LRD LSL
    LYD MAD MDL MGA MKD MMK MNT MOP MRU MUR MVR MWK MXN MYR MZN NAD NGN NIO NOK NPR
    NZD OMR PAB PEN PGK PHP PKR PLN PYG QAR RON RSD RUB RWF SAR SBD SCR SDG SEK SGD
    SHP SLE SOS SRD SSP STN SVC SYP SZL THB TJS TMT TND TOP TRY TTD TWD TZS UAH UGX
    USD UYU UZS VES VND VUV WST XAF XCD XOF XPF YER ZAR ZMW ZWL
    """.split()  # noqa: SIM905
)


def parse_amount(value: object) -> Decimal:
    """Convert a JSON number to Decimal; must be finite, > 0, with <= 2 decimal places."""
    # bool is a subclass of int; strings are rejected so only real JSON numbers pass.
    if isinstance(value, bool) or not isinstance(value, int | float | Decimal):
        # ValueError (not TypeError): Pydantic only turns ValueError into a validation error.
        raise ValueError(AMOUNT_POSITIVE_MSG)  # noqa: TRY004
    amount = value if isinstance(value, Decimal) else Decimal(str(value))
    if not amount.is_finite() or amount <= 0:
        raise ValueError(AMOUNT_POSITIVE_MSG)
    if amount.as_tuple().exponent < -2 and amount != amount.quantize(Decimal("0.01")):
        raise ValueError(AMOUNT_DECIMALS_MSG)
    return amount


def validate_account(value: str) -> str:
    if not ACCOUNT_RE.fullmatch(value):
        raise ValueError(ACCOUNT_FORMAT_MSG)
    return value


def validate_currency(value: object) -> str:
    if not isinstance(value, str) or value not in ISO_4217_CODES:
        raise ValueError(CURRENCY_MSG)
    return value
