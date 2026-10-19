"""毎月勤労統計調査の年報 CSV（第6表）から公表年の行を取り出す処理のテスト。"""

from pipelines.labour_earnings import _parse
from pipelines.labour_hours import _HEADER, _VALUE_KEYS

_CSV = (
    ",".join(_HEADER)
    + """
５人以上,TL 調査産業計,令和６,2024,年平均,17.6,18.3,16.7,140.1,152.4,124.9,128.2,137.6,116.6,11.9,14.8,8.3
５人以上,TL 調査産業計,令和7,2025,年平均,17.5,18.2,16.6,139.6,151.8,124.6,127.9,137.2,116.4,11.7,14.6,8.2
30人以上,"C 鉱業,採石業,砂利採取業",令和7,2025,1月,ｘ,ｘ,ｘ,ｘ,ｘ,ｘ,ｘ,ｘ,ｘ,ｘ,ｘ,ｘ
,,,,,,,,,,,,,,,,
第６－１表　産業、性別常用労働者の１人平均月間出勤日数及び実労働時間　（事業所規模５人以上）,,,,,,,,,,,,,,,,
"""
)


def test_parse_hours_table():
    records = _parse(_CSV, 2025, _HEADER, _VALUE_KEYS)

    assert len(records) == 2
    assert {r["establishment_size"] for r in records} == {"5人以上", "30人以上"}
    total = next(r for r in records if r["period"] == "年平均")
    assert total["days_worked"] == "17.5"
    assert total["overtime_hours_female"] == "8.2"
    mining = next(r for r in records if r["industry"].startswith("C "))
    assert mining["total_hours"] == "ｘ"
