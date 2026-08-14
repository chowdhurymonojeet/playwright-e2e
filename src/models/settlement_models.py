from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class SettlementStatus(str, Enum):
    draft = "draft"
    pending = "pending"
    approved = "approved"
    completed = "completed"
    failed = "failed"


class SettlementCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    borrower_id: str
    amount: Decimal = Field(gt=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    reason: str = Field(min_length=3)
    due_date: date | None = None


class SettlementRecord(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    settlement_id: str = Field(alias="id")
    borrower_id: str
    status: SettlementStatus
    amount: Decimal
    currency: str
    created_at: datetime
