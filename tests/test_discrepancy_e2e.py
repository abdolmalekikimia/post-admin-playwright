"""Discrepancy Report — End-to-End Tests against Live Environment

These tests run against the live https://example.invalid instance
using the provided admin credentials (demo.user).
"""
from __future__ import annotations

import allure
import pytest

from config import DEFAULT_CENTER_CODE


@allure.epic("Admin Panel — گزارش مغایرت")
@allure.feature("End-to-End (Live Backend)")
@pytest.mark.discrepancy
@pytest.mark.discrepancy_e2e
class TestDiscrepancyE2E:
    """Live E2E tests against example.invalid."""

    @allure.story("Full flow: Login -> Open Discrepancies -> Verify page loads")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_live_page_loads(self, auth_discrepancy_page):
        dp = auth_discrepancy_page
        page = dp.page

        dp.expect_visible(dp.page_heading, "Page heading")
        dp.expect_visible(dp.submit_button, "Submit button")
        dp.screenshot("live_page_loads")

    @allure.story("Center code combobox is interactive")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_live_center_code_interactive(self, auth_discrepancy_page):
        dp = auth_discrepancy_page
        page = dp.page

        dp.fill_filters(center=DEFAULT_CENTER_CODE)
        assert dp.center_code_input.input_value() != DEFAULT_CENTER_CODE, "A center option must be selected"

        dp.screenshot("live_center_code_search")

    @allure.story("Select center and click Show Report")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_live_show_report(self, auth_discrepancy_page):
        dp = auth_discrepancy_page
        page = dp.page

        dp.center_code_input.click()
        dp.center_code_input.fill(DEFAULT_CENTER_CODE)

        listbox = page.get_by_role("listbox")
        listbox.wait_for(state="visible", timeout=10000)
        center_option = listbox.get_by_role("option").filter(
            has_text=DEFAULT_CENTER_CODE
        ).first
        center_option.wait_for(state="visible", timeout=10000)
        center_option.click()
        listbox.wait_for(state="hidden", timeout=5000)

        with page.expect_response(
            lambda response: "/api/admin/parcels/discrepancies" in response.url,
            timeout=30000,
        ) as report_response:
            dp.submit_button.click()

        response = report_response.value
        assert response.status == 200, (
            f"Show Report request returned HTTP {response.status}: {response.url}"
        )
        payload = response.json()
        assert isinstance(payload.get("items"), list)
        assert isinstance(payload.get("totalCount"), int)
        if payload["items"]:
            barcode = payload["items"][0]["parcelBarcode"]
            dp.expect_visible(dp.table.get_by_role("link", name=barcode, exact=True), "Live report parcel")
        else:
            dp.expect_visible(dp.empty_title, "Live empty report")
        dp.screenshot("live_report_results")
    @allure.story("Submit without center code shows validation error")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_live_submit_without_center(self, auth_discrepancy_page):
        dp = auth_discrepancy_page
        page = dp.page

        dp.submit_button.click()
        dp.expect_visible(
            page.get_by_text("کد مرکز مبادله الزامی است"),
            "Center code required error",
        )
        dp.screenshot("live_submit_without_center")

