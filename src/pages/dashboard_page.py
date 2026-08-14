from __future__ import annotations

from typing import TYPE_CHECKING

from src.pages.base_page import BasePage

if TYPE_CHECKING:
    from typing_extensions import Self


class DashboardPage(BasePage):
    def expect_loaded(self: Self) -> Self:
        """Assert dashboard is fully loaded. Returns self for chaining."""
        self.expect_visible(self.by_test_id("dashboard-shell"))
        return self

    def search_borrower(self: Self, borrower_reference: str) -> Self:
        """Search for borrower by reference. Returns self for chaining."""
        self.by_test_id("borrower-search-input").fill(borrower_reference)
        self.by_test_id("borrower-search-submit").click()
        return self

    def open_settlement_drawer(self: Self) -> Self:
        """Open settlement drawer panel. Returns self for chaining."""
        self.by_test_id("settlement-drawer-trigger").click()
        return self
