"""Observable interactions shared across admin pages."""
from playwright.sync_api import expect
from urllib.parse import urlsplit, parse_qs
from config import BASE_URL, DEFAULT_TIMEOUT

PAGES = [
    ("", "نمای کلی عملیات"), ("parcels", "مرسوله‌ها"),
    ("discrepancies", "گزارش مغایرت"), ("edges", "سلامت لبه"),
    ("edge-management", "مدیریت دسترسی لبه"), ("devices", "مدیریت دستگاه‌ها"),
    ("bags-dispatches", "کیسه و دپش"),
]


class AdminPage:
    def __init__(self, page):
        self.page = page
        self.main = page.get_by_role("main")

    def open(self, path):
        self.page.goto(f"{BASE_URL}/admin/{path}", wait_until="domcontentloaded")
        expect(self.main).to_be_visible()
        title = dict(PAGES).get(path)
        if title:
            expect(self.main.get_by_role("heading", name=title, exact=True)).to_be_visible(timeout=DEFAULT_TIMEOUT)
        else:
            # Details/not-found routes also load lazily; a layout alone is not ready.
            expect(self.main.get_by_role("heading").first).to_be_visible(timeout=DEFAULT_TIMEOUT)

    def select_center(self, label="کد مرکز مبادله", code="10001", scope=None):
        scope = scope if scope is not None else self.page
        field = scope.get_by_role("combobox", name=label, exact=True)
        # A dropdown opened at the viewport edge can close when Playwright
        # scrolls its option into view. Scroll before opening it, like a user.
        field.evaluate("el => el.scrollIntoView({block: 'center', inline: 'nearest'})")
        field.click()
        with self.page.expect_response(lambda r:
            urlsplit(r.url).path.endswith("/api/admin/postal-codes") and
            parse_qs(urlsplit(r.url).query).get("search") == [code]
        ) as lookup:
            field.fill(code)
        assert lookup.value.status == 200, "Center lookup must succeed before selecting its result"
        lookup.value.finished()
        option = self.page.get_by_role("option").filter(has_text=code)
        expect(option).to_have_count(1)
        expect(option).to_be_visible()
        option.click()
        expect(field).not_to_have_value(code)

    def table_row(self, value, table=None):
        table = table if table is not None else self.main.get_by_role("table")
        row = table.locator("tbody tr").filter(has_text=value)
        expect(row).to_have_count(1)
        return row

    def dialog(self, name):
        dialog = self.page.get_by_role("dialog", name=name, exact=True)
        expect(dialog).to_be_visible()
        return dialog

    def choose(self, label, option):
        self.page.get_by_role("combobox", name=label, exact=True).click()
        self.page.get_by_role("option", name=option, exact=True).click()
