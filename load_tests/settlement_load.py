from __future__ import annotations

import os

from locust import HttpUser, between, task

from src.api.client_factory import create_settlement_api
from src.api.settlement_api import SettlementApi


class SettlementLoadUser(HttpUser):
    wait_time = between(1, 3)
    host = os.getenv("CG_API_BASE_URL", "http://localhost:8000")

    def on_start(self) -> None:
        # Factory handles all wiring; just pass Locust's session for connection pooling
        self.settlement_api: SettlementApi = create_settlement_api(self.client)

    @task
    def list_borrower_settlements(self) -> None:
        borrower_id = os.getenv("CG_LOAD_BORROWER_ID", "load-test-borrower")
        self.settlement_api.list_settlements(borrower_id)
