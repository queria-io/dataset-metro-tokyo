"""東京の労働力 年平均の第8表から男女 × 年 × 雇用形態 × 年齢階級の行を取り出す処理のテスト。"""

import csv

import pytest

from pipelines.labour_force_by_employment_type import (
    _is_employment_type_table,
    _parse,
)

_AGES = "15～24歳,25～34歳,35～44歳,45～54歳,55～64歳,65歳以上"

# 2015〜2019年の表: 雇用形態が行にある
_CSV_TYPE_IN_ROW = f"""男女・年,西暦(年),総数(千人),{",".join(f"{a}(千人)" for a in _AGES.split(","))}
実数／男女計／正規／平成27年平均,2015,3916,233,1105,1152,907,414,105
実数／女／非正規／平成26年平均,2014,1441,165,246,351,321,233,125
対前年増減数／男女計／正規／平成27年平均,2015,96,15,16,18,23,28,-3
,,,,,,,,
東京の労働力統計データ（平成27年平均）,,,,,,,,
第８表 年齢階級別雇用形態別の役員を除く雇用者数,,,,,,,,
注）正規：正規の職員･従業員,,,,,,,,
"""

_WIDE_HEADER = ",".join(
    f"{t}／{a}（千人）" for t in ("正規", "非正規") for a in ["総数", *_AGES.split(",")]
)

# 2023年からの表: 雇用形態が列にある
_CSV_TYPE_IN_COLUMN = f"""男女・年平均,西暦(年),{_WIDE_HEADER}
実数／男女計／令和７年,2025,4956,308,1498,1178,1171,679,123,2428,416,288,347,483,495,399
対前年増減数／男女計／令和７年,2025,152,18,90,29,-12,16,13,40,8,-17,9,16,27,-2
,,,,,,,,,,,,,,,
第８表　年齢階級、雇用形態別の役員を除く雇用者数,,,,,,,,,,,,,,,
"""

# 2021〜2022年の表: 西暦の列が無い
_CSV_NO_WESTERN_YEAR = f"""男女・年,{_WIDE_HEADER}
実数／男／令和３年平均,2850,139,710,746,773,403,79,795,172,117,93,84,134,196
"""


def test_parse_type_in_row():
    records = _parse(_CSV_TYPE_IN_ROW, 2015)

    # 実数の2行 × 7年齢階級。対前年増減数と表末尾の行は落ちる
    assert len(records) == 14
    by_key = {
        (r["year"], r["sex"], r["employment_type"], r["age_group"]): r["value"]
        for r in records
    }
    assert by_key[("2015", "男女計", "正規", "総数")] == "3916"
    assert by_key[("2014", "女", "非正規", "65歳以上")] == "125"
    assert {r["report_year"] for r in records} == {"2015"}


def test_parse_type_in_column():
    records = _parse(_CSV_TYPE_IN_COLUMN, 2025)

    assert len(records) == 14
    by_key = {(r["employment_type"], r["age_group"]): r["value"] for r in records}
    assert by_key[("正規", "総数")] == "4956"
    assert by_key[("正規", "15～24歳")] == "308"
    assert by_key[("非正規", "総数")] == "2428"
    assert by_key[("非正規", "65歳以上")] == "399"


def test_parse_without_western_year_column():
    records = _parse(_CSV_NO_WESTERN_YEAR, 2021)

    assert len(records) == 14
    assert {(r["year"], r["sex"]) for r in records} == {("2021", "男")}
    assert records[7]["employment_type"] == "非正規"
    assert records[7]["value"] == "795"


def test_parse_rejects_mismatched_western_year():
    text = _CSV_TYPE_IN_ROW.replace("平成27年平均,2015", "平成27年平均,2014", 1)

    with pytest.raises(ValueError, match="和暦と西暦"):
        _parse(text, 2015)


def test_parse_rejects_unknown_header():
    text = _CSV_TYPE_IN_COLUMN.replace("正規／総数（千人）", "正規／総数", 1)

    with pytest.raises(ValueError, match="ヘッダー"):
        _parse(text, 2025)


def test_parse_rejects_unknown_employment_type():
    text = _CSV_TYPE_IN_ROW.replace("男女計／正規／", "男女計／正規雇用／", 1)

    with pytest.raises(ValueError, match="雇用形態"):
        _parse(text, 2015)


def test_is_employment_type_table_reads_title_row():
    assert _is_employment_type_table(list(csv.reader(_CSV_TYPE_IN_ROW.splitlines())))
    assert _is_employment_type_table(list(csv.reader(_CSV_TYPE_IN_COLUMN.splitlines())))
    other = "年平均\n第８表　従業上の地位別就業者数\n"
    assert not _is_employment_type_table(list(csv.reader(other.splitlines())))
