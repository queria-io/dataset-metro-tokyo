"""毎月勤労統計調査の年報 CSV（第7表）から公表年の行を取り出す処理のテスト。"""

from pipelines.labour_earnings import _parse
from pipelines.labour_hours_by_employment_type import _HEADER, _VALUE_KEYS

_CSV = (
    ",".join(_HEADER)
    + """
５人以上,TL 調査産業計,令和２,2020,年平均,18.7,155.1,142.2,12.9,12,72.5,69.9,2.6
５人以上,TL 調査産業計,令和７,2025,年平均,18.8,157.7,143.5,14.2,12.1,74.5,71.8,2.7
30人以上,"C 鉱業，採石業，砂利採取業",令和７,2025,1月,17.8,155.1,132.1,23,－,－,－,－
,,,,,,,,,,,,
第７－１表　産業、就業形態別常用労働者の１人平均月間出勤日数及び実労働時間　（事業所規模５人以上）,,,,,,,,,,,,
"""
)


def test_parse_employment_type_hours_table():
    records = _parse(_CSV, 2025, _HEADER, _VALUE_KEYS)

    assert len(records) == 2
    assert {r["establishment_size"] for r in records} == {"5人以上", "30人以上"}
    total = next(r for r in records if r["industry"].startswith("TL "))
    assert total["general_days_worked"] == "18.8"
    assert total["part_time_total_hours"] == "74.5"
    assert total["part_time_overtime_hours"] == "2.7"
    mining = next(r for r in records if r["industry"].startswith("C "))
    assert mining["general_total_hours"] == "155.1"
    assert mining["part_time_days_worked"] == "－"
