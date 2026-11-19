"""東京都「東京の労働力」年平均の第6表（主な職業別就業者数）のダウンロード。

東京の労働力の年平均の第6表は、就業者数（千人）を主な職業（専門的・技術的職業従事者・
事務従事者・販売従事者・サービス職業従事者・生産工程従事者・運搬・清掃・包装等従事者・
その他）別・男女別に持つ。2012年の表から載り、各年の表には直近の3年分が載るので、
すべての年の表を取り込み、年ごとにどの年の表から取った値かを残す。どの年の表の値を
使うかは dbt 側で決める（基準人口の切り替えで後の年の表の値が改訂されている）。

CSV は 1行 = 男女 × 年（「実数／男女計／令和７年」など）、列 = 職業（「事務従事者（千人）」
など）。ここでは実数の行を職業ごとの行に分ける。対前年増減数の行は実数の差なので
取り込まない。2020〜2022年の表は西暦の列が無いので、列は見出しで読む。

各年のページは一覧ページから、CSV は各年のページのリンクのうちファイル名が
0600.csv で終わるものから解決し、表題の行で第6表（主な職業別就業者数）であることを
確かめる。2011年までの表の 0600.csv は別の表（企業の従業者規模別雇用者数）なので、
2012年の表から取り込む。

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

_FIRST_REPORT_YEAR = 2012
_CSV_LINK_RE = re.compile(r'href="([^"]+0600\.csv)"', re.IGNORECASE)
# 「第６表　主な職業別就業者数」。2022年の表からは「第 ６ 表」
_TITLE_RE = re.compile(r"^第\s*6\s*表\s*主な職業別就業者数$")
_SEXES = ("男女計", "男", "女")
# 「事務従事者（千人）」
_VALUE_HEADER_RE = re.compile(r"^(.+)\(千人\)$")
_OCCUPATIONS = (
    "専門的・技術的職業従事者",
    "事務従事者",
    "販売従事者",
    "サービス職業従事者",
    "生産工程従事者",
    "運搬・清掃・包装等従事者",
    "その他(左記以外のもの)",
)

_SOURCE_FILENAME = "source.ndjson"
_OUTPUT_FILENAME = "labour_force_by_occupation.ndjson"


def _is_occupation_table(rows: list[list[str]]) -> bool:
    """CSV の末尾に置かれた表題の行が第6表（主な職業別就業者数）かを見る。"""
    return any(row and _TITLE_RE.match(_normalize(row[0])) for row in rows)


def _parse(text: str, report_year: int) -> list[dict]:
    """第6表の CSV から実数の行を取り出し、男女 × 年 × 職業の行に分ける。

    職業は見出しを NFKC で正規化して「（千人）」を外したもの、値は原典の文字列のまま。
    """
    rows = list(csv.reader(text.splitlines()))
    if not rows:
        raise ValueError("空のファイルです")
    headers = [h.strip() for h in rows[0]]
    has_western_year = len(headers) > 1 and _normalize(headers[1]).startswith("西暦")
    first_value = 2 if has_western_year else 1
    occupations = []
    for header in headers[first_value:]:
        matched = _VALUE_HEADER_RE.match(_normalize(header))
        occupations.append(matched.group(1) if matched else None)
    if tuple(occupations) != _OCCUPATIONS:
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
        if len(values) != len(occupations):
            raise ValueError(f"列の数が見出しと合いません: {row[0]}")
        for occupation, value in zip(occupations, values, strict=True):
            records.append(
                {
                    "report_year": str(report_year),
                    "year": str(year),
                    "sex": sex,
                    "occupation": occupation,
                    "value": value.strip(),
                }
            )
    return records


def download_labour_force_by_occupation(dest_dir: str) -> None:
    """各年の年平均のページから第6表を取得し、男女 × 年 × 職業の行を NDJSON に出力する。"""
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)

    pages = [
        (year, url)
        for year, url in _annual_pages(_get(INDEX_URL))
        if year >= _FIRST_REPORT_YEAR
    ]
    if not pages:
        raise RuntimeError(f"年平均のページを見つけられません: {INDEX_URL}")

    records = []
    sources = []
    fetched_at = datetime.now(UTC).isoformat()
    for report_year, page_url in pages:
        links = _CSV_LINK_RE.findall(_get(page_url))
        if len(links) != 1:
            raise RuntimeError(f"第6表の CSV を1つに決められません: {page_url} {links}")
        url = urljoin(page_url, links[0])
        text = _get(url)
        if not _is_occupation_table(list(csv.reader(text.splitlines()))):
            raise RuntimeError(f"{url} は第6表（主な職業別就業者数）ではありません")
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
        f"  labour_force_by_occupation: {len(records)} rows"
        f" / {pages[0][0]}-{pages[-1][0]}"
    )
