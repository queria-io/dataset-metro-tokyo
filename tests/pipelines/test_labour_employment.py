"""毎月勤労統計調査の年報 CSV（第10表）から公表年の行を取り出す処理のテスト。"""

from pipelines.labour_earnings import _parse
from pipelines.labour_employment import _HEADER, _VALUE_KEYS

_CSV = (
    ",".join(_HEADER)
    + """
５人以上,TL 調査産業計,令和６,2024,年平均,8162036,4590321,3571715,175103,86542,88561,170255,84802,85453,8166884,4592061,3574823,25.5,14.6,39.5
５人以上,R サービス業（他に分類されないもの）,令和７,2025,1月,1096135,582673,513462,22003,9011,12992,28935,12499,16436,1089203,579185,510018,24.9,16.4,34.6
30人以上,"C 鉱業,採石業,砂利採取業",令和7,2025,1月,ｘ,ｘ,ｘ,ｘ,ｘ,ｘ,ｘ,ｘ,ｘ,ｘ,ｘ,ｘ,ｘ,ｘ,ｘ
,,,,,,,,,,,,,,,,,,,
第10－１表　産業、性別常用労働者数及びパートタイム労働者比率　（事業所規模５人以上）,,,,,,,,,,,,,,,,,,,
"""
)


def test_parse_employment_table():
    records = _parse(_CSV, 2025, _HEADER, _VALUE_KEYS)

    assert len(records) == 2
    assert {r["establishment_size"] for r in records} == {"5人以上", "30人以上"}
    service = next(r for r in records if r["industry"].startswith("R "))
    assert service["employees_start"] == "1096135"
    assert service["employees"] == "1089203"
    assert service["part_time_ratio_female"] == "34.6"
    mining = next(r for r in records if r["industry"].startswith("C "))
    assert mining["employees"] == "ｘ"
