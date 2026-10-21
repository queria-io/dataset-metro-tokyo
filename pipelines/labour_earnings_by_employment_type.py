"""東京都「毎月勤労統計調査」年報の就業形態別月間現金給与額のダウンロード。

東京都総務局統計部が公表する毎月勤労統計調査（地方調査）の年報から、
第2-1表（事業所規模5人以上）と第2-2表（事業所規模30人以上）の
「産業、就業形態別常用労働者の1人平均月間現金給与額」を取り込む。

表の形は第1表（月間現金給与額）と同じ 1行 = 事業所規模 × 産業 × 年 × 年平均・月 で、
取り出し方も同じ（各年の値はその年の年報から取る）。pipelines/labour_earnings.py を参照。
列は性別の代わりに一般労働者とパートタイム労働者に分かれる。

データソース: 東京都の統計
https://www.toukei.metro.tokyo.lg.jp/maikin/mk-index.htm
"""

from pipelines.labour_earnings import download_annual_tables

# 年報のページに並ぶ CSV の (並び位置, 表番号)。3個目と4個目が第2-1表と第2-2表
_TABLES = [(2, "第2-1表"), (3, "第2-2表")]

_HEADER = [
    "事業所規模",
    "産業",
    "和暦年",
    "西暦年",
    "年平均・月",
    "一般労働者／現金給与総額(円)",
    "一般労働者／きまって支給する給与(円)",
    "一般労働者／所定内給与(円)",
    "一般労働者／所定外給与(円)",
    "一般労働者／特別に支払われた給与(円)",
    "パートタイム労働者／現金給与総額(円)",
    "パートタイム労働者／きまって支給する給与(円)",
    "パートタイム労働者／所定内給与(円)",
    "パートタイム労働者／所定外給与(円)",
    "パートタイム労働者／特別に支払われた給与(円)",
]
_VALUE_KEYS = [
    "general_cash_earnings",
    "general_contractual_earnings",
    "general_scheduled_earnings",
    "general_overtime_earnings",
    "general_special_earnings",
    "part_time_cash_earnings",
    "part_time_contractual_earnings",
    "part_time_scheduled_earnings",
    "part_time_overtime_earnings",
    "part_time_special_earnings",
]

_OUTPUT_FILENAME = "labour_earnings_by_employment_type.ndjson"


def download_labour_earnings_by_employment_type(dest_dir: str) -> None:
    """各年の年報から第2-1表・第2-2表を取得し、公表年の行を NDJSON に出力する。"""
    download_annual_tables(dest_dir, _TABLES, _HEADER, _VALUE_KEYS, _OUTPUT_FILENAME)
