from __future__ import annotations

from src.pages.base_page import BasePage


class DashboardPage(BasePage):
    async def expect_loaded(self) -> None:
        """Assert dashboard-specific readiness after navigation."""
        await self._expect_visible(self._by_test_id("dashboard-shell"))

    async def search_borrower(self, borrower_reference: str) -> None:
        """Search for a borrower by reference."""
        await self._by_test_id("borrower-search-input").fill(borrower_reference)
        await self._by_test_id("borrower-search-submit").click()

    async def open_settlement_drawer(self) -> None:
        """Open the settlement drawer."""
        await self._by_test_id("settlement-drawer-trigger").click()
