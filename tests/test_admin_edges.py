"""Edge identity, one-time secrets, access changes and publishing requests."""
import pytest
from playwright.sync_api import expect
from utils.admin_testbed import EDGE_ID, FAKE_SECRET

pytestmark=[pytest.mark.admin_mock,pytest.mark.admin_edges]


def open_registration(ap):
    ap.open('edge-management')
    ap.main.get_by_role('button',name='ثبت دسترسی لبه',exact=True).click()
    return ap.dialog('ثبت دسترسی لبه')


def test_edge_registration_validation(admin_mock_page):
    ap,api=admin_mock_page;dialog=open_registration(ap)
    dialog.get_by_role('button',name='ثبت و تولید رمز',exact=True).click()
    expect(dialog.get_by_text('شناسه لبه الزامی است.',exact=True)).to_be_visible()
    expect(dialog.get_by_text('کد مرکز مبادله الزامی است.',exact=True)).to_be_visible()
    assert api.mutations==[]


def test_edge_registration_sends_identity_and_masks_secret(admin_mock_page):
    ap,api=admin_mock_page;dialog=open_registration(ap)
    dialog.get_by_label('شناسه لبه',exact=True).fill('QA-EDGE-NEW')
    ap.select_center(scope=dialog)
    dialog.get_by_role('button',name='ثبت و تولید رمز',exact=True).click()
    credential=ap.dialog('دسترسی لبه با موفقیت ایجاد شد')
    field=credential.get_by_label('رمز لبه',exact=True)
    expect(field).to_have_attribute('type','password');expect(field).to_have_value(FAKE_SECRET)
    request=api.mutations[0]
    assert request['path']=='/api/admin/edges' and request['method']=='POST'
    assert request['body']['edgeId']=='QA-EDGE-NEW'
    assert request['body']['authorizedCenterCode']=='10001'
    from uuid import UUID
    UUID(request['body']['clientId'])
    assert 'plaintextSecret' not in request['body']
    expect(credential.get_by_role('button',name='بستن پنجره',exact=True)).to_be_disabled()
    credential.get_by_role('button',name='ذخیره کردم و بستن',exact=True).click()
    expect(credential).to_be_hidden()
    expect(ap.main.get_by_role('table').get_by_text('QA-EDGE-NEW',exact=True)).to_be_visible()
    assert not ap.page.evaluate('(secret)=>Object.values(localStorage).some(v=>v.includes(secret))',FAKE_SECRET)


def test_edge_details_do_not_expose_secret(admin_mock_page):
    ap,api=admin_mock_page;ap.open('edge-management')
    ap.table_row(EDGE_ID).get_by_role('button',name='جزئیات '+EDGE_ID,exact=True).click()
    dialog=ap.dialog('جزئیات دسترسی لبه')
    expect(dialog.get_by_text('قابل بازیابی نیست',exact=True)).to_be_visible()
    expect(dialog.get_by_text(EDGE_ID,exact=True)).to_be_visible()
    expect(dialog.locator('input[type=password]')).to_have_count(0)
    assert api.mutations==[]


@pytest.mark.parametrize('initial_active',[True,False],ids=['disable','enable'])
def test_edge_access_change_requires_confirmation(admin_mock_page,initial_active):
    ap,api=admin_mock_page;api.edges[0]['isActive']=initial_active;ap.open('edge-management')
    label=('غیرفعال‌کردن ' if initial_active else 'فعال‌کردن ')+EDGE_ID
    ap.table_row(EDGE_ID).get_by_role('button',name=label,exact=True).click()
    dialog=ap.dialog('غیرفعال‌کردن دسترسی لبه' if initial_active else 'فعال‌کردن دسترسی لبه')
    assert api.mutations==[]
    dialog.get_by_role('button',name='غیرفعال شود' if initial_active else 'فعال شود',exact=True).click()
    expect(dialog).to_be_hidden()
    assert len(api.mutations)==1
    assert api.mutations[0]['path']==f"/api/admin/edges/{EDGE_ID}/"+('disable' if initial_active else 'enable')
    assert api.mutations[0]['method']=='POST'
    opposite=('فعال‌کردن ' if initial_active else 'غیرفعال‌کردن ')+EDGE_ID
    expect(ap.table_row(EDGE_ID).get_by_role('button',name=opposite,exact=True)).to_be_visible()


def open_publish(ap):
    ap.open('edge-management')
    ap.table_row(EDGE_ID).get_by_role('button',name='انتشار پیکربندی مرکز 10001',exact=True).click()
    return ap.dialog('انتشار پیکربندی مرکز')


def test_publish_configuration_uses_selected_center_and_numeric_windows(admin_mock_page):
    ap,api=admin_mock_page;dialog=open_publish(ap)
    dialog.get_by_label('بازه کوتاه تشخیص تکرار (ساعت)',exact=True).fill('12')
    dialog.get_by_label('بازه بلند تشخیص تکرار (ساعت)',exact=True).fill('96')
    dialog.get_by_role('button',name='انتشار پیکربندی',exact=True).click()
    expect(dialog).to_be_hidden()
    assert api.mutations==[dict(method='POST',path='/api/admin/configuration-snapshots',query={},
                               body=dict(exchangeCenterCode='10001',duplicateWindowShortHours=12,duplicateWindowLongHours=96))]
    expect(ap.main.get_by_text('نسخهٔ ۲ پیکربندی مرکز 10001 منتشر شد.',exact=True)).to_be_visible()


@pytest.mark.parametrize('value',['-1','1.5',''],ids=['negative','fraction','missing'])
def test_publish_rejects_invalid_window(admin_mock_page,value):
    ap,api=admin_mock_page;dialog=open_publish(ap)
    dialog.get_by_label('بازه کوتاه تشخیص تکرار (ساعت)',exact=True).fill(value)
    dialog.get_by_role('button',name='انتشار پیکربندی',exact=True).click()
    message='مقدار ساعت الزامی است.' if not value else 'مقدار ساعت باید یک عدد صحیح نامنفی باشد.'
    expect(dialog.get_by_text(message,exact=True)).to_be_visible()
    assert api.mutations==[]


def test_cancel_publish_sends_no_request(admin_mock_page):
    ap,api=admin_mock_page;dialog=open_publish(ap)
    dialog.get_by_role('button',name='انصراف',exact=True).click()
    expect(dialog).to_be_hidden();assert api.mutations==[]


def test_cancel_edge_deactivation_has_no_side_effect(admin_mock_page):
    ap,api=admin_mock_page;ap.open('edge-management')
    ap.table_row(EDGE_ID).get_by_role('button',name='غیرفعال‌کردن '+EDGE_ID,exact=True).click()
    dialog=ap.dialog('غیرفعال‌کردن دسترسی لبه')
    dialog.get_by_role('button',name='انصراف',exact=True).click()
    expect(dialog).to_be_hidden();assert api.mutations==[] and api.edges[0]['isActive']


def test_publish_service_error_keeps_window_values(admin_mock_page):
    ap,api=admin_mock_page;api.faults[('POST','/api/admin/configuration-snapshots')]=503
    dialog=open_publish(ap)
    dialog.get_by_label('بازه کوتاه تشخیص تکرار (ساعت)',exact=True).fill('12')
    dialog.get_by_role('button',name='انتشار پیکربندی',exact=True).click()
    expect(dialog.get_by_role('alert')).to_be_visible()
    expect(dialog.get_by_label('بازه کوتاه تشخیص تکرار (ساعت)',exact=True)).to_have_value('12')
    expect(dialog).to_be_visible()
    assert len(api.mutations)==1
