"""Business logic over the store (pure functions, no HTTP concerns)."""

import csv
import io
from collections import defaultdict
from decimal import Decimal

from src.models import Transaction, TransactionStatus, TransactionType
from src.storage import TransactionStore


def compute_balances(store: TransactionStore, account_id: str) -> dict[str, Decimal]:
    """Per-currency balance: incoming minus outgoing over *completed* transactions.

    Currencies are never mixed, so the result maps currency code -> balance.
    """
    balances: dict[str, Decimal] = defaultdict(Decimal)
    for t in store.list(account_id=account_id):
        if t.status is not TransactionStatus.COMPLETED:
            continue
        if t.to_account == account_id:
            balances[t.currency] += t.amount
        if t.from_account == account_id:
            balances[t.currency] -= t.amount
    return dict(balances)


def compute_summary(store: TransactionStore, account_id: str) -> dict:
    """Totals per currency (never mixed) plus count and latest timestamp for one account.

    * ``totalDeposits``: completed deposits credited to the account
    * ``totalWithdrawals``: completed withdrawals debited from the account
    * ``transactionCount``: every transaction involving the account (any type/status)
    """
    deposits: dict[str, Decimal] = defaultdict(Decimal)
    withdrawals: dict[str, Decimal] = defaultdict(Decimal)
    transactions = store.list(account_id=account_id)
    for t in transactions:
        if t.status is not TransactionStatus.COMPLETED:
            continue
        if t.type is TransactionType.DEPOSIT:
            deposits[t.currency] += t.amount
        elif t.type is TransactionType.WITHDRAWAL:
            withdrawals[t.currency] += t.amount
    latest = max((t.timestamp for t in transactions), default=None)
    return {
        "accountId": account_id,
        "totalDeposits": {c: float(v) for c, v in deposits.items()},
        "totalWithdrawals": {c: float(v) for c, v in withdrawals.items()},
        "transactionCount": len(transactions),
        "mostRecentTransaction": latest.isoformat().replace("+00:00", "Z") if latest else None,
    }


CSV_COLUMNS = [
    "id",
    "fromAccount",
    "toAccount",
    "amount",
    "currency",
    "type",
    "timestamp",
    "status",
]


def transactions_to_csv(transactions: list[Transaction]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(CSV_COLUMNS)
    for t in transactions:
        writer.writerow(
            [
                t.id,
                t.from_account or "",
                t.to_account or "",
                f"{t.amount:.2f}",
                t.currency,
                t.type.value,
                t.timestamp.isoformat().replace("+00:00", "Z"),
                t.status.value,
            ]
        )
    return buffer.getvalue()
