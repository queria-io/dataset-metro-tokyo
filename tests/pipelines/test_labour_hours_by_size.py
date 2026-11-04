"""毎月勤労統計調査の年報 CSV（第8表）から公表年の行を取り出す処理のテスト。"""

import csv

from pipelines.labour_earnings import _parse, _table_name
from pipelines.labour_hours import _VALUE_KEYS
from pipelines.labour_hours_by_size import _HEADER

_CSV = (
    ",".join(_HEADER)
    + """
５～29人,令和６,2024,年平均,16.4,17.6,15.1,124.0,140.1,106.9,117.0,130.3,102.9,7.0,9.8,4.0
５～29人,令和７,2025,年平均,16.2,17.4,14.8,122.3,139.2,104.5,115.7,129.8,100.8,6.6,9.4,3.7
500人以上,令和７,2025,12月,17.4,17.8,16.8,144.1,150.8,135,129.6,134,123.7,14.5,16.8,11.3
,,,,,,,,,,,,,,,
東京都の賃金、労働時間及び雇用の動き（毎月勤労統計調査）令和７年年報,,,,,,,,,,,,,,,
第８表　規模、性別常用労働者の１人平均月間出勤日数及び実労働時間（調査産業計）,,,,,,,,,,,,,,,
"""
)


def test_parse_size_table_without_industry():
    records = _parse(_CSV, 2025, _HEADER, _VALUE_KEYS)

    assert len(records) == 2
    assert {r["establishment_size"] for r in records} == {"5~29人", "500人以上"}
    assert all("industry" not in r for r in records)
    december = next(r for r in records if r["period"] == "12月")
    assert december["days_worked"] == "17.4"
    assert december["overtime_hours_female"] == "11.3"


def test_table_name_reads_table_8():
    rows = list(csv.reader(_CSV.splitlines()))
    assert _table_name(rows) == "第8表"
