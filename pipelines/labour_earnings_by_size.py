"""東京都「毎月勤労統計調査」年報の規模別月間現金給与額のダウンロード。

東京都総務局統計部が公表する毎月勤労統計調査（地方調査）の年報から、
第3表「規模、性別常用労働者の1人平均月間現金給与額（調査産業計）」を取り込む。

列は第1表（月間現金給与額）と同じで、産業の列が無い代わりに事業所規模が
5〜29人・30〜99人・100〜499人・500人以上の4区分に分かれる。
取り出し方は第1表と同じ（各年の値はその年の年報から取る）。pipelines/labour_earnings.py を参照。

データソース: 東京都の統計
https://www.toukei.metro.tokyo.lg.jp/maikin/mk-index.htm
"""

from pipelines.labour_earnings import _VALUE_KEYS, download_annual_tables

# 年報のページに並ぶ CSV の (並び位置, 表番号)。5個目が第3表
_TABLES = [(4, "第3表")]

_HEADER = [
    "事業所規模",
    "和暦年",
    "西暦年",
    "年平均・月",
    "現金給与総額／計(円)",
    "現金給与総額／男(円)",
    "現金給与総額／女(円)",
    "きまって支給する給与／計(円)",
    "きまって支給する給与／男(円)",
    "きまって支給する給与／女(円)",
    "所定内給与(円)",
    "所定外給与(円)",
    "特別に支払われた給与／計(円)",
    "特別に支払われた給与／男(円)",
    "特別に支払われた給与／女(円)",
]

_OUTPUT_FILENAME = "labour_earnings_by_size.ndjson"


def download_labour_earnings_by_size(dest_dir: str) -> None:
    """各年の年報から第3表を取得し、公表年の行を NDJSON に出力する。"""
    download_annual_tables(dest_dir, _TABLES, _HEADER, _VALUE_KEYS, _OUTPUT_FILENAME)
