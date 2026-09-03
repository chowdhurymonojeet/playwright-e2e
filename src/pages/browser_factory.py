"""Lifecycle-owning asynchronous Playwright browser module."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from playwright.async_api import Browser, BrowserContext, Page, Playwright, async_playwright

from src.config.settings import Settings
from src.services.test_context import TestContext


class BrowserSession:
    """Own a Playwright process, browser, and isolated context for one test run."""

    def __init__(self, settings: Settings, context: TestContext, artifact_dir: Path) -> None:
        self.settings = settings
        self.context = context
        self.artifact_dir = artifact_dir
        self.playwright: Playwright | None = None
        self.browser: Browser | None = None
        self.browser_context: BrowserContext | None = None

    async def __aenter__(self) -> "BrowserSession":
        self.artifact_dir.mkdir(parents=True, exist_ok=True)
        try:
            self.playwright = await async_playwright().start()
            self.browser = await _launch_browser(self.playwright, self.settings)
            self.browser_context = await self.browser.new_context(
                base_url=self.settings.base_url,
                record_video_dir=str(self.artifact_dir),
                record_har_path=str(self.artifact_dir / "network.har"),
            )
            await self.browser_context.tracing.start(
                screenshots=True, snapshots=True, sources=True
            )
        except BaseException:
            await self.__aexit__()
            raise
        return self

    async def new_page(self) -> Page:
        if self.browser_context is None:
            raise RuntimeError("BrowserSession must be opened before creating a page")
        return await self.browser_context.new_page()

    async def __aexit__(self, *args: Any) -> None:
        if self.browser_context is not None:
            await self.browser_context.tracing.stop(path=str(self.artifact_dir / "trace.zip"))
            await self.browser_context.close()
        if self.browser is not None:
            await self.browser.close()
        if self.playwright is not None:
            await self.playwright.stop()


async def _launch_browser(playwright: Playwright, settings: Settings) -> Browser:
    browser_name = settings.browser_name.lower()
    if browser_name == "chromium":
        return await playwright.chromium.launch(headless=settings.headless)
    if browser_name == "firefox":
        return await playwright.firefox.launch(headless=settings.headless)
    if browser_name == "webkit":
        return await playwright.webkit.launch(headless=settings.headless)
    raise ValueError(
        f"Unsupported browser: {browser_name}. "
        "Supported browsers: chromium, firefox, webkit"
    )
