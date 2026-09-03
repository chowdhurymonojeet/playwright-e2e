from __future__ import annotations

from typing import TYPE_CHECKING

import httpx

from src.api.base_client import BaseClient
from src.models.settlement_models import SettlementCreateRequest, SettlementRecord

if TYPE_CHECKING:
    from src.services.test_context import TestContext


class SettlementApi(BaseClient):
    """Domain-level client for settlement workflows."""

    SETTLEMENTS_PATH = "/settlements"

    def __init__(
        self,
        base_url: str,
        *,
        token: str | None = None,
        timeout_seconds: float = 15.0,
        session: httpx.AsyncClient | None = None,
        context: TestContext | None = None,
    ) -> None:
        super().__init__(
            base_url,
            timeout_seconds=timeout_seconds,
            session=session,
            context=context,
        )
        self._headers: dict[str, str] = {}
        if token:
            self.set_token(token)

    def set_token(self, token: str) -> None:
        self._headers["Authorization"] = f"Bearer {token}"

    async def create_settlement(
        self, request: SettlementCreateRequest
    ) -> SettlementRecord:
        payload = await self.get_json(
            "POST",
            self.SETTLEMENTS_PATH,
            expected_status=(200, 201),
            headers=self._headers,
            json=request.model_dump(mode="json"),
        )
        return SettlementRecord.model_validate(payload)

    async def get_settlement(self, settlement_id: str) -> SettlementRecord:
        payload = await self.get_json(
            "GET",
            f"{self.SETTLEMENTS_PATH}/{settlement_id}",
            expected_status=200,
            headers=self._headers,
        )
        return SettlementRecord.model_validate(payload)

    async def list_settlements(self, borrower_id: str) -> list[SettlementRecord]:
        payload = await self.get_json(
            "GET",
            self.SETTLEMENTS_PATH,
            expected_status=200,
            headers=self._headers,
            params={"borrower_id": borrower_id},
        )
        return [SettlementRecord.model_validate(item) for item in payload]
