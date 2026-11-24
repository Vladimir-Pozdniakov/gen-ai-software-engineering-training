from fastapi import APIRouter, HTTPException, status

from src.models import Transaction, TransactionCreate
from src.storage import StoreDep

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("", response_model=Transaction, status_code=status.HTTP_201_CREATED)
def create_transaction(body: TransactionCreate, store: StoreDep) -> Transaction:
    return store.add(body)


@router.get("", response_model=list[Transaction])
def list_transactions(store: StoreDep) -> list[Transaction]:
    return store.list()


@router.get("/{transaction_id}", response_model=Transaction)
def get_transaction(transaction_id: str, store: StoreDep) -> Transaction:
    transaction = store.get(transaction_id)
    if transaction is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Transaction not found")
    return transaction
