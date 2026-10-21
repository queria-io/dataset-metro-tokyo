"""毎月勤労統計調査の年報 CSV（第2表）から公表年の行を取り出す処理のテスト。"""

from pipelines.labour_earnings import _parse
from pipelines.labour_earnings_by_employment_type import _HEADER, _VALUE_KEYS

_CSV = (
    ",".join(_HEADER)
    + """
５人以上,TL 調査産業計,令和２,2020,年平均,508680,401124,374479,26645,107556,107401,104399,100985,3414,3002
５人以上,TL 調査産業計,令和７,2025,年平均,565723,433106,401287,31819,132617,124609,120598,116150,4448,4011
30人以上,"C 鉱業，採石業，砂利採取業",令和７,2025,1月,×,×,×,×,×,－,－,－,－,－
,,,,,,,,,,,,,,
第２－１表　産業、就業形態別常用労働者の１人平均月間現金給与額　（事業所規模５人以上）,,,,,,,,,,,,,,
"""
)


def test_parse_employment_type_table():
    records = _parse(_CSV, 2025, _HEADER, _VALUE_KEYS)

    assert len(records) == 2
    assert {r["establishment_size"] for r in records} == {"5人以上", "30人以上"}
    total = next(r for r in records if r["industry"].startswith("TL "))
    assert total["general_cash_earnings"] == "565723"
    assert total["part_time_cash_earnings"] == "124609"
    assert total["part_time_special_earnings"] == "4011"
    mining = next(r for r in records if r["industry"].startswith("C "))
    assert mining["general_cash_earnings"] == "×"
    assert mining["part_time_cash_earnings"] == "－"
