"""東京都「毎月勤労統計調査」年報の就業形態別月間出勤日数・実労働時間のダウンロード。

東京都総務局統計部が公表する毎月勤労統計調査（地方調査）の年報から、
第7-1表（事業所規模5人以上）と第7-2表（事業所規模30人以上）の
「産業、就業形態別常用労働者の1人平均月間出勤日数及び実労働時間」を取り込む。

表の形は第1表（月間現金給与額）と同じ 1行 = 事業所規模 × 産業 × 年 × 年平均・月 で、
取り出し方も同じ（各年の値はその年の年報から取る）。pipelines/labour_earnings.py を参照。
列は性別の代わりに一般労働者とパートタイム労働者に分かれる。

データソース: 東京都の統計
https://www.toukei.metro.tokyo.lg.jp/maikin/mk-index.htm
"""

from pipelines.labour_earnings import download_annual_tables

# 年報のページに並ぶ CSV の (並び位置, 表番号)。10個目と11個目が第7-1表と第7-2表
_TABLES = [(9, "第7-1表"), (10, "第7-2表")]

_HEADER = [
    "事業所規模",
    "産業",
    "和暦年",
    "西暦年",
    "年平均・月",
    "一般労働者／出勤日数(日)",
    "一般労働者／総実労働時間(時間)",
    "一般労働者／所定内労働時間(時間)",
    "一般労働者／所定外労働時間(時間)",
    "パートタイム労働者／出勤日数(日)",
    "パートタイム労働者／総実労働時間(時間)",
    "パートタイム労働者／所定内労働時間(時間)",
    "パートタイム労働者／所定外労働時間(時間)",
]
_VALUE_KEYS = [
    "general_days_worked",
    "general_total_hours",
    "general_scheduled_hours",
    "general_overtime_hours",
    "part_time_days_worked",
    "part_time_total_hours",
    "part_time_scheduled_hours",
    "part_time_overtime_hours",
]

_OUTPUT_FILENAME = "labour_hours_by_employment_type.ndjson"


def download_labour_hours_by_employment_type(dest_dir: str) -> None:
    """各年の年報から第7-1表・第7-2表を取得し、公表年の行を NDJSON に出力する。"""
    download_annual_tables(dest_dir, _TABLES, _HEADER, _VALUE_KEYS, _OUTPUT_FILENAME)
