"""毎月勤労統計調査の年報 CSV（第4表）から公表年の行を取り出す処理のテスト。"""

import csv

from pipelines.labour_earnings import _parse, _table_name
from pipelines.labour_earnings_by_employment_type import _VALUE_KEYS
from pipelines.labour_earnings_by_size_and_employment_type import _HEADER

_CSV = (
    ",".join(_HEADER)
    + """
５～29人,令和６,2024,年平均,430000,360000,340000,20000,70000,100000,98000,95000,3000,2000
５～29人,令和７,2025,年平均,431000,361000,341000,20000,70000,101000,99000,96000,3000,2000
500人以上,令和７,2025,12月,1275072,507918,465304,42614,767154,169279,148571,141177,7394,20708
,,,,,,,,,,,,,
東京都の賃金、労働時間及び雇用の動き（毎月勤労統計調査）令和７年年報,,,,,,,,,,,,,
第４表　規模、就業形態別常用労働者の１人平均月間現金給与額（調査産業計）,,,,,,,,,,,,,
"""
)


def test_parse_size_table_by_employment_type():
    records = _parse(_CSV, 2025, _HEADER, _VALUE_KEYS)

    assert len(records) == 2
    assert {r["establishment_size"] for r in records} == {"5~29人", "500人以上"}
    assert all("industry" not in r for r in records)
    december = next(r for r in records if r["period"] == "12月")
    assert december["general_cash_earnings"] == "1275072"
    assert december["part_time_special_earnings"] == "20708"


def test_table_name_reads_table_4():
    rows = list(csv.reader(_CSV.splitlines()))
    assert _table_name(rows) == "第4表"
