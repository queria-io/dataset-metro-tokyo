"""東京都「毎月勤労統計調査」年報の常用労働者数・パートタイム労働者比率のダウンロード。

東京都総務局統計部が公表する毎月勤労統計調査（地方調査）の年報から、
第10-1表（事業所規模5人以上）と第10-2表（事業所規模30人以上）の
「産業、性別常用労働者数及びパートタイム労働者比率」を取り込む。

表の形は第1表（月間現金給与額）と同じ 1行 = 事業所規模 × 産業 × 年 × 年平均・月 で、
取り出し方も同じ（各年の値はその年の年報から取る）。pipelines/labour_earnings.py を参照。

データソース: 東京都の統計
https://www.toukei.metro.tokyo.lg.jp/maikin/mk-index.htm
"""

from pipelines.labour_earnings import download_annual_tables

# 年報のページに並ぶ CSV の (並び位置, 表番号)。14個目と15個目が第10-1表と第10-2表
_TABLES = [(13, "第10-1表"), (14, "第10-2表")]

_HEADER = [
    "事業所規模",
    "産業",
    "和暦年",
    "西暦年",
    "年平均・月",
    "前月末労働者数／計(人)",
    "前月末労働者数／男(人)",
    "前月末労働者数／女(人)",
    "本月中の増加労働者数／計(人)",
    "本月中の増加労働者数／男(人)",
    "本月中の増加労働者数／女(人)",
    "本月中の減少労働者数／計(人)",
    "本月中の減少労働者数／男(人)",
    "本月中の減少労働者数／女(人)",
    "本月末労働者数／計(人)",
    "本月末労働者数／男(人)",
    "本月末労働者数／女(人)",
    "パートタイム労働者比率／計(％)",
    "パートタイム労働者比率／男(％)",
    "パートタイム労働者比率／女(％)",
]
_VALUE_KEYS = [
    "employees_start",
    "employees_start_male",
    "employees_start_female",
    "employees_added",
    "employees_added_male",
    "employees_added_female",
    "employees_removed",
    "employees_removed_male",
    "employees_removed_female",
    "employees",
    "employees_male",
    "employees_female",
    "part_time_ratio",
    "part_time_ratio_male",
    "part_time_ratio_female",
]

_OUTPUT_FILENAME = "labour_employment.ndjson"


def download_labour_employment(dest_dir: str) -> None:
    """各年の年報から第10-1表・第10-2表を取得し、公表年の行を NDJSON に出力する。"""
    download_annual_tables(dest_dir, _TABLES, _HEADER, _VALUE_KEYS, _OUTPUT_FILENAME)
