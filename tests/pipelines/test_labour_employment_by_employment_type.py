"""毎月勤労統計調査の年報 CSV（第11表）から公表年の行を取り出す処理のテスト。"""

from pipelines.labour_earnings import _parse
from pipelines.labour_employment_by_employment_type import _HEADER, _VALUE_KEYS

_CSV = (
    ",".join(_HEADER)
    + """
５人以上,TL 調査産業計,令和２,2020,年平均,6055773,96546,94394,6058950,2020556,77816,91936,2005412
５人以上,TL 調査産業計,令和７,2025,1月,6522820,74804,84405,6512903,2079358,48231,57189,2070716
30人以上,"C 鉱業，採石業，砂利採取業",令和７,2025,1月,1690,27,24,1693,－,－,－,－
,,,,,,,,,,,,
第１１－１表　産業、就業形態別常用労働者数　（事業所規模５人以上）,,,,,,,,,,,,
"""
)


def test_parse_employment_type_employment_table():
    records = _parse(_CSV, 2025, _HEADER, _VALUE_KEYS)

    assert len(records) == 2
    assert {r["establishment_size"] for r in records} == {"5人以上", "30人以上"}
    total = next(r for r in records if r["industry"].startswith("TL "))
    assert total["general_employees_start"] == "6522820"
    assert total["part_time_employees_removed"] == "57189"
    assert total["part_time_employees"] == "2070716"
    mining = next(r for r in records if r["industry"].startswith("C "))
    assert mining["general_employees"] == "1693"
    assert mining["part_time_employees_start"] == "－"
