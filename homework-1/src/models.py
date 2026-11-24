"""Pydantic models for the banking transactions API.

Input/output JSON uses camelCase (``fromAccount``); Python attributes use snake_case.
Business validation (amount rules, account format, currency, per-type account rules)
is added in ``validators.py`` (Step 3).
"""

from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Self
from uuid import uuid4

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_serializer,
    field_validator,
    model_validator,
)
from pydantic.alias_generators import to_camel
from pydantic_core import InitErrorDetails, PydanticCustomError

from src.validators import parse_amount, validate_account, validate_currency


class TransactionType(StrEnum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER = "transfer"


class TransactionStatus(StrEnum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class CamelModel(BaseModel):
    """Base model: camelCase aliases, populate by either name."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class TransactionCreate(CamelModel):
    """Request body for ``POST /transactions``."""

    from_account: str | None = None
    to_account: str | None = None
    amount: Decimal
    currency: str
    type: TransactionType

    @field_validator("amount", mode="before")
    @classmethod
    def _check_amount(cls, value: object) -> Decimal:
        return parse_amount(value)

    @field_validator("from_account", "to_account")
    @classmethod
    def _check_account(cls, value: str | None) -> str | None:
        return None if value is None else validate_account(value)

    @field_validator("currency", mode="before")
    @classmethod
    def _check_currency(cls, value: object) -> str:
        return validate_currency(value)

    @model_validator(mode="after")
    def _check_accounts_for_type(self) -> Self:
        """deposit -> toAccount; withdrawal -> fromAccount; transfer -> both, different."""
        errors: list[tuple[str, str]] = []
        needs_from = self.type in (TransactionType.WITHDRAWAL, TransactionType.TRANSFER)
        needs_to = self.type in (TransactionType.DEPOSIT, TransactionType.TRANSFER)
        if needs_from and self.from_account is None:
            errors.append(("fromAccount", f"fromAccount is required for {self.type}"))
        if needs_to and self.to_account is None:
            errors.append(("toAccount", f"toAccount is required for {self.type}"))
        if (
            self.type is TransactionType.TRANSFER
            and self.from_account is not None
            and self.from_account == self.to_account
        ):
            errors.append(("toAccount", "toAccount must differ from fromAccount"))
        if errors:
            # Carry the offending field in ctx so the error handler (Step 6) can report it.
            raise ValidationError.from_exception_data(
                self.__class__.__name__,
                [
                    InitErrorDetails(
                        type=PydanticCustomError("account_rule", msg),
                        loc=(field,),
                        input=None,
                    )
                    for field, msg in errors
                ],
            )
        return self


class Transaction(CamelModel):
    """A stored transaction (response model)."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    from_account: str | None = None
    to_account: str | None = None
    amount: Decimal
    currency: str
    type: TransactionType
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    status: TransactionStatus = TransactionStatus.COMPLETED

    @field_serializer("amount")
    def _amount_as_number(self, value: Decimal) -> float:
        # Spec models amount as a JSON number; Decimal is kept internally for exact math.
        return float(value)
