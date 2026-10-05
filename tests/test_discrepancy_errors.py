"""Discrepancy Report — Error Handling & Edge-Case Tests

Covers:
  • HTTP 400 (bad request)
  • HTTP 401 (unauthorized / session expired)
  • HTTP 403 (forbidden)
  • HTTP 503 (service unavailable)
  • Retry button after error
  • Retry recovers from transient error
"""
from __future__ import annotations

import json
import pytest
import allure

from utils.helpers import make_discrepancy_payload
from playwright.sync_api import expect


from utils.discrepancy_testing import select_center_and_submit


@allure.epic("Admin Panel — گزارش مغایرت")
@allure.feature("Error Handling")
@pytest.mark.discrepancy
@pytest.mark.discrepancy_error
@pytest.mark.discrepancy_mock
class TestDiscrepancyErrors:
    """Mock-based tests for error states and retry logic."""

    @allure.story("HTTP 400 shows 'filters not valid'")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_error_400(self, mocked_discrepancy_page):
        dp = mocked_discrepancy_page
        page = dp.page

        select_center_and_submit(dp, page, lambda route: route.fulfill(status=400))

        dp.expect_visible(page.get_by_text("فیلترهای گزارش معتبر نیستند"), "400 error message")
        dp.screenshot("error_400")

    @allure.story("HTTP 401 expires the session and returns to login")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_error_401(self, mocked_discrepancy_page):
        dp = mocked_discrepancy_page
        page = dp.page

        select_center_and_submit(dp, page, lambda route: route.fulfill(status=401))

        # The global authentication handler redirects after a 401. Assert the
        # final state, not the transient report heading and description.
        page.wait_for_url("**/admin/login**", timeout=10000)
        expect(page.get_by_text(
            "نشست شما پایان یافته است. برای ادامه دوباره وارد شوید.", exact=True
        )).to_be_visible()
        expect(dp.retry_button).to_have_count(0)
        dp.screenshot("error_401")

    @allure.story("HTTP 403 shows 'access denied'")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_error_403(self, mocked_discrepancy_page):
        dp = mocked_discrepancy_page
        page = dp.page

        select_center_and_submit(dp, page, lambda route: route.fulfill(status=403))

        dp.expect_visible(page.get_by_text("دسترسی به گزارش مجاز نیست"), "403 error message")
        dp.screenshot("error_403")

    @allure.story("HTTP 503 shows 'service unavailable'")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_error_503(self, mocked_discrepancy_page):
        dp = mocked_discrepancy_page
        page = dp.page

        select_center_and_submit(dp, page, lambda route: route.fulfill(status=503))

        dp.expect_visible(page.get_by_text("گزارش فعلاً در دسترس نیست"), "503 error message")
        dp.screenshot("error_503")

    @allure.story("Retry button is visible after error")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_retry_button_after_error(self, mocked_discrepancy_page):
        dp = mocked_discrepancy_page
        page = dp.page

        select_center_and_submit(dp, page, lambda route: route.fulfill(status=503))

        dp.expect_visible(dp.retry_button, "Retry button")
        dp.screenshot("error_retry_visible")

    @allure.story("Retry recovers from transient 503")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_retry_recovers(self, mocked_discrepancy_page):
        dp = mocked_discrepancy_page
        page = dp.page

        call_count = 0
        request_urls = []

        def handle_discrepancy(route):
            nonlocal call_count
            call_count += 1
            request_urls.append(route.request.url)
            if call_count == 1:
                route.fulfill(status=503)
            else:
                route.fulfill(
                    status=200,
                    content_type="application/json",
                    body=json.dumps(make_discrepancy_payload()),
                )

        select_center_and_submit(dp, page, handle_discrepancy)

        # First attempt: error
        dp.expect_visible(dp.retry_button, "Retry button after 503")

        # Click retry
        with page.expect_response(
            lambda response: "/api/admin/parcels/discrepancies" in response.url
        ) as retry_response:
            dp.retry_button.click()
        assert retry_response.value.status == 200
        assert call_count == 2, "Retry must send exactly one additional request"
        assert request_urls[0] == request_urls[1], "Retry must retain report filters"
        page.wait_for_selector("table tbody tr", timeout=10000)

        assert dp.has_results(), "Table should show results after retry"
        dp.screenshot("error_retry_success")

    @allure.story("Client-error actions follow the frontend retry policy")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize("status,message,has_retry", [
        (400, "فیلترهای گزارش معتبر نیستند", True),
        (403, "دسترسی به گزارش مجاز نیست", False),
    ])
    def test_client_error_actions(self, mocked_discrepancy_page, status, message, has_retry):
        dp = mocked_discrepancy_page
        page = dp.page
        # The implemented report policy offers retry for 400, suppresses it for
        # 403, and routes 401 through global authentication (tested separately).
        select_center_and_submit(dp, page, lambda route: route.fulfill(status=status))
        expect(page.get_by_role("heading", name=message, exact=True)).to_be_visible()
        if has_retry:
            expect(dp.retry_button).to_be_visible()
        else:
            expect(dp.retry_button).to_have_count(0)
        dp.screenshot(f"error_client_{status}_actions")
