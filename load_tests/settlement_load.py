from __future__ import annotations

import os

from locust import HttpUser, between, task

from src.api.locust_settlement_api import LocustSettlementApi


class SettlementLoadUser(HttpUser):
    wait_time = between(1, 3)
    host = os.getenv("CG_API_BASE_URL", "http://localhost:8000")

    def on_start(self) -> None:
        token = os.getenv("CG_API_TOKEN", "")
        self.settlement_api = LocustSettlementApi(self.client, token=token)

    @task
    def list_borrower_settlements(self) -> None:
        borrower_id = os.getenv("CG_LOAD_BORROWER_ID", "load-test-borrower")
        self.settlement_api.list_settlements(borrower_id)
