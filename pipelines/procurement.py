"""区市町村の調達情報のダウンロード。

東京都オープンデータカタログに登録された区市町村の「調達情報」から、
工事・物品の発注予定（CSV）と随意契約の締結状況（Excel）を取り込む。

- 発注予定は公共施設・AED と同じ自治体標準オープンデータセットの書式の CSV で、
  半期ごとに同じ URL のまま中身が差し替わる。取り込むのは公開中の最新の半期だけ
- 随意契約の締結状況は 4 か月ごとの Excel が増えていく。書式は年によって
  見出しの行の位置と列（「契約請求課」の有無）が違い、古いものは .xls

リソースは URL を固定せず、catalog スキーマ用に取得済みの packages.ndjson から
リソース名で分類する。1 リソースの失敗（リンク切れで HTML が返るなど）は
source_files.ndjson に記録して全体を止めない。

データソース: 東京都オープンデータカタログ
https://catalog.data.metro.tokyo.lg.jp/
"""

import csv
import io
import json
import logging
import re
import time
import unicodedata
from datetime import UTC, date, datetime
from pathlib import Path
from urllib.request import Request, urlopen

import openpyxl
import xlrd

logger = logging.getLogger("pipelines")

# 調達情報を公開しているパッケージ（CKAN の package name）
PACKAGES = ("t131202d0000000114",)  # 練馬区 調達情報

USER_AGENT = "dataset-metro-tokyo"
REQUEST_INTERVAL = 1.0

# 発注予定の CSV の見出し -> 列名。設計・測量・調査の CSV は工事の代わりに
# 業種・件名・履行場所・履行期間・業務概要の見出しを使うので、候補を並べる
_PLANNED_WORK_COLUMNS = {
    "org_code": ["全国地方公共団体コード"],
    "org_name": ["地方公共団体名"],
    "work_type": ["工事種別", "業種"],
    "title": ["工事件名", "件名"],
    "location": ["工事場所_連結表記", "履行場所_連結表記"],
    "location_prefecture": ["工事場所_都道府県", "履行場所_都道府県"],
    "location_city": ["工事場所_市区町村", "履行場所_市区町村"],
    "location_town": ["工事場所_町字", "履行場所_町字"],
    "location_block": ["工事場所_番地以下", "履行場所_番地以下"],
    "location_building": ["建物名等(方書)"],
    "lat": ["緯度"],
    "lon": ["経度"],
    "period_start": ["工期（始期）", "履行期間（始期）"],
    "period_end": ["工期（終期）", "履行期間（終期）"],
    "summary": ["工事概要", "業務概要"],
    "bidding_method": ["入札方法"],
    "bidding_timing": ["入札時期（予定）"],
    "note": ["備考"],
}
_PLANNED_GOODS_COLUMNS = {
    "org_code": ["全国地方公共団体コード"],
    "org_name": ["地方公共団体名"],
    "item_type": ["種目"],
    "title": ["件名"],
    "delivery_place": ["納入場所"],
    "delivery_deadline": ["納期"],
    "summary": ["概要"],
    "bidding_method": ["入札方法（予定）"],
    "bidding_timing": ["入札時期（予定）"],
    "note": ["備考"],
}

# 随意契約の Excel の見出し -> 列名。「件名」と「業種」がある行を見出しとみなす。
# 見出しの括弧書き（「契約金額（契約変更後の金額含む）」）は除いて照合する
_CONTRACT_COLUMNS = {
    "整理番号": "seq_no",
    "件名": "title",
    "業種": "business_type",
    "契約金額": "contract_amount",
    "契約年月日": "contract_date",
    "履行期間": "performance_period",
    "契約者": "contractor",
    "区内外": "contractor_area",
    "随意契約理由": "reason",
    "契約請求課": "requesting_section",
}

_PLANNED_WORK_RE = re.compile(r"^〔工事の発注予定〕(.+)[（(]((?:令和|平成).+)[）)]$")
_PLANNED_GOODS_RE = re.compile(r"^物品買入れ契約.*の発注予定[（(](.+)[）)]$")
_CONTRACT_RE = re.compile(r"^〔随意契約の締結状況〕(.+)[（(]((?:令和|平成).+まで)[）)]$")

_ERA_FIRST_YEAR = {"令和": 2019, "平成": 1989, "R": 2019, "H": 1989}
# 「令和 3年 7月20日」「令和7年10月28日」「R2.12.2」
_WAREKI_DATE_RE = re.compile(
    r"(令和|平成|R|H)\s*(元|\d+)\s*[年.]\s*(\d+)\s*[月.]\s*(\d+)\s*日?"
)
# 期間の文字列の中の「月」までの表記（「令和3年4月から令和3年7月まで」）
_WAREKI_MONTH_RE = re.compile(r"(令和|平成)\s*(元|\d+)\s*年\s*(\d+)\s*月")

