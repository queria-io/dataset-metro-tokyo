"""東京都「住民基本台帳による世帯と人口」（月次）のダウンロード。

東京都総務局統計部が毎月公開する区市町村別の世帯数・人口の CSV を、2001年1月分から
最新月分まで取り込む。公開済みの月にも数字の訂正が入ることがあり、公表実績では
3年近く前の月まで遡ることがあるため、直近 REFRESH_MONTHS か月分は毎回取得し直す。
それより古い月は取得済みのファイルを使う。

配布 URL は juukim/<西暦4桁>/jm<西暦下2桁><月>v0000_1.csv で、月は 1-9・a-c
（10-12月）。カタログの登録には抜けがある月があるため、取り込む月の範囲は
カタログから解決した最新月までを暦どおりに列挙して決める。

CSV のヘッダーは 2012年9月分を境に 2 種類ある（外国人住民の住民基本台帳への
記録開始に伴う様式変更）。ここでは行の構造解析（見出し行・表末尾の注記行の除去）と
列の標準キーへの割り当てまでを行い、型変換と重複行の除去は dbt 側で行う。

データソース: 東京都オープンデータカタログ
https://catalog.data.metro.tokyo.lg.jp/
"""

import csv
import json
import logging
import re
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

logger = logging.getLogger("pipelines")

USER_AGENT = "dataset-metro-tokyo"

# 一覧を公開している組織（CKAN の organization name）とデータセットの系列
ORG_NAME = "t000003"  # 東京都総務局
PACKAGE_TITLE_PREFIX = "住民基本台帳による世帯と人口"

BASE_URL = "https://www.toukei.metro.tokyo.lg.jp/juukim"

# 配布が始まる月（これより前は公開されていない）
FIRST_YEAR_MONTH = (2001, 1)

# 毎回取得し直す直近の月数。遡及訂正の公表実績（3年近く前の月まで）に合わせる
REFRESH_MONTHS = 36

# 同一ホストへの連続リクエストの間隔（秒）
REQUEST_INTERVAL = 0.3

# 配布ファイル名の月は 10-12 月が a-c
_MONTH_CHARS = "123456789abc"

# 月次ファイルの URL から年月を取り出す（_1.csv が世帯と人口の本表）
_URL_RE = re.compile(rf"/juukim/(\d{{4}})/jm\d{{2}}([{_MONTH_CHARS}])v0000_1\.csv$")

_SOURCE_FILENAME = "source.ndjson"
_OUTPUT_FILENAME = "resident_population.ndjson"

# ヘッダー（表記ゆれを吸収するため全角記号を除いた形で照合する）-> 標準キー。
# 2012年8月分までは外国人が外国人登録、日本人が住民基本台帳と別台帳のため、
# 世帯数の内訳（国籍別）と外国人の男女別が無い
_COLUMN_MAP = {
    "地域階層": "area_level",
    "地域コード": "area_code",
    "地域": "area_name",
    "人口総数（日本人＋外国人）": "population_total",
    "人口総数（A＋B）": "population_total",
    "前月人口総数との増減": "population_change",
    "人口／日本人／総数": "japanese_total",
    "人口／日本人／男": "japanese_male",
    "人口／日本人／女": "japanese_female",
    "人口／外国人／総数": "foreign_total",
    "人口／外国人／男": "foreign_male",
    "人口／外国人／女": "foreign_female",
    "世帯数／総世帯数": "household_total",
    "世帯数／日本人のみの世帯数": "household_japanese_only",
    "世帯数／外国人のみの世帯数": "household_foreign_only",
    "世帯数／日本人と外国人の複数国籍世帯数": "household_mixed",
    "住民基本台帳／世帯数": "household_total",
    "住民基本台帳／人口／総数（A）": "japanese_total",
    "住民基本台帳／人口／男": "japanese_male",
    "住民基本台帳／人口／女": "japanese_female",
    "外国人登録人口（B）": "foreign_total",
}

# 出力する標準キー（NDJSON の列順）
_KEYS = [
    "year_month",
    "area_level",
    "area_code",
    "area_name",
    "population_total",
    "population_change",
    "japanese_total",
    "japanese_male",
    "japanese_female",
    "foreign_total",
    "foreign_male",
    "foreign_female",
    "household_total",
    "household_japanese_only",
    "household_foreign_only",
    "household_mixed",
]


def _resolve_latest_year_month(packages_path: Path) -> tuple[int, int]:
    """カタログメタデータから公開済みの最新月を解決する。"""
    latest: tuple[int, int] | None = None

    with packages_path.open(encoding="utf-8") as f:
        for line in f:
            package = json.loads(line)
            if (package.get("organization") or {}).get("name") != ORG_NAME:
                continue
            if not (package.get("title") or "").startswith(PACKAGE_TITLE_PREFIX):
                continue
            for resource in package.get("resources") or []:
                matched = _URL_RE.search(resource.get("url") or "")
                if matched is None:
                    continue
                year = int(matched.group(1))
                month = _MONTH_CHARS.index(matched.group(2)) + 1
                if latest is None or (year, month) > latest:
                    latest = (year, month)

    if latest is None:
        raise RuntimeError(
            f"「{PACKAGE_TITLE_PREFIX}」の最新月を解決できません"
            f"（organization={ORG_NAME}）: {packages_path}"
        )
    return latest


