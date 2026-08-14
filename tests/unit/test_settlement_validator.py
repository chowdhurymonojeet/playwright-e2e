"""Tests for deep settlement validator interface.

These tests demonstrate the validator answering domain questions
rather than exposing raw SQL results.
"""

from __future__ import annotations

import pytest

from src.db.postgres_client import PostgresClient
from src.db.validators import SettlementValidator


@pytest.fixture
def mock_db_client(monkeypatch: pytest.MonkeyPatch) -> PostgresClient:
    """Mock PostgresClient that returns canned responses."""

    class MockClient:
        def __init__(self) -> None:
            self.queries: list[str] = []

        def fetch_one(self, query: str, **params: dict) -> dict | None:
            self.queries.append(query)
            settlement_id = params.get("settlement_id")

            if settlement_id == "STL-COMPLETE":
                return {"id": settlement_id, "status": "completed"}
            elif settlement_id == "STL-PENDING":
                return {"id": settlement_id, "status": "pending"}
            return None

        def fetch_all(self, query: str, **params: dict) -> list[dict]:
            self.queries.append(query)
            settlement_id = params.get("settlement_id")
            borrower_id = params.get("borrower_id")

            # Mock audit events for complete settlement
            if settlement_id == "STL-COMPLETE" and "audit_events" in query:
                return [
                    {"event_type": "settlement.created"},
                    {"event_type": "settlement.validated"},
                    {"event_type": "settlement.submitted"},
                    {"event_type": "settlement.completed"},
                ]
            elif settlement_id == "STL-PENDING" and "audit_events" in query:
                return [
                    {"event_type": "settlement.created"},
                ]

            # Mock borrower settlements
            if borrower_id == "BOR-001" and "borrower_id" in query:
                return [
                    {"id": "STL-001", "status": "completed"},
                    {"id": "STL-002", "status": "completed"},
                    {"id": "STL-003", "status": "pending"},
                ]

            return []

    return MockClient()  # type: ignore[return-value]


def test_assert_workflow_completed_correctly_passes_for_complete_workflow(
    mock_db_client: PostgresClient,
) -> None:
    """Domain question: Was workflow completed correctly? Yes."""
    validator = SettlementValidator(mock_db_client)

    result = validator.assert_workflow_completed_correctly("STL-COMPLETE")

    assert result.settlement_id == "STL-COMPLETE"
    assert result.status == "completed"
    assert result.is_completed is True
    assert result.has_complete_audit_trail is True
    assert result.missing_audit_events == []


def test_assert_workflow_completed_correctly_fails_for_incomplete_status(
    mock_db_client: PostgresClient,
) -> None:
    """Domain question: Was workflow completed correctly? No - wrong status."""
    validator = SettlementValidator(mock_db_client)

    with pytest.raises(
        AssertionError, match="Settlement STL-PENDING workflow incomplete: status=pending"
    ):
        validator.assert_workflow_completed_correctly("STL-PENDING")


def test_assert_workflow_completed_correctly_fails_for_missing_settlement(
    mock_db_client: PostgresClient,
) -> None:
    """Domain question: Was workflow completed correctly? No - doesn't exist."""
    validator = SettlementValidator(mock_db_client)

    with pytest.raises(
        AssertionError, match="Settlement STL-MISSING does not exist in database"
    ):
        validator.assert_workflow_completed_correctly("STL-MISSING")


def test_get_borrower_settlement_history_returns_domain_summary(
    mock_db_client: PostgresClient,
) -> None:
    """Domain question: What settlements exist for this borrower?"""
    validator = SettlementValidator(mock_db_client)

    history = validator.get_borrower_settlement_history("BOR-001")

    assert history.borrower_id == "BOR-001"
    assert history.total_settlements == 3
    assert history.completed_count == 2
    assert history.pending_count == 1
    assert history.failed_count == 0
    assert history.settlement_ids == ["STL-001", "STL-002", "STL-003"]


def test_legacy_method_still_works_for_backward_compatibility(
    mock_db_client: PostgresClient,
) -> None:
    """Legacy shallow interface maintained for backward compatibility."""
    validator = SettlementValidator(mock_db_client)

    result = validator.assert_settlement_persisted(
        "STL-COMPLETE", expected_status="completed"
    )

    assert result.settlement_id == "STL-COMPLETE"
    assert result.status == "completed"
    # Legacy method doesn't check audit trail
    assert result.has_complete_audit_trail is False
