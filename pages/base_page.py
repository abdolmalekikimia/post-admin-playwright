"""Base Page Object — shared helpers for every page."""
from __future__ import annotations

import allure
from playwright.sync_api import Page, expect


class BasePage:
    """Thin wrapper around Playwright `Page` that every POM inherits."""

    def __init__(self, page: Page) -> None:
        self.page = page

    # ── navigation ────────────────────────────────────────
    def goto(self, url: str) -> None:
        with allure.step(f"Navigate to {url}"):
            # Remote fonts or background requests are not evidence of UI readiness.
            # Each page object waits for its own observable controls after navigation.
            self.page.goto(url, wait_until="domcontentloaded")

    # ── waiting ───────────────────────────────────────────
    def wait_for_load_state(self, state: str = "networkidle") -> None:
        self.page.wait_for_load_state(state)

    def wait_for_selector(self, selector: str, timeout: int | None = None) -> None:
        self.page.wait_for_selector(selector, timeout=timeout)

    # ── assertions ────────────────────────────────────────
    def expect_visible(self, locator, message: str = "") -> None:
        with allure.step(f"Assert visible: {message or locator}"):
            expect(locator).to_be_visible()

    def expect_text(self, locator, text: str, message: str = "") -> None:
        with allure.step(f"Assert text '{text}': {message}"):
            expect(locator).to_have_text(text)

    def expect_url_contains(self, fragment: str) -> None:
        expect(self.page).to_have_url(f"*{fragment}*")

    # ── screenshot ────────────────────────────────────────
    def screenshot(self, name: str) -> None:
        import os
        reports_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports")
        os.makedirs(reports_dir, exist_ok=True)
        self.page.screenshot(path=os.path.join(reports_dir, f"{name}.png"), full_page=True)
