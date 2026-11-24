"""東京都生計分析調査「都民のくらしむき」年報の長期時系列表1（主な支出及び対前年増加率、全世帯）のダウンロード。

長期時系列表1は1975年から最新年までを1つの CSV に収めている。
年報は年ごとにページがあり、各年の CSV には同じ表が最新年まで延びた形で載るので、
一覧ページから最新年の年報ページを解決し、そのページの長期時系列表1の CSV だけを取り込む。

CSV は 1行 = 年 × 指標（実数・対前年名目増加率・対前年実質増加率）、列 = 項目
（「生計支出／消費支出／食料（円）」のようにスラッシュで階層を区切り、末尾に単位を付ける）。
ここでは列を項目ごとの行に分けるところまでを行い、型変換は dbt 側で行う。

データソース: 東京都の統計
https://www.toukei.metro.tokyo.lg.jp/seikei/sb-index.htm
"""

import csv
import json
import logging
import re
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urljoin

from pipelines.labour_earnings import USER_AGENT
from shared.fetch import fetch, replacing

logger = logging.getLogger("pipelines")

INDEX_URL = "https://www.toukei.metro.tokyo.lg.jp/seikei/sb-index.htm"

# 年報のページ（/seikei/2025/sb25q00000.htm）。月報は sb25820000.htm のように q が付かない
_ANNUAL_LINK_RE = re.compile(r'href="(/seikei/(\d{4})/sb\d{2}q00000\.htm)"')
_CSV_LINK_RE = re.compile(r'href="([^"]+qv0001\.csv)"', re.IGNORECASE)
_UNIT_RE = re.compile(r"（([^（）]+)）$")

_MEASURES = {
    "jissu": "actual",
    "meimoku": "nominal_growth",
    "jissitu": "real_growth",
}
_FIXED_COLUMNS = 4  # 実数・増加率, 年次コード, 年次, 西暦（年）

_SOURCE_FILENAME = "source.ndjson"
_OUTPUT_FILENAME = "household_budget.ndjson"


def _get(url: str) -> str:
    return fetch(url, user_agent=USER_AGENT).decode("utf-8-sig")


def _latest_annual_page(index_html: str) -> tuple[int, str]:
    """一覧ページから最新年の年報ページ (年, URL) を取り出す。"""
    pages = {
        int(year): urljoin(INDEX_URL, path)
        for path, year in _ANNUAL_LINK_RE.findall(index_html)
    }
    if not pages:
        raise RuntimeError(f"年報のページを見つけられません: {INDEX_URL}")
    year = max(pages)
    return year, pages[year]


def _parse(text: str) -> list[dict]:
    """長期時系列表1の CSV を、年 × 指標 × 項目の行に分ける。

    値は原典の文字列のまま（「-」は該当なし、空欄は原典に値がないセル）。
    """
    rows = list(csv.reader(text.splitlines()))
    if not rows or not rows[0] or not rows[0][0].startswith("実数"):
        raise ValueError("ヘッダーを認識できません")
    if not any(row and row[0].startswith("長期時系列表１") for row in rows):
        raise ValueError("長期時系列表1ではありません")
    items = []
    for header in rows[0][_FIXED_COLUMNS:]:
        name = header.strip()
        matched = _UNIT_RE.search(name)
        if not matched:
            raise ValueError(f"単位を読み取れません: {header}")
        items.append((name[: matched.start()], matched.group(1)))

    records = []
    for row in rows[1:]:
        if not row or row[0] not in _MEASURES:
            continue
        year = row[3].strip()
        if not year.isdigit():
            raise ValueError(f"西暦を読み取れません: {row[:4]}")
        for (item, unit), value in zip(items, row[_FIXED_COLUMNS:], strict=False):
            records.append(
                {
                    "year": year,
                    "measure": _MEASURES[row[0]],
                    "item_path": item,
                    "unit": unit,
                    "value": value.strip(),
                }
            )
    return records


def download_household_budget(dest_dir: str) -> None:
    """最新年の年報から長期時系列表1を取得し、年 × 指標 × 項目の行を NDJSON に出力する。"""
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)

    report_year, page_url = _latest_annual_page(_get(INDEX_URL))
    links = _CSV_LINK_RE.findall(_get(page_url))
    if len(links) != 1:
        raise RuntimeError(f"長期時系列表1の CSV を1つに決められません: {page_url} {links}")
    url = urljoin(page_url, links[0])
    records = _parse(_get(url))
    if not records:
        raise RuntimeError(f"{report_year}年の表から行を取り出せません: {url}")

    with replacing(dest / _OUTPUT_FILENAME) as partial:
        with partial.open("w", encoding="utf-8") as f:
            for record in records:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

    with replacing(dest / _SOURCE_FILENAME) as partial:
        with partial.open("w", encoding="utf-8") as f:
            entry = {
                "report_year": str(report_year),
                "url": url,
                "fetched_at": datetime.now(UTC).isoformat(),
                "row_count": len(records),
            }
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    logger.info(f"  household_budget: {len(records)} rows / report {report_year}")
