"""外国人人口の時系列 CSV を縦持ちに直す処理のテスト。"""

import pytest

from pipelines.foreign_population import _parse, _to_western_year

_CSV = """﻿国・地域,地域階層,地域コード,国・地域(人),昭和54年,昭和64年,平成2年,平成31年,令和2年
総数,0,13000,総数,110862,203677,211067,551683,577329
総数,4,13101,千代田区,3188,1858,1609,2996,"3,228"
台湾（平成29年から）,4,13101,千代田区,,,,240,251
,,,,,,,,
外国人人口　,,,,,,,,
注１）平成24年７月に外国人登録制度が廃止されたため、,,,,,,,,
地域階層（0:総数　1:区部・市部・町村部　2:郡部・島部　3:支庁　4:区市町村）,,,,,,,,
"""


@pytest.mark.parametrize(
    ("label", "year"),
    [
        ("昭和54年", 1979),
        ("昭和64年", 1989),
        ("平成2年", 1990),
        ("平成元年", 1989),
        ("平成31年", 2019),
        ("令和2年", 2020),
        ("令和8年", 2026),
    ],
)
def test_to_western_year(label, year):
    assert _to_western_year(label) == year


def test_parse_skips_notes_and_blank_years():
    records = _parse(_CSV)

    # 総数2地域 × 5年 + 台湾は値のある2年だけ。注記行は落ちる
    assert len(records) == 12
    assert {r["area_code"] for r in records} == {"13000", "13101"}
    taiwan = [r for r in records if r["nationality"] == "台湾（平成29年から）"]
    assert [r["year"] for r in taiwan] == ["2019", "2020"]


def test_parse_keeps_raw_value_and_label():
    records = _parse(_CSV)
    chiyoda_2020 = next(
        r
        for r in records
        if r["area_code"] == "13101"
        and r["nationality"] == "総数"
        and r["year"] == "2020"
    )
    assert chiyoda_2020 == {
        "year": "2020",
        "year_label": "令和2年",
        "area_level": "4",
        "area_code": "13101",
        "area_name": "千代田区",
        "nationality": "総数",
        "population": "3,228",
    }


def test_parse_rejects_unknown_header():
    with pytest.raises(ValueError):
        _parse("地域コード,地域,人口\n13000,東京都,1\n")
