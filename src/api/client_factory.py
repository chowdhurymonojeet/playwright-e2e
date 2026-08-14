"""Factory functions for creating configured API clients.

This module provides a deep interface for client initialization, hiding
complexity around Settings loading, token acquisition, and session management.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from src.api.auth_client import AuthClient
from src.api.settlement_api import SettlementApi
from src.config.settings import Settings

if TYPE_CHECKING:
    from src.services.test_context import TestContext


def create_settlement_api(
    session: Any | None = None,
    *,
    settings: Settings | None = None,
    context: TestContext | None = None,
) -> SettlementApi:
    """Create a configured SettlementApi client.

    This is a deep module interface that hides wiring complexity:
    - Settings loading from environment (when settings=None)
    - Token acquisition strategy (env var → login fallback)
    - Session lifecycle management
    - Test context correlation (injects X-Correlation-ID, X-Run-ID headers)

    Args:
        session: Optional HTTP session (Locust passes this for connection pooling).
                 If None, SettlementApi creates a new requests.Session().
        settings: Optional config. If None, loads from Settings.from_env().
        context: Optional TestContext for correlation headers.

    Returns:
        Ready-to-use SettlementApi with auth token and timeout configured.

    Raises:
        ValueError: When no token available and credentials missing for login.

    Examples:
        >>> # Pytest (80% case) - zero params
        >>> api = create_settlement_api()

        >>> # With test context (correlation tracing)
        >>> api = create_settlement_api(context=test_context)

        >>> # Locust (15% case) - pass session for connection pooling
        >>> api = create_settlement_api(self.client)

        >>> # Custom settings (5% case) - override config
        >>> api = create_settlement_api(settings=custom_settings)
    """
    # Load settings if not provided (depth: hides Settings.from_env pattern)
    if settings is None:
        settings = Settings.from_env()

    # Resolve token (depth: hides auth logic)
    token = _acquire_token(settings)

    # Create client with resolved dependencies
    return SettlementApi(
        settings.api_base_url,
        token=token,
        timeout_seconds=settings.api_timeout_seconds,
        session=session,
        context=context,
    )


def _acquire_token(settings: Settings) -> str:
    """Acquire authentication token from settings or via login.

    Internal adapter seam: handles token acquisition strategy.

    Args:
        settings: Configuration containing token or credentials.

    Returns:
        Valid bearer token.

    Raises:
        ValueError: When token unavailable and credentials missing.
    """
    # Priority 1: Use token from settings/environment
    if settings.api_token:
        return settings.api_token

    # Priority 2: Fall back to login flow
    if not settings.ui_username or not settings.ui_password:
        raise ValueError(
            "No API token found and no credentials available for authentication. "
            "Set CG_API_TOKEN or both CG_UI_USERNAME and CG_UI_PASSWORD."
        )

    # Perform login to acquire token
    auth_client = AuthClient(
        settings.auth_base_url,
        timeout_seconds=settings.api_timeout_seconds,
    )
    return auth_client.login(settings.ui_username, settings.ui_password)
