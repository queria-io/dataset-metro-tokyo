"""毎月勤労統計調査の年報 CSV から公表年の行を取り出す処理のテスト。"""

import csv

import pytest

from pipelines.labour_earnings import _parse, _report_pages, _table_name

_HEADER = (
    "事業所規模,産業,和暦年,西暦年,年平均・月,現金給与総額／計(円),現金給与総額／男(円),"
    "現金給与総額／女(円),きまって支給する給与／計(円),きまって支給する給与／男(円),"
    "きまって支給する給与／女(円),所定内給与(円),所定外給与(円),特別に支払われた給与／計(円),"
    "特別に支払われた給与／男(円),特別に支払われた給与／女(円)"
)

_CSV = f"""﻿{_HEADER}
５人以上,TL 調査産業計,令和６,2024,年平均,448243,547692,329257,354305,426389,268061,329304,25001,93938,121303,61196
５人以上,TL 調査産業計,令和7,2025,年平均,459078,560986,338202,362509,435599,275815,337657,24852,96569,125387,62387
５人以上,TL 調査産業計,令和7,2025,1月,380000,460000,290000,360000,430000,270000,335000,25000,20000,30000,20000
５人以上,"C 鉱業,採石業,砂利採取業",令和7,2025,1月,×,×,×,×,×,×,×,×,×,×,×
,,,,,,,,,,,,,,,
東京都の賃金、労働時間及び雇用の動き（毎月勤労統計調査）令和７年年報,,,,,,,,,,,,,,,
第１－１表　産業、性別常用労働者の１人平均月間現金給与額　（事業所規模５人以上）,,,,,,,,,,,,,,,
"""


def test_parse_keeps_only_report_year():
    records = _parse(_CSV.lstrip("﻿"), 2025)

    # 2024年の年平均と末尾の表題・空行は落ちる
    assert len(records) == 3
    assert {r["year"] for r in records} == {"2025"}
    assert {r["period"] for r in records} == {"年平均", "1月"}


def test_parse_normalizes_size_and_keeps_raw_values():
    records = _parse(_CSV.lstrip("﻿"), 2025)

    assert {r["establishment_size"] for r in records} == {"5人以上"}
    mining = next(r for r in records if r["industry"].startswith("C "))
    assert mining["cash_earnings"] == "×"
    total = next(r for r in records if r["period"] == "年平均")
    assert total["cash_earnings"] == "459078"
    assert total["special_earnings_female"] == "62387"


def test_parse_rejects_unknown_header():
    with pytest.raises(ValueError, match="ヘッダー"):
        _parse("事業所規模,産業,和暦年\n", 2025)


def test_table_name_reads_title_row():
    rows = list(csv.reader(_CSV.splitlines()))
    assert _table_name(rows) == "第1-1表"


def test_report_pages_resolves_annual_links():
    html = """
    <a href="/maikin/2025/mk25q30000.htm">年報</a>
    <a href="/maikin/2026/mk267tuki.htm">7月分</a>
    <a href="/maikin/2013/mk13q1nenp.htm">年報</a>
    """
    assert _report_pages(html) == [
        (2013, "https://www.toukei.metro.tokyo.lg.jp/maikin/2013/mk13q1nenp.htm"),
        (2025, "https://www.toukei.metro.tokyo.lg.jp/maikin/2025/mk25q30000.htm"),
    ]
