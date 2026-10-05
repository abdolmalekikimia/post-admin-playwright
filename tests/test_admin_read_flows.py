"""Data, filtering, paging, detail and recovery across read-only admin views."""
import pytest
from playwright.sync_api import expect
from utils.admin_testbed import BARCODE

pytestmark = [pytest.mark.admin_mock, pytest.mark.admin_read]


def test_dashboard_latest_parcel_opens_detail(admin_mock_page):
    ap, api = admin_mock_page; ap.open("")
    expect(ap.main.get_by_text("کارت‌های آماری، نمودارها و وضعیت لبه‌ها فعلاً دادهٔ آزمایشی‌اند؛ فقط فهرست آخرین مرسوله‌ها از درگاه خوانده می‌شود.", exact=True)).to_be_visible()
    ap.main.get_by_role("link").filter(has_text=BARCODE).click()
    expect(ap.main.get_by_role("heading", name="جزئیات مرسوله", exact=True)).to_be_visible()
    expect(ap.main.get_by_text("QA-READ-1", exact=True)).to_be_visible()


def test_parcel_detail_shows_readings_and_attachments(admin_mock_page):
    ap, api = admin_mock_page; ap.open(f"parcels/{BARCODE}")
    expect(ap.main.get_by_text("QA-READ-1", exact=True)).to_be_visible()
    expect(ap.main.get_by_text("qa/images/parcel-001.jpg", exact=True)).to_be_visible()
    expect(ap.main.get_by_text("image/jpeg", exact=True)).to_be_visible()
    ap.main.get_by_role("link", name="بازگشت به فهرست", exact=True).click()
    expect(ap.main.get_by_role("heading", name="مرسوله‌ها", exact=True)).to_be_visible()


def test_missing_parcel_reports_not_found(admin_mock_page):
    ap, api = admin_mock_page; ap.open("parcels/000000000000000000000000")
    expect(ap.main.get_by_role("heading", name="مرسوله پیدا نشد", exact=True)).to_be_visible()
    assert any(x['path'].endswith('/000000000000000000000000') for x in api.calls)


def test_parcel_barcode_filter_and_clear(admin_mock_page):
    ap, api = admin_mock_page; ap.open("parcels")
    table = ap.main.get_by_role("table")
    expect(table.locator("tbody tr")).to_have_count(10)
    ap.page.get_by_label("بارکد مرسوله", exact=True).fill(BARCODE)
    expect(table.locator("tbody tr")).to_have_count(1)
    expect(table.get_by_role("link", name=BARCODE, exact=True)).to_be_visible()
    ap.page.get_by_label("بارکد مرسوله", exact=True).fill("999999999999999999999999")
    expect(ap.main.get_by_role("heading", name="در این صفحه نتیجه‌ای با این فیلترها پیدا نشد", exact=True)).to_be_visible()
    ap.main.get_by_role("button", name="پاک‌کردن فیلترها", exact=True).click()
    expect(table.locator("tbody tr")).to_have_count(10)


def test_parcel_sort_changes_row_order(admin_mock_page):
    ap, api = admin_mock_page
    for i, parcel in enumerate(api.parcels, 1):
        parcel["createdAtUtc"] = f"2026-10-01T10:{i:02d}:00Z"
    ap.open("parcels")
    table = ap.main.get_by_role("table")
    expect(table.locator("tbody tr").first.get_by_role("link")).to_have_text("100010000000000000000010")
    ap.choose("مرتب‌سازی", "بارکد صعودی")
    expect(table.locator("tbody tr").first.get_by_role("link")).to_have_text(BARCODE)
    ap.choose("مرتب‌سازی", "جدیدترین ایجاد")
    expect(table.locator("tbody tr").first.get_by_role("link")).to_have_text("100010000000000000000010")


