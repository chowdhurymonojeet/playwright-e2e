from __future__ import annotations

from pathlib import Path
from typing import Generator

import pytest
from playwright.sync_api import Browser, BrowserContext, Page

from src.api.client_factory import create_settlement_api
from src.api.settlement_api import SettlementApi
from src.config.settings import Settings
from src.data_factory.borrower_factory import BorrowerFactory
from src.pages.browser_factory import create_browser_context, create_page
from src.services.test_context import TestContext

# Register pytest plugins
pytest_plugins = ["tests.pytest_plugins.reporter"]


@pytest.fixture(scope="session")
def settings() -> Settings:
    resolved = Settings.from_env()
    resolved.artifacts_dir.mkdir(parents=True, exist_ok=True)
    return resolved


@pytest.fixture
def settlement_api() -> SettlementApi:
    """Configured SettlementApi client using factory.

    All wiring (Settings, token, session) handled by factory.
    """
    return create_settlement_api()


@pytest.fixture(scope="session")
def browser_context(settings: Settings) -> Generator[tuple[BrowserContext, Browser], None, None]:
    """Configured Playwright browser context using factory.

    Scope is session to reuse browser across tests for performance.
    """
    context, browser = create_browser_context(settings=settings)
    yield (context, browser)
    # Cleanup
    context.close()
    browser.close()


@pytest.fixture
def page(browser_context: tuple[BrowserContext, Browser]) -> Generator[Page, None, None]:
    """Fresh Playwright page for each test.

    Uses session-scoped browser context but creates new page per test
    for isolation.
    """
    context, _ = browser_context
    page = context.new_page()
    yield page
    page.close()


@pytest.fixture
def borrower_factory() -> BorrowerFactory:
    return BorrowerFactory()


@pytest.fixture
def test_context() -> TestContext:
    return TestContext.new()


@pytest.fixture
def artifact_path(
    settings: Settings,
    request: pytest.FixtureRequest,
) -> Path:
    node_name = (
        request.node.nodeid.replace("/", "_")
        .replace("::", "__")
        .replace("[", "_")
        .replace("]", "")
    )
    destination = settings.artifacts_dir / node_name
    destination.mkdir(parents=True, exist_ok=True)
    return destination
