"""東京都保健医療局の保健所台帳のダウンロード。

東京都が設置する保健所（八王子市・町田市を除く多摩地域、および島しょ）が保有する
台帳のうち、食品関係営業台帳（許可・届出）と環境衛生施設台帳（理容所・美容所・
旅館・クリーニング所）を取り込む。23区・八王子市・町田市はそれぞれが保健所を
設置しているため、この台帳には含まれない。

配布ページには Excel と CSV の両方が並び、リンクの URL は更新のたびに変わる
（同じ台帳でも版によって -5 と -1-7 が入れ替わる）。台帳名はリンクの直前の本文に
しか書かれていないので、リンクの位置より前の本文から最も近い台帳名を拾って
対応づける。6 種すべてが揃わなければ止める。

データソース: 東京都保健医療局「食品関係営業台帳」「環境衛生施設台帳」
https://www.hokeniryo.metro.tokyo.lg.jp/kenkou/hokenjo_daicho/shokuhineigyokyokadaicho
"""

import csv
import html
import json
import logging
import re
import time
from datetime import UTC, date, datetime
from pathlib import Path
from urllib.request import Request, urlopen

logger = logging.getLogger("pipelines")

USER_AGENT = "dataset-metro-tokyo"

# 台帳を公開している組織（CKAN の organization name / title）。
# ジオコーディングの突合キーに使うので ODS と同じ形で行に持たせる
ORG_CODE = "t000055"
ORG_TITLE = "東京都保健医療局"

BASE_URL = "https://www.hokeniryo.metro.tokyo.lg.jp"
INDEX_PATH = "/kenkou/hokenjo_daicho/shokuhineigyokyokadaicho"

REQUEST_INTERVAL = 0.5

# 台帳の種別 -> 配布ページの本文に現れる台帳名。
# 本文での出現順に並べる必要はないが、ここに無い台帳（医療機関・薬局）は取り込まない
_FOOD_LEDGERS = {
    "許可": "食品関係営業台帳（許可）",
    "届出": "食品関係営業台帳（届出）",
}
_SANITATION_LEDGERS = {
    "理容所": "理容所台帳",
    "美容所": "美容所台帳",
    "旅館": "旅館台帳",
    "クリーニング所": "クリーニング所",
}

# 台帳ごとのヘッダー -> 標準キー。ここに無い列が来たら様式が変わったものとして止める
_FOOD_COLUMNS = {
    "屋号": "name",
    "営業所所在地": "address",
    "営業者氏名": "operator_name",
    "営業者住所": "operator_address",
    "営業の種類": "business_type",
    "申請区分": "application_type",
    "営業所電話番号": "phone_number",
    "営業者電話番号": "operator_phone_number",
    "法人代表者氏名": "representative_name",
    "初回許可日": "permit_date",
    "届出年月日": "permit_date",
}

_SANITATION_COLUMNS = {
    "確認番号": "permit_number",
    "許可番号": "permit_number",
    "営業形態": "business_form",
    "施設名称": "name",
    "施設TEL": "phone_number",
    "施設所在地": "address",
    "施設ビル名": "building",
    "営業者氏名": "operator_name",
    "法人代表者氏名": "representative_name",
    "営業者住所": "operator_address",
    "営業者ビル名": "operator_building",
    "営業者TEL": "operator_phone_number",
    "確認年月日": "permit_date",
    "許可年月日": "permit_date",
}

_FOOD_KEYS = [
    "permit_type",
    "name",
    "address",
    "business_type",
    "application_type",
    "phone_number",
    "permit_date",
    "operator_name",
    "operator_address",
    "operator_phone_number",
    "representative_name",
]

_SANITATION_KEYS = [
    "facility_type",
    "permit_number",
    "business_form",
    "name",
    "address",
    "building",
    "phone_number",
    "permit_date",
    "operator_name",
    "operator_address",
    "operator_building",
    "operator_phone_number",
    "representative_name",
]

# 元号 -> 元年の西暦。台帳の時点は「令和8年8月31日現在」の形で本文に書かれている
_ERA_FIRST_YEAR = {"令和": 2019, "平成": 1989, "昭和": 1926}
_AS_OF_RE = re.compile(r"(令和|平成|昭和)\s*(\d+)\s*年\s*(\d+)\s*月\s*(\d+)\s*日現在")
_ANCHOR_RE = re.compile(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', re.S)
_TAG_RE = re.compile(r"<[^>]+>")

_SOURCE_FILENAME = "source.ndjson"

# CSV のリンクと台帳名の距離の上限（本文の文字数）。
# 台帳名はリンクの直前に置かれているので、これを超えるものは別の台帳の見出し
_LEDGER_NAME_DISTANCE = 400


def _fetch(url: str) -> bytes:
    time.sleep(REQUEST_INTERVAL)
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=120) as resp:
        return resp.read()


