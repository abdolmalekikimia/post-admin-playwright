"""Pytest conftest — shared fixtures for all Admin Panel tests."""
from __future__ import annotations

import allure
import pytest
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page, expect, Error as PlaywrightError

expect.set_options(timeout=10000)

from config import (
    BASE_URL,
    DISCREPANCIES_URL,
    ADMIN_USERNAME,
    ADMIN_PASSWORD,
    HEADLESS,
    DEFAULT_TIMEOUT,
    SLOW_MO,
    DEFAULT_VIEWPORT,
    BROWSER_CHANNEL,
)
from pages.login_page import LoginPage
from pages.discrepancy_page import DiscrepancyPage


# ── Browser fixtures ──────────────────────────────────────


@pytest.fixture(scope="session")
def browser_instance():
    """Launch a shared browser for the entire test session."""
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=HEADLESS,
            slow_mo=SLOW_MO,
            channel=BROWSER_CHANNEL,
        )
        yield browser
        browser.close()


@pytest.fixture(scope="session")
def frontend_assets():
    from utils.frontend_assets import FrontendAssets
    return FrontendAssets()


@pytest.fixture(scope="function")
def context(browser_instance: Browser, frontend_assets) -> BrowserContext:
    """Fresh browser context (isolated cookies/storage) per test."""
    ctx = browser_instance.new_context(
        viewport=DEFAULT_VIEWPORT,
        locale="fa-IR",
        timezone_id="Asia/Tehran",
        ignore_https_errors=True,
    )
    frontend_assets.install(ctx)
    ctx.set_default_timeout(DEFAULT_TIMEOUT)
    yield ctx
    ctx.close()


@pytest.fixture(scope="function")
def page(context: BrowserContext) -> Page:
    """Single page inside the context."""
    p = context.new_page()
    yield p
    p.close()


# ── Page Object fixtures ──────────────────────────────────


@pytest.fixture
def login_page(page: Page) -> LoginPage:
    lp = LoginPage(page)
    lp.open()
    return lp


@pytest.fixture
def discrepancy_page(page: Page) -> DiscrepancyPage:
    dp = DiscrepancyPage(page)
    return dp


@pytest.fixture
def authenticated_page(context: BrowserContext, page: Page) -> Page:
    """A page that is already logged in — skips the login step."""
    lp = LoginPage(page)
    lp.open()
    lp.login()
    page.wait_for_url(
        lambda url: "/admin/" in url and "/admin/login" not in url,
        timeout=10000,
    )
    return page


@pytest.fixture
def auth_discrepancy_page(authenticated_page: Page) -> DiscrepancyPage:
    """DiscrepancyPage that is already authenticated."""
    dp = DiscrepancyPage(authenticated_page)
    dp.open()
    return dp


@pytest.fixture
def mocked_discrepancy_page(authenticated_page: Page) -> DiscrepancyPage:
    """Install reference routes before the report page loads."""
    from utils.discrepancy_testing import install_reference_mocks
    install_reference_mocks(authenticated_page)
    dp = DiscrepancyPage(authenticated_page)
    dp.open()
    return dp


# ── Screenshot on failure ─────────────────────────────────


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Attach a screenshot when a test fails."""
    outcome = yield
    report = outcome.get_result()
    if report.when == "call" and report.failed:
        page: Page | None = item.funcargs.get("page") or item.funcargs.get("authenticated_page")
        if page is None and "admin_mock_page" in item.funcargs:
            page = item.funcargs["admin_mock_page"][0].page
        if page is None and "admin_live_page" in item.funcargs:
            page = item.funcargs["admin_live_page"].page
        if page and not page.is_closed():
            import os
            reports_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")
            os.makedirs(reports_dir, exist_ok=True)
            import hashlib, re
            # Parameter IDs may contain slashes/escaped Unicode; keep filenames
            # Windows-safe and unique across parallel workers.
            label = re.sub(r"[^a-zA-Z0-9_.-]", "_", item.originalname or item.name)
            suffix = hashlib.sha256(item.nodeid.encode()).hexdigest()[:10]
            screenshot_path = os.path.join(reports_dir, f"{label}_{suffix}.png")
            try:
                page.screenshot(path=screenshot_path, full_page=True)
                allure.attach.file(screenshot_path, name="Failure Screenshot", attachment_type=allure.attachment_type.PNG)
            except PlaywrightError as artifact_error:
                # The original test remains failed. A closed/crashed browser
                # must not replace it with a pytest INTERNALERROR in this hook.
                allure.attach(str(artifact_error), name="Screenshot unavailable",
                              attachment_type=allure.attachment_type.TEXT)


@pytest.fixture(scope="session")
def admin_session_state(browser_instance):
    """Login once per worker; keep credentials/tokens in memory only."""
    ctx = browser_instance.new_context(ignore_https_errors=True)
    p = ctx.new_page()
    lp = LoginPage(p)
    lp.open()
    lp.login()
    p.wait_for_url(lambda url: "/admin/" in url and "/admin/login" not in url)
    state = ctx.storage_state()
    ctx.close()
    return state


@pytest.fixture
def admin_mock_page(browser_instance, admin_session_state, frontend_assets):
    from pages.admin_page import AdminPage
    from utils.admin_testbed import AdminTestbed
    ctx = browser_instance.new_context(storage_state=admin_session_state,
        viewport=DEFAULT_VIEWPORT, locale="fa-IR", timezone_id="Asia/Tehran", ignore_https_errors=True)
    frontend_assets.install(ctx)
    p = ctx.new_page()
    api = AdminTestbed()
    api.install(p)
    yield AdminPage(p), api
    ctx.close()
    assert not api.unexpected, "Unmocked API requests were blocked: " + str(api.unexpected)


@pytest.fixture
def admin_live_page(browser_instance, admin_session_state):
    """Real GETs only; prevent real configuration or identity mutations."""
    from pages.admin_page import AdminPage
    from urllib.parse import urlsplit
    ctx = browser_instance.new_context(storage_state=admin_session_state,
        viewport=DEFAULT_VIEWPORT, locale="fa-IR", timezone_id="Asia/Tehran", ignore_https_errors=True)
    p = ctx.new_page()
    blocked = []
    def guard(route):
        if route.request.method in ("GET", "HEAD", "OPTIONS"):
            route.continue_()
        else:
            blocked.append(route.request.method + " " + urlsplit(route.request.url).path)
            route.abort()
    p.route("**/api/**", guard)
    yield AdminPage(p)
    ctx.close()
    assert not blocked, "A read-only live test attempted a mutation: " + str(blocked)


def pytest_collection_modifyitems(config, items):
    """The source suite requires a compatible frontend and login service.

    Mock markers refer to intercepted feature APIs, not an offline frontend.
    Enable deliberately for a demo environment you control.
    """
    import os
    if os.getenv("RUN_DEMO_TESTS") != "1":
        marker = pytest.mark.skip(reason="Requires a compatible demo frontend; set RUN_DEMO_TESTS=1 explicitly")
        for item in items:
            item.add_marker(marker)
