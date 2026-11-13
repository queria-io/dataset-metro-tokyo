"""東京の労働力 年平均の第2表から男女 × 年 × 区分の行を取り出す処理のテスト。"""

import csv

import pytest

from pipelines.labour_force_activity import _parse, _table_name

_CSV = """男女・年平均,西暦(年),15歳以上人口（千人）,15歳以上人口／労働力人口（千人）,15歳以上人口／労働力人口／就業者数／雇用者数／うち非正規の職員･従業員（千人）,完全失業率（％、ポイント）
実数／男女計／平成31年・令和元年,2019,12343,8254,2417,2.3
実数／男／令和７年,2025,6227,4778,834,2.7
対前年増減数／男／令和７年,2025,51,75,14,0
,,,,,
東京の労働力統計データ（令和７年平均）,,,,,
第２表　就業状態、活動状態別15歳以上人口,,,,,
"""

# 2020〜2022年の表: 西暦の列が無く、調べていない区分は「   －」
_CSV_NO_WESTERN_YEAR = """男女・年,15歳以上人口（千人）,15歳以上人口／労働力人口／就業者数／雇用者数／うち正規の職員・従業員（千人）,就業率（％、ポイント）
実数／女／平成24年平均,6007,   －,…
"""


def test_parse_keeps_actual_rows_only():
    records = _parse(_CSV, 2025)

    # 実数の2行 × 4区分。対前年増減数と表末尾の行は落ちる
    assert len(records) == 8
    assert {(r["year"], r["sex"]) for r in records} == {("2019", "男女計"), ("2025", "男")}
    assert {r["report_year"] for r in records} == {"2025"}


def test_parse_maps_columns_to_items():
    records = _parse(_CSV, 2025)
    by_key = {(r["year"], r["item"]): r["value"] for r in records}

    assert by_key[("2019", "15歳以上人口（千人）")] == "12343"
    assert by_key[("2025", "15歳以上人口／労働力人口／就業者数／雇用者数／うち非正規の職員･従業員（千人）")] == "834"
    assert by_key[("2025", "完全失業率（％、ポイント）")] == "2.7"


def test_parse_without_western_year_column():
    records = _parse(_CSV_NO_WESTERN_YEAR, 2022)

    assert [(r["year"], r["sex"], r["value"]) for r in records] == [
        ("2012", "女", "6007"),
        ("2012", "女", "－"),
        ("2012", "女", "…"),
    ]


def test_parse_rejects_mismatched_western_year():
    text = _CSV.replace("令和７年,2025", "令和７年,2024", 1)

    with pytest.raises(ValueError, match="和暦と西暦"):
        _parse(text, 2025)


def test_parse_rejects_unknown_header():
    text = _CSV.replace("完全失業率（％、ポイント）", "完全失業率", 1)

    with pytest.raises(ValueError, match="ヘッダー"):
        _parse(text, 2025)


def test_table_name_reads_title_row():
    assert _table_name(list(csv.reader(_CSV.splitlines()))) == "第2表"
