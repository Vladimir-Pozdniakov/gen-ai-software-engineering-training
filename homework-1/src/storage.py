"""In-memory transaction storage (thread-safe, insertion-ordered)."""

from datetime import date
from threading import Lock

from src.models import Transaction, TransactionCreate, TransactionType


class TransactionStore:
    def __init__(self) -> None:
        self._items: dict[str, Transaction] = {}
        self._lock = Lock()

    def add(self, data: TransactionCreate) -> Transaction:
        """Create and persist a transaction (id, timestamp and status are assigned here)."""
        transaction = Transaction(**data.model_dump())
        with self._lock:
            self._items[transaction.id] = transaction
        return transaction

    def get(self, transaction_id: str) -> Transaction | None:
        with self._lock:
            return self._items.get(transaction_id)

    def list(
        self,
        *,
        account_id: str | None = None,
        type_: TransactionType | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> list[Transaction]:
        """Return transactions in creation order; all supplied filters are ANDed.

        ``account_id`` matches either side of the transaction. ``date_from`` and
        ``date_to`` are inclusive calendar days (UTC), so ``date_to`` covers the whole day.
        """
        with self._lock:
            items = list(self._items.values())
        return [
            t
            for t in items
            if (account_id is None or account_id in (t.from_account, t.to_account))
            and (type_ is None or t.type == type_)
            and (date_from is None or t.timestamp.date() >= date_from)
            and (date_to is None or t.timestamp.date() <= date_to)
        ]

    def clear(self) -> None:
        with self._lock:
            self._items.clear()


_store = TransactionStore()


def get_store() -> TransactionStore:
    """FastAPI dependency; override in tests via ``app.dependency_overrides``."""
    return _store
