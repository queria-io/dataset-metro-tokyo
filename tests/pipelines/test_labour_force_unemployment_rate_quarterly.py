"""東京の労働力 四半期平均の参考表から四半期 × 地域 × 男女の行を取り出す処理のテスト。"""

import pytest

from pipelines.labour_force_unemployment_rate_quarterly import (
    _parse,
    _year_quarter,
)

_AREAS = "東京都", "南関東", "全国"
_SEXES = "男女計", "男", "女"
_HEADER = "年・期平均,西暦(年),四半期," + ",".join(
    f"{area}／{sex}(％、ポイント）" for area in _AREAS for sex in _SEXES
)

_CSV = (
    _HEADER
    + """
完全失業率／令和６年,2024,,2.6,2.7,2.5,2.7,2.7,2.6,2.5,2.7,2.4
完全失業率／平成31年・令和元年４～６月,2019,04～06,2.3,2.5,2.2,2.3,2.4,2.1,2.4,2.5,2.2
完全失業率／令和７年10～12月,2025,10～12,2.4,2.7,2.2,2.5,2.7,2.3,2.5,2.7,2.3
対前年・対前年同期増減数／令和７年４～６月,2025,04～06,-0.2,0,-0.3,-0.2,0,-0.3,0,0,-0.1
,,,,,,,,,,,
東京の労働力統計データ（令和７年４～６月期平均）,,,,,,,,,,,
参考表　東京都、南関東及び全国の完全失業率（原数値）,,,,,,,,,,,
"""
)

# 2003〜2004年の表: 年の見出しが「年・期」で、四半期の行は「平成９年１～３月平均」
_CSV_OLD = (
    _HEADER.replace("年・期平均", "年・期")
    + """
完全失業率／平成９年平均,1997,,4.1,3.9,4.5,3.8,3.6,4.2,3.4,3.4,3.4
完全失業率／平成９年１～３月平均,1997,01～03,3.9,3.5,4.6,3.7,3.5,4.3,3.4,3.4,3.4
"""
)

# 2011年の表: 全国に「岩手県、宮城県及び福島県を除く」列が並び、全国の値は「…」
_CSV_2011 = (
    "年・期平均,西暦(年),四半期,"
    "東京都／男女計（％、ポイント）,東京都／男（％、ポイント）,東京都／女（％、ポイント）,"
    "南関東／男女計（％、ポイント）,南関東／男（％、ポイント）,南関東／女（％、ポイント）,"
    "全国／男女計（岩手県、宮城県及び福島県を除く）（％、ポイント）,全国／男女計（％、ポイント）,"
    "全国／男（岩手県、宮城県及び福島県を除く）（％、ポイント）,全国／男（％、ポイント）,"
    "全国／女（岩手県、宮城県及び福島県を除く）（％、ポイント）,全国／女（％、ポイント）\n"
    "完全失業率／平成23年４～６月,2011,04～06,4.9,5,4.8,4.8,4.7,5,4.7,…,4.8,…,4.5,…\n"
)


def test_parse_keeps_quarter_rows_only():
    records = _parse(_CSV, 2025, 4)

    # 四半期の2行 × 3地域 × 3区分。年の行・対前年同期増減数・表末尾の行は落ちる
    assert len(records) == 18
    assert {(r["year"], r["quarter"]) for r in records} == {("2019", "2"), ("2025", "4")}
    assert {(r["report_year"], r["report_quarter"]) for r in records} == {("2025", "4")}


def test_parse_maps_columns_to_area_and_sex():
    records = _parse(_CSV, 2025, 4)
    by_key = {
        (r["year"], r["quarter"], r["area"], r["sex"]): r["value"] for r in records
    }

    assert by_key[("2025", "4", "東京都", "女")] == "2.2"
    assert by_key[("2025", "4", "南関東", "男女計")] == "2.5"
    assert by_key[("2019", "2", "全国", "男")] == "2.5"


def test_parse_old_layout_reads_quarter_labelled_as_average():
    records = _parse(_CSV_OLD, 2003, 3)

    assert {(r["year"], r["quarter"]) for r in records} == {("1997", "1")}
    assert len(records) == 9


def test_parse_skips_columns_excluding_disaster_prefectures():
    records = _parse(_CSV_2011, 2011, 2)
    national = {r["sex"]: r["value"] for r in records if r["area"] == "全国"}

    assert len(records) == 9
    assert national == {"男女計": "…", "男": "…", "女": "…"}


def test_parse_rejects_unexpected_header():
    with pytest.raises(ValueError):
        _parse("年・期平均,西暦(年),四半期,東京都／男女計(％、ポイント）\n", 2025, 4)


def test_parse_rejects_mismatched_western_year():
    with pytest.raises(ValueError):
        _parse(_CSV.replace("令和７年10～12月,2025", "令和７年10～12月,2024"), 2025, 4)


@pytest.mark.parametrize(
    ("label", "expected"),
    [
        ("完全失業率／平成９年１～３月平均", (1997, 1)),
        ("完全失業率／平成31年・令和元年４～６月", (2019, 2)),
        ("完全失業率／令和２年(2020年)７～９月", (2020, 3)),
        ("完全失業率／令和７年10～12月", (2025, 4)),
        ("完全失業率／令和７年", None),
        ("完全失業率／平成９年平均", None),
    ],
)
def test_year_quarter_from_label(label, expected):
    assert _year_quarter(label) == expected
