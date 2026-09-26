"""地域・年齢別人口の重複解消（stg_population と ods_latest_resource マクロ）。

同じ（自治体・調査年月日・地域）の行が複数のリソースから入る形を DuckDB 上に作り、
stg_population.sql をそのまま展開して適用する。マクロだけを単体で試すと、規則を
当てる位置がずれていても気付けない（qualify から raw の列が見えると survey_date が
正規化前の文字列で束縛され、日付の表記が違うだけの重複が残る）。

規則を通す前の一意性の検査が落ちることも同じ形で確かめる（規則が効いていることの裏側）。

dbt も DuckLake も要らない。モデルとマクロは dbt と同じ Jinja の記法なので、
ファイルをそのまま読み、ref() だけ差し替えて展開する。
"""

import re
from datetime import date
from pathlib import Path

import duckdb
import jinja2
import pytest

REPO_ROOT = Path(__file__).parents[2]
MACRO_NAMES = ["ods_date.sql", "ods_latest_resource.sql"]
MODEL_PATH = REPO_ROOT / "models" / "ods" / "stg" / "stg_population.sql"
RAW_MODEL_PATH = REPO_ROOT / "models" / "ods" / "raw" / "raw_population.sql"

# mart の population に付けた unique_key 検査と同じ列
UNIQUE_KEY = ["org_code", "survey_date", "area_code", "area_name"]

# 行を組み立てるのに使う列。残りは NULL でよい
INSERT_COLUMNS = [
    "_org_code",
    "survey_date",
    "area_code",
    "area_name",
    "total_population",
    "_resource_id",
    "_resource_modified",
]


def raw_columns():
    """raw_population.sql の read_json 宣言から (列名, 型) を読む。"""
    source = RAW_MODEL_PATH.read_text(encoding="utf-8")
    return re.findall(r"'([^']+)':\s*'([A-Z]+)'", source)


def render_model():
    """stg_population.sql を dbt と同じマクロで展開する。ref は表名そのまま。"""
    source = "".join(
        (REPO_ROOT / "macros" / name).read_text(encoding="utf-8")
        for name in MACRO_NAMES
    ) + MODEL_PATH.read_text(encoding="utf-8")
    return jinja2.Environment().from_string(source).render(ref=lambda name: name)


@pytest.fixture
def con():
    connection = duckdb.connect()
    columns = raw_columns()
    assert ("_resource_modified", "VARCHAR") in columns, (
        "raw_population が _resource_modified を宣言していないと規則が働かない"
    )
    connection.execute(
        "create table raw_population ("
        + ", ".join(f'"{name}" {type_}' for name, type_ in columns)
        + ")"
    )
    connection.execute(f"create view stg_population as {render_model()}")
    yield connection
    connection.close()


def insert(con, *records):
    placeholders = ", ".join("?" for _ in INSERT_COLUMNS)
    names = ", ".join(f'"{c}"' for c in INSERT_COLUMNS)
    con.executemany(
        f"insert into raw_population ({names}) values ({placeholders})", list(records)
    )


def violations(con, table):
    keys = ", ".join(UNIQUE_KEY)
    return con.execute(
        f"select {keys}, count(*) as n from {table} group by {keys} having count(*) > 1"
    ).fetchall()


def normalized_without_the_rule(con):
    """規則を外した形。stg_population から qualify 句だけ落とす。"""
    sql = render_model()
    stripped = re.sub(r"qualify\s+row_number\(\).*?=\s*1\s*$", "", sql, flags=re.S)
    assert "qualify" not in stripped
    con.execute(f"create view no_rule as {stripped}")
    return "no_rule"


