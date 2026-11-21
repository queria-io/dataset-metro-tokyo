"""東京都第3次産業活動指数（月次）の CSV から業種 × 月の行を取り出す処理のテスト。"""

import pytest

from pipelines.tertiary_activity_index import _month_columns, _parse, _resource_urls

_CSV = """品目階層Item_Class,品目番号Item_Number,品目名称Item_Name,Item_Name,ウェイトWeight,13-Jan,13-Feb,25-Dec
0,K1D000000I,第３次産業総合,Tertiary Industry,10000,98.4,98.5,108.6
2,DBC0000I,情報サービス業,Information Services,920.7,97.6,―,130
,,,,,,,
"品目階層（1:大分類）",,,,,,,
"""


def test_parse_wide_to_long():
    records = _parse(_CSV, "seasonally_adjusted")
    assert len(records) == 6
    first = records[0]
    assert first == {
        "index_type": "seasonally_adjusted",
        "item_class": "0",
        "item_code": "K1D000000I",
        "item_name": "第３次産業総合",
        "item_name_en": "Tertiary Industry",
        "weight": "10000",
        "year": "2013",
        "month": "1",
        "value": "98.4",
    }
    assert (records[2]["year"], records[2]["month"], records[2]["value"]) == (
        "2025",
        "12",
        "108.6",
    )
    # 値が「―」の月も行は残し、型変換は dbt 側で行う
    assert records[4]["value"] == "―"


def test_parse_rejects_unknown_header():
    with pytest.raises(ValueError):
        _parse("a,b\n1,2\n", "original")


def test_month_columns_requires_month_header():
    with pytest.raises(ValueError):
        _month_columns(["品目階層", "CY2013"])


def test_resource_urls_picks_monthly_only():
    package = {
        "result": {
            "resources": [
                {"name": "業種別原指数（月次）（平成27年＝100）", "url": "u1"},
                {"name": "業種別原指数（四半期）（平成27年＝100）", "url": "u2"},
                {"name": "業種別季節調整済指数（月次）（平成27年＝100）", "url": "u3"},
            ]
        }
    }
    assert _resource_urls(package) == {
        "original": "u1",
        "seasonally_adjusted": "u3",
    }


def test_resource_urls_rejects_missing():
    with pytest.raises(RuntimeError):
        _resource_urls({"result": {"resources": []}})
