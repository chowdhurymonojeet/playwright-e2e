from __future__ import annotations

import pytest
from playwright.sync_api import Page

from src.pages.login_page import LoginPage


@pytest.mark.ui
def test_login_navigates_to_dashboard(page: Page) -> None:
    """Fluent interface: login returns DashboardPage for type-safe chaining."""
    dashboard = (
        LoginPage(page)
        .open()
        .login("test@example.com", "password123")
        .expect_loaded()
    )

    # Type system guides navigation
    assert dashboard is not None


@pytest.mark.ui
def test_dashboard_actions_are_chainable(page: Page) -> None:
    """Fluent interface: dashboard methods return self for chaining."""
    dashboard = (
        LoginPage(page)
        .open()
        .login("test@example.com", "password123")
        .expect_loaded()
        .search_borrower("BOR-001")
        .open_settlement_drawer()
    )

    assert dashboard is not None
