"""Login Page tests — must pass before any admin feature can be reached."""
from __future__ import annotations

import allure
import pytest

from config import LOGIN_URL, ADMIN_USERNAME, ADMIN_PASSWORD


@allure.epic("Admin Panel — Authentication")
@allure.feature("Login")
@pytest.mark.smoke
@pytest.mark.login
class TestLogin:
    """Validate login flow for the admin panel."""

    @allure.story("Successful login redirects to dashboard")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_successful_login(self, login_page):
        login_page.login()
        login_page.screenshot("login_success")
        login_page.page.wait_for_url(lambda url: "/admin/" in url and "/admin/login" not in url)
        login_page.expect_visible(login_page.page.get_by_text(ADMIN_USERNAME, exact=True), "Authenticated principal")

    @allure.story("Empty username shows validation error")
    @allure.severity(allure.severity_level.NORMAL)
    def test_empty_username(self, login_page):
        login_page.login_expect_fail(username="", password="somepassword")
        login_page.expect_visible(login_page.page.get_by_text("نام کاربری الزامی است"), "Username required error")
        login_page.screenshot("login_empty_username")

    @allure.story("Empty password shows validation error")
    @allure.severity(allure.severity_level.NORMAL)
    def test_empty_password(self, login_page):
        login_page.login_expect_fail(username="admin", password="")
        login_page.expect_visible(login_page.page.get_by_text("رمز عبور الزامی است"), "Password required error")
        login_page.screenshot("login_empty_password")

    @allure.story("Invalid credentials shows error")
    @allure.severity(allure.severity_level.NORMAL)
    def test_invalid_credentials(self, login_page):
        login_page.login_expect_fail(username="wrong_user_xyz", password="wrong_pass_xyz")
        login_page.expect_visible(login_page.error_message, "Error toast shown")
        login_page.screenshot("login_invalid")

    @allure.story("Login page elements are visible")
    @allure.severity(allure.severity_level.MINOR)
    def test_login_page_elements(self, login_page):
        login_page.expect_visible(login_page.username_input, "Username field")
        login_page.expect_visible(login_page.password_input, "Password field")
        login_page.expect_visible(login_page.login_button, "Login button")
        login_page.screenshot("login_elements")
