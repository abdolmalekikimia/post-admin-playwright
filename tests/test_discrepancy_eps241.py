"""EPS-241 frontend acceptance. Report data mocked; authentication/frontend live.
Passing these tests is not evidence of backend calculation correctness.
"""
import json
import re
import pytest
from playwright.sync_api import expect
from utils.helpers import make_discrepancy_payload
from utils.discrepancy_testing import select_center_and_submit

def number(text):
    return text.translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")).replace("٬", "").replace(",", "").replace("−", "-").replace("\u200e", "").replace("\u200f", "")

def column(dp, row, pattern):
    headers = dp.table.get_by_role("columnheader").all_text_contents()
    indices = [i for i, label in enumerate(headers) if re.search(pattern, label)]
    assert len(indices) == 1, f"Missing/ambiguous EPS-241 column {pattern}: {headers}"
    return row.locator("td").nth(indices[0])

def render(dp, size="5", price=320000, aggregate=False):
    payload = make_discrepancy_payload()
    reading = payload["items"][0]["readings"][0]
    reading["deviceName"] = "دستگاه سورت ۱"
    for item in reading["discrepancies"]:
        item["recalculatedPriceRial"] = price
        if item["type"] == "BoxSizeDiscrepancy":
            item.update(registeredValue="2", measuredValue=size)
    # Totals count each reading once, including both discrepancy types.
    payload.update(totalCount=45 if aggregate else 1,
                   totalRecordedPriceRial=11250000 if aggregate else 250000,
                   totalRecalculatedPriceRial=14400000 if aggregate else price)
    select_center_and_submit(dp, dp.page, lambda route: route.fulfill(
        status=200, content_type="application/json", body=json.dumps(payload)))
    link = dp.table.get_by_role("link", name=payload["items"][0]["parcelBarcode"], exact=True)
    expect(link).to_be_visible()
    return link.locator("xpath=ancestor::tr[1]")

def color_channels(locator):
    return [int(x) for x in re.findall(r"[0-9]+", locator.evaluate(
        "(el) => getComputedStyle(el).color"))[:3]]

@pytest.mark.discrepancy
@pytest.mark.discrepancy_results
@pytest.mark.discrepancy_mock
class TestEPS241:
    def test_device_name_in_row(self, mocked_discrepancy_page):
        dp = mocked_discrepancy_page
        expect(render(dp).get_by_text("دستگاه سورت ۱", exact=True)).to_be_visible()

    @pytest.mark.parametrize("code,label", [("5", "5"), ("11", "+9"), ("12", "++9")])
    def test_postal_dimension_labels(self, mocked_discrepancy_page, code, label):
        dp = mocked_discrepancy_page
        row = render(dp, size=code)
        assert number(column(dp, row, "ابعاد اندازه").inner_text()).strip() == label

    @pytest.mark.parametrize("price,difference", [(320000, 70000), (180000, -70000), (250000, 0)])
    def test_cost_difference_and_colors(self, mocked_discrepancy_page, price, difference):
        dp = mocked_discrepancy_page
        row = render(dp, price=price)
        delta = column(dp, row, "اختلاف هزینه")
        text = number(delta.inner_text())
        assert re.search(r"(?<![0-9])" + re.escape(str(difference)) + r"(?![0-9])", text), text
        recalculated = column(dp, row, "هزینه باز|قیمت محاسبه")
        assert str(price) in number(recalculated.inner_text())
        rgb = color_channels(recalculated)
        assert len(rgb) == 3 and max(rgb) <= 110 and max(rgb)-min(rgb) <= 40, rgb
        if difference:
            rgb = color_channels(delta)
            assert len(rgb) == 3 and max(rgb)-min(rgb) > 40, rgb

    def test_bold_first_row_totals_across_pages(self, mocked_discrepancy_page):
        dp = mocked_discrepancy_page
        render(dp, aggregate=True)
        row = dp.table.locator("tbody tr").first
        expect(row).to_contain_text(re.compile("مجموع|جمع"))
        for pattern, total in [("هزینه ثبت|قیمت اصلی", 11250000),
                               ("هزینه باز|قیمت محاسبه", 14400000),
                               ("اختلاف هزینه", 3150000)]:
            value = column(dp, row, pattern)
            assert str(total) in number(value.inner_text())
            assert int(value.evaluate("(el) => getComputedStyle(el).fontWeight")) >= 700