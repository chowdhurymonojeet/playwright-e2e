"""Per-test asynchronous orchestration module."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from playwright.async_api import Page

from src.api.client_factory import create_settlement_api
from src.api.settlement_api import SettlementApi
from src.config.settings import Settings
from src.db.postgres_client import PostgresClient
from src.pages.browser_factory import BrowserSession
from src.services.test_context import TestContext


class TestRun:
    """Own all resources and evidence for one isolated test execution.

    The interface deliberately exposes domain adapters and a ready page, while
    browser, HTTP, tracing, and teardown ordering remain implementation details.
    """

    __test__ = False

    def __init__(
        self,
        settings: Settings | None = None,
        context: TestContext | None = None,
    ) -> None:
        self.settings = settings or Settings.from_env()
        self.context = context or TestContext.new()
        self.artifact_dir = self.settings.artifacts_dir / self.context.run_id
        self.browser_session = BrowserSession(
            self.settings, self.context, self.artifact_dir
        )
        self.page: Page | None = None
        self.api: SettlementApi | None = None
        self.database: PostgresClient | None = None
        self._failed = False

    async def __aenter__(self) -> "TestRun":
        self.artifact_dir.mkdir(parents=True, exist_ok=True)
        return self

    async def get_page(self) -> Page:
        """Lazily open the browser resources needed by a UI workflow."""
        if self.page is None:
            try:
                await self.browser_session.__aenter__()
                self.page = await self.browser_session.new_page()
            except BaseException:
                await self.browser_session.__aexit__()
                raise
        return self.page

    async def get_api(self) -> SettlementApi:
        """Lazily open the HTTP client needed by an API workflow."""
        if self.api is None:
            self.api = await create_settlement_api(
                settings=self.settings, context=self.context
            )
        return self.api

    def get_database(self) -> PostgresClient | None:
        """Return the optional database adapter for environments that configure one."""
        if self.database is None and self.settings.db_dsn:
            self.database = PostgresClient(self.settings.db_dsn, context=self.context)
        return self.database

    def mark_failed(self) -> None:
        """Record a pytest failure for asynchronous teardown evidence capture."""
        self._failed = True

    async def __aexit__(self, *args: Any) -> None:
        if self._failed:
            await self._capture_failure_artifacts()
        if self.api is not None:
            await self.api.aclose()
        if self.database is not None:
            await self.database.aclose()
        if self.page is not None:
            await self.browser_session.__aexit__(*args)

    async def _capture_failure_artifacts(self) -> None:
        if self.page is None:
            return
        try:
            screenshot = await self.page.screenshot(full_page=True)
            (self.artifact_dir / "failure.png").write_bytes(screenshot)
            (self.artifact_dir / "failure.html").write_text(
                await self.page.content(), encoding="utf-8"
            )
        except Exception as error:
            (self.artifact_dir / "artifact-capture-error.txt").write_text(
                repr(error), encoding="utf-8"
            )
