"""東京都「第3次産業活動指数」（月次）のダウンロード。

東京都総務局統計部が公表する第3次産業活動指数のうち、業種別の原指数（月次）と
季節調整済指数（月次）を取り込む。CSV は 1行 = 業種、列 = 月（「13-Jan」など）の横持ちなので、
業種 × 月 × 指数の種類の縦持ちに直す。型変換は dbt 側で行う。

CSV のファイル名は公表のたびに変わるので、東京都オープンデータカタログ（CKAN）の
パッケージから、リソース名で2つのファイルを解決する。

データソース: 東京都の統計
https://www.toukei.metro.tokyo.lg.jp/ssisuu/ss-index.htm
"""

import csv
import json
import logging
import re
from datetime import UTC, datetime
from pathlib import Path

from pipelines.labour_earnings import USER_AGENT
from shared.fetch import fetch, replacing

logger = logging.getLogger("pipelines")

PACKAGE_URL = (
    "https://catalog.data.metro.tokyo.lg.jp/api/3/action/package_show"
    "?id=t000003d1800000002"
)

# リソース名の先頭で指数の種類を決める（括弧内の「月次」で四半期・暦年・年度の表と区別する）
_RESOURCES = {
    "original": "業種別原指数（月次）",
    "seasonally_adjusted": "業種別季節調整済指数（月次）",
}

_MONTHS = {
    m: i + 1
    for i, m in enumerate(
        ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    )
}
_MONTH_RE = re.compile(r"^(\d{2})-([A-Z][a-z]{2})$")

_SOURCE_FILENAME = "source.ndjson"
_OUTPUT_FILENAME = "tertiary_activity_index.ndjson"


def _resource_urls(package: dict) -> dict[str, str]:
    """パッケージのリソースから、指数の種類ごとの CSV の URL を決める。"""
    urls = {}
    for index_type, prefix in _RESOURCES.items():
        found = [
            r["url"]
            for r in package["result"]["resources"]
            if r["name"].startswith(prefix + "（平成27年")
        ]
        if len(found) != 1:
            raise RuntimeError(f"{prefix} のリソースを1つに決められません: {found}")
        urls[index_type] = found[0]
    return urls


def _month_columns(header: list[str]) -> dict[int, tuple[int, int]]:
    """見出しの「13-Jan」を列位置 → (西暦, 月) に直す。2000年代として読む。"""
    columns = {}
    for i, name in enumerate(header):
        matched = _MONTH_RE.match(name.strip())
        if matched:
            columns[i] = (2000 + int(matched.group(1)), _MONTHS[matched.group(2)])
    if not columns:
        raise ValueError(f"月の列を認識できません: {header[:8]}")
    return columns


def _parse(text: str, index_type: str) -> list[dict]:
    """CSV から業種 × 月の行を取り出す。値は原典の文字列のまま（「―」は該当なし）。"""
    rows = list(csv.reader(text.splitlines()))
    if not rows or not rows[0] or not rows[0][0].startswith("品目階層"):
        raise ValueError("見出しを認識できません")
    months = _month_columns(rows[0])
    records = []
    for row in rows[1:]:
        if not row or not row[0].strip().isdigit():
            continue
        for i, (year, month) in months.items():
            records.append(
                {
                    "index_type": index_type,
                    "item_class": row[0].strip(),
                    "item_code": row[1].strip(),
                    "item_name": row[2].strip(),
                    "item_name_en": row[3].strip(),
                    "weight": row[4].strip(),
                    "year": str(year),
                    "month": str(month),
                    "value": row[i].strip() if i < len(row) else "",
                }
            )
    return records


def download_tertiary_activity_index(dest_dir: str) -> None:
    """月次の原指数と季節調整済指数を取得し、業種 × 月 × 指数の種類の行を NDJSON に出力する。"""
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)

    package = json.loads(fetch(PACKAGE_URL, user_agent=USER_AGENT))
    urls = _resource_urls(package)

    records = []
    sources = []
    fetched_at = datetime.now(UTC).isoformat()
    for index_type, url in urls.items():
        text = fetch(url, user_agent=USER_AGENT).decode("utf-8-sig")
        parsed = _parse(text, index_type)
        if not parsed:
            raise RuntimeError(f"{url} から行を取り出せません")
        records.extend(parsed)
        sources.append(
            {
                "index_type": index_type,
                "url": url,
                "fetched_at": fetched_at,
                "row_count": str(len(parsed)),
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

    logger.info(f"  tertiary_activity_index: {len(records)} rows")