# 随意契約の表題「随意契約の公表について（令和３年４月から令和３年７月まで）【…】」の期間
_PERIOD_IN_TITLE_RE = re.compile(r"[（(]((?:令和|平成).+?まで)[）)]")

_SOURCE_FILENAME = "source_files.ndjson"


def classify(resource_name: str) -> tuple[str, str, str] | None:
    """リソース名から (種別, 区分, 対象期間の表記) を返す。対象外なら None。

    種別は planned_works / planned_goods / private_contracts。
    """
    name = resource_name.strip()
    if m := _PLANNED_WORK_RE.match(name):
        return "planned_works", m.group(1), m.group(2)
    if m := _PLANNED_GOODS_RE.match(name):
        return "planned_goods", "物品買入れ", m.group(1)
    if m := _CONTRACT_RE.match(name):
        category = "工事・設計等" if m.group(1).startswith("工事") else "物品・委託・賃貸借等"
        return "private_contracts", category, m.group(2)
    return None


def _year(era: str, number: str) -> int:
    return _ERA_FIRST_YEAR[era] + (0 if number == "元" else int(number) - 1)


def parse_wareki_dates(text: str | None) -> list[date]:
    """文字列に含まれる和暦の日付を順に返す（「R2.12.3～R3.2.26」なら 2 つ）。"""
    if not text:
        return []
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):  # Excel の日付セル
        return [date.fromisoformat(text)]
    return [
        date(_year(era, y), int(m), int(d))
        for era, y, m, d in _WAREKI_DATE_RE.findall(text)
    ]


def parse_period_months(text: str) -> tuple[str | None, str | None]:
    """「令和3年4月から令和3年7月まで」を ('2021-04', '2021-07') にする。"""
    months = [
        f"{_year(era, y)}-{int(m):02d}" for era, y, m in _WAREKI_MONTH_RE.findall(text)
    ]
    if not months:
        return None, None
    return months[0], months[-1]


def parse_amount(value) -> int | None:
    """「1,947,660」や 695200.0 を整数の円にする。空欄・数字以外は None。"""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return int(value)
    digits = re.sub(r"[,\s円]", "", str(value))
    return int(digits) if digits.isdigit() else None


def _cell_text(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    if isinstance(value, datetime):
        return value.date().isoformat()
    text = re.sub(r"\s*\r?\n\s*", "", str(value)).strip()
    return text or None


def _sheet_rows(data: bytes) -> list[list]:
    """Excel（.xlsx / .xls）の全シートの行を返す。Excel でなければ ValueError。"""
    if data[:2] == b"PK":
        wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
        return [list(r) for ws in wb.worksheets for r in ws.iter_rows(values_only=True)]
    if data[:8] == b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1":
        wb = xlrd.open_workbook(file_contents=data)
        return [s.row_values(i) for s in wb.sheets() for i in range(s.nrows)]
    raise ValueError("not_excel")


def parse_contracts(rows: list[list]) -> tuple[str | None, list[dict]]:
    """随意契約の締結状況の表を (表題, 行) にする。

    表題は見出しより前の「随意契約の公表について（令和3年4月から令和3年7月まで）…」。
    見出しの行より後で、件名のある行だけを取る。古い表は整理番号の見出しが空欄なので、
    見出しの無い先頭の列を整理番号とみなす。
    """
    title = None
    out = []
    header: dict[int, str] | None = None
    for row in rows:
        cells = [_cell_text(v) for v in row]
        keys = [re.sub(r"[（(].*$", "", c) if c else None for c in cells]
        if "件名" in keys and "業種" in keys:
            header = {i: _CONTRACT_COLUMNS[k] for i, k in enumerate(keys) if k in _CONTRACT_COLUMNS}
            if 0 not in header and cells[0] is None:
                header[0] = "seq_no"
            continue
        if header is None:
            title = title or next((c for c in cells if c and "随意契約" in c), None)
            continue
        record = {key: cells[i] if i < len(cells) else None for i, key in header.items()}
        if not record.get("title"):
            continue
        amount_index = next((i for i, k in header.items() if k == "contract_amount"), None)
        record["contract_amount_text"] = record.get("contract_amount")
        record["contract_amount"] = (
            parse_amount(row[amount_index]) if amount_index is not None else None
        )
        out.append(record)
    return title, out


def to_contract_record(record: dict) -> dict:
    """随意契約の行に日付を付ける。原典の表記も残す。"""
    contract_dates = parse_wareki_dates(record.get("contract_date"))
    period = parse_wareki_dates(record.get("performance_period"))
    return {
        **record,
        "contract_date_text": record.get("contract_date"),
        "contract_date": contract_dates[0].isoformat() if contract_dates else None,
        "performance_start": period[0].isoformat() if len(period) == 2 else None,
        "performance_end": period[-1].isoformat() if period else None,
    }


def parse_planned(text: str, columns: dict[str, list[str]]) -> list[dict]:
    """発注予定の CSV を列名をキーにした行にする。見出しが合わなければ ValueError。"""
    reader = csv.DictReader(io.StringIO(text.lstrip("\ufeff")))
    fields = [f.strip().replace('"', "") for f in reader.fieldnames or []]
    reader.fieldnames = fields
    resolved = {key: next((c for c in cands if c in fields), None) for key, cands in columns.items()}
    missing = [key for key, col in resolved.items() if col is None]
    if missing:
        raise ValueError(f"header_mismatch: {missing}")
    return [
        {key: (row.get(col) or "").strip() or None for key, col in resolved.items()}
        for row in reader
        if any((v or "").strip() for v in row.values() if isinstance(v, str))
    ]


def _fetch(url: str) -> bytes:
    time.sleep(REQUEST_INTERVAL)
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=120) as resp:
        return resp.read()


