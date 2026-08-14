"""Factory functions for creating Playwright browser instances and contexts.

This module provides a deep interface for browser initialization, hiding
complexity around browser selection, launch options, and context configuration.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright

from src.config.settings import Settings

if TYPE_CHECKING:
    from src.services.test_context import TestContext


def create_browser_context(
    context: BrowserContext | None = None,
    *,
    settings: Settings | None = None,
    test_context: TestContext | None = None,
) -> tuple[BrowserContext, Browser]:
    """Create a configured Playwright browser context.

    This is a deep module interface that hides browser complexity:
    - Settings loading from environment (when settings=None)
    - Browser selection (chromium/firefox/webkit)
    - Headless mode configuration
    - Base URL setup
    - Test context tracing (injects run_id into trace metadata)

    Args:
        context: Optional existing context (for reuse scenarios).
                 If provided, returns it immediately without launching browser.
        settings: Optional config. If None, loads from Settings.from_env().
        test_context: Optional TestContext for trace tagging.

    Returns:
        Tuple of (BrowserContext, Browser) ready for page creation.

    Raises:
        ValueError: When browser_name is not supported.

    Examples:
        >>> # Pytest (80% case) - zero params
        >>> context, browser = create_browser_context()

        >>> # With test context (trace correlation)
        >>> context, browser = create_browser_context(test_context=ctx)

        >>> # Custom settings
        >>> context, browser = create_browser_context(settings=custom_settings)

        >>> # Reuse existing context
        >>> context, browser = create_browser_context(context=existing_context)
    """
    # If context provided, return it (with placeholder browser)
    if context is not None:
        # Context reuse scenario - caller manages browser lifecycle
        return (context, None)  # type: ignore[return-value]

    # Load settings if not provided
    if settings is None:
        settings = Settings.from_env()

    # Launch browser based on settings
    with sync_playwright() as playwright:
        browser = _launch_browser(playwright, settings)

        # Create context with base URL and optional trace metadata
        context_options: dict[str, Any] = {"base_url": settings.base_url}

        # Inject test context metadata for tracing
        if test_context:
            context_options["record_video_dir"] = str(
                settings.artifacts_dir / test_context.run_id
            )
            context_options["record_har_path"] = str(
                settings.artifacts_dir / test_context.run_id / "network.har"
            )

        browser_context = browser.new_context(**context_options)

        # Start tracing with run_id tag
        if test_context:
            browser_context.tracing.start(
                screenshots=True,
                snapshots=True,
                sources=True,
            )

        return (browser_context, browser)


def create_page(
    context: BrowserContext | None = None,
    *,
    settings: Settings | None = None,
    test_context: TestContext | None = None,
) -> Page:
    """Create a Playwright Page ready for automation.

    Convenience function that creates both context and page.
    For tests that need fine-grained control, use create_browser_context() directly.

    Args:
        context: Optional existing context. If None, creates new browser context.
        settings: Optional config. If None, loads from Settings.from_env().
        test_context: Optional TestContext for trace tagging.

    Returns:
        Playwright Page ready for navigation and interaction.

    Examples:
        >>> # Pytest fixture - one-liner
        >>> page = create_page()

        >>> # With test context (trace correlation)
        >>> page = create_page(test_context=ctx)

        >>> # Reuse context across multiple pages
        >>> context, browser = create_browser_context()
        >>> page1 = create_page(context)
        >>> page2 = create_page(context)
    """
    if context is None:
        context, _ = create_browser_context(settings=settings, test_context=test_context)

    return context.new_page()


def _launch_browser(playwright: Any, settings: Settings) -> Browser:
    """Launch browser based on settings.

    Internal adapter: maps settings.browser_name to Playwright browser type.

    Args:
        playwright: Playwright sync API instance.
        settings: Configuration with browser_name and headless.

    Returns:
        Launched Browser instance.

    Raises:
        ValueError: When browser_name not in (chromium, firefox, webkit).
    """
    browser_name = settings.browser_name.lower()
    headless = settings.headless

    if browser_name == "chromium":
        return playwright.chromium.launch(headless=headless)
    elif browser_name == "firefox":
        return playwright.firefox.launch(headless=headless)
    elif browser_name == "webkit":
        return playwright.webkit.launch(headless=headless)
    else:
        raise ValueError(
            f"Unsupported browser: {browser_name}. "
            f"Supported browsers: chromium, firefox, webkit"
        )
