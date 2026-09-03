"""Unit tests for client_factory module."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.api.client_factory import create_settlement_api
from src.api.settlement_api import SettlementApi
from src.config.settings import Settings


class TestCreateSettlementApi:
    """Test suite for create_settlement_api factory function."""

    async def test_creates_client_with_defaults_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should create SettlementApi with settings loaded from environment."""
        # Arrange
        monkeypatch.setenv("CG_API_BASE_URL", "https://api.test.example")
        monkeypatch.setenv("CG_API_TOKEN", "test-token-123")
        monkeypatch.setenv("CG_API_TIMEOUT_SECONDS", "20")

        # Act
        api = await create_settlement_api()

        # Assert
        assert isinstance(api, SettlementApi)
        assert api.base_url == "https://api.test.example/"
        assert api.timeout_seconds == 20.0
        assert api._headers["Authorization"] == "Bearer test-token-123"
        await api.aclose()

    async def test_creates_client_with_custom_settings(self) -> None:
        """Should use provided Settings instead of loading from environment."""
        # Arrange
        custom_settings = Settings(
            environment_name="custom",
            base_url="https://custom.example",
            api_base_url="https://api.custom.example",
            auth_base_url="https://auth.custom.example",
            db_dsn="postgresql://custom",
            api_token="custom-token-456",
            ui_username=None,
            ui_password=None,
            browser_name="firefox",
            headless=False,
            api_timeout_seconds=30.0,
            artifacts_dir=Path("/tmp"),
        )

        # Act
        api = await create_settlement_api(settings=custom_settings)

        # Assert
        assert api.base_url == "https://api.custom.example/"
        assert api.timeout_seconds == 30.0
        assert api._headers["Authorization"] == "Bearer custom-token-456"
        await api.aclose()

    async def test_creates_client_with_custom_session(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should use provided session (Locust use case)."""
        # Arrange
        monkeypatch.setenv("CG_API_TOKEN", "test-token")
        mock_session = AsyncMock()

        # Act
        api = await create_settlement_api(mock_session)

        # Assert
        assert api.session is mock_session

    async def test_acquires_token_via_login_when_not_in_settings(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should fall back to login flow when CG_API_TOKEN not set."""
        # Arrange
        monkeypatch.setenv("CG_API_BASE_URL", "https://api.test.example")
        monkeypatch.setenv("CG_AUTH_BASE_URL", "https://auth.test.example")
        monkeypatch.setenv("CG_UI_USERNAME", "testuser")
        monkeypatch.setenv("CG_UI_PASSWORD", "testpass")
        monkeypatch.delenv("CG_API_TOKEN", raising=False)

        with patch("src.api.client_factory.AuthClient") as mock_auth_class:
            mock_auth_instance = MagicMock()
            mock_auth_instance.login = AsyncMock(return_value="acquired-token-789")
            mock_auth_instance.aclose = AsyncMock()
            mock_auth_class.return_value = mock_auth_instance

            # Act
            api = await create_settlement_api()

            # Assert
            mock_auth_class.assert_called_once_with(
                "https://auth.test.example",
                timeout_seconds=15.0,
            )
            mock_auth_instance.login.assert_awaited_once_with("testuser", "testpass")
            assert api._headers["Authorization"] == "Bearer acquired-token-789"
            await api.aclose()

    async def test_raises_error_when_no_token_and_no_credentials(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should raise ValueError when token missing and no credentials for login."""
        # Arrange
        monkeypatch.delenv("CG_API_TOKEN", raising=False)
        monkeypatch.delenv("CG_UI_USERNAME", raising=False)
        monkeypatch.delenv("CG_UI_PASSWORD", raising=False)

        # Act & Assert
        with pytest.raises(ValueError, match="No API token found and no credentials available"):
            await create_settlement_api()

    async def test_session_param_takes_precedence_over_settings(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should use session param even when settings provided."""
        # Arrange
        monkeypatch.setenv("CG_API_TOKEN", "test-token")
        custom_session = MagicMock()
        custom_settings = Settings.from_env()

        # Act
        api = await create_settlement_api(custom_session, settings=custom_settings)

        # Assert
        assert api.session is custom_session

    async def test_handles_missing_password_gracefully(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should raise clear error when username set but password missing."""
        # Arrange
        monkeypatch.delenv("CG_API_TOKEN", raising=False)
        monkeypatch.setenv("CG_UI_USERNAME", "testuser")
        monkeypatch.delenv("CG_UI_PASSWORD", raising=False)

        # Act & Assert
        with pytest.raises(ValueError, match="No API token found and no credentials available"):
            await create_settlement_api()

    async def test_url_normalization(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should normalize base_url by ensuring trailing slash."""
        # Arrange
        monkeypatch.setenv("CG_API_BASE_URL", "https://api.test.example")  # No trailing slash
        monkeypatch.setenv("CG_API_TOKEN", "test-token")

        # Act
        api = await create_settlement_api()

        # Assert
        assert api.base_url == "https://api.test.example/"  # Trailing slash added
        await api.aclose()
