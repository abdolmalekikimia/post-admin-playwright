"""Login Page Object — handles authentication for Admin Panel."""
from __future__ import annotations

import allure
from playwright.sync_api import Page, expect

from config import LOGIN_URL, ADMIN_USERNAME, ADMIN_PASSWORD, DEFAULT_TIMEOUT
from pages.base_page import BasePage


class LoginPage(BasePage):
    """Page Object for /admin/login."""

    # ── locators ──────────────────────────────────────────
    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.username_input = page.get_by_label("نام کاربری")
        self.password_input = page.get_by_role("textbox", name="رمز عبور")
        self.login_button = page.get_by_role("button", name="ورود به داشبورد")
        self.error_message = page.locator("[role='alert']")

    # ── actions ───────────────────────────────────────────
    @allure.step("Navigate to login page")
    def open(self) -> None:
        self.goto(LOGIN_URL)
        expect(self.username_input).to_be_visible(timeout=DEFAULT_TIMEOUT)
        expect(self.login_button).to_be_enabled()

    @allure.step("Login with user: {username}")
    def login(self, username: str = ADMIN_USERNAME, password: str = ADMIN_PASSWORD) -> None:
        self.username_input.fill(username)
        self.password_input.fill(password)
        self.login_button.click()
        self.page.wait_for_url(lambda url: "/admin/" in url and "/admin/login" not in url, timeout=15000)

    @allure.step("Login with invalid credentials")
    def login_expect_fail(self, username: str, password: str) -> None:
        self.username_input.fill(username)
        self.password_input.fill(password)
        self.login_button.click()

    # ── state checks ──────────────────────────────────────
    def is_on_login_page(self) -> bool:
        return "/login" in self.page.url

    def is_logged_in(self) -> bool:
        return "/login" not in self.page.url
