"""find_csv_links() が自治体のページから種別の CSV だけを拾うこと。

自治体のサイトには、別の種別の CSV が同じページに並ぶ。ファイル名がスラッグに
沿っていない自治体もあるので、リンクの文言でも照合する。
"""

from pipelines.ods import OdsDataset, find_csv_links

PAGE = "https://www.city.example.lg.jp/opendata/opendataichiran/1001604.html"


def dataset(dataset_id, slugs, titles):
    return OdsDataset(
        id=dataset_id,
        title="",
        slug_patterns=slugs,
        title_patterns=titles,
        header_map={},
        required_columns=[],
        identity_column="name",
    )


PUBLIC_FACILITY = dataset("public_facility", ["public_facility"], ["公共施設一覧"])

# 清瀬市のページ（1001604）の並びを縮めたもの
MIXED_PAGE = """
<ul>
<li><a href="../../../_res/1001604/132217_kiyoseshi_koukyoushisetu1.csv">公共施設一覧 （CSV 25.5 KB）</a></li>
<li><a href="../../../_res/1001604/132217_kiyoseshi_koukyoushisetu1.xlsx">公共施設一覧 （Excel 30 KB）</a></li>
<li><a href="../../../_res/1001604/132217_kiyoseshi_kyouikukikan.csv">教育機関一覧 （CSV 2.8 KB）</a></li>
<li><a href="../../../_res/1001604/132217_kiyoseshi_koukyoushisetuyoyakutannmatu.csv">公共施設予約端末設置場所一覧 （CSV 2.8 KB）</a></li>
<li><a href="../../../_res/1001604/132217_kiyoseshi_kaigosabisujijyosyo..csv">市民葬儀取扱店一覧 （CSV 25.4 KB）</a></li>
</ul>
"""


def test_matches_by_link_text_when_file_name_does_not_follow_slug():
    links = find_csv_links(MIXED_PAGE, PAGE, PUBLIC_FACILITY)

    assert links == [
        (
            "https://www.city.example.lg.jp/_res/1001604/132217_kiyoseshi_koukyoushisetu1.csv",
            "公共施設一覧 （CSV 25.5 KB）",
        )
    ]


def test_matches_by_file_name_slug():
    html = '<a href="/_res/905/132128_aed.csv">132128_aed （CSV 50.0KB）</a>'
    links = find_csv_links(html, PAGE, dataset("aed", ["aed"], ["AED設置"]))

    assert [url for url, _ in links] == ["https://www.city.example.lg.jp/_res/905/132128_aed.csv"]


def test_same_file_linked_twice_is_returned_once():
    html = (
        '<a href="/p/132217_population_20260901.csv">人口</a>'
        '<a href="/p/132217_population_20260901.csv">人口</a>'
        '<a href="/p/132217_population_20260801.csv">人口</a>'
    )
    links = find_csv_links(html, PAGE, dataset("population", ["population"], []))

    assert [url.rsplit("/", 1)[1] for url, _ in links] == [
        "132217_population_20260901.csv",
        "132217_population_20260801.csv",
    ]


def test_non_csv_links_are_ignored():
    html = '<a href="/a/132128_aed.xlsx">AED設置箇所一覧</a><a href="/a/132128_aed.html">AED設置</a>'

    assert find_csv_links(html, PAGE, dataset("aed", ["aed"], ["AED設置"])) == []
