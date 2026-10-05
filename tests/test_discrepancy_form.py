"""Observable validation and reset of discrepancy filters; report data is mocked."""
import json
from urllib.parse import urlsplit, parse_qs
from datetime import datetime
import allure
import pytest
from playwright.sync_api import expect
from utils.helpers import make_discrepancy_payload
from utils.discrepancy_testing import select_center_and_submit, MOCK_DISCREPANCY_URL


@allure.epic("Admin Panel — گزارش مغایرت")
@allure.feature("Form Validation & Filters")
@pytest.mark.discrepancy
@pytest.mark.discrepancy_form
@pytest.mark.discrepancy_mock
class TestDiscrepancyFormValidation:
    def test_missing_center_code(self, mocked_discrepancy_page):
        dp=mocked_discrepancy_page
        requests=[]
        dp.page.on('request',lambda r:requests.append(r.url) if '/parcels/discrepancies' in r.url else None)
        dp.submit()
        expect(dp.page.get_by_text('کد مرکز مبادله الزامی است',exact=True)).to_be_visible()
        assert requests==[], 'Invalid filters must not send a report request'

    def test_to_before_from(self, mocked_discrepancy_page):
        # End dates earlier than the start are disabled by the visible picker.
        dp=mocked_discrepancy_page;page=dp.page
        before=dp.to_date_input.get_attribute('aria-label')
        dp.to_date_input.click()
        calendar=page.locator('.rmdp-calendar:visible')
        expect(calendar).to_be_visible()
        disabled=calendar.locator('.rmdp-day-picker .rmdp-day.rmdp-disabled:not(.rmdp-day-hidden):visible')
        for _ in range(3):
            if disabled.count(): break
            calendar.locator('button.rmdp-arrow-container.rmdp-left').click()
        assert disabled.count()>0, 'The calendar must expose disabled days before the start'
        disabled.first.click()
        page.get_by_role('button',name='تأیید',exact=True).click()
        expect(dp.to_date_input).to_have_attribute('aria-label',before)
        expect(dp.initial_empty_title).to_be_visible()

    def test_reset_clears_filters(self, mocked_discrepancy_page):
        dp=mocked_discrepancy_page;page=dp.page
        select_center_and_submit(dp,page,lambda route:route.fulfill(json=make_discrepancy_payload()))
        expect(dp.table.locator('tbody tr')).to_have_count(1)
        dp.reset_filters()
        expect(dp.center_code_input).to_have_value('')
        expect(dp.device_select).to_be_disabled()
        expect(dp.price_direction_select).to_have_text('همهٔ جهت‌ها')
        expect(dp.table).to_have_count(0)
        expect(dp.initial_empty_title).to_be_visible()

    def test_price_direction_options(self, mocked_discrepancy_page):
        dp=mocked_discrepancy_page;dp.price_direction_select.click()
        for name in ('همهٔ جهت‌ها','افزایش قیمت','کاهش قیمت'):
            expect(dp.page.get_by_role('option',name=name,exact=True)).to_be_visible()

    def test_valid_filter_submit(self, mocked_discrepancy_page):
        dp=mocked_discrepancy_page;page=dp.page
        page.route(MOCK_DISCREPANCY_URL,lambda route:route.fulfill(json=make_discrepancy_payload()))
        dp.fill_filters(center='10001',device='دستگاه سورت ۱',direction='افزایش قیمت')
        with page.expect_response(lambda r:'/parcels/discrepancies' in r.url) as response:
            dp.submit()
        assert response.value.status==200
        query=parse_qs(urlsplit(response.value.url).query)
        assert query['exchangeCenterCode']==['10001']
        assert query['deviceId']==['DEV-001']
        assert query['priceDirection']==['Positive']
        assert datetime.fromisoformat(query['fromUtc'][0]) < datetime.fromisoformat(query['toUtc'][0])
        expect(dp.table.locator('tbody tr')).to_have_count(1)

    @pytest.mark.parametrize('field',['from','to'])
    def test_required_date_blocks_report(self,mocked_discrepancy_page,field):
        dp=mocked_discrepancy_page;page=dp.page
        calls=[]
        page.on('request',lambda r:calls.append(r.url) if '/parcels/discrepancies' in r.url else None)
        dp.fill_filters(center='10001')
        label='پاک‌کردن از تاریخ و زمان' if field=='from' else 'پاک‌کردن تا تاریخ و زمان (غیرشامل)'
        page.get_by_role('button',name=label,exact=True).click()
        dp.submit()
        expect(page.get_by_text('تاریخ و زمان الزامی است',exact=True)).to_be_visible()
        assert calls==[]

    def test_equal_start_and_end_blocks_report(self, mocked_discrepancy_page):
        dp=mocked_discrepancy_page;page=dp.page
        calls=[]
        page.on('request',lambda r:calls.append(r.url) if '/parcels/discrepancies' in r.url else None)
        tomorrow=page.evaluate('() => { const date=new Date(); date.setHours(0,0,0,0); date.setDate(date.getDate()+1); return date.toISOString(); }')
        dp.fill_filters(center='10001',from_dt=tomorrow)
        dp.submit()
        expect(page.get_by_text('زمان پایان باید بعد از زمان شروع باشد',exact=True)).to_be_visible()
        assert calls==[]
