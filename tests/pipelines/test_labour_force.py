"""東京の労働力 年平均の第1表から区分 × 男女の行を取り出す処理のテスト。"""

import csv

import pytest

from pipelines.labour_force import _annual_pages, _parse, _table_name

_HEADER = (
    "区分,"
    "男女計／実数（千人、％）,男女計／前年（千人、％）,男女計／対前年／増減数（千人、ポイント）,男女計／対前年／増減率（％）,"
    "男／実数（千人、％）,男／前年（千人、％）,男／対前年／増減数（千人、ポイント）,男／対前年／増減率（％）,"
    "女／実数（千人、％）,女／前年（千人、％）,女／対前年／増減数（千人、ポイント）,女／対前年／増減率（％）"
)

_CSV = (
    _HEADER
    + """
15歳以上人口,12749,12645,104,0.8,6227,6176,51,0.8,6522,6469,53,0.8
〔就業状態〕／労働力人口／完全失業者数,214,224,-10,-4.5,127,126,1,0.8,88,98,-10,-10.2
〔完全失業率（年齢階級別）(%)〕／総数,2.4,2.6,-0.2,…,2.7,2.7,0,…,2.2,2.5,-0.3,…
,,,,,,,,,,,,
東京の労働力統計データ（令和７年平均）,,,,,,,,,,,,
第１表　就業状態別15歳以上人口、産業別就業者数及び完全失業者数,,,,,,,,,,,,
令和７年(2025年)平均,,,,,,,,,,,,
"""
)


def test_parse_splits_sexes_and_drops_trailer():
    records = _parse(_CSV, 2025)

    # 3区分 × 男女計・男・女。末尾の空行・表題・注記は落ちる
    assert len(records) == 9
    assert [r["sex"] for r in records[:3]] == ["男女計", "男", "女"]
    assert {r["year"] for r in records} == {"2025"}


def test_parse_maps_value_columns_per_sex():
    female = _parse(_CSV, 2025)[5]

    assert female["item"] == "〔就業状態〕／労働力人口／完全失業者数"
    assert female["sex"] == "女"
    assert female["value"] == "88"
    assert female["previous_year_value"] == "98"
    assert female["change"] == "-10"
    assert female["change_rate"] == "-10.2"


def test_parse_keeps_not_applicable_raw():
    rate = _parse(_CSV, 2025)[6]
    assert rate["change_rate"] == "…"


def test_parse_accepts_older_header_wording():
    # 2004〜2006年の表は増減率の見出しが「比（％）」
    old = _CSV.replace("対前年／増減率（％）", "対前年／比（％）")
    assert len(_parse(old, 2006)) == 9


def test_parse_rejects_unknown_header():
    with pytest.raises(ValueError, match="ヘッダー"):
        _parse("男女・年,西暦(年),15歳以上人口（千人）\n", 2003)


def test_table_name_reads_title_row():
    rows = list(csv.reader(_CSV.splitlines()))
    assert _table_name(rows) == "第1表"


def test_annual_pages_skip_2003_and_quarterly_pages():
    html = """
    <a href="/roudou/2025/rd25qd1000.htm">令和7年</a>
    <a href="/roudou/2003/rd03qd1000.htm">平成15年</a>
    <a href="/roudou/2004/rd04qd1000.htm">平成16年</a>
    <a href="/roudou/2025/rd25ed1000.htm">1～3月平均</a>
    """
    pages = _annual_pages(html)
    assert [year for year, _ in pages] == [2004, 2025]
    assert pages[1][1] == "https://www.toukei.metro.tokyo.lg.jp/roudou/2025/rd25qd1000.htm"
