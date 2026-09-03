from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from src.config.settings import Settings
from src.services.test_run import TestRun


def _settings(artifacts_dir: Path) -> Settings:
    return Settings(
        environment_name="test", base_url="http://localhost:3000",
        api_base_url="http://localhost:8000", auth_base_url="http://localhost:8000",
        db_dsn="", api_token="token", ui_username=None, ui_password=None,
        browser_name="chromium", headless=True, api_timeout_seconds=15.0,
        artifacts_dir=artifacts_dir,
    )


@patch("src.services.test_run.create_settlement_api")
@patch("src.services.test_run.BrowserSession")
async def test_run_composes_context_resources_and_failure_artifacts(
    browser_session_class: MagicMock,
    create_api: AsyncMock,
    tmp_path: Path,
) -> None:
    browser_session = MagicMock()
    browser_session.__aenter__ = AsyncMock(return_value=browser_session)
    browser_session.__aexit__ = AsyncMock()
    page = MagicMock()
    page.screenshot = AsyncMock(return_value=b"png")
    page.content = AsyncMock(return_value="<html/>")
    browser_session.new_page = AsyncMock(return_value=page)
    browser_session_class.return_value = browser_session
    api = MagicMock()
    api.aclose = AsyncMock()
    create_api.return_value = api

    async with TestRun(_settings(tmp_path)) as run:
        assert await run.get_page() is page
        assert await run.get_api() is api
        run.mark_failed()

    assert create_api.await_args.kwargs["context"] is run.context
    assert (run.artifact_dir / "failure.png").read_bytes() == b"png"
    assert (run.artifact_dir / "failure.html").read_text() == "<html/>"
    api.aclose.assert_awaited_once()
    browser_session.__aexit__.assert_awaited_once()