@pytest.mark.parametrize("path,endpoint", [("parcels","parcels"),("devices","devices"),("edge-management","edges")])
def test_center_filter_is_sent_to_api(admin_mock_page, path, endpoint):
    ap, api = admin_mock_page; ap.open(path)
    if path == "parcels":
        with ap.page.expect_response(lambda r: r.url.split('?')[0].endswith('/api/admin/parcels') and 'exchangeCenterCode=10001' in r.url):
            ap.select_center(label="کد مرکز")
    else:
        ap.select_center()
    if path in ("devices", "edge-management"):
        with ap.page.expect_response(lambda r: r.url.split('?')[0].endswith('/api/admin/'+endpoint)):
            ap.main.get_by_role("button", name="جست‌وجو", exact=True).click()
    else:
        expect(ap.main.get_by_role("table")).to_be_visible()
    def has_filter():
        return any(x['path']=='/api/admin/'+endpoint and x['query'].get('exchangeCenterCode')==['10001'] for x in api.calls)
    assert has_filter(), 'Selected center must reach the API query'


@pytest.mark.parametrize("endpoint,title,path", [
    ("devices","دستگاه‌ها دریافت نشدند","devices"),
    ("edges","دسترسی‌های لبه دریافت نشدند","edge-management"),
    ("parcels","مرسوله‌ها دریافت نشدند","parcels"),
])
def test_api_error_retry_recovers(admin_mock_page, endpoint, title, path):
    ap, api = admin_mock_page; api.faults[("GET",'/api/admin/'+endpoint)] = 403
    ap.open(path)
    expect(ap.main.get_by_role('heading',name=title,exact=True)).to_be_visible()
    before = len([x for x in api.calls if x['path']=='/api/admin/'+endpoint])
    del api.faults[("GET",'/api/admin/'+endpoint)]
    with ap.page.expect_response(lambda r:r.url.split('?')[0].endswith('/api/admin/'+endpoint)) as response:
        ap.main.get_by_role('button',name='تلاش دوباره',exact=True).click()
    assert response.value.status == 200
    expect(ap.main.get_by_role('table').locator('tbody tr').first).to_be_visible()
    assert len([x for x in api.calls if x['path']=='/api/admin/'+endpoint]) == before+1


def test_device_contract_error_is_visible(admin_mock_page):
    ap, api = admin_mock_page;api.overrides[('GET','/api/admin/devices')]={'items':[{'deviceId':'bad'}]}
    ap.open('devices')
    expect(ap.main.get_by_role('heading',name='دستگاه‌ها دریافت نشدند',exact=True)).to_be_visible()
    expect(ap.main.get_by_text('پاسخ درگاه با قرارداد مورد انتظار هماهنگ نیست.',exact=True)).to_be_visible()


@pytest.mark.parametrize('endpoint,title,path',[("parcels","مرسوله‌ای ثبت نشده است","parcels"),("devices","دستگاهی ثبت نشده است","devices"),("edges","دسترسی لبه‌ای ثبت نشده است","edge-management")])
def test_empty_list_has_explicit_state(admin_mock_page,endpoint,title,path):
    ap, api=admin_mock_page
    api.overrides[('GET','/api/admin/'+endpoint)]={'items':[],'page':1,'pageSize':10,'totalCount':0}
    ap.open(path)
    expect(ap.main.get_by_role('heading',name=title,exact=True)).to_be_visible()
    expect(ap.main.get_by_role('table')).to_have_count(0)


def test_health_search_and_clear_local_preview(admin_mock_page):
    ap, api=admin_mock_page;ap.open('edges')
    expect(ap.main.get_by_text('وضعیت اتصال، ضربان اتصال و صف‌های پردازشی فعلاً از دادهٔ آزمایشی محلی نمایش داده می‌شوند.',exact=True)).to_be_visible()
    table=ap.main.get_by_role('table')
    expect(table.locator('tbody tr')).to_have_count(8)
    ap.page.get_by_label('شناسه لبه',exact=True).fill('EDGE-THR-01')
    expect(table.locator('tbody tr')).to_have_count(1)
    ap.page.get_by_label('شناسه لبه',exact=True).fill('QA-NO-SUCH-EDGE')
    expect(ap.main.get_by_role('heading',name='لبه‌ای با این فیلترها پیدا نشد',exact=True)).to_be_visible()
    ap.main.get_by_role('button',name='پاک‌کردن فیلترها',exact=True).click()
    expect(table.locator('tbody tr')).to_have_count(8)


