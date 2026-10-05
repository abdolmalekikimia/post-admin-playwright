"""Device registration, editing, concurrency and activation via intercepted API."""
import pytest
from playwright.sync_api import expect
from utils.admin_testbed import DEVICE_ID, FAKE_SECRET

pytestmark=[pytest.mark.admin_mock,pytest.mark.admin_devices]


def open_create(ap):
    ap.open('devices')
    ap.main.get_by_role('button',name='ثبت دستگاه',exact=True).click()
    return ap.dialog('ثبت دستگاه جدید')


def fill_device(ap,dialog):
    dialog.get_by_label('کد منطقی',exact=True).fill('QA-NEW-SCANNER')
    ap.select_center(scope=dialog)
    dialog.get_by_label('نام دستگاه',exact=True).fill('QA New Scanner')
    dialog.get_by_label('نوع دستگاه',exact=True).fill('Scanner')
    dialog.get_by_label('مالک / مسئول',exact=True).fill('QA Owner')
    dialog.get_by_label('توضیحات',exact=True).fill('QA test device')


def test_create_device_requires_fields_and_sends_no_request(admin_mock_page):
    ap,api=admin_mock_page;dialog=open_create(ap)
    dialog.get_by_role('button',name='ثبت دستگاه',exact=True).click()
    for text in ('کد منطقی دستگاه الزامی است.','کد مرکز مبادله الزامی است.','نام دستگاه الزامی است.','نوع دستگاه الزامی است.'):
        expect(dialog.get_by_text(text,exact=True)).to_be_visible()
    assert api.mutations==[]


def test_create_device_payload_and_one_time_token(admin_mock_page):
    ap,api=admin_mock_page;dialog=open_create(ap);fill_device(ap,dialog)
    dialog.get_by_role('button',name='ثبت دستگاه',exact=True).click()
    credential=ap.dialog('دستگاه با موفقیت ثبت شد')
    secret=credential.get_by_label('توکن دستگاه',exact=True)
    expect(secret).to_have_attribute('type','password')
    expect(secret).to_have_value(FAKE_SECRET)
    request=next(x for x in api.mutations if x['path']=='/api/admin/devices')
    assert request['body']==dict(logicalCode='QA-NEW-SCANNER',exchangeCenterCode='10001',
        deviceName='QA New Scanner',deviceType='Scanner',owner='QA Owner',description='QA test device')
    expect(credential.get_by_role('button',name='بستن پنجره',exact=True)).to_be_disabled()
    credential.get_by_role('button',name='ذخیره کردم و بستن',exact=True).click()
    expect(credential).to_be_hidden()
    expect(ap.main.get_by_role('table').get_by_text('QA-NEW-SCANNER',exact=True)).to_be_visible()
    assert not ap.page.evaluate('(secret)=>Object.values(localStorage).some(v=>v.includes(secret))',FAKE_SECRET)


def test_cancel_device_creation_has_no_side_effect(admin_mock_page):
    ap,api=admin_mock_page;dialog=open_create(ap);fill_device(ap,dialog)
    dialog.get_by_role('button',name='انصراف',exact=True).click()
    expect(dialog).to_be_hidden()
    assert api.mutations==[]
    expect(ap.main.get_by_role('table').locator('tbody tr')).to_have_count(2)


def open_edit(ap):
    ap.open('devices')
    ap.table_row('QA-SCANNER-1').get_by_role('button',name='ویرایش QA-SCANNER-1',exact=True).click()
    dialog=ap.dialog('ویرایش دستگاه')
    expect(dialog.get_by_label('نام دستگاه',exact=True)).to_have_value('دستگاه سورت ۱')
    return dialog


