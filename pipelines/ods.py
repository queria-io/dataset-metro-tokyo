"""自治体標準オープンデータセット (ODS) リソースの取り込み。

catalog スキーマ用に取得済みの packages.ndjson から、ods_datasets.yml に定義した
種別ごとに対象 CSV リソースを判定してダウンロードし、ヘッダーを標準キーに正規化して
data/ods/<id>.ndjson に出力する。取得結果（成功・失敗・理由）は
data/ods/source_files.ndjson に記録し、1リソースの失敗で全体を止めない。

リソースは自治体ごとの多ドメインに分散ホストされているため、ホスト別に
リクエスト間隔を制御する。エンコーディングは utf-8-sig → cp932 の順に
strict デコードを試行する。

データソース: 東京都オープンデータカタログ
https://catalog.data.metro.tokyo.lg.jp/
"""

import csv
import json
import logging
import re
import time
import unicodedata
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

import yaml

logger = logging.getLogger("pipelines")

USER_AGENT = "dataset-metro-tokyo"

# ホスト別の最小リクエスト間隔（秒）。data.bodik.jp は一括アクセスで
# IP が一時ブロックされる実績があるため長めにとる
DEFAULT_INTERVAL = 0.5
HOST_INTERVALS = {"data.bodik.jp": 2.0}

# 5xx / 接続断のリトライ回数
MAX_RETRIES = 2

# ヘッダー行とみなす条件: 先頭 N 行のうち、既知ヘッダーが M 個以上並ぶ最初の行
HEADER_SCAN_ROWS = 5
HEADER_MIN_MATCHES = 2

# 取り込み対象とするライセンス
ALLOWED_LICENSES = {"CC-BY-4.0"}


@dataclass
class OdsDataset:
    """ods_datasets.yml の1エントリ（データセット種別）。"""

    id: str
    title: str
    slug_patterns: list[str]
    title_patterns: list[str]
    # 正規化済みヘッダー名 → 標準キー（先勝ちのため列挙順を保持した dict）
    header_map: dict[str, str]


def normalize_header(header: str) -> str:
    """CSV ヘッダー名を照合用に正規化する（BOM・引用符・空白・改行の除去、NFKC）。"""
    s = header.replace("\ufeff", "").strip().strip('"').strip("'")
    s = unicodedata.normalize("NFKC", s)
    return re.sub(r"\s+", "", s)


def load_config(path: str = "ods_datasets.yml") -> list[OdsDataset]:
    config = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    datasets = []
    for entry in config["datasets"]:
        header_map: dict[str, str] = {}
        for column in entry["columns"]:
            for source in column["source"]:
                header_map.setdefault(normalize_header(source), column["key"])
        datasets.append(
            OdsDataset(
                id=entry["id"],
                title=entry["title"],
                slug_patterns=entry["slug_patterns"],
                title_patterns=entry.get("title_patterns", []),
                header_map=header_map,
            )
        )
    return datasets


def classify(
    packages_path: str, datasets: list[OdsDataset]
) -> list[tuple[OdsDataset, dict, dict]]:
    """packages.ndjson から取り込み対象の (種別, パッケージ, リソース) を判定する。

    リソース URL のファイル名スラッグを主判定、データセットタイトルを副判定とする。
    副判定はパッケージ内の全 CSV リソースを候補にし、ヘッダー検査で最終判定する。
    """
    targets = []
    seen: set[tuple[str, str]] = set()

    with open(packages_path, encoding="utf-8") as f:
        for line in f:
            package = json.loads(line)
            if package.get("license_id") not in ALLOWED_LICENSES:
                continue
            title = package.get("title") or ""

            for resource in package.get("resources") or []:
                url = resource.get("url") or ""
                is_csv = (resource.get("format") or "").upper() == "CSV" or (
                    url.lower().endswith(".csv")
                )
                if not is_csv:
                    continue
                stem = Path(urlparse(url).path).stem.lower()

                for dataset in datasets:
                    slug_hit = any(
                        re.search(rf"(^|[_\-]){re.escape(s)}([_\-.]|\d|$)", stem)
                        for s in dataset.slug_patterns
                    )
                    title_hit = any(p in title for p in dataset.title_patterns)
                    if not (slug_hit or title_hit):
                        continue
                    key = (dataset.id, resource["id"])
                    if key in seen:
                        continue
                    seen.add(key)
                    targets.append((dataset, package, resource))

    targets.sort(
        key=lambda t: (t[0].id, t[1]["organization"]["name"], t[2]["id"])
    )
    return targets


class _HostThrottle:
    """ホスト別に最小リクエスト間隔を保証する。"""

    def __init__(self):
        self._last: dict[str, float] = {}

    def wait(self, url: str) -> None:
        host = urlparse(url).netloc
        interval = HOST_INTERVALS.get(host, DEFAULT_INTERVAL)
        elapsed = time.monotonic() - self._last.get(host, 0.0)
        if elapsed < interval:
            time.sleep(interval - elapsed)
        self._last[host] = time.monotonic()


def _fetch(url: str, throttle: _HostThrottle) -> bytes:
    """リソースを取得する。5xx・接続断は指数バックオフで再試行、4xx は即失敗。"""
    for attempt in range(MAX_RETRIES + 1):
        throttle.wait(url)
        try:
            req = Request(url, headers={"User-Agent": USER_AGENT})
            with urlopen(req, timeout=60) as resp:
                return resp.read()
        except (HTTPError, URLError, TimeoutError) as e:
            status = getattr(e, "code", None)
            retryable = status is None or status >= 500
            if not retryable or attempt == MAX_RETRIES:
                raise
            time.sleep(2**attempt)
    raise AssertionError("unreachable")


