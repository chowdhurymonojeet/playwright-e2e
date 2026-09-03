from __future__ import annotations

from src.pages.base_page import BasePage


class LoginPage(BasePage):
    path = "/login"

    async def open(self) -> None:
        """Navigate to the login page."""
        await self.goto(self.path)

    async def login(self, username: str, password: str) -> "DashboardPage":
        """Submit credentials and return the dashboard module."""
        await self._by_test_id("username-input").fill(username)
        await self._by_test_id("password-input").fill(password)
        await self._by_test_id("login-submit").click()

        from src.pages.dashboard_page import DashboardPage

        return DashboardPage(self.page)
