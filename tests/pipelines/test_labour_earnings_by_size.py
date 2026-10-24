"""毎月勤労統計調査の年報 CSV（第3表）から公表年の行を取り出す処理のテスト。"""

import csv

from pipelines.labour_earnings import _parse, _table_name
from pipelines.labour_earnings_by_size import _HEADER, _VALUE_KEYS

_CSV = (
    ",".join(_HEADER)
    + """
５～29人,令和６,2024,年平均,300000,380000,210000,256000,325000,185000,244000,12000,44000,55000,25000
５～29人,令和７,2025,年平均,307233,392563,214866,258961,327954,184317,246632,12329,48272,64609,30549
500人以上,令和７,2025,12月,1141064,1373380,824307,464370,542118,358362,426024,38346,676694,831262,465945
,,,,,,,,,,,,,,
東京都の賃金、労働時間及び雇用の動き（毎月勤労統計調査）令和７年年報,,,,,,,,,,,,,,
第３表　規模、性別常用労働者の１人平均月間現金給与額　（調査産業計）,,,,,,,,,,,,,,
"""
)


def test_parse_size_table_without_industry():
    records = _parse(_CSV, 2025, _HEADER, _VALUE_KEYS)

    assert len(records) == 2
    assert {r["establishment_size"] for r in records} == {"5~29人", "500人以上"}
    assert all("industry" not in r for r in records)
    december = next(r for r in records if r["period"] == "12月")
    assert december["cash_earnings"] == "1141064"
    assert december["special_earnings_female"] == "465945"


def test_table_name_reads_title_without_subnumber():
    rows = list(csv.reader(_CSV.splitlines()))
    assert _table_name(rows) == "第3表"
