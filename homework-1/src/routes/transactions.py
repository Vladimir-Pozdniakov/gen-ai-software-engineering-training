from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query, Response, status
from fastapi.exceptions import RequestValidationError
from pydantic import AfterValidator

from src.models import Transaction, TransactionCreate, TransactionType
from src.services import transactions_to_csv
from src.storage import StoreDep
from src.validators import validate_account

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("", response_model=Transaction, status_code=status.HTTP_201_CREATED)
def create_transaction(body: TransactionCreate, store: StoreDep) -> Transaction:
    return store.add(body)


@router.get("", response_model=list[Transaction])
def list_transactions(
    store: StoreDep,
    account_id: Annotated[
        str | None,
        AfterValidator(lambda v: v if v is None else validate_account(v)),
        Query(
            alias="accountId",
            description="Match transactions where the account is sender or receiver",
        ),
    ] = None,
    type_: Annotated[TransactionType | None, Query(alias="type")] = None,
    date_from: Annotated[
        date | None, Query(alias="from", description="Inclusive start date, YYYY-MM-DD")
    ] = None,
    date_to: Annotated[
        date | None, Query(alias="to", description="Inclusive end date, YYYY-MM-DD")
    ] = None,
) -> list[Transaction]:
    if date_from and date_to and date_from > date_to:
        raise RequestValidationError(
            [
                {
                    "type": "value_error",
                    "loc": ("query", "to"),
                    "msg": "'to' must not be earlier than 'from'",
                }
            ]
        )
    return store.list(account_id=account_id, type_=type_, date_from=date_from, date_to=date_to)


# Declared before "/{transaction_id}" so "export" isn't captured as an id.
@router.get("/export")
def export_transactions(
    store: StoreDep, format_: Annotated[Literal["csv"], Query(alias="format")] = "csv"
) -> Response:
    return Response(
        content=transactions_to_csv(store.list()),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="transactions.csv"'},
    )


@router.get("/{transaction_id}", response_model=Transaction)
def get_transaction(transaction_id: str, store: StoreDep) -> Transaction:
    transaction = store.get(transaction_id)
    if transaction is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Transaction not found")
    return transaction
