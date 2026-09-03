from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime
from uuid import uuid4


@dataclass(frozen=True, slots=True)
class TestContext:
    __test__ = False

    run_id: str
    correlation_id: str
    created_at: datetime
    borrower_reference: str | None = None
    settlement_id: str | None = None

    @classmethod
    def new(cls, prefix: str = "cg") -> "TestContext":
        identifier = uuid4().hex[:12]
        return cls(
            run_id=f"{prefix}-{identifier}",
            correlation_id=str(uuid4()),
            created_at=datetime.now(tz=UTC),
        )

    def with_borrower_reference(self, borrower_reference: str) -> "TestContext":
        return replace(self, borrower_reference=borrower_reference)

    def with_settlement_id(self, settlement_id: str) -> "TestContext":
        return replace(self, settlement_id=settlement_id)
