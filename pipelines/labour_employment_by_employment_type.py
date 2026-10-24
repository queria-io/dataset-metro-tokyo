"""東京都「毎月勤労統計調査」年報の就業形態別常用労働者数のダウンロード。

東京都総務局統計部が公表する毎月勤労統計調査（地方調査）の年報から、
第11-1表（事業所規模5人以上）と第11-2表（事業所規模30人以上）の
「産業、就業形態別常用労働者数」を取り込む。

表の形は第1表（月間現金給与額）と同じ 1行 = 事業所規模 × 産業 × 年 × 年平均・月 で、
取り出し方も同じ（各年の値はその年の年報から取る）。pipelines/labour_earnings.py を参照。
列は性別の代わりに一般労働者とパートタイム労働者に分かれる。

データソース: 東京都の統計
https://www.toukei.metro.tokyo.lg.jp/maikin/mk-index.htm
"""

from pipelines.labour_earnings import download_annual_tables

# 年報のページに並ぶ CSV の (並び位置, 表番号)。16個目と17個目が第11-1表と第11-2表
_TABLES = [(15, "第11-1表"), (16, "第11-2表")]

_HEADER = [
    "事業所規模",
    "産業",
    "和暦年",
    "西暦年",
    "年平均・月",
    "一般労働者／前月末労働者数(人)",
    "一般労働者／本月中の増加労働者数(人)",
    "一般労働者／本月中の減少労働者数(人)",
    "一般労働者／本月末労働者数(人)",
    "パートタイム労働者／前月末労働者数(人)",
    "パートタイム労働者／本月中の増加労働者数(人)",
    "パートタイム労働者／本月中の減少労働者数(人)",
    "パートタイム労働者／本月末労働者数(人)",
]
_VALUE_KEYS = [
    "general_employees_start",
    "general_employees_added",
    "general_employees_removed",
    "general_employees",
    "part_time_employees_start",
    "part_time_employees_added",
    "part_time_employees_removed",
    "part_time_employees",
]

_OUTPUT_FILENAME = "labour_employment_by_employment_type.ndjson"


def download_labour_employment_by_employment_type(dest_dir: str) -> None:
    """各年の年報から第11-1表・第11-2表を取得し、公表年の行を NDJSON に出力する。"""
    download_annual_tables(dest_dir, _TABLES, _HEADER, _VALUE_KEYS, _OUTPUT_FILENAME)
