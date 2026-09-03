from __future__ import annotations

import pytest
from playwright.async_api import Page

from src.pages.login_page import LoginPage


@pytest.mark.ui
async def test_login_navigates_to_dashboard(page: Page) -> None:
    login = LoginPage(page)
    await login.open()
    dashboard = await login.login("test@example.com", "password123")
    await dashboard.expect_loaded()
    assert dashboard is not None


@pytest.mark.ui
async def test_dashboard_actions_are_sequential(page: Page) -> None:
    login = LoginPage(page)
    await login.open()
    dashboard = await login.login("test@example.com", "password123")
    await dashboard.expect_loaded()
    await dashboard.search_borrower("BOR-001")
    await dashboard.open_settlement_drawer()
    assert dashboard is not None
