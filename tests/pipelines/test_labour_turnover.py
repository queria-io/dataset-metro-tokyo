"""毎月勤労統計調査の年報 第12表（産業別労働異動率）を産業ごとの行に分ける処理のテスト。"""

import csv

import pytest

from pipelines.labour_earnings import _table_name
from pipelines.labour_turnover import _parse

_HEADER = (
    "事業所規模,和暦年,西暦年,年平均・月,"
    "調査産業計／入職率(％),調査産業計／離職率(％),"
    "鉱業，採石業，砂利採取業／入職率(％),鉱業，採石業，砂利採取業／離職率(％),"
    "サービス業（他に分類されないもの）／入職率(％),サービス業（他に分類されないもの）／離職率(％)"
)
_CSV = (
    _HEADER
    + """
５人以上,令和６,2024,年平均,2.11,2.01,2.07,2.28,2.49,2.49
５人以上,令和７,2025,年平均,2.1,1.98,2.42,2.18,2.62,2.68
５人以上,令和７,2025,4月,6.22,4.06,×,－,5.34,4.26
,,,,,,,,,
東京都の賃金、労働時間及び雇用の動き（毎月勤労統計調査）令和７年年報,,,,,,,,,
第12－１表　産業別労働異動率（事業所規模５人以上）,,,,,,,,,
"""
)


def test_parse_keeps_report_year_rows_only():
    records = _parse(_CSV, 2025)

    # 過去年の年平均・末尾の空行・表題の行は落ち、2行 × 3産業が残る
    assert len(records) == 6
    assert {r["year"] for r in records} == {"2025"}
    assert {r["period"] for r in records} == {"年平均", "4月"}
    assert {r["establishment_size"] for r in records} == {"5人以上"}


def test_parse_splits_industry_columns_with_codes():
    records = _parse(_CSV, 2025)

    assert [r["industry"] for r in records[:3]] == [
        "TL 調査産業計",
        "C 鉱業，採石業，砂利採取業",
        "R サービス業（他に分類されないもの）",
    ]
    service = records[2]
    assert service["hiring_rate"] == "2.62"
    assert service["separation_rate"] == "2.68"


def test_parse_keeps_suppressed_values_raw():
    mining_april = next(
        r
        for r in _parse(_CSV, 2025)
        if r["period"] == "4月" and r["industry"].startswith("C ")
    )
    assert mining_april["hiring_rate"] == "×"
    assert mining_april["separation_rate"] == "－"


def test_parse_rejects_unknown_industry():
    text = "事業所規模,和暦年,西暦年,年平均・月,農業／入職率(％),農業／離職率(％)\n"
    with pytest.raises(ValueError, match="産業符号"):
        _parse(text, 2025)


def test_parse_rejects_unpaired_columns():
    text = "事業所規模,和暦年,西暦年,年平均・月,建設業／入職率(％),製造業／離職率(％)\n"
    with pytest.raises(ValueError, match="産業が違います"):
        _parse(text, 2025)


def test_parse_rejects_unknown_header():
    with pytest.raises(ValueError, match="ヘッダー"):
        _parse("事業所規模,産業,和暦年\n", 2025)


def test_table_name_reads_title_row():
    rows = list(csv.reader(_CSV.splitlines()))
    assert _table_name(rows) == "第12-1表"
