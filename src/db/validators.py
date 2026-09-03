from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING

from src.db.postgres_client import PostgresClient

if TYPE_CHECKING:
    from src.services.test_context import TestContext


@dataclass(frozen=True, slots=True)
class SettlementWorkflowResult:
    """Domain answer: Was the settlement workflow completed correctly?"""

    settlement_id: str
    status: str
    is_completed: bool
    has_complete_audit_trail: bool
    missing_audit_events: list[str]


@dataclass(frozen=True, slots=True)
class BorrowerSettlementHistory:
    """Domain answer: What settlements exist for this borrower?"""

    borrower_id: str
    total_settlements: int
    completed_count: int
    pending_count: int
    failed_count: int
    settlement_ids: list[str]


class SettlementValidator:
    """Deep module: answers domain questions about settlement correctness.

    Small interface hiding complex SQL + business logic. Methods answer
    "Was workflow completed correctly?" rather than exposing raw SQL results.
    """

    # Expected audit events for complete settlement workflow
    REQUIRED_AUDIT_EVENTS = [
        "settlement.created",
        "settlement.validated",
        "settlement.submitted",
        "settlement.completed",
    ]

    def __init__(self, client: PostgresClient) -> None:
        self.client = client

    async def assert_workflow_completed_correctly(
        self,
        settlement_id: str,
    ) -> SettlementWorkflowResult:
        """Domain question: Was the settlement workflow completed correctly?

        Verifies:
        - Settlement exists
        - Status is 'completed'
        - All required audit events present

        Args:
            settlement_id: Settlement to verify.

        Returns:
            SettlementWorkflowResult with completion status and missing events.

        Raises:
            AssertionError: When settlement doesn't exist or workflow incomplete.
        """
        # Query settlement status
        settlement_row = await self.client.fetch_one(
            "SELECT id, status FROM settlements WHERE id = :settlement_id",
            settlement_id=settlement_id,
        )
        if settlement_row is None:
            raise AssertionError(
                f"Settlement {settlement_id} does not exist in database"
            )

        status = str(settlement_row["status"])
        is_completed = status == "completed"

        # Query audit trail
        audit_rows = await self.client.fetch_all(
            "SELECT event_type FROM settlement_audit_events WHERE settlement_id = :settlement_id",
            settlement_id=settlement_id,
        )
        actual_events = {str(row["event_type"]) for row in audit_rows}

        # Check for missing required events
        missing_events = [
            event for event in self.REQUIRED_AUDIT_EVENTS if event not in actual_events
        ]
        has_complete_audit_trail = len(missing_events) == 0

        result = SettlementWorkflowResult(
            settlement_id=settlement_id,
            status=status,
            is_completed=is_completed,
            has_complete_audit_trail=has_complete_audit_trail,
            missing_audit_events=missing_events,
        )

        # Domain assertion: workflow must be complete
        if not is_completed:
            raise AssertionError(
                f"Settlement {settlement_id} workflow incomplete: status={status}"
            )

        if not has_complete_audit_trail:
            raise AssertionError(
                f"Settlement {settlement_id} missing audit events: {missing_events}"
            )

        return result

    async def get_borrower_settlement_history(
        self,
        borrower_id: str,
    ) -> BorrowerSettlementHistory:
        """Domain question: What settlements exist for this borrower?

        Args:
            borrower_id: Borrower to query.

        Returns:
            BorrowerSettlementHistory with settlement counts and IDs.
        """
        settlements = await self.client.fetch_all(
            """
            SELECT id, status
            FROM settlements
            WHERE borrower_id = :borrower_id
            ORDER BY created_at DESC
            """,
            borrower_id=borrower_id,
        )

        settlement_ids = [str(row["id"]) for row in settlements]
        completed = sum(1 for row in settlements if row["status"] == "completed")
        pending = sum(1 for row in settlements if row["status"] == "pending")
        failed = sum(1 for row in settlements if row["status"] == "failed")

        return BorrowerSettlementHistory(
            borrower_id=borrower_id,
            total_settlements=len(settlements),
            completed_count=completed,
            pending_count=pending,
            failed_count=failed,
            settlement_ids=settlement_ids,
        )

    async def assert_no_duplicate_settlements(
        self,
        borrower_id: str,
        amount: Decimal,
        *,
        tolerance_seconds: int = 60,
    ) -> None:
        """Domain question: Are there duplicate settlements for this borrower?

        Checks for settlements with same borrower + amount within time window.

        Args:
            borrower_id: Borrower to check.
            amount: Settlement amount.
            tolerance_seconds: Time window for duplicate detection.

        Raises:
            AssertionError: When duplicates found.
        """
        duplicates = await self.client.fetch_all(
            """
            SELECT id, created_at
            FROM settlements
            WHERE borrower_id = :borrower_id
              AND amount = :amount
              AND created_at >= NOW() - (:tolerance * INTERVAL '1 second')
            ORDER BY created_at DESC
            """,
            borrower_id=borrower_id,
            amount=amount,
            tolerance=tolerance_seconds,
        )

        if len(duplicates) > 1:
            duplicate_ids = [str(row["id"]) for row in duplicates]
            raise AssertionError(
                f"Found {len(duplicates)} duplicate settlements for borrower {borrower_id} "
                f"with amount {amount}: {duplicate_ids}"
            )

    # Legacy method (shallow interface - kept for backward compatibility)
    async def assert_settlement_persisted(
        self,
        settlement_id: str,
        *,
        expected_status: str | None = None,
    ) -> SettlementWorkflowResult:
        """Legacy: verify settlement exists with optional status check.

        Deprecated: Use assert_workflow_completed_correctly() instead for
        domain-level validation.
        """
        settlement_row = await self.client.fetch_one(
            "SELECT id, status FROM settlements WHERE id = :settlement_id",
            settlement_id=settlement_id,
        )
        if settlement_row is None:
            raise AssertionError(f"Settlement {settlement_id} was not persisted")

        actual_status = str(settlement_row["status"])
        if expected_status and actual_status != expected_status:
            raise AssertionError(
                f"Settlement {settlement_id} has status {actual_status}; "
                f"expected {expected_status}"
            )

        # Return minimal result (not checking audit trail)
        return SettlementWorkflowResult(
            settlement_id=settlement_id,
            status=actual_status,
            is_completed=(actual_status == "completed"),
            has_complete_audit_trail=False,  # Not checked
            missing_audit_events=[],
        )
