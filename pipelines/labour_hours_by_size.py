"""東京都「毎月勤労統計調査」年報の規模別月間出勤日数・実労働時間のダウンロード。

東京都総務局統計部が公表する毎月勤労統計調査（地方調査）の年報から、
第8表「規模、性別常用労働者の1人平均月間出勤日数及び実労働時間（調査産業計）」を取り込む。

列は第6表（月間出勤日数・実労働時間）と同じで、産業の列が無い代わりに事業所規模が
5〜29人・30〜99人・100〜499人・500人以上の4区分に分かれる。
取り出し方は第1表と同じ（各年の値はその年の年報から取る）。pipelines/labour_earnings.py を参照。

データソース: 東京都の統計
https://www.toukei.metro.tokyo.lg.jp/maikin/mk-index.htm
"""

from pipelines.labour_earnings import download_annual_tables
from pipelines.labour_hours import _VALUE_KEYS

# 年報のページに並ぶ CSV の (並び位置, 表番号)。12個目が第8表
_TABLES = [(11, "第8表")]

_HEADER = [
    "事業所規模",
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

_OUTPUT_FILENAME = "labour_hours_by_size.ndjson"


def download_labour_hours_by_size(dest_dir: str) -> None:
    """各年の年報から第8表を取得し、公表年の行を NDJSON に出力する。"""
    download_annual_tables(dest_dir, _TABLES, _HEADER, _VALUE_KEYS, _OUTPUT_FILENAME)
