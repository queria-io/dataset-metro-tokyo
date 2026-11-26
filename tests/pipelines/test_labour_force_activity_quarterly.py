"""東京の労働力 四半期平均の第2表から男女 × 四半期 × 区分の行を取り出す処理のテスト。"""

import pytest

from pipelines.labour_force_activity_quarterly import (
    _csv_url,
    _parse,
    _quarter_of,
)

# 2023年4〜6月期以降の表: 年平均の行と四半期の行が並び、対前年・対前年同期増減数が続く
_CSV = """年・期平均,西暦(年),四半期,男女計／１５歳以上人口（千人）,男女計／労働力人口比率（％、ポイント）,男計／１５歳以上人口（千人）,女計／１５歳以上人口（千人）
実数／令和６年,2024,,12645,68.6,6176,6469
実数／令和６年４～６月,2024,04～06,12647,68.7,6176,6471
実数／令和６年10～12月,2024,10～12,12686,68.6,6197,6489
対前年・対前年同期増減数／令和６年４～６月,2024,04～06,74,-0.1,38,36
,,,,,,
東京の労働力統計データ（令和７年４～６月期平均）,,,,,,
第２表　主な就業状態、男女別15歳以上人口　,,,,,,
"""

# 2020年1〜3月期〜2023年1〜3月期の表: 西暦と四半期の列が無く、年は和暦のラベルだけ
_CSV_NO_WESTERN_YEAR = """年・期,男女計／１５歳以上人口（千人）,男／労働力人口比率（％、ポイント）
実数／平成31年・令和元年10～12月平均,12343,75.9
実数／令和４年(2022年)１～３月,12457,76.2
"""

# 2003年7〜9月期の表: 年平均の行は「平成９年平均」、四半期の行は「平成15年７～９月平均」
_CSV_OLD = """年・期,西暦(年),四半期,男女計／労働力人口／総数（千人）
実数／平成９年平均,1997,,10311
実数／平成９年１～３月平均,1997,01～03,10300
"""


def test_quarter_of_reads_months():
    assert _quarter_of("実数／令和６年４～６月") == 2
    assert _quarter_of("実数／令和６年10～12月") == 4
    assert _quarter_of("実数／平成15年７～９月平均") == 3
    assert _quarter_of("実数／令和４年(2022年)１～３月") == 1


def test_quarter_of_returns_none_for_annual_rows():
    assert _quarter_of("実数／令和６年") is None
    assert _quarter_of("実数／平成９年平均") is None


def test_quarter_of_rejects_other_month_ranges():
    with pytest.raises(ValueError, match="四半期の月"):
        _quarter_of("実数／令和６年５～７月")


def test_parse_keeps_quarterly_actual_rows_only():
    records = _parse(_CSV, 2025, 2)

    # 四半期の実数の2行 × 4列。年平均の行・対前年同期増減数・表末尾の行は落ちる
    assert len(records) == 8
    assert {(r["year"], r["quarter"]) for r in records} == {("2024", "2"), ("2024", "4")}
    assert {(r["report_year"], r["report_quarter"]) for r in records} == {("2025", "2")}


def test_parse_maps_sex_and_item():
    records = _parse(_CSV, 2025, 2)
    by_key = {(r["quarter"], r["sex"], r["item"]): r["value"] for r in records}

    assert by_key[("2", "男女計", "１５歳以上人口（千人）")] == "12647"
    assert by_key[("2", "男女計", "労働力人口比率（％、ポイント）")] == "68.7"
    # 「男計」「女計」は「男」「女」にそろえる
    assert by_key[("4", "男", "１５歳以上人口（千人）")] == "6197"
    assert by_key[("4", "女", "１５歳以上人口（千人）")] == "6489"


def test_parse_without_western_year_column():
    records = _parse(_CSV_NO_WESTERN_YEAR, 2023, 1)

    assert [(r["year"], r["quarter"], r["sex"], r["value"]) for r in records] == [
        ("2019", "4", "男女計", "12343"),
        ("2019", "4", "男", "75.9"),
        ("2022", "1", "男女計", "12457"),
        ("2022", "1", "男", "76.2"),
    ]


def test_parse_old_table_with_annual_rows_before_2003():
    records = _parse(_CSV_OLD, 2003, 3)

    assert [(r["year"], r["quarter"], r["item"], r["value"]) for r in records] == [
        ("1997", "1", "労働力人口／総数（千人）", "10300"),
    ]


def test_parse_rejects_mismatched_western_year():
    text = _CSV.replace("令和６年４～６月,2024", "令和６年４～６月,2023", 1)

    with pytest.raises(ValueError, match="西暦・四半期"):
        _parse(text, 2025, 2)


def test_parse_rejects_mismatched_quarter_column():
    text = _CSV.replace("令和６年４～６月,2024,04～06", "令和６年４～６月,2024,07～09", 1)

    with pytest.raises(ValueError, match="西暦・四半期"):
        _parse(text, 2025, 2)


def test_parse_rejects_mismatched_parenthesized_year():
    text = _CSV_NO_WESTERN_YEAR.replace("(2022年)", "(2021年)")

    with pytest.raises(ValueError, match="和暦と西暦"):
        _parse(text, 2023, 1)


def test_parse_rejects_unknown_header():
    text = _CSV.replace("男女計／労働力人口比率（％、ポイント）", "男女計／労働力人口比率", 1)

    with pytest.raises(ValueError, match="ヘッダー"):
        _parse(text, 2025, 2)


def test_parse_rejects_unknown_sex():
    text = _CSV.replace("男計／", "外国人／", 1)

    with pytest.raises(ValueError, match="ヘッダー"):
        _parse(text, 2025, 2)


def test_parse_rejects_row_with_wrong_column_count():
    text = _CSV.replace("12647,68.7,6176,6471", "12647,68.7,6176", 1)

    with pytest.raises(ValueError, match="列の数"):
        _parse(text, 2025, 2)


def test_csv_url_dedupes_repeated_links():
    # 2008年7〜9月期のページは同じリンクを2回載せる
    html = (
        '<a href="/roudou/2008/rd08gv0100.csv">CSV</a>'
        '<a href="/roudou/2008/rd08gv0200.csv">CSV</a>'
        '<a href="/roudou/2008/rd08gv0200.csv">CSV</a>'
    )

    assert (
        _csv_url("https://www.toukei.metro.tokyo.lg.jp/roudou/2008/rd08gd1000.htm", html)
        == "https://www.toukei.metro.tokyo.lg.jp/roudou/2008/rd08gv0200.csv"
    )


def test_csv_url_rejects_missing_link():
    with pytest.raises(RuntimeError, match="1つに決められません"):
        _csv_url("https://example.com/p.htm", '<a href="/a/rd08gv0100.csv">CSV</a>')