def _iter_year_months(last: tuple[int, int]):
    """FIRST_YEAR_MONTH から last までの (年, 月) を順に返す。"""
    year, month = FIRST_YEAR_MONTH
    while (year, month) <= last:
        yield year, month
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)


def _source_url(year: int, month: int) -> str:
    return f"{BASE_URL}/{year}/jm{year % 100:02d}{_MONTH_CHARS[month - 1]}v0000_1.csv"


def _decode(data: bytes) -> str:
    """配布 CSV を文字列にする。月によって UTF-8 と cp932 が混在する。"""
    for encoding in ("utf-8-sig", "cp932"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError("UTF-8 でも cp932 でもデコードできません")


def _normalize_header(header: str) -> str:
    return header.replace("﻿", "").strip()


def _parse(text: str, year_month: str) -> tuple[list[dict], list[str]]:
    """月次 CSV を標準キーの行に変換する。

    表末尾には空行と注記行（表題・地域階層の凡例）が続くため、地域コードが
    5桁の数字である行だけを取り込む。
    """
    rows = list(csv.reader(text.splitlines()))
    if not rows:
        raise ValueError(f"{year_month}: 空のファイルです")

    headers = [_normalize_header(h) for h in rows[0]]
    unknown = [h for h in headers if h and h not in _COLUMN_MAP]
    keys = [_COLUMN_MAP.get(h) for h in headers]
    if "area_code" not in keys or "population_total" not in keys:
        raise ValueError(f"{year_month}: ヘッダーを認識できません: {headers}")

    records = []
    for row in rows[1:]:
        record = {"year_month": year_month}
        for key, value in zip(keys, row, strict=False):
            if key is not None:
                record[key] = value.strip()
        if not re.fullmatch(r"\d{5}", record.get("area_code") or ""):
            continue
        records.append({key: record.get(key) for key in _KEYS})

    return records, unknown


def download_resident_population(
    dest_dir: str, packages_path: str = "data/catalog/packages.ndjson"
) -> None:
    """月次 CSV を取得し、標準キーに正規化した NDJSON を出力する。

    直近 REFRESH_MONTHS か月分と未取得の月をダウンロードし、それより古い月は
    保存済みのファイルを読み直す。取り込んだ月と取得元 URL は source.ndjson に記録する。
    """
    dest = Path(dest_dir)
    csv_dir = dest / "csv"
    csv_dir.mkdir(parents=True, exist_ok=True)

    latest = _resolve_latest_year_month(Path(packages_path))
    logger.info(f"  latest month: {latest[0]}-{latest[1]:02d}")

    months = list(_iter_year_months(latest))
    refresh_from = (
        months[-REFRESH_MONTHS] if len(months) > REFRESH_MONTHS else months[0]
    )

    fetched_at = datetime.now(UTC).isoformat()
    entries = []
    records = []
    unknown_headers: set[str] = set()

    for year, month in months:
        year_month = f"{year}-{month:02d}"
        url = _source_url(year, month)
        path = csv_dir / f"{year}{month:02d}.csv"

        if path.exists() and (year, month) < refresh_from:
            text = path.read_text(encoding="utf-8")
            status = "cached"
        else:
            time.sleep(REQUEST_INTERVAL)
            req = Request(url, headers={"User-Agent": USER_AGENT})
            try:
                with urlopen(req, timeout=60) as resp:
                    data = resp.read()
            except HTTPError as e:
                # 未公開の月が混ざりうるため、取得できない月は記録して続ける。
                # 取得済みの月であれば保存済みのファイルをそのまま使う
                if not path.exists():
                    logger.warning(f"  {year_month}: skipped (HTTP {e.code})")
                    entries.append(
                        {
                            "year_month": year_month,
                            "url": url,
                            "fetched_at": fetched_at,
                            "status": f"http_{e.code}",
                            "row_count": None,
                        }
                    )
                    continue
                logger.warning(f"  {year_month}: HTTP {e.code}, using cached file")
                text = path.read_text(encoding="utf-8")
                status = "cached"
            else:
                text = _decode(data)
                path.write_text(text, encoding="utf-8")
                status = "downloaded"

        parsed, unknown = _parse(text, year_month)
        unknown_headers.update(unknown)
        records.extend(parsed)
        entries.append(
            {
                "year_month": year_month,
                "url": url,
                "fetched_at": fetched_at,
                "status": status,
                "row_count": len(parsed),
            }
        )
        if status == "downloaded":
            logger.info(f"  {year_month}: {len(parsed)} rows downloaded")

    if unknown_headers:
        # 様式変更で列が増えたときに気付けるよう警告する（取り込みは止めない）
        logger.warning(f"  unmapped headers: {sorted(unknown_headers)}")

    with (dest / _OUTPUT_FILENAME).open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    with (dest / _SOURCE_FILENAME).open("w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    months = sum(1 for e in entries if e["status"] != "http_404")
    logger.info(f"  resident_population: {len(records)} rows / {months} months")