def _resources(packages_path: Path):
    with packages_path.open(encoding="utf-8") as f:
        for line in f:
            package = json.loads(line)
            if package.get("name") not in PACKAGES:
                continue
            org = package.get("organization") or {}
            for resource in package.get("resources") or []:
                yield package, org, resource


def download_procurement(
    dest_dir: str, packages_path: str = "data/catalog/packages.ndjson"
) -> None:
    """調達情報を取得し、種別ごとの NDJSON と取得結果の台帳を保存する。"""
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)
    fetched_at = datetime.now(UTC).isoformat()
    outputs: dict[str, list[dict]] = {
        "planned_works": [],
        "planned_goods": [],
        "private_contracts": [],
    }
    ledger = []
    seen_contracts: set[tuple[str, str]] = set()

    for package, org, resource in _resources(Path(packages_path)):
        name = (resource.get("name") or "").strip()
        url = resource.get("url") or ""
        entry = {
            "package_id": package["id"],
            "package_name": package["name"],
            "org_name": org.get("title"),
            "resource_name": name,
            "url": url,
            "kind": None,
            "category": None,
            "period_label": None,
            "status": "ok",
            "reason": None,
            "rows": 0,
            "fetched_at": fetched_at,
        }
        classified = classify(name)
        if classified is None:
            ledger.append({**entry, "status": "skipped", "reason": "unknown_resource"})
            continue
        kind, category, period_label = classified
        org_code = package["name"][1:7]  # t131202d... -> 131202
        entry.update(kind=kind, category=category, period_label=period_label)
        common = {
            "category": category,
            "period_label": period_label,
            "source_resource": name,
            "source_url": url,
        }

        try:
            data = _fetch(url)
            if kind == "private_contracts":
                title, rows = parse_contracts(_sheet_rows(data))
                # リソース名と中身の期間が食い違うことがある（令和6年12月〜令和7年3月の
                # リソースに令和5年12月〜令和6年3月の表が入っている）。期間は表題から取る
                file_period = _PERIOD_IN_TITLE_RE.search(title or "")
                period_label = unicodedata.normalize(
                    "NFKC", file_period.group(1) if file_period else period_label
                )
                entry["period_label"] = period_label
                if (category, period_label) in seen_contracts:
                    ledger.append({**entry, "status": "skipped", "reason": "duplicate_content"})
                    continue
                seen_contracts.add((category, period_label))
                start, end = parse_period_months(period_label)
                records = [
                    {
                        **to_contract_record(r),
                        **common,
                        "period_label": period_label,
                        "org_code": org_code,
                        "org_name": org.get("title"),
                        "period_start_month": start,
                        "period_end_month": end,
                    }
                    for r in rows
                ]
            else:
                columns = (
                    _PLANNED_WORK_COLUMNS if kind == "planned_works" else _PLANNED_GOODS_COLUMNS
                )
                records = [
                    {**r, **common}
                    for r in parse_planned(data.decode("utf-8-sig"), columns)
                ]
        except Exception as e:  # 1 リソースの失敗は台帳に残して続ける
            reason = str(e) if isinstance(e, ValueError) else f"{type(e).__name__}: {e}"
            logger.warning(f"  failed: {name}: {reason}")
            ledger.append({**entry, "status": "error", "reason": reason})
            continue

        if not records:
            ledger.append({**entry, "status": "error", "reason": "no_rows"})
            continue
        outputs[kind].extend(records)
        ledger.append({**entry, "rows": len(records)})
        logger.info(f"  {name}: {len(records)} rows")

    for kind, records in outputs.items():
        with (dest / f"{kind}.ndjson").open("w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with (dest / _SOURCE_FILENAME).open("w", encoding="utf-8") as f:
        for e in ledger:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
