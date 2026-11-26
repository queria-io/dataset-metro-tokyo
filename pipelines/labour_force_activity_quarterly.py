"""東京都「東京の労働力」四半期平均の第2表（就業状態、活動状態別15歳以上人口）のダウンロード。

四半期平均の第2表は、年平均の第2表（pipelines/labour_force_activity.py）と同じ区分を
四半期ごとに持つ。各四半期のページの表には、直近の約5年の四半期（2003〜2011年の表は
1997年からの年平均と2003年7〜9月期から）が載るので、すべてのページの表を取り込み、
どの四半期の表から取った値かを残す。どの表の値を使うかは dbt 側で決める。

CSV は 1行 = 年平均または四半期（「実数／令和７年４～６月」など）、列 = 男女 × 区分
（「男女計／１５歳以上人口／労働力人口（千人）」のように見出しを「／」でつないだ文字列）。
年と四半期は行のラベルから読む（西暦と四半期の列は2020年1〜3月期から2023年1〜3月期の
表に無い）。年平均の行は年平均の第2表と同じ値なので取り込まず、対前年・対前年同期増減数の
行は実数の差なので取り込まない。列の有無と並びは表で違うので、列は見出しで読む。

各四半期のページは一覧ページから、CSV は各ページのリンクのうちファイル名が 0200.csv で
終わるものから解決し、表題の行で第2表であることを確かめる。

データソース: 東京都の統計
https://www.toukei.metro.tokyo.lg.jp/roudou/rd-index.htm
"""

import csv
import json
import logging
import re
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urljoin

from pipelines.labour_force import INDEX_URL
from pipelines.labour_force_activity import _TABLE, _VALUE_HEADER_RE, _table_name
from pipelines.labour_force_quarterly import _get, _quarter_pages
from pipelines.labour_force_unemployment_rate import _normalize, _year
from shared.fetch import replacing

logger = logging.getLogger("pipelines")

_CSV_LINK_RE = re.compile(r'href="([^"]+0200\.csv)"', re.IGNORECASE)
# 見出しの先頭の男女。2018年の表までは「男／」「女／」、後の表は「男計／」「女計／」
_SEXES = {"男女計": "男女計", "男計": "男", "男": "男", "女計": "女", "女": "女"}
_MONTHS_RE = re.compile(r"(\d{1,2})[~〜～](\d{1,2})月")
_PAREN_YEAR_RE = re.compile(r"\((\d{4})年\)")

_SOURCE_FILENAME = "source.ndjson"
_OUTPUT_FILENAME = "labour_force_activity_quarterly.ndjson"


def _quarter_of(label: str) -> int | None:
    """行のラベルの「４～６月」などから四半期（1〜4）を出す。年平均の行は None。"""
    matched = _MONTHS_RE.search(_normalize(label))
    if not matched:
        return None
    start, end = int(matched.group(1)), int(matched.group(2))
    if start not in (1, 4, 7, 10) or end != start + 2:
        raise ValueError(f"四半期の月を読み取れません: {label}")
    return (start + 2) // 3


def _columns(headers: list[str], first_value: int) -> list[tuple[str, str]]:
    """値の列の見出しを (男女, 区分) に分ける。区分は原典の見出しから男女を除いたもの。"""
    columns = []
    for header in headers[first_value:]:
        sex_label, _, item = header.strip().partition("／")
        if sex_label not in _SEXES or not _VALUE_HEADER_RE.search(_normalize(item)):
            raise ValueError(f"ヘッダーを認識できません: {header}")
        columns.append((_SEXES[sex_label], item))
    if not columns:
        raise ValueError(f"ヘッダーを認識できません: {headers}")
    return columns


def _parse(text: str, report_year: int, report_quarter: int) -> list[dict]:
    """第2表の CSV から四半期の実数の行を取り出し、男女 × 四半期 × 区分の行に分ける。

    区分は原典の見出しのまま、値は原典の文字列のまま（「…」は該当なし、
    「-」「－」は調べていない区分）。
    """
    rows = list(csv.reader(text.splitlines()))
    if not rows:
        raise ValueError("空のファイルです")
    headers = [h.strip() for h in rows[0]]
    has_western_year = len(headers) > 1 and _normalize(headers[1]).startswith("西暦")
    first_value = 3 if has_western_year else 1
    if has_western_year and _normalize(headers[2]) != "四半期":
        raise ValueError(f"ヘッダーを認識できません: {headers[:3]}")
    columns = _columns(headers, first_value)

    records = []
    for row in rows[1:]:
        if not row or not row[0].strip().startswith("実数"):
            continue
        label = row[0].strip()
        quarter = _quarter_of(label)
        if quarter is None:
            continue
        year = _year(label)
        paren = _PAREN_YEAR_RE.search(_normalize(label))
        if paren and int(paren.group(1)) != year:
            raise ValueError(f"和暦と西暦が合いません: {label}")
        if has_western_year:
            if row[1].strip() != str(year) or _quarter_of(f"{row[2]}月") != quarter:
                raise ValueError(f"ラベルと西暦・四半期の列が合いません: {row[:3]}")
        values = row[first_value:]
        if len(values) != len(columns):
            raise ValueError(f"列の数が見出しと合いません: {label}")
        for (sex, item), value in zip(columns, values, strict=True):
            records.append(
                {
                    "report_year": str(report_year),
                    "report_quarter": str(report_quarter),
                    "year": str(year),
                    "quarter": str(quarter),
                    "sex": sex,
                    "item": item,
                    "value": value.strip(),
                }
            )
    return records


def _csv_url(page_url: str, page_html: str) -> str:
    """ページのリンクから第2表の CSV の URL を1つに決める（同じリンクが重なる年がある）。"""
    links = sorted(set(_CSV_LINK_RE.findall(page_html)))
    if len(links) != 1:
        raise RuntimeError(f"第2表の CSV を1つに決められません: {page_url} {links}")
    return urljoin(page_url, links[0])


def download_labour_force_activity_quarterly(dest_dir: str) -> None:
    """各四半期平均のページから第2表を取得し、男女 × 四半期 × 区分の行を NDJSON に出力する。"""
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)

    pages = _quarter_pages(_get(INDEX_URL))
    if not pages:
        raise RuntimeError(f"四半期平均のページを見つけられません: {INDEX_URL}")

    records = []
    sources = []
    fetched_at = datetime.now(UTC).isoformat()
    for report_year, report_quarter, page_url in pages:
        url = _csv_url(page_url, _get(page_url))
        text = _get(url)
        table = _table_name(list(csv.reader(text.splitlines())))
        if table != _TABLE:
            raise RuntimeError(f"{url} は {_TABLE} ではありません（{table}）")
        parsed = _parse(text, report_year, report_quarter)
        if not parsed:
            raise RuntimeError(f"{report_year}年{report_quarter}四半期の表から行を取り出せません: {url}")
        records.extend(parsed)
        sources.append(
            {
                "report_year": str(report_year),
                "report_quarter": str(report_quarter),
                "url": url,
                "fetched_at": fetched_at,
                "row_count": len(parsed),
            }
        )

    with replacing(dest / _OUTPUT_FILENAME) as partial:
        with partial.open("w", encoding="utf-8") as f:
            for record in records:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

    with replacing(dest / _SOURCE_FILENAME) as partial:
        with partial.open("w", encoding="utf-8") as f:
            for entry in sources:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    first, last = pages[0], pages[-1]
    logger.info(
        f"  labour_force_activity_quarterly: {len(records)} rows"
        f" / {first[0]}Q{first[1]}-{last[0]}Q{last[1]}"
    )