def _decode(data: bytes) -> tuple[str, str]:
    """バイト列を (テキスト, エンコーディング名) で返す。

    UTF-16 は BOM がある場合のみ受理（BOM 無しの推定は誤判定リスクが高い）。
    それ以外は utf-8-sig → cp932 の順に strict で試し、どちらも失敗したら
    utf-8 の置換デコードにフォールバックする。cp932 は UTF-8 バイト列を
    誤って受理しうるため、必ず utf-8 を先に試す。
    """
    if data[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return data.decode("utf-16"), "utf-16"
    for encoding in ("utf-8-sig", "cp932"):
        try:
            return data.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace"), "utf-8(replace)"


def _find_header(rows: list[list[str]], header_map: dict[str, str]) -> int | None:
    """既知ヘッダーが並ぶ最初の行番号を返す（タイトル行・注釈行のスキップ用）。"""
    for i, row in enumerate(rows[:HEADER_SCAN_ROWS]):
        matches = sum(1 for cell in row if normalize_header(cell) in header_map)
        if matches >= HEADER_MIN_MATCHES:
            return i
    return None


def _normalize_rows(
    rows: list[list[str]], header_index: int, dataset: OdsDataset
) -> tuple[list[dict], list[str]]:
    """ヘッダーを標準キーにマッピングし、1行=1dict に正規化する。

    どの標準キーにもマッチしないヘッダーの値は _extras に退避する。
    標準キーは先勝ち（同じキーに複数ヘッダーがマッチしたら最初の列を採用）。
    """
    header = rows[header_index]
    key_by_index: dict[int, str] = {}
    extra_by_index: dict[int, str] = {}
    mapped: set[str] = set()
    for i, cell in enumerate(header):
        normalized = normalize_header(cell)
        key = dataset.header_map.get(normalized)
        if key and key not in mapped:
            key_by_index[i] = key
            mapped.add(key)
        elif normalized:
            extra_by_index[i] = normalized

    records = []
    for row in rows[header_index + 1 :]:
        record: dict = {}
        extras: dict = {}
        for i, cell in enumerate(row):
            value = cell.strip()
            if not value:
                continue
            if i in key_by_index:
                record[key_by_index[i]] = value
            elif i in extra_by_index:
                extras[extra_by_index[i]] = value
        if not record and not extras:
            continue
        if extras:
            record["_extras"] = extras
        records.append(record)
    return records, sorted(mapped)


def download_and_normalize(
    config_path: str = "ods_datasets.yml",
    packages_path: str = "data/catalog/packages.ndjson",
    dest_dir: str = "data/ods",
) -> None:
    """対象リソースをダウンロードして種別ごとの NDJSON に正規化する。

    失敗は1リソース単位で隔離し、source_files.ndjson に理由を記録して続行する。
    """
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)

    datasets = load_config(config_path)
    targets = classify(packages_path, datasets)
    logger.info(f"  {len(targets)} resources classified")

    throttle = _HostThrottle()
    fetched_at = datetime.now(UTC).isoformat()

    writers = {d.id: (dest / f"{d.id}.ndjson").open("w", encoding="utf-8") for d in datasets}
    ok_counts = dict.fromkeys(writers, 0)

    with (dest / "source_files.ndjson").open("w", encoding="utf-8") as source_files:

        def log_source(dataset, package, resource, **fields):
            entry = {
                "dataset_id": dataset.id,
                "package_id": package["id"],
                "package_title": package.get("title"),
                "resource_id": resource["id"],
                "resource_name": resource.get("name"),
                "org_code": package["organization"]["name"],
                "org_title": package["organization"]["title"],
                "url": resource.get("url"),
                "fetched_at": fetched_at,
                **fields,
            }
            source_files.write(json.dumps(entry, ensure_ascii=False) + "\n")

        for dataset, package, resource in targets:
            url = resource.get("url") or ""
            try:
                data = _fetch(url, throttle)
            except Exception as e:
                logger.info(f"  failed: {url} ({e})")
                log_source(
                    dataset, package, resource,
                    status="failed", reason=f"fetch_error: {e}",
                )
                continue

            # CSV を装った zip/xlsx（PK マジック）はテキストとして扱えないため隔離
            if data[:4] == b"PK\x03\x04":
                log_source(
                    dataset, package, resource,
                    status="skipped", reason="not_csv: zip/xlsx content",
                )
                continue

            text, encoding = _decode(data)
            rows = list(csv.reader(text.splitlines()))
            header_index = _find_header(rows, dataset.header_map)
            if header_index is None:
                log_source(
                    dataset, package, resource,
                    status="skipped", reason="header_mismatch", encoding=encoding,
                )
                continue

            records, mapped = _normalize_rows(rows, header_index, dataset)
            # 名称と所在地の両方を取れないファイルは種別誤判定とみなして隔離する
            if "name" not in mapped or "address" not in mapped:
                log_source(
                    dataset, package, resource,
                    status="skipped",
                    reason=f"required_columns_missing: mapped={mapped}",
                    encoding=encoding,
                )
                continue

            for record in records:
                record["_package_id"] = package["id"]
                record["_resource_id"] = resource["id"]
                record["_org_code"] = package["organization"]["name"]
                record["_org_title"] = package["organization"]["title"]
                record["_source_url"] = url
                record["_fetched_at"] = fetched_at
                writers[dataset.id].write(json.dumps(record, ensure_ascii=False) + "\n")

            ok_counts[dataset.id] += 1
            log_source(
                dataset, package, resource,
                status="ok", encoding=encoding, row_count=len(records),
            )

    for writer in writers.values():
        writer.close()
    for dataset_id, count in ok_counts.items():
        logger.info(f"  {dataset_id}: {count} files ingested")
