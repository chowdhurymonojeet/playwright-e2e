from __future__ import annotations

import pytest

from src.config.settings import Settings
from src.services.test_context import TestContext


@pytest.mark.smoke
def test_settings_defaults_are_safe_for_local_execution() -> None:
    settings = Settings.from_env()

    assert settings.environment_name == "local"
    assert settings.base_url.startswith("http")
    assert settings.api_timeout_seconds > 0


@pytest.mark.smoke
def test_test_context_generates_traceable_identifiers() -> None:
    context = TestContext.new()

    assert context.run_id.startswith("cg-")
    assert len(context.correlation_id) == 36
    assert context.settlement_id is None
