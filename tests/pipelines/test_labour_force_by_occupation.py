"""東京の労働力 年平均の第6表から男女 × 年 × 職業の行を取り出す処理のテスト。"""

import csv

import pytest

from pipelines.labour_force_by_occupation import _is_occupation_table, _parse

_HEADER = (
    "専門的・技術的職業従事者（千人）,事務従事者（千人）,販売従事者（千人）,"
    "サービス職業従事者（千人）,生産工程従事者（千人）,運搬・清掃・包装等従事者（千人）,"
    "その他（左記以外のもの）（千人）"
)

_CSV = f"""男女・年平均,西暦(年),{_HEADER}
実数／男女計／令和７年,2025,2313,2459,1088,1001,464,427,868
実数／女／平成31年・令和元年,2019,812,1215,469,595,111,79,357
対前年増減数／男女計／令和７年,2025,102,102,4,12,-21,-15,-5
,,,,,,,,
東京の労働力統計データ（令和７年平均）,,,,,,,,
第 ６ 表　主な職業別就業者数,,,,,,,,
"""

# 2020〜2022年の表: 西暦の列が無い
_CSV_NO_WESTERN_YEAR = f"""男女・年,{_HEADER}
実数／男／令和２年平均,1310,914,642,351,330,357,509
"""


def test_parse_keeps_actual_rows_only():
    records = _parse(_CSV, 2025)

    # 実数の2行 × 7職業。対前年増減数と表末尾の行は落ちる
    assert len(records) == 14
    assert {(r["year"], r["sex"]) for r in records} == {
        ("2025", "男女計"),
        ("2019", "女"),
    }
    assert {r["report_year"] for r in records} == {"2025"}


def test_parse_maps_columns_to_occupations():
    records = _parse(_CSV, 2025)
    by_key = {(r["year"], r["occupation"]): r["value"] for r in records}

    assert by_key[("2025", "専門的・技術的職業従事者")] == "2313"
    assert by_key[("2019", "サービス職業従事者")] == "595"
    assert by_key[("2025", "その他(左記以外のもの)")] == "868"


def test_parse_without_western_year_column():
    records = _parse(_CSV_NO_WESTERN_YEAR, 2020)

    assert [(r["year"], r["sex"], r["value"]) for r in records][:2] == [
        ("2020", "男", "1310"),
        ("2020", "男", "914"),
    ]
    assert len(records) == 7


def test_parse_rejects_mismatched_western_year():
    text = _CSV.replace("令和７年,2025", "令和７年,2024", 1)

    with pytest.raises(ValueError, match="和暦と西暦"):
        _parse(text, 2025)


def test_parse_rejects_unknown_header():
    text = _CSV.replace("事務従事者（千人）", "事務従事者", 1)

    with pytest.raises(ValueError, match="ヘッダー"):
        _parse(text, 2025)


def test_is_occupation_table_reads_title_row():
    assert _is_occupation_table(list(csv.reader(_CSV.splitlines())))
    # 2011年までの表の 0600.csv は別の表
    other = "年平均\n第６表　企業の従業者規模別雇用者数\n"
    assert not _is_occupation_table(list(csv.reader(other.splitlines())))