# 練馬区の地域・年齢別人口で起きた形。131202_population_202503.csv（令和7年3月として
# 登録されたまま 2026-03-01 のデータを返す）と 131202_population_202603.csv が
# 同じ月の同じ地域を二重に入れる
OLD_NAME = ("t131202", "2026-03-01", "1", "豊玉北一丁目", "3705", "r-202503", "2025-10-16 15:00:00")
NEW_NAME = ("t131202", "2026-03-01", "1", "豊玉北一丁目", "3705", "r-202603", "2026-03-15 15:00:00")


def test_unique_key_fails_without_the_rule(con):
    """規則を外すと一意性の検査が落ちる（負のテスト）。"""
    insert(con, OLD_NAME, NEW_NAME)

    assert violations(con, normalized_without_the_rule(con)) == [
        ("t131202", date(2026, 3, 1), "1", "豊玉北一丁目", 2)
    ]


def test_rule_makes_the_unique_key_hold(con):
    insert(con, OLD_NAME, NEW_NAME)

    assert violations(con, "stg_population") == []


def test_newer_resource_wins(con):
    """同じ月の同じ地域は、最終更新時点が新しいリソースの1行に決まる。"""
    insert(con, OLD_NAME, NEW_NAME)

    assert con.execute("select resource_id from stg_population").fetchall() == [
        ("r-202603",)
    ]


def test_same_month_written_in_different_notations_is_still_one_row(con):
    """日付の表記が違うだけの重複も1行になる。

    規則を正規化前の列に当てると（qualify から raw の列が見える形）ここが2行になり、
    mart の unique_key が落ちて本番の Sync が止まる。
    """
    insert(
        con,
        ("t131202", "20260301", "1", "豊玉北一丁目", "3705", "r-old", "2025-10-16 15:00:00"),
        ("t131202", "2026-03-01", "1", "豊玉北一丁目", "3705", "r-new", "2026-03-15 15:00:00"),
    )

    assert violations(con, "stg_population") == []
    assert con.execute("select resource_id from stg_population").fetchall() == [
        ("r-new",)
    ]


def test_different_months_are_kept(con):
    """月が違えば両方残る（複数月をまとめたファイルが登録されても消さない）。"""
    insert(
        con,
        ("t131202", "2025-08-01", "1", "豊玉北一丁目", "3700", "r-range", "2026-09-30 15:00:00"),
        ("t131202", "2025-10-01", "1", "豊玉北一丁目", "3702", "r-202510", "2025-10-16 15:00:00"),
    )

    kept = con.execute(
        "select survey_date from stg_population order by survey_date"
    ).fetchall()

    assert kept == [(date(2025, 8, 1),), (date(2025, 10, 1),)]


def test_different_areas_in_the_same_month_are_kept(con):
    insert(
        con,
        ("t131202", "2026-03-01", "1", "豊玉北一丁目", "3705", "r-202603", "2026-03-15 15:00:00"),
        ("t131202", "2026-03-01", "2", "豊玉北二丁目", "2801", "r-202603", "2026-03-15 15:00:00"),
    )

    assert len(con.execute("select area_name from stg_population").fetchall()) == 2


def test_resource_id_decides_when_modified_times_are_equal(con):
    """最終更新時点が並んでも、ビルドのたびに採用行が入れ替わらない。"""
    insert(
        con,
        ("t131202", "2026-03-01", "1", "豊玉北一丁目", "3705", "r-b", None),
        ("t131202", "2026-03-01", "1", "豊玉北一丁目", "3705", "r-a", None),
    )

    assert con.execute("select resource_id from stg_population").fetchall() == [("r-a",)]


def test_resource_without_modified_time_loses_to_one_with(con):
    """最終更新時点の登録が無いリソースは、登録があるリソースに譲る。"""
    insert(
        con,
        ("t131202", "2026-03-01", "1", "豊玉北一丁目", "3705", "r-no-time", None),
        ("t131202", "2026-03-01", "1", "豊玉北一丁目", "3705", "r-dated", "2025-01-01 00:00:00"),
    )

    assert con.execute("select resource_id from stg_population").fetchall() == [
        ("r-dated",)
    ]
