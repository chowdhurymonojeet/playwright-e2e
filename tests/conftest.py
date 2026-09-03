from __future__ import annotations

from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
from playwright.async_api import Page

from src.api.settlement_api import SettlementApi
from src.config.settings import Settings
from src.data_factory.borrower_factory import BorrowerFactory
from src.services.test_context import TestContext
from src.services.test_run import TestRun

pytest_plugins = ["tests.pytest_plugins.reporter"]


@pytest.fixture(scope="session")
def settings() -> Settings:
    resolved = Settings.from_env()
    resolved.artifacts_dir.mkdir(parents=True, exist_ok=True)
    return resolved


@pytest.fixture
async def test_run(settings: Settings) -> AsyncGenerator[TestRun, None]:
    """One context, browser, API client, and artifact directory per test."""
    async with TestRun(settings) as run:
        yield run


@pytest.fixture
def test_context(test_run: TestRun) -> TestContext:
    return test_run.context


@pytest.fixture
async def settlement_api(test_run: TestRun) -> SettlementApi:
    return await test_run.get_api()


@pytest.fixture
async def page(test_run: TestRun) -> Page:
    return await test_run.get_page()


@pytest.fixture
def artifact_path(test_run: TestRun) -> Path:
    return test_run.artifact_dir


@pytest.fixture
def borrower_factory() -> BorrowerFactory:
    return BorrowerFactory()
