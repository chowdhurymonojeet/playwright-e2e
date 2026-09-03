"""Synchronous settlement adapter for Locust's gevent HTTP client.

Functional tests use :class:`SettlementApi`, whose interface is asynchronous.
Locust supplies a synchronous, instrumented client, so it needs this separate
adapter rather than leaking a sync-or-async session option into that interface.
"""

from __future__ import annotations

from typing import Any

from src.models.settlement_models import SettlementRecord


class LocustSettlementApi:
    """Small adapter over a Locust HTTP session for load scenarios."""

    SETTLEMENTS_PATH = "/settlements"

    def __init__(self, session: Any, *, token: str) -> None:
        if not token:
            raise ValueError("CG_API_TOKEN is required for Locust load tests")
        self.session = session
        self._headers = {"Authorization": f"Bearer {token}"}

    def list_settlements(self, borrower_id: str) -> list[SettlementRecord]:
        response = self.session.get(
            self.SETTLEMENTS_PATH,
            headers=self._headers,
            params={"borrower_id": borrower_id},
            name="settlements:list",
        )
        response.raise_for_status()
        return [SettlementRecord.model_validate(item) for item in response.json()]
