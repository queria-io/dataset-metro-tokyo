"""東京都「東京の労働力」（労働力調査結果）年平均の第1表のダウンロード。

東京都総務局統計部が労働力調査の東京都分を集計して公表する「東京の労働力」から、
年平均の第1表「就業状態別15歳以上人口、産業別就業者数及び完全失業者数」を取り込む。

CSV は 1行 = 区分（「〔就業状態〕／労働力人口／就業者数」のように見出しを「／」で
つないだ文字列）、列 = 男女計・男・女 × 実数・前年・対前年増減数・対前年増減率。
ここでは男女を行に分けるところまでを行い、区分の分解と型変換は dbt 側で行う。
前年の値は、基準人口の切り替えや産業分類の改定があった年は前年の表の実数と違う
（その年の基準で遡って計算し直した値）ので、そのまま残す。

各年のページは一覧ページから、CSV は各年のページの先頭のリンクから解決し、
表題の行で第1表であることを確かめる。2003年の第1表は1997年からの時系列で
形が違うので、2004年から取り込む。

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

from pipelines.labour_earnings import _fetch, _normalize

logger = logging.getLogger("pipelines")

INDEX_URL = "https://www.toukei.metro.tokyo.lg.jp/roudou/rd-index.htm"

# 年平均のページ（/roudou/2025/rd25qd1000.htm など）
_ANNUAL_LINK_RE = re.compile(r'href="(/roudou/(\d{4})/rd\d{2}qd1000\.htm)"')
_CSV_LINK_RE = re.compile(r'href="([^"]+\.csv)"', re.IGNORECASE)

_FIRST_YEAR = 2004
_TABLE = "第1表"

_SEXES = ["男女計", "男", "女"]
_VALUE_KEYS = ["value", "previous_year_value", "change", "change_rate"]

_SOURCE_FILENAME = "source.ndjson"
_OUTPUT_FILENAME = "labour_force.ndjson"


def _annual_pages(index_html: str) -> list[tuple[int, str]]:
    """一覧ページから (年, 年平均のページ URL) を取り出す。"""
    pages = {
        int(year): urljoin(INDEX_URL, path)
        for path, year in _ANNUAL_LINK_RE.findall(index_html)
    }
    return sorted((year, url) for year, url in pages.items() if year >= _FIRST_YEAR)


def _table_name(rows: list[list[str]]) -> str | None:
    """CSV の末尾に置かれた表題の行から「第1表」などを取り出す。"""
    for row in rows:
        if not row:
            continue
        matched = re.match(r"第\d+表", _normalize(row[0]))
        if matched:
            return matched.group(0)
    return None


def _check_header(headers: list[str]) -> None:
    """区分の後に 男女計・男・女 × 実数・前年・増減数・増減率 の12列が並ぶことを確かめる。

    増減数・増減率の見出しは年によって「増減」「比」と揺れるので、男女と並びだけを見る。
    """
    expected = [
        f"{sex}／{kind}"
        for sex in _SEXES
        for kind in ("実数", "前年", "対前年／増減", "対前年／")
    ]
    if (
        len(headers) < 13
        or headers[0] != "区分"
        or not all(h.startswith(e) for h, e in zip(headers[1:13], expected))
    ):
        raise ValueError(f"ヘッダーを認識できません: {headers}")


def _parse(text: str, year: int) -> list[dict]:
    """第1表の CSV から区分ごとの行を取り出し、男女ごとの行に分ける。

    表末尾の空行・表題・注記の行は値の列が空なので落ちる。値は原典の文字列のまま
    （「…」は該当なし、「-」は前年が無い区分）。
    """
    rows = list(csv.reader(text.splitlines()))
    if not rows:
        raise ValueError("空のファイルです")
    _check_header([h.strip() for h in rows[0]])

    records = []
    for row in rows[1:]:
        if len(row) < 13:
            continue
        item = row[0].strip()
        values = [v.strip() for v in row[1:13]]
        if not item or not any(values):
            continue
        for i, sex in enumerate(_SEXES):
            records.append(
                {
                    "year": str(year),
                    "item": item,
                    "sex": sex,
                    **dict(zip(_VALUE_KEYS, values[i * 4 : i * 4 + 4], strict=True)),
                }
            )
    return records


def download_labour_force(dest_dir: str) -> None:
    """各年の年平均のページから第1表を取得し、区分 × 男女の行を NDJSON に出力する。"""
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)

    pages = _annual_pages(_fetch(INDEX_URL))
    if not pages:
        raise RuntimeError(f"年平均のページを見つけられません: {INDEX_URL}")

    records = []
    sources = []
    fetched_at = datetime.now(UTC).isoformat()
    for year, page_url in pages:
        links = _CSV_LINK_RE.findall(_fetch(page_url))
        if not links:
            raise RuntimeError(f"CSV のリンクを見つけられません: {page_url}")
        url = urljoin(page_url, links[0])
        text = _fetch(url)
        table = _table_name(list(csv.reader(text.splitlines())))
        if table != _TABLE:
            raise RuntimeError(f"{url} は {_TABLE} ではありません（{table}）")
        parsed = _parse(text, year)
        if not parsed:
            raise RuntimeError(f"{year}年の行を取り出せません: {url}")
        records.extend(parsed)
        sources.append(
            {
                "year": str(year),
                "table": table,
                "url": url,
                "fetched_at": fetched_at,
                "row_count": len(parsed),
            }
        )

    with (dest / _OUTPUT_FILENAME).open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    with (dest / _SOURCE_FILENAME).open("w", encoding="utf-8") as f:
        for entry in sources:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    logger.info(
        f"  labour_force: {len(records)} rows / {pages[0][0]}-{pages[-1][0]}"
    )
