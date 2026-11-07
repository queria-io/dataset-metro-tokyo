"""毎月勤労統計調査の年報 第5表（夏・冬季賞与）から産業ごとの行を取り出す処理のテスト。"""

import csv

import pytest

from pipelines.labour_bonus import _HEADER, _parse
from pipelines.labour_earnings import _table_name

_CSV = (
    ",".join(_HEADER)
    + """
30人以上,TL 調査産業計,761977,3.6,81.7,85.7,1.45,-0.01,720569,0,84,87.1,1.47,0
30人以上,"C 鉱業,採石業,砂利採取業",2409554,5.9,54.8,93.3,6.08,0.59,1864138,-1,100,100,1.26,-1.31
30人以上,E11 繊維工業,×,×,×,×,×,×,×,×,×,×,×,×
30人以上,PSＰ一括分,321327,-6.2,81.4,80.3,1.15,-0.07,333699,-2,85.4,85.7,1.26,-0.08
,,,,,,,,,,,,,
東京都の賃金、労働時間及び雇用の動き（毎月勤労統計調査）令和７年年報,,,,,,,,,,,,,
第５表　夏・冬季賞与の産業別支給状況（事業所規模30人以上）,,,,,,,,,,,,,
"""
)


def test_parse_adds_report_year_and_drops_trailer():
    records = _parse(_CSV, 2025)

    # 末尾の空行と表題の行は落ちる
    assert len(records) == 4
    assert {r["year"] for r in records} == {"2025"}
    assert {r["report_year"] for r in records} == {"2025"}
    assert {r["establishment_size"] for r in records} == {"30人以上"}


def test_parse_maps_summer_and_winter_columns():
    total = _parse(_CSV, 2025)[0]

    assert total["industry"] == "TL 調査産業計"
    assert total["summer_bonus"] == "761977"
    assert total["summer_bonus_months_change"] == "-0.01"
    assert total["winter_bonus"] == "720569"
    assert total["winter_receiving_employee_ratio"] == "87.1"
    assert total["winter_bonus_months"] == "1.47"


def test_parse_keeps_suppressed_values_raw():
    textile = next(r for r in _parse(_CSV, 2025) if r["industry"].startswith("E11"))
    assert textile["summer_bonus"] == "×"


def test_parse_rejects_unknown_header():
    with pytest.raises(ValueError, match="ヘッダー"):
        _parse("事業所規模,産業,和暦年\n", 2025)


def test_table_name_reads_title_row():
    rows = list(csv.reader(_CSV.splitlines()))
    assert _table_name(rows) == "第5表"
