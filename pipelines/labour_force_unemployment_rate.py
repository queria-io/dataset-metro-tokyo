"""東京都「東京の労働力」年平均の参考表（東京都、南関東及び全国の完全失業率）のダウンロード。

東京の労働力の年平均には、東京都・南関東・全国の完全失業率を男女別に並べた参考表が付く。
各年の参考表には直近の約10年分（2004〜2010年の表は1997年から）が載るので、
すべての年の表を取り込み、年ごとにどの年の表から取った値かを残す。どの年の表の値を
使うかは dbt 側で決める（後の年の表で改訂された値がある）。

CSV は 1行 = 年（「実数／平成27年」「対前年増減数／令和７年」など）、
列 = 地域（東京都・南関東・全国）× 男女（男女計・男・女）。ここでは実数の行を
地域 × 男女の行に分けるところまでを行い、型変換は dbt 側で行う。
対前年増減数の行は実数の差なので取り込まない。2011年の表にある全国の
「岩手県、宮城県及び福島県を除く」列も取り込まない（後の年の表に全国の値が載る）。

各年のページは一覧ページから、CSV は各年のページのリンクのうち
ファイル名が 0000.csv で終わるものから解決し、表題の行で参考表であることを確かめる。
2003年の表は四半期を含む別の形なので、2004年の表から取り込む（1997年からの値が載る）。

データソース: 東京都の統計
https://www.toukei.metro.tokyo.lg.jp/roudou/rd-index.htm
"""

import csv
import json
import logging
import re
import unicodedata
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urljoin

from pipelines.labour_earnings import USER_AGENT
from pipelines.labour_force import INDEX_URL
from shared.fetch import fetch, replacing

logger = logging.getLogger("pipelines")

# 年平均のページ（/roudou/2025/rd25qd1000.htm など）
_ANNUAL_LINK_RE = re.compile(r'href="(/roudou/(\d{4})/rd\d{2}qd1000\.htm)"')
_CSV_LINK_RE = re.compile(r'href="([^"]+0000\.csv)"', re.IGNORECASE)
# 「東京都／男女計（％、ポイント）」。2011年の表の「全国／男女計（岩手県…を除く）」は対象外
_COLUMN_RE = re.compile(r"^(東京都|南関東|全国)/(男女計|男|女)\(%")
_ERA_RE = re.compile(r"(平成|令和)(\d+|元)年")
_ERA_OFFSET = {"平成": 1988, "令和": 2018}

_FIRST_REPORT_YEAR = 2004

_SOURCE_FILENAME = "source.ndjson"
_OUTPUT_FILENAME = "labour_force_unemployment_rate.ndjson"


def _get(url: str) -> str:
    return fetch(url, user_agent=USER_AGENT).decode("utf-8-sig")


def _normalize(text: str) -> str:
    return unicodedata.normalize("NFKC", text).strip()


def _annual_pages(index_html: str) -> list[tuple[int, str]]:
    """一覧ページから (年, 年平均のページ URL) を取り出す。"""
    pages = {
        int(year): urljoin(INDEX_URL, path)
        for path, year in _ANNUAL_LINK_RE.findall(index_html)
    }
    return sorted(
        (year, url) for year, url in pages.items() if year >= _FIRST_REPORT_YEAR
    )


def _is_reference_table(rows: list[list[str]]) -> bool:
    """表題の行（「参考表　東京都、南関東及び全国の完全失業率」）があるかを見る。"""
    return any(
        row and row[0].startswith("参考") and "完全失業率" in row[0] for row in rows
    )


def _year(label: str) -> int:
    """「実数／平成31年・令和元年平均」などの和暦から西暦を出す。

    「平成31年・令和元年」は先に現れる平成31年で 2019 になる。
    """
    matched = _ERA_RE.search(_normalize(label))
    if not matched:
        raise ValueError(f"年を読み取れません: {label}")
    era, number = matched.groups()
    return _ERA_OFFSET[era] + (1 if number == "元" else int(number))


def _parse(text: str, report_year: int) -> list[dict]:
    """参考表の CSV から実数の行を取り出し、地域 × 男女の行に分ける。

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
        if not row or not row[0].strip().startswith("実数"):
            continue
        year = _year(row[0])
        if has_western_year and row[1].strip() != str(year):
            raise ValueError(f"和暦と西暦が合いません: {row[:2]}")
        for i, (area, sex) in columns.items():
            records.append(
                {
                    "report_year": str(report_year),
                    "year": str(year),
                    "area": area,
                    "sex": sex,
                    "value": row[i].strip() if i < len(row) else "",
                }
            )
    return records


def download_labour_force_unemployment_rate(dest_dir: str) -> None:
    """各年の年平均のページから参考表を取得し、年 × 地域 × 男女の行を NDJSON に出力する。"""
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)

    pages = _annual_pages(_get(INDEX_URL))
    if not pages:
        raise RuntimeError(f"年平均のページを見つけられません: {INDEX_URL}")

    records = []
    sources = []
    fetched_at = datetime.now(UTC).isoformat()
    for report_year, page_url in pages:
        links = _CSV_LINK_RE.findall(_get(page_url))
        if len(links) != 1:
            raise RuntimeError(f"参考表の CSV を1つに決められません: {page_url} {links}")
        url = urljoin(page_url, links[0])
        text = _get(url)
        if not _is_reference_table(list(csv.reader(text.splitlines()))):
            raise RuntimeError(f"{url} は参考表ではありません")
        parsed = _parse(text, report_year)
        if not parsed:
            raise RuntimeError(f"{report_year}年の表から行を取り出せません: {url}")
        records.extend(parsed)
        sources.append(
            {
                "report_year": str(report_year),
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

    logger.info(
        f"  labour_force_unemployment_rate: {len(records)} rows"
        f" / {pages[0][0]}-{pages[-1][0]}"
    )
