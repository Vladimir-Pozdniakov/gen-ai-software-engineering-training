from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.exceptions import RequestValidationError

from src.services import compute_balances
from src.storage import StoreDep
from src.validators import validate_account

router = APIRouter(prefix="/accounts", tags=["accounts"])


def valid_account_id(account_id: str) -> str:
    """Path dependency: reject malformed ids as a validation error (HTTP 400 after Step 6)."""
    try:
        return validate_account(account_id)
    except ValueError as exc:
        raise RequestValidationError(
            [{"type": "value_error", "loc": ("path", "accountId"), "msg": str(exc)}]
        ) from None


AccountId = Annotated[str, Depends(valid_account_id)]


@router.get("/{account_id}/balance")
def get_balance(
    account_id: AccountId,
    store: StoreDep,
) -> dict:
    balances = compute_balances(store, account_id)
    return {"accountId": account_id, "balances": {c: float(v) for c, v in balances.items()}}
