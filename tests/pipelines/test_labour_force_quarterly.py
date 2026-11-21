"""東京の労働力 四半期平均の第1表から区分 × 男女の行を取り出す処理のテスト。"""

import pytest

from pipelines.labour_force_quarterly import _parse_quarter, _quarter_pages

_HEADER = (
    "区分,"
    "男女計／実数（千人、％）,男女計／前年同期（千人、％）,"
    "男女計／対前年同期／増減数（千人、ポイント）,男女計／対前年同期／増減率（％）,"
    "男／実数（千人、％）,男／前年同期（千人、％）,"
    "男／対前年同期／増減数（千人、ポイント）,男／対前年同期／増減率（％）,"
    "女／実数（千人、％）,女／前年同期（千人、％）,"
    "女／対前年同期／増減数（千人、ポイント）,女／対前年同期／増減率（％）"
)

_CSV = (
    _HEADER
    + """
15歳以上人口,12700,12586,114,0.9,6205,6147,58,0.9,6495,6439,56,0.9
〔就業状態〕／労働力人口／完全失業者数,215,213,2,0.9,113,125,-12,-9.6,102,88,14,15.9
,,,,,,,,,,,,
第１表　就業状態別15歳以上人口、産業別就業者数及び完全失業者数　　,,,,,,,,,,,,
"""
)


def test_parse_quarter_adds_quarter_to_each_row():
    records = _parse_quarter(_CSV, 2025, 1)

    # 2区分 × 男女計・男・女。末尾の空行と表題は落ちる
    assert len(records) == 6
    assert {(r["year"], r["quarter"]) for r in records} == {("2025", "1")}
    female = records[5]
    assert female["item"] == "〔就業状態〕／労働力人口／完全失業者数"
    assert female["sex"] == "女"
    assert (female["value"], female["previous_year_value"]) == ("102", "88")
    assert (female["change"], female["change_rate"]) == ("14", "15.9")


def test_parse_quarter_accepts_older_header_wording():
    # 2003年10〜12月期〜2007年の表は増減率の見出しが「比」、2010〜2011年の表は増減数が「増減」
    old = _CSV.replace("増減数（千人", "増減（千人").replace("増減率（％）", "比（％）")
    assert len(_parse_quarter(old, 2004, 2)) == 6


def test_parse_quarter_rejects_annual_header():
    # 年平均の表（前年・対前年）を四半期として読まない
    annual = _CSV.replace("前年同期", "前年")
    with pytest.raises(ValueError, match="ヘッダー"):
        _parse_quarter(annual, 2025, 1)


def test_quarter_pages_map_letters_to_quarters():
    html = """
    <a href="/roudou/2025/rd25qd1000.htm">令和7年平均</a>
    <a href="/roudou/2025/rd25hd1000.htm">10～12月平均</a>
    <a href="/roudou/2025/rd25ed1000.htm">1～3月平均</a>
    <a href="/roudou/2025/rd25fd1000.htm">4～6月平均</a>
    <a href="/roudou/2025/rd25gd1000.htm">7～9月平均</a>
    <a href="/roudou/2003/03edjr10000.htm">平成15年1～3月平均</a>
    """
    pages = _quarter_pages(html)

    assert [(year, quarter) for year, quarter, _ in pages] == [
        (2025, 1),
        (2025, 2),
        (2025, 3),
        (2025, 4),
    ]
    assert (
        pages[0][2] == "https://www.toukei.metro.tokyo.lg.jp/roudou/2025/rd25ed1000.htm"
    )