def _decode(data: bytes) -> str:
    """配布ファイルを文字列にする。

    cp932 は UTF-8 のバイト列を誤って受理しうるので、必ず UTF-8 から試す。
    """
    for encoding in ("utf-8-sig", "cp932"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError("UTF-8 でも cp932 でもデコードできません")


def _plain_text(markup: str) -> str:
    return html.unescape(_TAG_RE.sub("", markup))


def _as_of_before(text: str, position: int) -> date | None:
    """指定位置より前で最も近い「○年○月○日現在」を日付にする。"""
    matched = None
    for m in _AS_OF_RE.finditer(text, 0, position):
        matched = m
    if matched is None:
        return None
    era, year, month, day = matched.groups()
    return date(_ERA_FIRST_YEAR[era] + int(year) - 1, int(month), int(day))


def resolve_csv_links(index_html: str, ledgers: dict[str, str]) -> dict[str, dict]:
    """配布ページから台帳ごとの CSV の URL と時点を解決する。

    リンクテキストに台帳名が入っているのは食品の 2 種だけで、環境衛生の 4 種は
    「(CSV:162KB)」としか書かれていない。リンクより前の本文を末尾から辿り、
    最初に見つかった台帳名をその CSV の台帳とみなす。
    """
    plain = _plain_text(index_html)
    resolved: dict[str, dict] = {}

    for anchor in _ANCHOR_RE.finditer(index_html):
        label = _plain_text(anchor.group(2)).strip()
        if "CSV" not in label.upper():
            continue
        before = _plain_text(index_html[: anchor.start()]) + label
        # 末尾に最も近い台帳名を採る。前の台帳名も本文には残っているため。
        # 遠すぎる台帳名を拾うと、対象外の台帳（医療機関・薬局）の CSV が
        # 直前のセクションの台帳として紛れ込むので、距離に上限を置く
        nearest: tuple[int, str] | None = None
        for key, ledger_name in ledgers.items():
            index = before.rfind(ledger_name)
            if index < 0 or len(before) - index > _LEDGER_NAME_DISTANCE:
                continue
            if nearest is None or index > nearest[0]:
                nearest = (index, key)
        if nearest is None or nearest[1] in resolved:
            continue
        resolved[nearest[1]] = {
            "url": BASE_URL + anchor.group(1),
            "label": label,
            "as_of": _as_of_before(plain, plain.rfind(ledgers[nearest[1]]) + 1),
        }

    missing = sorted(set(ledgers) - set(resolved))
    if missing:
        raise ValueError(f"配布ページで CSV を解決できない台帳があります: {missing}")
    return resolved


def _parse(text: str, columns: dict[str, str], fixed: dict[str, str]) -> list[dict]:
    """台帳 CSV を標準キーの行に変換する。

    様式が変わったことに気付けるよう、未知の列が 1 つでもあれば止める。
    """
    rows = list(csv.reader(text.splitlines()))
    if not rows:
        raise ValueError("空のファイルです")

    headers = [h.replace("﻿", "").strip() for h in rows[0]]
    unknown = [h for h in headers if h and h not in columns]
    if unknown:
        raise ValueError(f"未知の列があります: {unknown}")
    keys = [columns.get(h) for h in headers]
    if "address" not in keys or "name" not in keys:
        raise ValueError(f"ヘッダーを認識できません: {headers}")

    records = []
    for row in rows[1:]:
        record = dict(fixed)
        for key, value in zip(keys, row, strict=False):
            if key is not None:
                record[key] = value.strip()
        if not (record.get("address") or ""):
            continue
        records.append(record)
    return records


def _write(path: Path, records: list[dict], keys: list[str]) -> None:
    """標準キーの行に由来メタを付けて NDJSON に書く。

    _org_code / _org_title は ODS の行と同じ形。pipelines/geocode.py が
    この2つを見て住所を組み立て、突合キーにする。
    """
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            row = {key: record.get(key) for key in keys}
            row["_org_code"] = ORG_CODE
            row["_org_title"] = ORG_TITLE
            row["_source_url"] = record["_source_url"]
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def download_hokenjo(dest_dir: str = "data/hokenjo") -> None:
    """保健所台帳を取得し、標準キーに正規化した NDJSON を出力する。"""
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)

    index_html = _decode(_fetch(BASE_URL + INDEX_PATH))
    ledgers = {**_FOOD_LEDGERS, **_SANITATION_LEDGERS}
    links = resolve_csv_links(index_html, ledgers)

    fetched_at = datetime.now(UTC).isoformat()
    entries = []
    food: list[dict] = []
    sanitation: list[dict] = []

    for key, link in links.items():
        text = _decode(_fetch(link["url"]))
        if key in _FOOD_LEDGERS:
            records = _parse(text, _FOOD_COLUMNS, {"permit_type": key})
            food.extend({**r, "_source_url": link["url"]} for r in records)
        else:
            records = _parse(text, _SANITATION_COLUMNS, {"facility_type": key})
            sanitation.extend({**r, "_source_url": link["url"]} for r in records)
        entries.append(
            {
                "ledger": key,
                "url": link["url"],
                "as_of": link["as_of"].isoformat() if link["as_of"] else None,
                "fetched_at": fetched_at,
                "row_count": len(records),
            }
        )
        logger.info("  %s: %d rows", key, len(records))

    _write(dest / "food_establishment.ndjson", food, _FOOD_KEYS)
    _write(dest / "sanitation_facility.ndjson", sanitation, _SANITATION_KEYS)

    with (dest / _SOURCE_FILENAME).open("w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    logger.info(
        "  hokenjo: food_establishment %d rows / sanitation_facility %d rows",
        len(food),
        len(sanitation),
    )
