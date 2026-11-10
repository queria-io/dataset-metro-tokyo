"""東京都「毎月勤労統計調査」年報の指数（賃金・労働時間・常用雇用）のダウンロード。

東京都総務局統計部が公表する毎月勤労統計調査（地方調査）の年報から、
第13表〜第21表の「規模、産業別」の指数を取り込む。9表とも同じ形で、
指数の種類（名目賃金指数（現金給与総額）など）だけが違う。

表は 1行 = 事業所規模 × 年 × 年平均・月（と、その前年比・前年同月比）で、
産業が列に横持ちになっている（1列が1産業）。これを
1行 = 指数の種類 × 事業所規模 × 産業 × 年 × 年平均・月 に縦持ちに直し、
指数の行と前年比（年平均）・前年同月比（月）の行を同じ行にまとめる。
指数の基準年（「平成22年平均=100」など）は表の注記の行から取る。年報によって基準年が違う。
産業符号は第12表と同じく産業名から引く。取り出し方の残りは第1表と同じ。
pipelines/labour_earnings.py を参照。

データソース: 東京都の統計
https://www.toukei.metro.tokyo.lg.jp/maikin/mk-index.htm
"""

import csv
import re

from pipelines.labour_earnings import _normalize, _table_name, download_annual_tables
from pipelines.labour_turnover import _INDUSTRY_CODES

# 年報のページに並ぶ CSV の (並び位置, 表番号)。20個目から28個目が第13表〜第21表
_TABLES = [(19 + i, f"第{13 + i}表") for i in range(9)]

# 表番号と指数の種類。表題の行に指数の種類が書かれているかで確かめる
_INDEX_TYPES = {
    "第13表": "名目賃金指数（現金給与総額）",
    "第14表": "名目賃金指数（きまって支給する給与）",
    "第15表": "名目賃金指数（所定内給与）",
    "第16表": "実質賃金指数（現金給与総額）",
    "第17表": "実質賃金指数（きまって支給する給与）",
    "第18表": "労働時間指数（総実労働時間）",
    "第19表": "労働時間指数（所定内労働時間）",
    "第20表": "労働時間指数（所定外労働時間）",
    "第21表": "常用雇用指数",
}

# 産業の列より前に並ぶ列
_HEADER = ["事業所規模", "和暦年", "西暦年", "年平均・月・前年比・前年同月比"]
_VALUE_KEYS = ["index_value", "change_rate"]

# 「年平均（前年比（％））」「1月（前年同月比（％））」を _normalize した形
_CHANGE_RE = re.compile(r"^(.+)\(前年(?:同月)?比\(%\)\)$")
# 「（平成22年平均=100）」「（令和2年平均=100）」
_BASE_RE = re.compile(r"^\(?(平成|令和)(\d+|元)年平均=100\)?$")
_ERA_OFFSETS = {"平成": 1988, "令和": 2018}

_OUTPUT_FILENAME = "labour_index.ndjson"


def _base_year(rows: list[list[str]]) -> str:
    """表の注記の行から指数の基準年（西暦）を取り出す。"""
    for row in rows:
        if not row:
            continue
        text = _normalize(row[0]).replace(" ", "").replace("（", "(").replace("）", ")")
        matched = _BASE_RE.match(text)
        if matched:
            era, year = matched.groups()
            return str(_ERA_OFFSETS[era] + (1 if year == "元" else int(year)))
    raise ValueError("指数の基準年の行が見つかりません")


def _index_type(rows: list[list[str]]) -> str:
    """表題の行から指数の種類を引く。表題に種類の名前が無ければ止める。"""
    table = _table_name(rows)
    index_type = _INDEX_TYPES.get(table or "")
    if index_type is None:
        raise ValueError(f"指数の表ではありません: {table}")
    title = next(
        _normalize(row[0]).replace(" ", "")
        for row in rows
        if row and _normalize(row[0]).startswith(table)
    )
    if _normalize(index_type) not in title:
        raise ValueError(f"{table} の表題が {index_type} ではありません: {title}")
    return index_type


def _industry_columns(headers: list[str], header: list[str]) -> list[tuple[str, int]]:
    """産業の列の見出しから (産業, 列位置) を取り出す。産業は「<符号> <原典の産業名>」にする。"""
    if headers[: len(header)] != header:
        raise ValueError(f"ヘッダーを認識できません: {headers}")
    industry_headers = headers[len(header) :]
    if not industry_headers:
        raise ValueError(f"産業の列がありません: {headers}")

    columns = []
    for offset, industry in enumerate(industry_headers):
        code = _INDUSTRY_CODES.get(_normalize(industry))
        if code is None:
            raise ValueError(f"産業符号が分かりません: {industry}")
        columns.append((f"{code} {industry}", len(header) + offset))
    return columns


def _parse(
    text: str,
    report_year: int,
    header: list[str] = _HEADER,
    value_keys: list[str] = _VALUE_KEYS,
) -> list[dict]:
    """年報の第13〜21表の CSV から公表年の行を取り出し、産業ごとの行に分ける。

    指数の行と、同じ年平均・月の前年比・前年同月比の行を1行にまとめる。
    前年比の行が無い期間は change_rate を空文字にする。表末尾の空行・表題の行は
    西暦年が数字でないので落ちる。値は原典の文字列のまま（「×」「x」「ｘ」は秘匿、「－」は該当なし）。
    """
    rows = list(csv.reader(text.splitlines()))
    if not rows:
        raise ValueError("空のファイルです")
    headers = [h.strip() for h in rows[0]]
    columns = _industry_columns(headers, header)
    index_type = _index_type(rows)
    base_year = _base_year(rows)
    index_key, change_key = value_keys

    # (事業所規模, 年平均・月) → {"index": 行, "change": 行}
    periods: dict[tuple[str, str], dict[str, list[str]]] = {}
    for row in rows[1:]:
        if len(row) < len(headers):
            continue
        size, _, year, label = (v.strip() for v in row[: len(header)])
        if not year.isdigit() or int(year) != report_year:
            continue
        changed = _CHANGE_RE.match(_normalize(label))
        period = changed.group(1) if changed else _normalize(label)
        kind = "change" if changed else "index"
        entry = periods.setdefault((_normalize(size), period), {})
        if kind in entry:
            raise ValueError(f"同じ期間の行が重なっています: {size} {year} {label}")
        entry[kind] = row

    records = []
    for (size, period), entry in periods.items():
        if "index" not in entry:
            raise ValueError(f"指数の行がありません: {size} {report_year} {period}")
        for industry, position in columns:
            change = entry.get("change")
            records.append(
                {
                    "report_year": str(report_year),
                    "index_type": index_type,
                    "base_year": base_year,
                    "establishment_size": size,
                    "industry": industry,
                    "year": str(report_year),
                    "period": period,
                    index_key: entry["index"][position].strip(),
                    change_key: change[position].strip() if change else "",
                }
            )
    return records


def download_labour_index(dest_dir: str) -> None:
    """各年の年報から第13〜21表を取得し、公表年の行を指数の種類・産業ごとに NDJSON に出力する。"""
    download_annual_tables(
        dest_dir, _TABLES, _HEADER, _VALUE_KEYS, _OUTPUT_FILENAME, parse=_parse
    )
