"""Read-only live integration. HTTP/API failures are reported, never replaced by mocks."""
from contextlib import ExitStack
import pytest
from playwright.sync_api import expect

pytestmark=pytest.mark.admin_live


@pytest.mark.parametrize('path,title,endpoints',[
    ('','نمای کلی عملیات',['parcels']),
    ('parcels','مرسوله‌ها',['parcels']),
    ('devices','مدیریت دستگاه‌ها',['devices']),
    ('edge-management','مدیریت دسترسی لبه',['edges']),
    ('bags-dispatches','کیسه و دپش',['bags','dispatches']),
],ids=['dashboard','parcels','devices','edge-management','bags-dispatches'])
def test_live_admin_list_contract(admin_live_page,path,title,endpoints):
    ap=admin_live_page
    # Arm each expected API response before navigation; heading visibility does
    # not imply that asynchronous list requests have finished.
    with ExitStack() as stack:
        pending={endpoint:stack.enter_context(ap.page.expect_response(
            lambda r, endpoint=endpoint: r.url.split('?')[0].endswith('/api/admin/'+endpoint)
        )) for endpoint in endpoints}
        ap.open(path)
    expect(ap.main.get_by_role('heading',name=title,exact=True)).to_be_visible()
    for endpoint in endpoints:
        response=pending[endpoint].value
        assert response.status==200, f'Live {endpoint} API returned HTTP {response.status}'
        payload=response.json()
        assert isinstance(payload.get('items'),list), f'Live {endpoint} response has no items collection'
        assert isinstance(payload.get('totalCount'),int), f'Live {endpoint} response has no numeric totalCount'
        assert payload['totalCount']>=len(payload['items'])
        assert payload.get('page',0)>=1 and payload.get('pageSize',0)>=1
