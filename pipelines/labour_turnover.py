"""東京都「毎月勤労統計調査」年報の労働異動率（入職率・離職率）のダウンロード。

東京都総務局統計部が公表する毎月勤労統計調査（地方調査）の年報から、
第12-1表（事業所規模5人以上）と第12-2表（事業所規模30人以上）の
「産業別労働異動率」を取り込む。

表は 1行 = 事業所規模 × 年 × 年平均・月 で、産業が列に横持ちになっている
（「建設業／入職率(％)」「建設業／離職率(％)」のように産業ごとに2列）。
これを 1行 = 事業所規模 × 産業 × 年 × 年平均・月 に縦持ちに直す。
表の列には産業符号が無いので、ほかの表と同じ符号（TL・C〜R）を産業名から付ける。
取り出し方の残りは第1表と同じ。pipelines/labour_earnings.py を参照。

データソース: 東京都の統計
https://www.toukei.metro.tokyo.lg.jp/maikin/mk-index.htm
"""

import csv
import re

from pipelines.labour_earnings import _normalize, download_annual_tables

# 年報のページに並ぶ CSV の (並び位置, 表番号)。18個目と19個目が第12-1表と第12-2表
_TABLES = [(17, "第12-1表"), (18, "第12-2表")]

# 産業の列より前に並ぶ列
_HEADER = ["事業所規模", "和暦年", "西暦年", "年平均・月"]
# 産業ごとに並ぶ2列の見出しの末尾と、出力のキー
_RATE_SUFFIXES = {"入職率(％)": "hiring_rate", "離職率(％)": "separation_rate"}
_VALUE_KEYS = list(_RATE_SUFFIXES.values())

# 産業名から、ほかの表の産業符号を引く。キーは _normalize でそろえて引く
_INDUSTRY_NAMES = {
    "調査産業計": "TL",
    "鉱業，採石業，砂利採取業": "C",
    "建設業": "D",
    "製造業": "E",
    "電気・ガス・熱供給・水道業": "F",
    "情報通信業": "G",
    "運輸業，郵便業": "H",
    "卸売業，小売業": "I",
    "金融業，保険業": "J",
    "不動産業，物品賃貸業": "K",
    "学術研究，専門・技術サービス業": "L",
    "宿泊業，飲食サービス業": "M",
    "生活関連サービス業，娯楽業": "N",
    "教育，学習支援業": "O",
    "医療，福祉": "P",
    "複合サービス事業": "Q",
    "サービス業（他に分類されないもの）": "R",
}
_INDUSTRY_CODES = {_normalize(name): code for name, code in _INDUSTRY_NAMES.items()}

_RATE_COLUMN_RE = re.compile(r"^(.+)／(.+)$")

_OUTPUT_FILENAME = "labour_turnover.ndjson"


def _industry_columns(
    headers: list[str], header: list[str]
) -> list[tuple[str, int, int]]:
    """産業の列の見出しから (産業, 入職率の列位置, 離職率の列位置) を取り出す。

    産業は「<符号> <原典の産業名>」にする（ほかの表の産業の列と同じ形）。
    見出しが「産業／入職率(％)」「産業／離職率(％)」の順に並んでいなければ止める。
    """
    if headers[: len(header)] != header:
        raise ValueError(f"ヘッダーを認識できません: {headers}")

    rate_headers = headers[len(header) :]
    if not rate_headers or len(rate_headers) % 2:
        raise ValueError(
            f"産業の列が入職率・離職率の組になっていません: {rate_headers}"
        )

    columns = []
    suffixes = list(_RATE_SUFFIXES)
    for i in range(0, len(rate_headers), 2):
        pair = [_RATE_COLUMN_RE.match(h) for h in rate_headers[i : i + 2]]
        if not all(pair) or [m.group(2) for m in pair] != suffixes:
            raise ValueError(f"産業の列を認識できません: {rate_headers[i : i + 2]}")
        industry = pair[0].group(1)
        if pair[1].group(1) != industry:
            raise ValueError(
                f"入職率と離職率の産業が違います: {rate_headers[i : i + 2]}"
            )
        code = _INDUSTRY_CODES.get(_normalize(industry))
        if code is None:
            raise ValueError(f"産業符号が分かりません: {industry}")
        position = len(header) + i
        columns.append((f"{code} {industry}", position, position + 1))
    return columns


def _parse(
    text: str,
    report_year: int,
    header: list[str] = _HEADER,
    value_keys: list[str] = _VALUE_KEYS,
) -> list[dict]:
    """年報の第12表の CSV から公表年の行（各月と年平均）を取り出し、産業ごとの行に分ける。

    表末尾の空行・表題の行は西暦年が数字でないので落ちる。値は原典の文字列のまま
    （「×」は秘匿、「－」は該当なし）。
    """
    rows = list(csv.reader(text.splitlines()))
    if not rows:
        raise ValueError("空のファイルです")
    headers = [h.strip() for h in rows[0]]
    columns = _industry_columns(headers, header)

    records = []
    for row in rows[1:]:
        if len(row) < len(headers):
            continue
        size, _, year, period = (v.strip() for v in row[: len(header)])
        if not year.isdigit() or int(year) != report_year:
            continue
        for industry, hiring, separation in columns:
            records.append(
                {
                    "report_year": str(report_year),
                    "establishment_size": _normalize(size),
                    "industry": industry,
                    "year": year,
                    "period": period,
                    **dict(
                        zip(
                            value_keys,
                            [row[hiring].strip(), row[separation].strip()],
                            strict=True,
                        )
                    ),
                }
            )
    return records


def download_labour_turnover(dest_dir: str) -> None:
    """各年の年報から第12-1表・第12-2表を取得し、公表年の行を産業ごとに NDJSON に出力する。"""
    download_annual_tables(
        dest_dir, _TABLES, _HEADER, _VALUE_KEYS, _OUTPUT_FILENAME, parse=_parse
    )
