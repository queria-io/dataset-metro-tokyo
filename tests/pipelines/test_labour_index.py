"""毎月勤労統計調査の年報 第13〜21表（規模、産業別の指数）を産業ごとの行に分ける処理のテスト。"""

import pytest

from pipelines.labour_index import _parse

_HEADER = (
    "事業所規模,和暦年,西暦年,年平均・月・前年比・前年同月比,"
    "調査産業計,鉱業，採石業，砂利採取業,サービス業（他に分類されないもの）"
)
_ROWS = """
５人以上,令和６,2024,年平均,109.5,123.1,109
５人以上,令和７,2025,年平均,112.2,128.6,112.1
５人以上,令和７,2025,8月,91.6,x,102.4
５人以上,令和６,2024,年平均（前年比（％））,2.4,8,2.1
５人以上,令和７,2025,年平均（前年比（％））,2.5,4.5,2.8
５人以上,令和７,2025,8月（前年同月比（％））,0.4,x,5.2
30人以上,令和７,2025,年平均,113,－,110
,,,,,,
第13表　規模、産業別名目賃金指数（現金給与総額）,,,,,,
（令和２年平均=100）,,,,,,
"""
_CSV = _HEADER + _ROWS


def test_parse_keeps_report_year_rows_only():
    records = _parse(_CSV, 2025)

    # 過去年の行・末尾の空行・注記の行は落ち、3期間 × 3産業が残る
    assert len(records) == 9
    assert {r["year"] for r in records} == {"2025"}
    assert {(r["establishment_size"], r["period"]) for r in records} == {
        ("5人以上", "年平均"),
        ("5人以上", "8月"),
        ("30人以上", "年平均"),
    }


def test_parse_merges_change_rows_into_index_rows():
    records = _parse(_CSV, 2025)
    total = {
        (r["establishment_size"], r["period"]): r
        for r in records
        if r["industry"] == "TL 調査産業計"
    }

    assert total[("5人以上", "年平均")]["index_value"] == "112.2"
    assert total[("5人以上", "年平均")]["change_rate"] == "2.5"
    assert total[("5人以上", "8月")]["change_rate"] == "0.4"
    # 前年比の行が無い期間は空文字
    assert total[("30人以上", "年平均")]["change_rate"] == ""


def test_parse_reads_index_type_base_year_and_industry_codes():
    records = _parse(_CSV, 2025)

    assert {r["index_type"] for r in records} == {"名目賃金指数（現金給与総額）"}
    assert {r["base_year"] for r in records} == {"2020"}
    assert [r["industry"] for r in records[:3]] == [
        "TL 調査産業計",
        "C 鉱業，採石業，砂利採取業",
        "R サービス業（他に分類されないもの）",
    ]


def test_parse_keeps_suppressed_values_raw():
    mining = next(
        r
        for r in _parse(_CSV, 2025)
        if r["period"] == "8月" and r["industry"].startswith("C ")
    )
    assert mining["index_value"] == "x"
    assert mining["change_rate"] == "x"


def test_parse_reads_heisei_base_year():
    text = _CSV.replace("（令和２年平均=100）", "（平成２２年平均＝１００）")
    assert {r["base_year"] for r in _parse(text, 2025)} == {"2010"}


def test_parse_rejects_title_mismatch():
    text = _CSV.replace(
        "第13表　規模、産業別名目賃金指数（現金給与総額）", "第13表　常用雇用指数"
    )
    with pytest.raises(ValueError, match="表題"):
        _parse(text, 2025)


def test_parse_rejects_missing_base_year():
    text = _CSV.replace("（令和２年平均=100）", "")
    with pytest.raises(ValueError, match="基準年"):
        _parse(text, 2025)


def test_parse_rejects_unknown_industry():
    text = _CSV.replace("調査産業計,", "農業,", 1)
    with pytest.raises(ValueError, match="産業符号"):
        _parse(text, 2025)
