from __future__ import annotations

from pathlib import Path

from playwright.async_api import Locator, Page, expect


class BasePage:
    """Shared asynchronous browser helpers for domain page modules."""

    def __init__(self, page: Page) -> None:
        self.page = page

    async def goto(self, path: str = "") -> None:
        await self.page.goto(path)
        await self.page.wait_for_load_state("domcontentloaded")

    def _by_test_id(self, test_id: str) -> Locator:
        return self.page.get_by_test_id(test_id)

    async def _expect_visible(self, locator: Locator) -> None:
        await expect(locator).to_be_visible()

    async def take_screenshot(self, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        await self.page.screenshot(path=str(destination), full_page=True)
