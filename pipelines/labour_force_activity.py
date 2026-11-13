"""東京都「東京の労働力」年平均の第2表（就業状態、活動状態別15歳以上人口）のダウンロード。

東京の労働力の年平均の第2表は、15歳以上人口を就業状態（労働力人口・就業者・完全失業者・
非労働力人口）と活動状態（主に仕事・通学のかたわらに仕事など）、従業上の地位（自営業主・
雇用者など）で分けた実数と、労働力人口比率・就業率・完全失業率を男女別に持つ。
各年の表には直近の約10年分（2004〜2010年の表は1997年から）が載るので、
すべての年の表を取り込み、年ごとにどの年の表から取った値かを残す。どの年の表の値を
使うかは dbt 側で決める（基準人口の切り替えで後の年の表の値が改訂されている）。

CSV は 1行 = 男女 × 年（「実数／男女計／平成27年」など）、列 = 区分（「15歳以上人口／
労働力人口／就業者数（千人）」のように見出しを「／」でつないだ文字列）。列の有無と並びは
年の表で違う（正規・非正規の職員・従業員は2013年の表から、就業率は2011年の表からなど）ので、
列は見出しで読む。ここでは実数の行を区分ごとの行に分けるところまでを行い、
見出しの単位の分離と型変換は dbt 側で行う。対前年増減数の行は実数の差なので取り込まない。

各年のページは一覧ページから、CSV は各年のページのリンクのうち
ファイル名が 0200.csv で終わるものから解決し、表題の行で第2表であることを確かめる。
2003年の表は四半期を含む別の形なので、2004年の表から取り込む（1997年からの値が載る）。

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
from pipelines.labour_force_unemployment_rate import (
    _annual_pages,
    _get,
    _normalize,
    _year,
)
from shared.fetch import replacing

logger = logging.getLogger("pipelines")

_CSV_LINK_RE = re.compile(r'href="([^"]+0200\.csv)"', re.IGNORECASE)
_TABLE = "第2表"
_SEXES = ("男女計", "男", "女")
# 値の列の見出しは「（千人）」か「（％、ポイント）」で終わる
_VALUE_HEADER_RE = re.compile(r"\((千人|%、ポイント)\)$")

_SOURCE_FILENAME = "source.ndjson"
_OUTPUT_FILENAME = "labour_force_activity.ndjson"


def _table_name(rows: list[list[str]]) -> str | None:
    """CSV の末尾に置かれた表題の行から「第2表」などを取り出す。"""
    for row in rows:
        if not row:
            continue
        matched = re.match(r"第\d+表", _normalize(row[0]))
        if matched:
            return matched.group(0)
    return None


def _parse(text: str, report_year: int) -> list[dict]:
    """第2表の CSV から実数の行を取り出し、男女 × 年 × 区分の行に分ける。

    区分は原典の見出しのまま、値は原典の文字列のまま（「…」は該当なし、
    「-」「－」は調べていない区分）。
    """
    rows = list(csv.reader(text.splitlines()))
    if not rows:
        raise ValueError("空のファイルです")
    headers = [h.strip() for h in rows[0]]
    has_western_year = len(headers) > 1 and _normalize(headers[1]).startswith("西暦")
    first_value = 2 if has_western_year else 1
    items = headers[first_value:]
    if not items or not all(_VALUE_HEADER_RE.search(_normalize(h)) for h in items):
        raise ValueError(f"ヘッダーを認識できません: {headers}")

    records = []
    for row in rows[1:]:
        if not row or not row[0].strip().startswith("実数"):
            continue
        parts = row[0].strip().split("／")
        if len(parts) != 3 or parts[1] not in _SEXES:
            raise ValueError(f"男女と年を読み取れません: {row[0]}")
        sex = parts[1]
        year = _year(parts[2])
        if has_western_year and row[1].strip() != str(year):
            raise ValueError(f"和暦と西暦が合いません: {row[:2]}")
        values = row[first_value:]
        if len(values) != len(items):
            raise ValueError(f"列の数が見出しと合いません: {row[0]}")
        for item, value in zip(items, values, strict=True):
            records.append(
                {
                    "report_year": str(report_year),
                    "year": str(year),
                    "sex": sex,
                    "item": item,
                    "value": value.strip(),
                }
            )
    return records


def download_labour_force_activity(dest_dir: str) -> None:
    """各年の年平均のページから第2表を取得し、男女 × 年 × 区分の行を NDJSON に出力する。"""
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
            raise RuntimeError(f"第2表の CSV を1つに決められません: {page_url} {links}")
        url = urljoin(page_url, links[0])
        text = _get(url)
        table = _table_name(list(csv.reader(text.splitlines())))
        if table != _TABLE:
            raise RuntimeError(f"{url} は {_TABLE} ではありません（{table}）")
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
        f"  labour_force_activity: {len(records)} rows"
        f" / {pages[0][0]}-{pages[-1][0]}"
    )
