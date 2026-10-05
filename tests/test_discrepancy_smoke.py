"""Discrepancy Report Page — Smoke Tests

Fast checks that verify the page loads and core elements render.
"""
from __future__ import annotations

import allure
import pytest

from config import DISCREPANCIES_URL


@allure.epic("Admin Panel — گزارش مغایرت")
@allure.feature("Smoke Tests")
@pytest.mark.smoke
@pytest.mark.discrepancy
@pytest.mark.discrepancy_smoke
class TestDiscrepancySmoke:
    """Minimal smoke tests for the discrepancy report page."""

    @allure.story("Page loads and shows heading")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_page_heading_visible(self, auth_discrepancy_page):
        dp = auth_discrepancy_page
        dp.expect_visible(dp.page_heading, "Page heading 'گزارش مغایرت'")
        dp.screenshot("smoke_heading")

    @allure.story("Page description text is shown")
    @allure.severity(allure.severity_level.NORMAL)
    def test_page_description_visible(self, auth_discrepancy_page):
        dp = auth_discrepancy_page
        dp.expect_visible(dp.page_description, "Page description text")
        dp.screenshot("smoke_description")

    @allure.story("Filter form is visible with all fields")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_filter_form_visible(self, auth_discrepancy_page):
        dp = auth_discrepancy_page
        dp.expect_visible(dp.center_code_input, "کد مرکز مبادله input")
        dp.expect_visible(dp.from_date_input, "از تاریخ و زمان input")
        dp.expect_visible(dp.to_date_input, "تا تاریخ و زمان input")
        dp.expect_visible(dp.price_direction_select, "جهت تغییر هزینه select")
        dp.expect_visible(dp.submit_button, "نمایش گزارش button")
        dp.screenshot("smoke_form")

    @allure.story("Initial state shows 'report not requested' empty state")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_initial_empty_state(self, auth_discrepancy_page):
        dp = auth_discrepancy_page
        dp.expect_visible(dp.initial_empty_title, "Empty state title")
        dp.screenshot("smoke_initial_state")

    @allure.story("Submit button is clickable")
    @allure.severity(allure.severity_level.NORMAL)
    def test_submit_button_clickable(self, auth_discrepancy_page):
        dp = auth_discrepancy_page
        assert dp.submit_button.is_enabled(), "Submit button should be enabled"
        dp.screenshot("smoke_submit_enabled")
