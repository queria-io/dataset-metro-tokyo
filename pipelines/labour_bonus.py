"""東京都「毎月勤労統計調査」年報の夏季・冬季賞与のダウンロード。

東京都総務局統計部が公表する毎月勤労統計調査（地方調査）の年報から、
第5表「夏・冬季賞与の産業別支給状況（事業所規模30人以上）」を取り込む。

夏季賞与は公表年の6〜8月、冬季賞与は公表年の11月〜翌年1月に支払われた
「特別に支払われた給与」のうち賞与として支給されたものを特別集計した値。
表は年1回で 1行 = 事業所規模 × 産業 になっており、年・月の列が無いので、
年は年報の公表年を付ける。取り出し方の残りは第1表と同じ。pipelines/labour_earnings.py を参照。

データソース: 東京都の統計
https://www.toukei.metro.tokyo.lg.jp/maikin/mk-index.htm
"""

import csv

from pipelines.labour_earnings import _normalize, download_annual_tables

# 年報のページに並ぶ CSV の (並び位置, 表番号)。7個目が第5表
_TABLES = [(6, "第5表")]

_HEADER = [
    "事業所規模",
    "産業",
    "夏季／1人平均支給額(円)",
    "夏季／1人平均支給額／前年比(％)",
    "夏季／支給事業所数割合(％)",
    "夏季／支給労働者数割合(％)",
    "夏季／平均支給月数(か月)",
    "夏季／平均支給月数／前年月数差(か月)",
    "冬季／1人平均支給額(円)",
    "冬季／1人平均支給額／前年比(％)",
    "冬季／支給事業所数割合(％)",
    "冬季／支給労働者数割合(％)",
    "冬季／平均支給月数(か月)",
    "冬季／平均支給月数／前年月数差(か月)",
]
_VALUE_KEYS = [
    f"{season}_{key}"
    for season in ("summer", "winter")
    for key in (
        "bonus",
        "bonus_change_rate",
        "paying_establishment_ratio",
        "receiving_employee_ratio",
        "bonus_months",
        "bonus_months_change",
    )
]

_OUTPUT_FILENAME = "labour_bonus.ndjson"


def _parse(
    text: str,
    report_year: int,
    header: list[str] = _HEADER,
    value_keys: list[str] = _VALUE_KEYS,
) -> list[dict]:
    """年報の第5表の CSV から産業ごとの行を取り出し、年報の公表年を付ける。

    表末尾の空行・表題の行は産業の列が空なので落ちる。値は原典の文字列のまま
    （「×」は秘匿、「－」は該当なし）。
    """
    rows = list(csv.reader(text.splitlines()))
    if not rows:
        raise ValueError("空のファイルです")
    headers = [h.strip() for h in rows[0]]
    if headers != header:
        raise ValueError(f"ヘッダーを認識できません: {headers}")

    records = []
    for row in rows[1:]:
        if len(row) < len(header):
            continue
        size, industry = row[0].strip(), row[1].strip()
        if not size or not industry:
            continue
        values = [v.strip() for v in row[2 : len(header)]]
        records.append(
            {
                "report_year": str(report_year),
                "establishment_size": _normalize(size),
                "industry": industry,
                "year": str(report_year),
                **dict(zip(value_keys, values, strict=True)),
            }
        )
    return records


def download_labour_bonus(dest_dir: str) -> None:
    """各年の年報から第5表を取得し、産業ごとの行を NDJSON に出力する。"""
    download_annual_tables(
        dest_dir, _TABLES, _HEADER, _VALUE_KEYS, _OUTPUT_FILENAME, parse=_parse
    )
