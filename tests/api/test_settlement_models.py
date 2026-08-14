from __future__ import annotations

from decimal import Decimal

import pytest
from pydantic import ValidationError

from src.models.settlement_models import (
    SettlementCreateRequest,
    SettlementRecord,
    SettlementStatus,
)


@pytest.mark.api
def test_settlement_request_rejects_non_positive_amount() -> None:
    with pytest.raises(ValidationError):
        SettlementCreateRequest(
            borrower_id="borrower-123",
            amount=Decimal("0"),
            reason="Initial settlement",
        )


@pytest.mark.api
def test_settlement_record_parses_api_payload() -> None:
    payload = {
        "id": "set-123",
        "borrower_id": "borrower-123",
        "status": "pending",
        "amount": "150.25",
        "currency": "USD",
        "created_at": "2026-08-13T09:30:00Z",
    }

    record = SettlementRecord.model_validate(payload)

    assert record.settlement_id == "set-123"
    assert record.borrower_id == "borrower-123"
    assert record.status is SettlementStatus.pending
    assert record.amount == Decimal("150.25")
