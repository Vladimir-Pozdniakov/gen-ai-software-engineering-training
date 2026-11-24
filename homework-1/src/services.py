"""Business logic over the store (pure functions, no HTTP concerns)."""

from collections import defaultdict
from decimal import Decimal

from src.models import TransactionStatus
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
