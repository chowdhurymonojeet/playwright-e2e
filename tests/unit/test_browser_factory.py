"""Tests for the async browser lifecycle module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.config.settings import Settings
from src.pages.browser_factory import BrowserSession
from src.services.test_context import TestContext


def _settings(browser_name: str = "chromium") -> Settings:
    return Settings(
        environment_name="test", base_url="http://localhost:3000",
        api_base_url="http://localhost:8000", auth_base_url="http://localhost:8000",
        db_dsn="", api_token="token", ui_username=None, ui_password=None,
        browser_name=browser_name, headless=True, api_timeout_seconds=15.0,
        artifacts_dir=Path("/tmp"),
    )


@patch("src.pages.browser_factory.async_playwright")
async def test_session_owns_chromium_lifecycle(mock_playwright: MagicMock, tmp_path: Path) -> None:
    manager = MagicMock()
    mock_playwright.return_value = manager
    playwright = MagicMock()
    manager.start = AsyncMock(return_value=playwright)
    browser = MagicMock()
    browser_context = MagicMock()
    page = MagicMock()
    playwright.chromium.launch = AsyncMock(return_value=browser)
    browser.new_context = AsyncMock(return_value=browser_context)
    browser_context.tracing.start = AsyncMock()
    browser_context.tracing.stop = AsyncMock()
    browser_context.new_page = AsyncMock(return_value=page)
    browser_context.close = AsyncMock()
    browser.close = AsyncMock()
    playwright.stop = AsyncMock()

    artifact_dir = tmp_path / "run"
    async with BrowserSession(_settings(), TestContext.new(), artifact_dir) as session:
        assert await session.new_page() is page

    playwright.chromium.launch.assert_awaited_once_with(headless=True)
    browser.new_context.assert_awaited_once_with(
        base_url="http://localhost:3000",
        record_video_dir=str(artifact_dir),
        record_har_path=str(artifact_dir / "network.har"),
    )
    browser_context.tracing.stop.assert_awaited_once_with(path=str(artifact_dir / "trace.zip"))
    browser_context.close.assert_awaited_once()
    browser.close.assert_awaited_once()
    playwright.stop.assert_awaited_once()


@patch("src.pages.browser_factory.async_playwright")
async def test_session_uses_requested_browser(mock_playwright: MagicMock, tmp_path: Path) -> None:
    manager = MagicMock()
    mock_playwright.return_value = manager
    playwright = MagicMock()
    manager.start = AsyncMock(return_value=playwright)
    browser = MagicMock()
    browser_context = MagicMock()
    playwright.firefox.launch = AsyncMock(return_value=browser)
    browser.new_context = AsyncMock(return_value=browser_context)
    browser_context.tracing.start = AsyncMock()
    browser_context.tracing.stop = AsyncMock()
    browser_context.close = AsyncMock()
    browser.close = AsyncMock()
    playwright.stop = AsyncMock()

    async with BrowserSession(_settings("firefox"), TestContext.new(), tmp_path / "run"):
        pass

    playwright.firefox.launch.assert_awaited_once_with(headless=True)


@patch("src.pages.browser_factory.async_playwright")
async def test_session_rejects_unsupported_browser(mock_playwright: MagicMock, tmp_path: Path) -> None:
    manager = MagicMock()
    mock_playwright.return_value = manager
    playwright = MagicMock()
    playwright.stop = AsyncMock()
    manager.start = AsyncMock(return_value=playwright)

    with pytest.raises(ValueError, match="Unsupported browser: edge"):
        await BrowserSession(_settings("edge"), TestContext.new(), tmp_path / "run").__aenter__()
