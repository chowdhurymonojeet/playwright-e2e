"""Unit tests for browser_factory module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from playwright.sync_api import Browser, BrowserContext, Page

from src.pages.browser_factory import create_browser_context, create_page
from src.config.settings import Settings


class TestCreateBrowserContext:
    """Test suite for create_browser_context factory function."""

    @patch("src.pages.browser_factory.sync_playwright")
    def test_creates_chromium_browser_by_default(self, mock_playwright: Mock) -> None:
        """Should launch Chromium browser when browser_name is 'chromium'."""
        # Arrange
        mock_pw = MagicMock()
        mock_playwright.return_value.__enter__.return_value = mock_pw
        mock_browser = MagicMock(spec=Browser)
        mock_context = MagicMock(spec=BrowserContext)
        mock_pw.chromium.launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_context

        settings = Settings(
            environment_name="test",
            base_url="http://localhost:3000",
            api_base_url="http://localhost:8000",
            auth_base_url="http://localhost:8000",
            db_dsn="",
            api_token=None,
            ui_username=None,
            ui_password=None,
            browser_name="chromium",
            headless=True,
            api_timeout_seconds=15.0,
            artifacts_dir=Path("/tmp"),
        )

        # Act
        context, browser = create_browser_context(settings=settings)

        # Assert
        mock_pw.chromium.launch.assert_called_once_with(headless=True)
        mock_browser.new_context.assert_called_once_with(base_url="http://localhost:3000")
        assert context is mock_context
        assert browser is mock_browser

    @patch("src.pages.browser_factory.sync_playwright")
    def test_creates_firefox_browser(self, mock_playwright: Mock) -> None:
        """Should launch Firefox when browser_name is 'firefox'."""
        # Arrange
        mock_pw = MagicMock()
        mock_playwright.return_value.__enter__.return_value = mock_pw
        mock_browser = MagicMock(spec=Browser)
        mock_context = MagicMock(spec=BrowserContext)
        mock_pw.firefox.launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_context

        settings = Settings(
            environment_name="test",
            base_url="http://localhost:3000",
            api_base_url="http://localhost:8000",
            auth_base_url="http://localhost:8000",
            db_dsn="",
            api_token=None,
            ui_username=None,
            ui_password=None,
            browser_name="firefox",
            headless=False,
            api_timeout_seconds=15.0,
            artifacts_dir=Path("/tmp"),
        )

        # Act
        context, browser = create_browser_context(settings=settings)

        # Assert
        mock_pw.firefox.launch.assert_called_once_with(headless=False)
        assert context is mock_context

    @patch("src.pages.browser_factory.sync_playwright")
    def test_raises_error_for_unsupported_browser(self, mock_playwright: Mock) -> None:
        """Should raise ValueError for unsupported browser names."""
        # Arrange
        mock_pw = MagicMock()
        mock_playwright.return_value.__enter__.return_value = mock_pw

        settings = Settings(
            environment_name="test",
            base_url="http://localhost:3000",
            api_base_url="http://localhost:8000",
            auth_base_url="http://localhost:8000",
            db_dsn="",
            api_token=None,
            ui_username=None,
            ui_password=None,
            browser_name="edge",  # Not supported
            headless=True,
            api_timeout_seconds=15.0,
            artifacts_dir=Path("/tmp"),
        )

        # Act & Assert
        with pytest.raises(ValueError, match="Unsupported browser: edge"):
            create_browser_context(settings=settings)

    @patch("src.pages.browser_factory.sync_playwright")
    def test_loads_settings_from_env_when_not_provided(
        self, mock_playwright: Mock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should load Settings.from_env() when settings=None."""
        # Arrange
        monkeypatch.setenv("CG_BROWSER_NAME", "webkit")
        monkeypatch.setenv("CG_BASE_URL", "http://test.example")
        monkeypatch.setenv("CG_HEADLESS", "false")

        mock_pw = MagicMock()
        mock_playwright.return_value.__enter__.return_value = mock_pw
        mock_browser = MagicMock(spec=Browser)
        mock_context = MagicMock(spec=BrowserContext)
        mock_pw.webkit.launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_context

        # Act
        context, browser = create_browser_context()

        # Assert
        mock_pw.webkit.launch.assert_called_once_with(headless=False)
        mock_browser.new_context.assert_called_once_with(base_url="http://test.example")


class TestCreatePage:
    """Test suite for create_page factory function."""

    def test_creates_page_from_context(self) -> None:
        """Should create new page from browser context."""
        # Arrange
        mock_context = MagicMock(spec=BrowserContext)
        mock_page = MagicMock(spec=Page)
        mock_context.new_page.return_value = mock_page

        # Act
        page = create_page(mock_context)

        # Assert
        mock_context.new_page.assert_called_once()
        assert page is mock_page

    @patch("src.pages.browser_factory.create_browser_context")
    def test_creates_page_with_default_context(
        self, mock_create_context: Mock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should create browser context when context=None."""
        # Arrange
        monkeypatch.setenv("CG_BROWSER_NAME", "chromium")
        mock_context = MagicMock(spec=BrowserContext)
        mock_browser = MagicMock(spec=Browser)
        mock_page = MagicMock(spec=Page)
        mock_create_context.return_value = (mock_context, mock_browser)
        mock_context.new_page.return_value = mock_page

        # Act
        page = create_page()

        # Assert
        mock_create_context.assert_called_once_with(settings=None, test_context=None)
        mock_context.new_page.assert_called_once()
        assert page is mock_page
