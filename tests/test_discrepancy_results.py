"""Discrepancy Report — Results Table & Pagination Tests

All tests in this file use **mocked** API responses via `page.route()`
for report and reference data. Authentication still uses the live login service.
"""
from __future__ import annotations

import json

import allure
import pytest

from utils.helpers import (
    make_discrepancy_payload,
    make_empty_discrepancy_payload,
)


from utils.discrepancy_testing import select_center_and_submit


@allure.epic("Admin Panel — گزارش مغایرت")
@allure.feature("Results Table & Pagination")
@pytest.mark.discrepancy
@pytest.mark.discrepancy_results
@pytest.mark.discrepancy_mock
class TestDiscrepancyResults:
    """Mock-based tests for the results table and pagination."""

    @allure.story("Table renders with mock data")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_table_renders_mock_data(self, mocked_discrepancy_page):
        dp = mocked_discrepancy_page
        page = dp.page

        select_center_and_submit(dp, page, lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(make_discrepancy_payload()),
        ))
        page.wait_for_selector("table tbody tr", timeout=10000)

        assert dp.has_results(), "Table should be visible"
        assert dp.get_row_count() >= 1, "At least 1 row"
        dp.screenshot("results_table_data")

    @allure.story("Parcel barcode is displayed in the table")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_barcode_in_table(self, mocked_discrepancy_page):
        dp = mocked_discrepancy_page
        page = dp.page

        barcode = "111122223333444455556677"
        select_center_and_submit(dp, page, lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(make_discrepancy_payload(barcodes=[barcode])),
        ))
        page.wait_for_selector("table tbody tr", timeout=10000)
        dp.expect_visible(dp.table.get_by_role("link", name=barcode, exact=True), "Barcode in table")
        dp.screenshot("results_barcode")

    @allure.story("Empty results shows 'no discrepancy found' message")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_empty_results(self, mocked_discrepancy_page):
        dp = mocked_discrepancy_page
        page = dp.page

        select_center_and_submit(dp, page, lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(make_empty_discrepancy_payload()),
        ))
        dp.expect_visible(dp.empty_title, "Empty state title")
        dp.screenshot("results_empty")

    @allure.story("Multiple readings per parcel expand correctly")
    @allure.severity(allure.severity_level.NORMAL)
    def test_multiple_readings(self, mocked_discrepancy_page):
        dp = mocked_discrepancy_page
        page = dp.page

        payload = make_discrepancy_payload(barcodes=["333344445555666677778888"], total_count=1)
        reading2 = payload["items"][0]["readings"][0].copy()
        reading2["readingId"] = "read-2"
        reading2["deviceId"] = "DEV-002"
        payload["items"][0]["readings"].append(reading2)
        payload["totalRecordedPriceRial"] *= 2
        payload["totalRecalculatedPriceRial"] *= 2

        select_center_and_submit(dp, page, lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(payload),
        ))
        page.wait_for_selector("table tbody tr", timeout=10000)

        dp.expect_visible(dp.table.get_by_text("۲ خوانش", exact=True), "Reading count badge")
        dp.screenshot("results_multi_reading")

    @allure.story("Weight and Box Size discrepancy columns are shown")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_discrepancy_type_columns(self, mocked_discrepancy_page):
        dp = mocked_discrepancy_page
        page = dp.page

        select_center_and_submit(dp, page, lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(make_discrepancy_payload()),
        ))
        page.wait_for_selector("table tbody tr", timeout=10000)

        for header in ["وزن ثبت‌شده", "وزن اندازه‌گیری‌شده", "ابعاد ثبت‌شده", "ابعاد اندازه‌گیری‌شده"]:
            dp.expect_visible(page.get_by_role("columnheader", name=header), f"Column '{header}'")
        dp.screenshot("results_columns")

    @allure.story("Page size selector has expected options")
    @allure.severity(allure.severity_level.MINOR)
    def test_page_size_options(self, mocked_discrepancy_page):
        dp = mocked_discrepancy_page
        page = dp.page

        select_center_and_submit(dp, page, lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(make_discrepancy_payload()),
        ))
        page.wait_for_selector("table tbody tr", timeout=10000)

        dp.page_size_select.click()
        for opt in ["۱۰ مرسوله", "۲۰ مرسوله", "۵۰ مرسوله", "۱۰۰ مرسوله"]:
            dp.expect_visible(page.get_by_role("option", name=opt), f"Page size option '{opt}'")
        dp.screenshot("results_page_size_options")

    @allure.story("Parcel barcode links to detail page")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_barcode_links_to_detail(self, mocked_discrepancy_page):
        dp = mocked_discrepancy_page
        page = dp.page

        barcode = "999988887777666655554444"
        select_center_and_submit(dp, page, lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(make_discrepancy_payload(barcodes=[barcode])),
        ))
        page.wait_for_selector("table tbody tr", timeout=10000)

        link = dp.table.get_by_role("link", name=barcode, exact=True)
        dp.expect_visible(link, "Barcode link")
        assert "/parcels/" in (link.get_attribute("href") or ""), "Link should point to parcel detail"
        dp.screenshot("results_barcode_link")