def test_edit_device_preserves_identity_and_row_version(admin_mock_page):
    ap,api=admin_mock_page;dialog=open_edit(ap)
    expect(dialog.get_by_role('combobox')).to_have_count(0)
    dialog.get_by_label('نام دستگاه',exact=True).fill('QA Renamed Scanner')
    dialog.get_by_role('button',name='ذخیره تغییرات',exact=True).click()
    expect(dialog).to_be_hidden()
    expect(ap.table_row('QA-SCANNER-1').get_by_text('QA Renamed Scanner',exact=True)).to_be_visible()
    request=next(x for x in api.mutations if x['method']=='PUT')
    assert request['path']=='/api/admin/devices/'+DEVICE_ID
    assert request['body']['rowVersion']=='AAAAAAAB'
    assert request['body']['deviceName']=='QA Renamed Scanner'
    assert 'logicalCode' not in request['body'] and 'exchangeCenterCode' not in request['body']


def test_device_edit_conflict_keeps_form_and_original_row(admin_mock_page):
    ap,api=admin_mock_page;api.faults[('PUT','/api/admin/devices/'+DEVICE_ID)]=409
    dialog=open_edit(ap)
    dialog.get_by_label('نام دستگاه',exact=True).fill('QA Conflicting Edit')
    dialog.get_by_role('button',name='ذخیره تغییرات',exact=True).click()
    expect(dialog.get_by_role('alert')).to_be_visible()
    expect(dialog).to_be_visible()
    assert api.devices[0]['deviceName']=='دستگاه سورت ۱'
    assert len(api.mutations)==1


@pytest.mark.parametrize('initial_active',[True,False],ids=['deactivate','activate'])
def test_device_activation_requires_confirmation_and_version(admin_mock_page,initial_active):
    ap,api=admin_mock_page
    api.devices[0]['activationStatus']='Active' if initial_active else 'Inactive'
    ap.open('devices')
    label=('غیرفعال‌کردن ' if initial_active else 'فعال‌کردن ')+'QA-SCANNER-1'
    ap.table_row('QA-SCANNER-1').get_by_role('button',name=label,exact=True).click()
    dialog=ap.dialog('غیرفعال‌کردن دستگاه' if initial_active else 'فعال‌کردن دستگاه')
    assert api.mutations==[]
    dialog.get_by_role('button',name='غیرفعال شود' if initial_active else 'فعال شود',exact=True).click()
    expect(dialog).to_be_hidden()
    assert len(api.mutations)==1
    request=api.mutations[0]
    assert request['method']=='PATCH'
    assert request['path']==f"/api/admin/devices/{DEVICE_ID}/"+('deactivate' if initial_active else 'activate')
    assert request['body']=={'rowVersion':'AAAAAAAB'}
    opposite=('فعال‌کردن ' if initial_active else 'غیرفعال‌کردن ')+'QA-SCANNER-1'
    expect(ap.table_row('QA-SCANNER-1').get_by_role('button',name=opposite,exact=True)).to_be_visible()


def test_cancel_device_deactivation_sends_no_mutation(admin_mock_page):
    ap,api=admin_mock_page;ap.open('devices')
    ap.table_row('QA-SCANNER-1').get_by_role('button',name='غیرفعال‌کردن QA-SCANNER-1',exact=True).click()
    dialog=ap.dialog('غیرفعال‌کردن دستگاه')
    dialog.get_by_role('button',name='انصراف',exact=True).click()
    expect(dialog).to_be_hidden();assert api.mutations==[]


def test_registration_conflict_does_not_show_token_or_add_row(admin_mock_page):
    ap,api=admin_mock_page;api.faults[('POST','/api/admin/devices')]=409
    dialog=open_create(ap);fill_device(ap,dialog)
    dialog.get_by_role('button',name='ثبت دستگاه',exact=True).click()
    expect(dialog.get_by_role('alert')).to_be_visible()
    expect(dialog.get_by_label('نام دستگاه',exact=True)).to_have_value('QA New Scanner')
    expect(ap.page.get_by_role('dialog',name='دستگاه با موفقیت ثبت شد',exact=True)).to_have_count(0)
    assert len(api.devices)==2 and len(api.mutations)==1
