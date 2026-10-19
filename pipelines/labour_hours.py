"""東京都「毎月勤労統計調査」年報の月間出勤日数・実労働時間のダウンロード。

東京都総務局統計部が公表する毎月勤労統計調査（地方調査）の年報から、
第6-1表（事業所規模5人以上）と第6-2表（事業所規模30人以上）の
「産業、性別常用労働者の1人平均月間出勤日数及び実労働時間」を取り込む。

表の形は第1表（月間現金給与額）と同じ 1行 = 事業所規模 × 産業 × 年 × 年平均・月 で、
取り出し方も同じ（各年の値はその年の年報から取る）。pipelines/labour_earnings.py を参照。

データソース: 東京都の統計
https://www.toukei.metro.tokyo.lg.jp/maikin/mk-index.htm
"""

from pipelines.labour_earnings import download_annual_tables

# 年報のページに並ぶ CSV の (並び位置, 表番号)。8つ目と9つ目が第6-1表と第6-2表
# （2024年報はファイル名の番号が1つずれているので、ファイル名では選ばない）
_TABLES = [(7, "第6-1表"), (8, "第6-2表")]

_HEADER = [
    "事業所規模",
    "産業",
    "和暦年",
    "西暦年",
    "年平均・月",
    "出勤日数／計(日)",
    "出勤日数／男(日)",
    "出勤日数／女(日)",
    "総実労働時間／計(時間)",
    "総実労働時間／男(時間)",
    "総実労働時間／女(時間)",
    "所定内労働時間／計(時間)",
    "所定内労働時間／男(時間)",
    "所定内労働時間／女(時間)",
    "所定外労働時間／計(時間)",
    "所定外労働時間／男(時間)",
    "所定外労働時間／女(時間)",
]
_VALUE_KEYS = [
    "days_worked",
    "days_worked_male",
    "days_worked_female",
    "total_hours",
    "total_hours_male",
    "total_hours_female",
    "scheduled_hours",
    "scheduled_hours_male",
    "scheduled_hours_female",
    "overtime_hours",
    "overtime_hours_male",
    "overtime_hours_female",
]

_OUTPUT_FILENAME = "labour_hours.ndjson"


def download_labour_hours(dest_dir: str) -> None:
    """各年の年報から第6-1表・第6-2表を取得し、公表年の行を NDJSON に出力する。"""
    download_annual_tables(dest_dir, _TABLES, _HEADER, _VALUE_KEYS, _OUTPUT_FILENAME)
