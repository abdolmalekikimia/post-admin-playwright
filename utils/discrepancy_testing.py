"""Browser setup shared by mocked discrepancy-report scenarios."""
import json
from urllib.parse import urlsplit, parse_qs
from utils.helpers import make_devices_payload, make_postal_codes_payload

MOCK_DISCREPANCY_URL = "**/api/admin/parcels/discrepancies*"


def install_reference_mocks(page):
    # Install before navigation so all reference requests use the same test data.
    page.route("**/api/admin/postal-codes*", lambda route: route.fulfill(
        status=200, content_type="application/json",
        body=json.dumps(make_postal_codes_payload()),
    ))
    page.route("**/api/admin/devices*", lambda route: route.fulfill(
        status=200, content_type="application/json",
        body=json.dumps(make_devices_payload()),
    ))


def select_center_and_submit(dp, page, discrepancy_handler):
    page.route(MOCK_DISCREPANCY_URL, discrepancy_handler)
    dp.center_code_input.click()
    dp.center_code_input.fill("10001")
    option = page.get_by_role("option").filter(has_text="10001").first
    option.wait_for(state="visible", timeout=10000)
    option.click()
    option.wait_for(state="hidden", timeout=5000)
    with page.expect_response(
        lambda response: "/api/admin/parcels/discrepancies" in response.url,
        timeout=10000,
    ) as report_response:
        dp.submit_button.click()
    query = parse_qs(urlsplit(report_response.value.url).query)
    assert query.get("exchangeCenterCode") == ["10001"], "Report must use the selected center"
