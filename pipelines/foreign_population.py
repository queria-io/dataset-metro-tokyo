"""東京都「外国人人口」時系列（各年1月1日現在）のダウンロード。

東京都総務局統計部が公表する、昭和54年（1979年）以降の各年1月1日現在の
外国人人口を、区市町村 × 国籍・地域で1ファイルにまとめた CSV を取り込む。
毎年1月分の公表時に最新年の列が追加されるため、毎回取得し直す。

CSV は 1行 = 国籍・地域 × 地域、列 = 年（和暦）の横持ち。ここでは表末尾の注記行の
除去と、年の列を西暦に直した縦持ちへの変換までを行い、型変換は dbt 側で行う。

データソース: 東京都オープンデータカタログ
https://catalog.data.metro.tokyo.lg.jp/
"""

import csv
import json
import logging
import re
from datetime import UTC, datetime
from pathlib import Path
from urllib.request import Request, urlopen

logger = logging.getLogger("pipelines")

USER_AGENT = "dataset-metro-tokyo"

SOURCE_URL = "https://www.toukei.metro.tokyo.lg.jp/gaikoku/ga000v0001.csv"

# 和暦の元年 -> 西暦の差
_ERA_OFFSETS = {"昭和": 1925, "平成": 1988, "令和": 2018}
_YEAR_RE = re.compile(r"^(昭和|平成|令和)(元|\d+)年$")

# 先頭4列（国籍・地域 / 地域階層 / 地域コード / 地域名）の後ろが年の列
_ID_COLUMNS = ["国・地域", "地域階層", "地域コード", "国・地域(人)"]

_SOURCE_FILENAME = "source.ndjson"
_OUTPUT_FILENAME = "foreign_population.ndjson"


def _to_western_year(label: str) -> int:
    """「昭和54年」「平成元年」などの見出しを西暦にする。"""
    matched = _YEAR_RE.match(label.strip())
    if matched is None:
        raise ValueError(f"年の見出しを認識できません: {label!r}")
    era, number = matched.groups()
    return _ERA_OFFSETS[era] + (1 if number == "元" else int(number))


def _parse(text: str) -> list[dict]:
    """横持ちの CSV を 国籍・地域 × 地域 × 年 の行に変換する。

    表末尾には表題・注記・地域階層の凡例が続くため、地域コードが5桁の数字である
    行だけを取り込む。値は原典の文字列のまま（桁区切りのカンマを含むことがある）。
    """
    rows = list(csv.reader(text.splitlines()))
    if not rows:
        raise ValueError("空のファイルです")

    headers = [h.replace("﻿", "").strip() for h in rows[0]]
    if headers[: len(_ID_COLUMNS)] != _ID_COLUMNS:
        raise ValueError(f"ヘッダーを認識できません: {headers[: len(_ID_COLUMNS)]}")
    years = [
        (index, label, _to_western_year(label))
        for index, label in enumerate(headers)
        if index >= len(_ID_COLUMNS) and label
    ]

    records = []
    for row in rows[1:]:
        if len(row) < len(_ID_COLUMNS):
            continue
        nationality, area_level, area_code, area_name = (
            value.strip() for value in row[: len(_ID_COLUMNS)]
        )
        if not re.fullmatch(r"\d{5}", area_code):
            continue
        for index, label, year in years:
            value = row[index].strip() if index < len(row) else ""
            # 国籍・地域の区分が無い年（「台湾（平成29年から）」の平成28年以前など）は空欄
            if not value:
                continue
            records.append(
                {
                    "year": str(year),
                    "year_label": label,
                    "area_level": area_level,
                    "area_code": area_code,
                    "area_name": area_name,
                    "nationality": nationality,
                    "population": value,
                }
            )
    return records


def download_foreign_population(dest_dir: str) -> None:
    """時系列 CSV を取得し、縦持ちに直した NDJSON を出力する。

    取得元 URL と行数は source.ndjson に記録する。
    """
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)

    req = Request(SOURCE_URL, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=60) as resp:
        text = resp.read().decode("utf-8-sig")
    (dest / "ga000v0001.csv").write_text(text, encoding="utf-8")

    records = _parse(text)
    if not records:
        raise RuntimeError(f"外国人人口の行を取り出せません: {SOURCE_URL}")

    with (dest / _OUTPUT_FILENAME).open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    with (dest / _SOURCE_FILENAME).open("w", encoding="utf-8") as f:
        entry = {
            "url": SOURCE_URL,
            "fetched_at": datetime.now(UTC).isoformat(),
            "row_count": len(records),
        }
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    years = sorted({int(r["year"]) for r in records})
    logger.info(f"  foreign_population: {len(records)} rows / {years[0]}-{years[-1]}")
