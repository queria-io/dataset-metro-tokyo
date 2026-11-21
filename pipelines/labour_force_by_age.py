"""東京都「東京の労働力」年平均の第3表（年齢階級別就業状態）のダウンロード。

東京の労働力の年平均の第3表は、15歳以上人口・労働力人口・就業者数・完全失業者数・
非労働力人口（千人）と労働力人口比率・就業率・完全失業率（％）を年齢階級別に持つ。
男女計・男・女で別のファイル（…0301.csv・…0302.csv・…0303.csv）に分かれている。
各年の表には直近の約10年分（2004〜2010年の表は1997年から）が載るので、
すべての年の表を取り込み、年ごとにどの年の表から取った値かを残す。どの年の表の値を
使うかは dbt 側で決める（基準人口の切り替えで後の年の表の値が改訂されている）。

CSV は 1行 = 区分 × 年（「労働力人口／平成27年」など）、列 = 実数・対前年増減数・
対前年増減率 × 年齢階級（「実数／15～24歳（千人、％）」など）。ここでは実数の列だけを
年齢階級ごとの行に分ける。対前年増減数・増減率は実数の差と比なので取り込まない。
2020〜2022年の表は西暦の列が無いので、列は見出しで読む。

各年のページは一覧ページから、CSV は各年のページのリンクのうちファイル名が
0301.csv・0302.csv・0303.csv で終わるものから解決し、表題の行で第3表であることと
男女を確かめる。2003年の表は四半期を含む別の形なので、2004年の表から取り込む。

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

# ファイル名の末尾と男女の対応
_FILES = {"0301": "男女計", "0302": "男", "0303": "女"}
# 「第3表 年齢階級別就業状態(男女計)」。2004〜2008年の表は「年齢階層別」
_TITLE_RE = re.compile(r"^第3表\s*年齢階[級層]別就業状態\((男女計|男|女)\)$")
# 「実数／15～24歳（千人、％）」。男の表は「実数／15～24歳／（千人、％）」
_VALUE_HEADER_RE = re.compile(r"^実数／(.+?)／?（千人、％）$")
_ITEMS = (
    "15歳以上人口",
    "労働力人口",
    "就業者数",
    "完全失業者数",
    "非労働力人口",
    "労働力人口比率",
    "就業率",
    "完全失業率",
)

_SOURCE_FILENAME = "source.ndjson"
_OUTPUT_FILENAME = "labour_force_by_age.ndjson"


def _title_sex(rows: list[list[str]]) -> str | None:
    """CSV の末尾に置かれた表題の行から男女を取り出す。第3表でなければ None。"""
    for row in rows:
        if not row:
            continue
        matched = _TITLE_RE.match(_normalize(row[0]))
        if matched:
            return matched.group(1)
    return None


def _parse(text: str, report_year: int, sex: str) -> list[dict]:
    """第3表の CSV から実数の列を取り出し、区分 × 年 × 年齢階級の行に分ける。

    年齢階級は原典の見出しのまま、値は原典の文字列のまま。
    """
    rows = list(csv.reader(text.splitlines()))
    if not rows:
        raise ValueError("空のファイルです")
    headers = [h.strip() for h in rows[0]]
    has_western_year = len(headers) > 1 and _normalize(headers[1]).startswith("西暦")
    first_value = 2 if has_western_year else 1
    columns = []
    for index, header in enumerate(headers[first_value:], start=first_value):
        matched = _VALUE_HEADER_RE.match(header)
        if matched:
            columns.append((index, matched.group(1)))
    if [age for _, age in columns][:1] != ["総数"] or len(columns) < 2:
        raise ValueError(f"ヘッダーを認識できません: {headers}")

    records = []
    for row in rows[1:]:
        if not row or "／" not in row[0]:
            continue
        item, label = row[0].strip().split("／", 1)
        if item not in _ITEMS:
            raise ValueError(f"区分を認識できません: {row[0]}")
        year = _year(label)
        if has_western_year and row[1].strip() != str(year):
            raise ValueError(f"和暦と西暦が合いません: {row[:2]}")
        if len(row) < len(headers):
            raise ValueError(f"列の数が見出しと合いません: {row[0]}")
        for index, age_group in columns:
            records.append(
                {
                    "report_year": str(report_year),
                    "year": str(year),
                    "sex": sex,
                    "age_group": age_group,
                    "item": item,
                    "value": row[index].strip(),
                }
            )
    return records


def download_labour_force_by_age(dest_dir: str) -> None:
    """各年の年平均のページから第3表を取得し、男女 × 区分 × 年 × 年齢階級の行を NDJSON に出力する。"""
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)

    pages = _annual_pages(_get(INDEX_URL))
    if not pages:
        raise RuntimeError(f"年平均のページを見つけられません: {INDEX_URL}")

    records = []
    sources = []
    fetched_at = datetime.now(UTC).isoformat()
    for report_year, page_url in pages:
        html = _get(page_url)
        for suffix, sex in _FILES.items():
            links = re.findall(rf'href="([^"]+{suffix}\.csv)"', html, re.IGNORECASE)
            if len(links) != 1:
                raise RuntimeError(
                    f"第3表（{sex}）の CSV を1つに決められません: {page_url} {links}"
                )
            url = urljoin(page_url, links[0])
            text = _get(url)
            title_sex = _title_sex(list(csv.reader(text.splitlines())))
            if title_sex != sex:
                raise RuntimeError(
                    f"{url} は第3表（{sex}）ではありません（{title_sex}）"
                )
            parsed = _parse(text, report_year, sex)
            if not parsed:
                raise RuntimeError(f"{report_year}年の表から行を取り出せません: {url}")
            records.extend(parsed)
            sources.append(
                {
                    "report_year": str(report_year),
                    "sex": sex,
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
        f"  labour_force_by_age: {len(records)} rows / {pages[0][0]}-{pages[-1][0]}"
    )
