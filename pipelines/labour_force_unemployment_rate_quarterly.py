"""東京都「東京の労働力」四半期平均の参考表（東京都、南関東及び全国の完全失業率）のダウンロード。

年平均の参考表（pipelines/labour_force_unemployment_rate.py）と同じ表が、各四半期平均の
ページにも付く。各四半期の参考表には1997年からの四半期の値が載る（年ごとの値も載るが、
年平均の参考表と重なるので取り込まない）ので、すべての四半期の表を取り込み、
行ごとにどの年・四半期の表から取った値かを残す。どの表の値を使うかは dbt 側で決める
（後の表で改訂された値がある）。

CSV は 1行 = 四半期（「完全失業率／令和７年４～６月」など）、列 = 地域（東京都・南関東・全国）×
男女（男女計・男・女）。ここでは四半期の行を地域 × 男女の行に分けるところまでを行い、
型変換は dbt 側で行う。「対前年同期増減数」の行は実数の差なので取り込まない。
2011年の表にある全国の「岩手県、宮城県及び福島県を除く」列も取り込まない。

各四半期のページは一覧ページから、CSV は各ページのリンクのうちファイル名が 0000.csv で
終わるものから解決し、表題の行で参考表であることを確かめる。

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
from pipelines.labour_force import INDEX_URL
from pipelines.labour_force_quarterly import _quarter_pages
from pipelines.labour_force_unemployment_rate import (
    _COLUMN_RE,
    _CSV_LINK_RE,
    _ERA_OFFSET,
    _ERA_RE,
    _is_reference_table,
    _normalize,
)
from shared.fetch import fetch, replacing

logger = logging.getLogger("pipelines")

# 「平成9年1～3月平均」「令和2年(2020年)4～6月」など。正規化（NFKC）後は ～ が ~ になる
_QUARTER_RE = re.compile(r"(\d{1,2})~(\d{1,2})月")

_SOURCE_FILENAME = "source.ndjson"
_OUTPUT_FILENAME = "labour_force_unemployment_rate_quarterly.ndjson"


def _get(url: str) -> str:
    return fetch(url, user_agent=USER_AGENT).decode("utf-8-sig")


def _year_quarter(label: str) -> tuple[int, int] | None:
    """「完全失業率／平成31年・令和元年4～6月平均」から (西暦, 四半期) を出す。

    月の範囲が無い行（年平均）は None。「平成31年・令和元年」は先に現れる平成31年で 2019 になる。
    """
    text = _normalize(label)
    month = _QUARTER_RE.search(text)
    if not month:
        return None
    start, end = int(month.group(1)), int(month.group(2))
    if end - start != 2 or start not in (1, 4, 7, 10):
        raise ValueError(f"四半期の範囲を読み取れません: {label}")
    era = _ERA_RE.search(text)
    if not era:
        raise ValueError(f"年を読み取れません: {label}")
    name, number = era.groups()
    year = _ERA_OFFSET[name] + (1 if number == "元" else int(number))
    return year, (start - 1) // 3 + 1


def _parse(text: str, report_year: int, report_quarter: int) -> list[dict]:
    """参考表の CSV から四半期の実数の行を取り出し、地域 × 男女の行に分ける。

    値は原典の文字列のまま（「…」は該当なし）。
    """
    rows = list(csv.reader(text.splitlines()))
    if not rows:
        raise ValueError("空のファイルです")
    headers = [_normalize(h) for h in rows[0]]
    columns = {}
    for i, header in enumerate(headers):
        matched = _COLUMN_RE.match(header)
        if matched:
            columns[i] = matched.groups()
    if len(columns) != 9:
        raise ValueError(f"ヘッダーを認識できません: {headers}")
    has_western_year = len(headers) > 1 and headers[1].startswith("西暦")

    records = []
    for row in rows[1:]:
        if not row or not _normalize(row[0]).startswith("完全失業率"):
            continue
        parsed = _year_quarter(row[0])
        if parsed is None:
            continue
        year, quarter = parsed
        if has_western_year and row[1].strip() and row[1].strip() != str(year):
            raise ValueError(f"和暦と西暦が合いません: {row[:3]}")
        for i, (area, sex) in columns.items():
            records.append(
                {
                    "report_year": str(report_year),
                    "report_quarter": str(report_quarter),
                    "year": str(year),
                    "quarter": str(quarter),
                    "area": area,
                    "sex": sex,
                    "value": row[i].strip() if i < len(row) else "",
                }
            )
    return records


def download_labour_force_unemployment_rate_quarterly(dest_dir: str) -> None:
    """各四半期平均のページから参考表を取得し、四半期 × 地域 × 男女の行を NDJSON に出力する。"""
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)

    pages = _quarter_pages(_get(INDEX_URL))
    if not pages:
        raise RuntimeError(f"四半期平均のページを見つけられません: {INDEX_URL}")

    records = []
    sources = []
    fetched_at = datetime.now(UTC).isoformat()
    for report_year, report_quarter, page_url in pages:
        links = sorted(set(_CSV_LINK_RE.findall(_get(page_url))))
        if len(links) != 1:
            raise RuntimeError(f"参考表の CSV を1つに決められません: {page_url} {links}")
        url = urljoin(page_url, links[0])
        text = _get(url)
        if not _is_reference_table(list(csv.reader(text.splitlines()))):
            raise RuntimeError(f"{url} は参考表ではありません")
        parsed = _parse(text, report_year, report_quarter)
        if not parsed:
            raise RuntimeError(
                f"{report_year}年{report_quarter}四半期の表から行を取り出せません: {url}"
            )
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
        f"  labour_force_unemployment_rate_quarterly: {len(records)} rows"
        f" / {first[0]}Q{first[1]}-{last[0]}Q{last[1]}"
    )
