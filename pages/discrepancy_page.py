"""Discrepancy Report Page Object — the main page under test.

Locators are based on Persian labels extracted from the minified bundle:
  DiscrepancyReportPage-BrQ0E2J8.js
"""
from __future__ import annotations

import re
import allure
from playwright.sync_api import Page, Locator, expect

from config import DISCREPANCIES_URL, DEFAULT_CENTER_CODE, DEFAULT_TIMEOUT
from pages.base_page import BasePage


class DiscrepancyPage(BasePage):
    """Page Object for /admin/discrepancies."""

    def __init__(self, page: Page) -> None:
        super().__init__(page)

        # ── heading ───────────────────────────────────────
        self.page_heading: Locator = page.get_by_role("heading", name="گزارش مغایرت")
        self.page_description: Locator = page.get_by_text("اختلاف وزن یا ابعاد ثبت‌شده")

        # ── filter form ───────────────────────────────────
        self.center_code_input: Locator = page.get_by_role("combobox", name="کد مرکز مبادله")
        self.device_select: Locator = page.get_by_role("combobox", name="دستگاه")
        self.from_date_input: Locator = page.get_by_role("button", name=re.compile(r"^از تاریخ و زمان:"))
        self.to_date_input: Locator = page.get_by_role("button", name=re.compile(r"^تا تاریخ و زمان"))
        self.price_direction_select: Locator = page.get_by_role("combobox", name="جهت تغییر هزینه")

        # ── buttons ───────────────────────────────────────
        self.submit_button: Locator = page.get_by_role("button", name="نمایش گزارش")
        self.reset_button: Locator = page.get_by_role("button", name="پاک‌کردن همه")
        self.retry_button: Locator = page.get_by_role("button", name="تلاش دوباره")

        # ── results area ──────────────────────────────────
        self.results_section: Locator = page.get_by_label("نتیجهٔ گزارش مغایرت")
        self.table: Locator = page.get_by_role("table")
        self.table_caption: Locator = page.get_by_text("گزارش مغایرت مرسوله‌ها و خوانش‌های هر مرسوله")
        self.total_count_text: Locator = page.locator(".text-slate-500").first
        self.page_size_select: Locator = page.get_by_label("تعداد در صفحه")

        # ── empty / error states ──────────────────────────
        self.empty_title: Locator = page.get_by_text("مغایرتی در این محدوده پیدا نشد")
        self.empty_description: Locator = page.get_by_text("مرکز مبادله، بازهٔ زمانی یا فیلتر")
        self.initial_empty_title: Locator = page.get_by_text("گزارش هنوز درخواست نشده است")
        self.initial_empty_desc: Locator = page.get_by_text("مرکز مبادله و بازهٔ زمانی را مشخص کنید")
        self.error_title: Locator = page.locator("[role='alert']")

        # ── skeleton / loading ────────────────────────────
        self.skeleton_loader: Locator = page.locator(".animate-pulse")

    # ── navigation ────────────────────────────────────────
    @allure.step("Navigate to Discrepancy Report page")
    def open(self) -> None:
        self.goto(DISCREPANCIES_URL)
        expect(self.page_heading).to_be_visible(timeout=DEFAULT_TIMEOUT)
        expect(self.submit_button).to_be_visible()

    # ── filter actions ────────────────────────────────────
    @allure.step("Fill filter: center={center}, device={device}, from={from_dt} → {to_dt}, direction={direction}")
    def fill_filters(
        self,
        center: str = "",
        device: str | None = None,
        from_dt: str | None = None,
        to_dt: str | None = None,
        direction: str | None = None,
    ) -> None:
        if center:
            self._fill_center_code(center)

        if device:
            self.device_select.click()
            self.page.get_by_role("option", name=device).click()

        if from_dt:
            self._set_date_value(0, from_dt)

        if to_dt:
            self._set_date_value(1, to_dt)

        if direction:
            self.price_direction_select.click()
            self.page.get_by_role("option", name=direction).click()

    def _fill_center_code(self, code: str) -> None:
        """Choose an actual center; typed search text is not a selected value."""
        self.center_code_input.click()
        self.center_code_input.fill(code)
        option = self.page.get_by_role("option").filter(has_text=code)
        option.wait_for(state="visible", timeout=10000)
        option.click()

    def _set_date_value(self, index: int, value: str) -> None:
        """Pick date/time through the public calendar UI; never alter React internals."""
        from playwright.sync_api import expect
        target = self.page.evaluate("""iso => {
            const date = new Date(iso);
            if (Number.isNaN(date.getTime())) throw new Error('Invalid ISO date');
            const parts = Object.fromEntries(new Intl.DateTimeFormat('en-u-ca-persian', {
                timeZone: 'Asia/Tehran', year: 'numeric', month: '2-digit', day: '2-digit',
                hour: '2-digit', minute: '2-digit', hourCycle: 'h23'
            }).formatToParts(date).filter(p => p.type !== 'literal').map(p => [p.type, p.value]));
            return parts;
        }""", value)
        trigger = self.from_date_input if index == 0 else self.to_date_input
        trigger.click()
        calendar = self.page.locator('.rmdp-calendar:visible')
        expect(calendar).to_be_visible()
        months = ['فروردین','اردیبهشت','خرداد','تیر','مرداد','شهریور',
                  'مهر','آبان','آذر','دی','بهمن','اسفند']
        digits = str.maketrans('۰۱۲۳۴۵۶۷۸۹', '0123456789')
        wanted = int(target['year']) * 12 + int(target['month'])
        for _ in range(36):
            header = calendar.locator('.rmdp-header-values').inner_text().translate(digits)
            year = int(re.search(r'\d{4}', header).group())
            month = next(i+1 for i, name in enumerate(months) if name in header)
            current = year * 12 + month
            if current == wanted:
                break
            direction = 'rmdp-left' if wanted < current else 'rmdp-right'
            calendar.locator('button.rmdp-arrow-container.' + direction).click()
        else:
            raise AssertionError('Requested date is outside the supported 36-month navigation range')
        day = str(int(target['day'])).translate(str.maketrans('0123456789','۰۱۲۳۴۵۶۷۸۹'))
        cell = calendar.locator('.rmdp-day-picker .rmdp-day:not(.rmdp-day-hidden):not(.rmdp-disabled):visible').filter(
            has_text=re.compile('^' + re.escape(day) + '$'))
        expect(cell).to_have_count(1)
        cell.click()
        time_fields = self.page.locator('.rmdp-wrapper:visible .rmdp-time-picker input')
        assert time_fields.count() == 2, 'Expected hour and minute controls'
        time_fields.nth(0).fill(target['hour'])
        time_fields.nth(1).fill(target['minute'])
        self.page.get_by_role('button', name='تأیید', exact=True).click()
        expect(calendar).to_be_hidden()

    @allure.step("Click 'نمایش گزارش' (Show Report)")
    def submit(self) -> None:
        self.submit_button.click()

    @allure.step("Click reset filters")
    def reset_filters(self) -> None:
        self.reset_button.click()

    @allure.step("Search with full filters")
    def search(
        self,
        center: str = DEFAULT_CENTER_CODE,
        device: str | None = None,
        from_dt: str | None = None,
        to_dt: str | None = None,
        direction: str | None = None,
    ) -> None:
        self.fill_filters(center=center, device=device, from_dt=from_dt, to_dt=to_dt, direction=direction)
        self.submit()

    # ── state checks ──────────────────────────────────────
    def is_initial_state(self) -> bool:
        return self.initial_empty_title.is_visible()

    def is_empty_state(self) -> bool:
        return self.empty_title.is_visible()

    def is_loading(self) -> bool:
        return self.skeleton_loader.first.is_visible()

    def has_results(self) -> bool:
        return self.table.is_visible()

    def get_row_count(self) -> int:
        return self.table.locator("tbody tr").count()

    def get_total_count_text(self) -> str:
        return self.total_count_text.text_content() or ""
