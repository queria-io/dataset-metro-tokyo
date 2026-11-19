"""東京都「東京の労働力」（労働力調査結果）四半期平均の第1表のダウンロード。

年平均の第1表（pipelines/labour_force.py）と同じ区分の表が、1〜3月・4〜6月・7〜9月・
10〜12月の四半期平均にもある。列の並びは年平均と同じで、前年の値と増減が
「前年同期」「対前年同期」になる。CSV の読み方は年平均と同じ処理を使い、
四半期（1〜4）の列を足す。

各四半期のページは一覧ページの rdYYed1000.htm（1〜3月）・fd（4〜6月）・gd（7〜9月）・
hd（10〜12月）から、CSV は各ページの先頭のリンクから解決し、表題の行で第1表で
あることを確かめる。一覧にある四半期平均は2003年7〜9月期からで、それより前の
ページは形が違う（ファイル名も別の規則）ので対象にならない。

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

from pipelines.labour_earnings import USER_AGENT
from pipelines.labour_force import INDEX_URL, _parse, _table_name
from shared.fetch import fetch, replacing

logger = logging.getLogger("pipelines")

# 四半期平均のページ（/roudou/2025/rd25ed1000.htm など）。e〜h が 1〜4 の四半期
_QUARTER_LINK_RE = re.compile(r'href="(/roudou/(\d{4})/rd\d{2}([efgh])d1000\.htm)"')
_QUARTERS = {"e": 1, "f": 2, "g": 3, "h": 4}
_CSV_LINK_RE = re.compile(r'href="([^"]+\.csv)"', re.IGNORECASE)

_TABLE = "第1表"
_VALUE_HEADERS = ("実数", "前年同期", "対前年同期／増減", "対前年同期／")

_SOURCE_FILENAME = "source.ndjson"
_OUTPUT_FILENAME = "labour_force_quarterly.ndjson"


def _get(url: str) -> str:
    return fetch(url, user_agent=USER_AGENT).decode("utf-8-sig")


def _quarter_pages(index_html: str) -> list[tuple[int, int, str]]:
    """一覧ページから (年, 四半期, 四半期平均のページ URL) を取り出す。"""
    pages = {
        (int(year), _QUARTERS[letter]): urljoin(INDEX_URL, path)
        for path, year, letter in _QUARTER_LINK_RE.findall(index_html)
    }
    return sorted((year, quarter, url) for (year, quarter), url in pages.items())


def _parse_quarter(text: str, year: int, quarter: int) -> list[dict]:
    """四半期平均の第1表の CSV を区分 × 男女の行に分け、四半期を足す。"""
    return [{**r, "quarter": str(quarter)} for r in _parse(text, year, _VALUE_HEADERS)]


def download_labour_force_quarterly(dest_dir: str) -> None:
    """各四半期平均のページから第1表を取得し、区分 × 男女の行を NDJSON に出力する。"""
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)

    pages = _quarter_pages(_get(INDEX_URL))
    if not pages:
        raise RuntimeError(f"四半期平均のページを見つけられません: {INDEX_URL}")

    records = []
    sources = []
    fetched_at = datetime.now(UTC).isoformat()
    for year, quarter, page_url in pages:
        links = _CSV_LINK_RE.findall(_get(page_url))
        if not links:
            raise RuntimeError(f"CSV のリンクを見つけられません: {page_url}")
        url = urljoin(page_url, links[0])
        text = _get(url)
        table = _table_name(list(csv.reader(text.splitlines())))
        if table != _TABLE:
            raise RuntimeError(f"{url} は {_TABLE} ではありません（{table}）")
        parsed = _parse_quarter(text, year, quarter)
        if not parsed:
            raise RuntimeError(f"{year}年{quarter}四半期の行を取り出せません: {url}")
        records.extend(parsed)
        sources.append(
            {
                "year": str(year),
                "quarter": str(quarter),
                "table": table,
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
        f"  labour_force_quarterly: {len(records)} rows"
        f" / {first[0]}Q{first[1]}-{last[0]}Q{last[1]}"
    )
