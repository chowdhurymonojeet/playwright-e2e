from __future__ import annotations

from typing import TYPE_CHECKING

from src.pages.base_page import BasePage

if TYPE_CHECKING:
    from src.pages.dashboard_page import DashboardPage
    from typing_extensions import Self


class LoginPage(BasePage):
    path = "/login"

    def open(self: Self) -> Self:
        """Navigate to login page. Returns self for chaining."""
        self.goto(self.path)
        return self

    def login(self, username: str, password: str) -> DashboardPage:
        """Submit credentials and navigate to dashboard. Returns DashboardPage."""
        self.by_test_id("username-input").fill(username)
        self.by_test_id("password-input").fill(password)
        self.by_test_id("login-submit").click()
        self.page.wait_for_load_state("networkidle")

        # Import here to avoid circular dependency
        from src.pages.dashboard_page import DashboardPage
        return DashboardPage(self.page)
