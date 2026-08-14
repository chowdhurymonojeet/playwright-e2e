"""Pytest hooks for test reporting and failure handling.

This plugin provides automatic screenshot capture on UI test failures
and integrates with Allure reporting for rich test artifacts.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import allure
import pytest
from playwright.sync_api import Page

if TYPE_CHECKING:
    from _pytest.config import Config
    from _pytest.nodes import Item
    from _pytest.reports import TestReport


def pytest_configure(config: Config) -> None:
    """Configure pytest with custom markers and settings."""
    config.addinivalue_line(
        "markers",
        "ui: mark test as UI test (will auto-capture screenshots on failure)",
    )


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item: Item) -> TestReport:  # type: ignore[misc]
    """Hook to capture test results and artifacts on failure."""
    outcome = yield
    report: TestReport = outcome.get_result()

    # Only process failures in call phase (not setup/teardown)
    if report.when == "call" and report.failed:
        _capture_failure_artifacts(item, report)

    return report


def _capture_failure_artifacts(item: Item, report: TestReport) -> None:
    """Capture screenshots and logs on test failure.

    Args:
        item: Test item that failed.
        report: Test report containing failure details.
    """
    # Check if this is a UI test with page fixture
    if hasattr(item, "funcargs") and "page" in item.funcargs:  # type: ignore[attr-defined]
        page: Page = item.funcargs["page"]  # type: ignore[attr-defined]
        _capture_screenshot(page, item, report)
        _capture_page_source(page, item)

    # Attach test context if available
    if hasattr(item, "funcargs") and "test_context" in item.funcargs:  # type: ignore[attr-defined]
        from src.services.test_context import TestContext

        context: TestContext = item.funcargs["test_context"]  # type: ignore[attr-defined]
        allure.attach(
            f"Correlation ID: {context.correlation_id}\nRun ID: {context.run_id}",
            name="Test Context",
            attachment_type=allure.attachment_type.TEXT,
        )


def _capture_screenshot(page: Page, item: Item, report: TestReport) -> None:
    """Capture and attach screenshot to test report.

    Args:
        page: Playwright Page instance.
        item: Test item.
        report: Test report.
    """
    try:
        screenshot_bytes = page.screenshot(full_page=True)

        # Attach to Allure report
        allure.attach(
            screenshot_bytes,
            name=f"failure-screenshot-{item.name}",
            attachment_type=allure.attachment_type.PNG,
        )

        # Save to artifacts directory if available, tagged with run_id
        if hasattr(item, "funcargs") and "artifact_path" in item.funcargs:  # type: ignore[attr-defined]
            artifact_path: Path = item.funcargs["artifact_path"]  # type: ignore[attr-defined]
            screenshot_path = artifact_path / "failure.png"
            screenshot_path.write_bytes(screenshot_bytes)
        elif hasattr(item, "funcargs") and "test_context" in item.funcargs:  # type: ignore[attr-defined]
            # Fallback: use run_id from test_context
            from src.services.test_context import TestContext

            context: TestContext = item.funcargs["test_context"]  # type: ignore[attr-defined]
            from src.config.settings import Settings

            settings = Settings.from_env()
            run_dir = settings.artifacts_dir / context.run_id
            run_dir.mkdir(parents=True, exist_ok=True)
            screenshot_path = run_dir / f"failure-{item.name}.png"
            screenshot_path.write_bytes(screenshot_bytes)

    except Exception as e:
        # Don't fail the test report if screenshot capture fails
        allure.attach(
            f"Screenshot capture failed: {e}",
            name="screenshot-error",
            attachment_type=allure.attachment_type.TEXT,
        )


def _capture_page_source(page: Page, item: Item) -> None:
    """Capture and attach page HTML source.

    Args:
        page: Playwright Page instance.
        item: Test item.
    """
    try:
        html_content = page.content()
        allure.attach(
            html_content,
            name=f"page-source-{item.name}",
            attachment_type=allure.attachment_type.HTML,
        )
    except Exception as e:
        allure.attach(
            f"Page source capture failed: {e}",
            name="page-source-error",
            attachment_type=allure.attachment_type.TEXT,
        )
