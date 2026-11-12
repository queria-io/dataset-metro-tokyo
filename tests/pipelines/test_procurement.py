"""調達情報のリソースの分類と、随意契約・発注予定の表の読み取りのテスト。"""

from datetime import date

import pytest

from pipelines.procurement import (
    _PLANNED_WORK_COLUMNS,
    classify,
    parse_amount,
    parse_contracts,
    parse_period_months,
    parse_planned,
    parse_wareki_dates,
    to_contract_record,
)


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        (
            "〔随意契約の締結状況〕工事請負契約、工事系委託（設計、工事監理、測量等）(令和3年4月から令和3年7月まで)",
            ("private_contracts", "工事・設計等", "令和3年4月から令和3年7月まで"),
        ),
        (
            "〔随意契約の締結状況〕物品、委託、賃貸借等(令和2年12月から令和3年3月まで)",
            ("private_contracts", "物品・委託・賃貸借等", "令和2年12月から令和3年3月まで"),
        ),
        (
            "〔工事の発注予定〕電気工事（街路灯等）(令和8年度上半期)",
            ("planned_works", "電気工事（街路灯等）", "令和8年度上半期"),
        ),
        (
            "物品買入れ契約（一般競争入札案件）の発注予定(令和8年度上半期)",
            ("planned_goods", "物品買入れ", "令和8年度上半期"),
        ),
        ("区のお知らせ", None),
    ],
)
def test_classify(name, expected):
    assert classify(name) == expected


def test_parse_wareki_dates():
    assert parse_wareki_dates("令和 3年 7月21日～令和 3年 9月30日") == [
        date(2021, 7, 21),
        date(2021, 9, 30),
    ]
    assert parse_wareki_dates("R2.12.3～R3.2.26") == [date(2020, 12, 3), date(2021, 2, 26)]
    assert parse_wareki_dates("2025-04-01") == [date(2025, 4, 1)]
    assert parse_wareki_dates(None) == []


def test_parse_period_months():
    assert parse_period_months("令和５年12月から令和６年３月まで") == ("2023-12", "2024-03")


@pytest.mark.parametrize(
    ("value", "expected"),
    [("1,947,660", 1947660), (695200.0, 695200), (None, None), ("1.54", None)],
)
def test_parse_amount(value, expected):
    assert parse_amount(value) == expected


def test_parse_contracts_header_variants():
    rows = [
        ["随意契約の公表について（令和３年４月から令和３年７月まで）【物品・委託・賃貸借等】", None],
        [None, "件名", "業種", "契約金額（契約変更後の金額含む）", "契約年月日", "履行期間", "契約者"],
        ["1", "業務委託（単価契約）", "医療事務", None, "令和 3年 4月 1日", "令和 4年 3月31日", "A社"],
        ["2", "清掃委託", "建物清掃", "1,000,000", "令和 3年 5月 6日", "令和 3年 5月 7日～令和 4年 3月31日", "B社"],
        [None, None, None, None, None, None, None],
    ]
    title, records = parse_contracts(rows)
    assert title.startswith("随意契約の公表について")
    assert [r["seq_no"] for r in records] == ["1", "2"]
    assert records[0]["contract_amount"] is None
    assert records[1]["contract_amount"] == 1_000_000

    single = to_contract_record(records[0])
    assert single["performance_start"] is None
    assert single["performance_end"] == "2022-03-31"
    ranged = to_contract_record(records[1])
    assert (ranged["performance_start"], ranged["performance_end"]) == ("2021-05-07", "2022-03-31")


def test_parse_planned_design_headers():
    text = (
        "﻿全国地方公共団体コード,地方公共団体名,業種,件名,履行場所_連結表記,履行場所_都道府県,"
        "履行場所_市区町村,履行場所_町字,履行場所_番地以下,建物名等(方書),緯度,経度,"
        '履行期間（始期）,履行期間（終期）,業務概要,入札方法,"入札時期（予定）",備考\n'
        "131202,東京都練馬区,土木設計,補修設計委託,大泉学園駅南ペデ,東京都,練馬区,,,,,,"
        "2026-10,2027-03,橋梁補修設計業務,一般競争入札,第3四半期,\n"
    )
    [row] = parse_planned(text, _PLANNED_WORK_COLUMNS)
    assert row["work_type"] == "土木設計"
    assert row["period_start"] == "2026-10"
    assert row["note"] is None


def test_parse_planned_header_mismatch():
    with pytest.raises(ValueError, match="header_mismatch"):
        parse_planned("件名,備考\nA,\n", _PLANNED_WORK_COLUMNS)
