"""Protected routes, desktop/mobile navigation, logout, and unknown URLs."""
import pytest
from playwright.sync_api import expect
from config import BASE_URL
from pages.admin_page import AdminPage, PAGES

pytestmark = pytest.mark.admin_navigation


@pytest.mark.parametrize("path,title", PAGES, ids=[p or "dashboard" for p,t in PAGES])
def test_protected_route_requires_login(page, path, title):
    page.goto(f"{BASE_URL}/admin/{path}", wait_until="domcontentloaded")
    page.wait_for_url("**/admin/login**")
    expect(page.get_by_role("textbox", name="نام کاربری")).to_be_visible()
    expect(page.get_by_role("heading", name=title, exact=True)).to_have_count(0)


@pytest.mark.admin_mock
@pytest.mark.parametrize("width", [1440, 390], ids=["desktop", "mobile"])
@pytest.mark.parametrize("path,title", PAGES, ids=[p or "dashboard" for p,t in PAGES])
def test_admin_route_renders_at_each_viewport(admin_mock_page, path, title, width):
    ap, api = admin_mock_page
    ap.page.set_viewport_size({"width": width, "height": 900})
    ap.open(path)
    expect(ap.main.get_by_role("heading", name=title, exact=True)).to_be_visible()
    expect(ap.main).to_be_visible()
    assert not api.mutations


@pytest.mark.admin_mock
def test_sidebar_link_opens_devices(admin_mock_page):
    ap, api = admin_mock_page; ap.open("")
    ap.page.get_by_role("link", name="مدیریت دستگاه‌ها", exact=True).click()
    expect(ap.page).to_have_url(f"{BASE_URL}/admin/devices")
    expect(ap.main.get_by_role("table").get_by_text("QA-SCANNER-1", exact=True)).to_be_visible()


@pytest.mark.admin_mock
def test_logout_prevents_reopening_protected_route(admin_mock_page):
    ap, api = admin_mock_page; ap.open("devices")
    ap.page.get_by_role("button", name="خروج از حساب", exact=True).click()
    ap.page.wait_for_url("**/admin/login**")
    ap.page.goto(f"{BASE_URL}/admin/devices", wait_until="domcontentloaded")
    ap.page.wait_for_url("**/admin/login**")
    expect(ap.page.get_by_role("textbox", name="نام کاربری")).to_be_visible()


@pytest.mark.admin_mock
def test_unknown_route_can_return_to_dashboard(admin_mock_page):
    ap, api = admin_mock_page; ap.open("qa-path-does-not-exist")
    expect(ap.main.get_by_role("heading", name="این صفحه پیدا نشد", exact=True)).to_be_visible()
    ap.page.get_by_role("link", name="بازگشت به داشبورد").click()
    expect(ap.main.get_by_role("heading", name="نمای کلی عملیات", exact=True)).to_be_visible()
