"""東京の労働力 年平均の第3表から区分 × 年 × 年齢階級の行を取り出す処理のテスト。"""

import csv

import pytest

from pipelines.labour_force_by_age import _parse, _title_sex

_CSV = """区分・年平均,西暦(年),実数／総数（千人、％）,実数／15～24歳（千人、％）,対前年増減数／総数（千人、ポイント）,対前年増減数／15～24歳（千人、ポイント）,対前年増減率／総数（％）,対前年増減率／15～24歳（％）
15歳以上人口／平成31年・令和元年,2019,12343,1423,92,4,0.8,0.3
完全失業率／令和７年,2025,2.4,2.6,-0.2,-1,…,…
,,,,,,,
東京の労働力統計データ（令和７年平均）,,,,,,,
第３表　年齢階級別就業状態（男女計）,,,,,,,
"""

# 男の表は見出しの単位の前に「／」が入る。2020〜2022年の表は西暦の列が無い
_CSV_MALE_NO_WESTERN_YEAR = """区分・年,実数／総数／（千人、％）,実数／65歳以上／（千人、％）,対前年増減数／総数／（千人、ポイント）
就業率／平成24年平均,68.1,29.5,0.3
第３表　年齢階級別就業状態（男）,,,
"""


def test_parse_keeps_actual_columns_only():
    records = _parse(_CSV, 2025, "男女計")

    # 2行 × 実数の2列。対前年増減数・増減率の列と表末尾の行は落ちる
    assert [(r["year"], r["item"], r["age_group"], r["value"]) for r in records] == [
        ("2019", "15歳以上人口", "総数", "12343"),
        ("2019", "15歳以上人口", "15～24歳", "1423"),
        ("2025", "完全失業率", "総数", "2.4"),
        ("2025", "完全失業率", "15～24歳", "2.6"),
    ]
    assert {(r["report_year"], r["sex"]) for r in records} == {("2025", "男女計")}


def test_parse_without_western_year_column():
    records = _parse(_CSV_MALE_NO_WESTERN_YEAR, 2022, "男")

    assert [(r["year"], r["item"], r["age_group"], r["value"]) for r in records] == [
        ("2012", "就業率", "総数", "68.1"),
        ("2012", "就業率", "65歳以上", "29.5"),
    ]


def test_parse_rejects_mismatched_western_year():
    text = _CSV.replace("令和７年,2025", "令和７年,2024", 1)

    with pytest.raises(ValueError, match="和暦と西暦"):
        _parse(text, 2025, "男女計")


def test_parse_rejects_unknown_item():
    text = _CSV.replace("完全失業率／", "失業率／", 1)

    with pytest.raises(ValueError, match="区分"):
        _parse(text, 2025, "男女計")


def test_parse_rejects_unknown_header():
    text = _CSV.replace("実数／総数（千人、％）", "実数／総数", 1)

    with pytest.raises(ValueError, match="ヘッダー"):
        _parse(text, 2025, "男女計")


def test_title_sex_reads_title_row():
    assert _title_sex(list(csv.reader(_CSV.splitlines()))) == "男女計"
    assert _title_sex(list(csv.reader(_CSV_MALE_NO_WESTERN_YEAR.splitlines()))) == "男"


def test_title_sex_accepts_older_title():
    # 2004〜2008年の表は「年齢階層別」
    rows = [["第３表　年齢階層別就業状態（女）"]]

    assert _title_sex(rows) == "女"


def test_title_sex_rejects_other_table():
    assert _title_sex([["第２表　就業状態、活動状態別15歳以上人口"]]) is None
