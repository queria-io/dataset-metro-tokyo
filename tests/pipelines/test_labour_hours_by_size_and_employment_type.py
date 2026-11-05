"""毎月勤労統計調査の年報 CSV（第9表）から公表年の行を取り出す処理のテスト。"""

import csv

from pipelines.labour_earnings import _parse, _table_name
from pipelines.labour_hours_by_employment_type import _VALUE_KEYS
from pipelines.labour_hours_by_size_and_employment_type import _HEADER

_CSV = (
    ",".join(_HEADER)
    + """
５～29人,令和６,2024,年平均,19.5,162.5,151.4,11.1,11.6,67.5,65.7,1.8
５～29人,令和７,2025,年平均,19.4,161.8,150.9,10.9,11.5,67.1,65.3,1.8
500人以上,令和７,2025,12月,18.1,153,137,16,12.3,78.9,75.8,3.1
,,,,,,,,,,,
東京都の賃金、労働時間及び雇用の動き（毎月勤労統計調査）令和７年年報,,,,,,,,,,,
第９表　規模、就業形態別常用労働者の１人平均月間出勤日数及び実労働時間（調査産業計）,,,,,,,,,,,
"""
)


def test_parse_size_table_by_employment_type():
    records = _parse(_CSV, 2025, _HEADER, _VALUE_KEYS)

    assert len(records) == 2
    assert {r["establishment_size"] for r in records} == {"5~29人", "500人以上"}
    assert all("industry" not in r for r in records)
    december = next(r for r in records if r["period"] == "12月")
    assert december["general_days_worked"] == "18.1"
    assert december["part_time_overtime_hours"] == "3.1"


def test_table_name_reads_table_9():
    rows = list(csv.reader(_CSV.splitlines()))
    assert _table_name(rows) == "第9表"
