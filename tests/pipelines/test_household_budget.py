"""都民のくらしむき 長期時系列表1から年 × 指標 × 項目の行を取り出す処理のテスト。"""

import pytest

from pipelines.household_budget import _latest_annual_page, _parse

_CSV = """"実数・増加率","年次コード","年次","西暦（年）","調査世帯数（世帯）","生計支出（円）","生計支出／消費支出／食料（円）","エンゲル係数（％）"
"jissu","nen","令和 6年","2024",600,300000,100000,29.5
"jissu","nen","令和 7年","2025",594,310000,104143,-
"meimoku","nen","対前年名目増加率_令和 7年","2025",-,3.3,4.1,-
"jissitu","nen","対前年実質増加率_令和 7年","2025",-,-,-0.7,
"","","","","","","",""
"東京都生計分析調査　令和 7年"
"長期時系列表１　主な支出及び対前年増加率　―　全世帯　―"
"""


def test_parse_splits_measures_and_items():
    records = _parse(_CSV)
    assert len(records) == 16  # 実数2行 + 名目1行 + 実質1行、各4項目
    assert {
        "year": "2025",
        "measure": "actual",
        "item_path": "生計支出／消費支出／食料",
        "unit": "円",
        "value": "104143",
    } in records
    assert {
        "year": "2025",
        "measure": "real_growth",
        "item_path": "生計支出／消費支出／食料",
        "unit": "円",
        "value": "-0.7",
    } in records


def test_parse_keeps_missing_markers():
    records = _parse(_CSV)
    values = {
        (r["measure"], r["item_path"]): r["value"]
        for r in records
        if r["year"] == "2025"
    }
    assert values[("actual", "エンゲル係数")] == "-"
    assert values[("real_growth", "エンゲル係数")] == ""


def test_parse_rejects_other_table():
    with pytest.raises(ValueError, match="長期時系列表1"):
        _parse(_CSV.replace("長期時系列表１", "長期時系列表２"))


def test_parse_rejects_header_without_unit():
    with pytest.raises(ValueError, match="単位"):
        _parse(_CSV.replace("生計支出（円）", "生計支出"))


def test_parse_rejects_non_numeric_year():
    with pytest.raises(ValueError, match="西暦"):
        _parse(_CSV.replace('"2024"', '"x"'))


def test_latest_annual_page_ignores_monthly_pages():
    html = (
        '<a href="/seikei/2025/sb25q00000.htm">令和7年</a>'
        '<a href="/seikei/2024/sb24q00000.htm">令和6年</a>'
        '<a href="/seikei/2026/sb26820000.htm">8月</a>'
    )
    year, url = _latest_annual_page(html)
    assert year == 2025
    assert url.endswith("/seikei/2025/sb25q00000.htm")


def test_latest_annual_page_requires_a_link():
    with pytest.raises(RuntimeError):
        _latest_annual_page("<a href='/seikei/2026/sb26820000.htm'>8月</a>")
