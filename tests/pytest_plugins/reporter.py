"""Pytest integration for asynchronous TestRun artifact capture."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from _pytest.config import Config
    from _pytest.nodes import Item
    from _pytest.reports import TestReport


def pytest_configure(config: Config) -> None:
    config.addinivalue_line(
        "markers", "ui: mark test as UI test (captures TestRun artifacts on failure)"
    )


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item: Item) -> TestReport:  # type: ignore[misc]
    outcome = yield
    report: TestReport = outcome.get_result()
    if report.when == "call" and report.failed:
        run = getattr(item, "funcargs", {}).get("test_run")
        if run is not None:
            run.mark_failed()
    return report
