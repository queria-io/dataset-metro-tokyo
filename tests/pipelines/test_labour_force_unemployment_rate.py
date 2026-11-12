"""東京の労働力 年平均の参考表から年 × 地域 × 男女の行を取り出す処理のテスト。"""

import csv

import pytest

from pipelines.labour_force_unemployment_rate import (
    _is_reference_table,
    _parse,
    _year,
)

_AREAS = "東京都", "南関東", "全国"
_SEXES = "男女計", "男", "女"
_HEADER = "年平均,西暦(年)," + ",".join(
    f"{area}／{sex}(％、ポイント）" for area in _AREAS for sex in _SEXES
)

_CSV = (
    _HEADER
    + """
実数／平成31年・令和元年,2019,2.3,2.5,2.2,2.3,2.4,2.1,2.4,2.5,2.2
実数／令和７年,2025,2.4,2.7,2.2,2.5,2.7,2.3,2.5,2.7,2.3
対前年増減数／令和７年,2025,-0.2,0,-0.3,-0.2,0,-0.3,0,0,-0.1
,,,,,,,,,,
東京の労働力統計データ（令和７年平均）,,,,,,,,,,
参考表　東京都、南関東及び全国の完全失業率,,,,,,,,,,
注）南関東：埼玉県、千葉県、東京都、神奈川県,,,,,,,,,,
"""
)

# 2011年の表: 全国に「岩手県、宮城県及び福島県を除く」列が並び、全国の値は「…」
_CSV_2011 = """年,西暦(年),東京都／男女計（％、ポイント）,東京都／男（％、ポイント）,東京都／女（％、ポイント）,南関東／男女計（％、ポイント）,南関東／男（％、ポイント）,南関東／女（％、ポイント）,全国／男女計（岩手県、宮城県及び福島県を除く）（％、ポイント）,全国／男女計（％、ポイント）,全国／男（岩手県、宮城県及び福島県を除く）（％、ポイント）,全国／男（％、ポイント）,全国／女（岩手県、宮城県及び福島県を除く）（％、ポイント）,全国／女（％、ポイント）
実数／平成23年平均,2011,4.8,4.9,4.6,4.6,4.6,4.5,4.5,…,4.7,…,4.2,…
"""

# 2020〜2022年の表: 西暦の列が無い
_CSV_NO_WESTERN_YEAR = "年," + ",".join(
    f"{area}／{sex}(％、ポイント）" for area in _AREAS for sex in _SEXES
) + "\n実数／令和２年平均,3.1,3.3,2.8,3,3.2,2.7,2.8,3,2.5\n"


def test_parse_keeps_actual_rows_only():
    records = _parse(_CSV, 2025)

    # 実数の2年 × 3地域 × 3区分。対前年増減数と表末尾の行は落ちる
    assert len(records) == 18
    assert {r["year"] for r in records} == {"2019", "2025"}
    assert {r["report_year"] for r in records} == {"2025"}


def test_parse_maps_columns_to_area_and_sex():
    records = _parse(_CSV, 2025)
    by_key = {(r["year"], r["area"], r["sex"]): r["value"] for r in records}

    assert by_key[("2025", "東京都", "女")] == "2.2"
    assert by_key[("2025", "南関東", "男女計")] == "2.5"
    assert by_key[("2019", "全国", "男")] == "2.5"


def test_parse_skips_columns_excluding_disaster_prefectures():
    records = _parse(_CSV_2011, 2011)
    national = {r["sex"]: r["value"] for r in records if r["area"] == "全国"}

    assert len(records) == 9
    assert national == {"男女計": "…", "男": "…", "女": "…"}


def test_parse_reads_year_from_era_when_western_year_is_missing():
    records = _parse(_CSV_NO_WESTERN_YEAR, 2020)

    assert {r["year"] for r in records} == {"2020"}
    assert records[0]["value"] == "3.1"


def test_parse_rejects_unexpected_header():
    with pytest.raises(ValueError):
        _parse("年,西暦(年),東京都／男女計(％、ポイント）\n", 2025)


def test_parse_rejects_mismatched_western_year():
    with pytest.raises(ValueError):
        _parse(_CSV.replace("実数／令和７年,2025", "実数／令和７年,2024"), 2025)


@pytest.mark.parametrize(
    ("label", "year"),
    [
        ("実数／平成９年平均", 1997),
        ("実数／平成31年・令和元年平均", 2019),
        ("実数／令和元年", 2019),
        ("実数／令和７年", 2025),
    ],
)
def test_year_from_era(label, year):
    assert _year(label) == year


def test_is_reference_table():
    assert _is_reference_table(list(csv.reader(_CSV.splitlines())))
    assert not _is_reference_table([["第4表　主な産業別就業者数"]])
