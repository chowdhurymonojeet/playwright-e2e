from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, TypeVar

from playwright.sync_api import Locator, Page, expect

if TYPE_CHECKING:
    from typing_extensions import Self

TPage = TypeVar("TPage", bound="BasePage")


class BasePage:
    """Shared browser helpers for page objects.

    Methods return Self for fluent chaining when staying on the same page.
    """

    def __init__(self, page: Page) -> None:
        self.page = page

    def goto(self: Self, path: str = "") -> Self:
        """Navigate to path and wait for DOM ready. Returns self for chaining."""
        self.page.goto(path)
        self.page.wait_for_load_state("domcontentloaded")
        return self

    def by_test_id(self, test_id: str) -> Locator:
        return self.page.get_by_test_id(test_id)

    def expect_visible(self: Self, locator: Locator) -> Self:
        """Assert locator is visible. Returns self for chaining."""
        expect(locator).to_be_visible()
        return self

    def take_screenshot(self: Self, destination: Path) -> Self:
        """Capture full-page screenshot. Returns self for chaining."""
        destination.parent.mkdir(parents=True, exist_ok=True)
        self.page.screenshot(path=str(destination), full_page=True)
        return self