def test_bags_and_dispatches_show_distinct_records(admin_mock_page):
    ap, api=admin_mock_page;ap.open('bags-dispatches')
    tables=ap.main.get_by_role('table')
    expect(tables).to_have_count(2)
    expect(tables.nth(0).get_by_text('QA-BAG-001',exact=True)).to_be_visible()
    expect(tables.nth(1).get_by_text('QA-DISPATCH-001',exact=True)).to_be_visible()
    expect(tables.nth(0).get_by_text('QA-SEAL-1',exact=True)).to_be_visible()


@pytest.mark.parametrize('path,endpoint,record',[
    ('parcels','parcels','100010000000000000000011'),
    ('devices','devices','QA-SCANNER-11'),
    ('edge-management','edges','QA-EDGE-011'),
    ('bags-dispatches','bags','QA-BAG-011'),
    ('bags-dispatches','dispatches','QA-DISPATCH-011'),
],ids=['parcels','devices','edges','bags','dispatches'])
def test_pagination_requests_second_page_and_changes_records(admin_mock_page,path,endpoint,record):
    from copy import deepcopy
    ap,api=admin_mock_page
    if endpoint=='devices':
        for i in range(3,13):
            item=deepcopy(api.devices[0]);item.update(deviceId=f'DEV-{i:03d}',logicalCode=f'QA-SCANNER-{i}')
            api.devices.append(item)
    if endpoint=='edges':
        for i in range(3,13):
            item=deepcopy(api.edges[0]);item['edgeId']=f'QA-EDGE-{i:03d}';api.edges.append(item)
    ap.open(path)
    scope=ap.main
    if endpoint in ('bags','dispatches'):
        scope=ap.main.get_by_role('region',name='فهرست کیسه‌ها' if endpoint=='bags' else 'فهرست دپش‌ها',exact=True)
    table=scope.get_by_role('table')
    expect(table.locator('tbody tr')).to_have_count(10)
    with ap.page.expect_response(lambda r:r.url.split('?')[0].endswith('/api/admin/'+endpoint) and 'page=2' in r.url):
        scope.get_by_role('button',name='صفحه بعد',exact=True).click()
    expect(table.locator('tbody tr')).to_have_count(2)
    expect(table.get_by_text(record,exact=True)).to_be_visible()
    assert any(x['path']=='/api/admin/'+endpoint and x['query'].get('page')==['2'] for x in api.calls)


@pytest.mark.parametrize('endpoint,label', [('bags','کد مرکز کیسه‌ها'),('dispatches','کد مرکز دپش‌ها')],ids=['bags','dispatches'])
def test_logistics_filters_are_independent(admin_mock_page,endpoint,label):
    ap,api=admin_mock_page;ap.open('bags-dispatches')
    before={name:len([x for x in api.calls if x['path']=='/api/admin/'+name]) for name in ('bags','dispatches')}
    ap.select_center(label=label,code='10002')
    filter_region=ap.main.get_by_role('region',name='فیلترهای فهرست کیسه‌ها' if endpoint=='bags' else 'فیلترهای فهرست دپش‌ها',exact=True)
    with ap.page.expect_response(lambda r:r.url.split('?')[0].endswith('/api/admin/'+endpoint) and 'exchangeCenterCode=10002' in r.url):
        filter_region.get_by_role('button',name='اعمال فیلتر',exact=True).click()
    other='dispatches' if endpoint=='bags' else 'bags'
    assert len([x for x in api.calls if x['path']=='/api/admin/'+other])==before[other]
    latest=[x for x in api.calls if x['path']=='/api/admin/'+endpoint][-1]
    assert latest['query']['exchangeCenterCode']==['10002']


def test_mobile_parcel_card_opens_detail(admin_mock_page):
    ap,api=admin_mock_page;ap.page.set_viewport_size({'width':390,'height':844});ap.open('parcels')
    expect(ap.main.get_by_role('table')).to_have_count(0)
    card=ap.main.get_by_role('link').filter(has_text=BARCODE)
    expect(card).to_have_count(1)
    card.click()
    expect(ap.main.get_by_role('heading',name='جزئیات مرسوله',exact=True)).to_be_visible()
    expect(ap.main.get_by_text('QA-READ-1',exact=True)).to_be_visible()
