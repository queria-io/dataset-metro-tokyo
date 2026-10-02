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
import ssl
import time
import unicodedata
from dataclasses import dataclass
from html.parser import HTMLParser
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

import certifi
import yaml

logger = logging.getLogger("pipelines")

USER_AGENT = "dataset-metro-tokyo"

# 証明書の検証には Mozilla のルート証明書 (certifi) を使う。実行環境の OS のストアには
# GlobalSign Root R46 が無いことがあり、それを使う自治体のサイト（福生市・清瀬市など）は
# 正しいチェーンを送っていても検証に失敗する
SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())

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

# 種別誤判定を弾くために最低限マッピングできていなければならない標準キー。
# 施設系の種別は所在地を持つ前提だが、住所列を持たない種別（小中学校通学区域情報など）は
# ods_datasets.yml の required_columns で上書きする
DEFAULT_REQUIRED_COLUMNS = ["name", "address"]

# 値が空なら実体を持たない行とみなす標準キー（表末尾のバージョン表記などの除去用）。
# 名称列を持たない種別（消防水利施設一覧など）は ods_datasets.yml の identity_column で上書きする
DEFAULT_IDENTITY_COLUMN = "name"


@dataclass
class OdsDataset:
    """ods_datasets.yml の1エントリ（データセット種別）。"""

    id: str
    title: str
    slug_patterns: list[str]
    title_patterns: list[str]
    # 正規化済みヘッダー名 → 標準キー（先勝ちのため列挙順を保持した dict）
    header_map: dict[str, str]
    required_columns: list[str]
    identity_column: str


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
                required_columns=entry.get(
                    "required_columns", DEFAULT_REQUIRED_COLUMNS
                ),
                identity_column=entry.get(
                    "identity_column", DEFAULT_IDENTITY_COLUMN
                ),
            )
        )
    return datasets


def _is_csv(resource: dict) -> bool:
    """リソースが CSV か。format の申告が無い登録があるので URL の拡張子も見る。"""
    url = resource.get("url") or ""
    return (resource.get("format") or "").upper() == "CSV" or url.lower().endswith(".csv")


def _matches(dataset: OdsDataset, resource: dict, title: str) -> bool:
    """リソースが種別に一致するか。URL スラッグが主判定、パッケージタイトルが副判定。"""
    stem = Path(urlparse(resource.get("url") or "").path).stem.lower()
    slug_hit = any(
        re.search(rf"(^|[_\-]){re.escape(s)}([_\-.]|\d|$)", stem)
        for s in dataset.slug_patterns
    )
    title_hit = any(p in title for p in dataset.title_patterns)
    return slug_hit or title_hit


def _is_html(resource: dict) -> bool:
    """リソースが HTML のページか。自治体のサイトのページへのリンクとして登録されている。"""
    path = urlparse(resource.get("url") or "").path.lower()
    return (resource.get("format") or "").upper() == "HTML" or path.endswith((".html", ".htm"))


class _CsvLinkParser(HTMLParser):
    """ページの中の CSV へのリンクを (URL, リンクの文言) で集める。"""

    def __init__(self, base_url: str):
        super().__init__()
        self._base_url = base_url
        self._href: str | None = None
        self._text: list[str] = []
        self.links: list[tuple[str, str]] = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self._href = dict(attrs).get("href")
            self._text = []

    def handle_data(self, data):
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag):
        if tag != "a" or self._href is None:
            return
        url = urljoin(self._base_url, self._href.strip())
        if urlparse(url).path.lower().endswith(".csv"):
            text = re.sub(r"\s+", " ", "".join(self._text)).strip()
            self.links.append((url, text))
        self._href = None


def find_csv_links(html: str, page_url: str, dataset: OdsDataset) -> list[tuple[str, str]]:
    """ページに置かれた CSV のうち、種別に一致するものを (URL, リンクの文言) で返す。

    自治体のサイトでは、別の種別の CSV が同じページに並ぶことがある。ファイル名の
    スラッグか、リンクの文言に種別の名前が入っているものだけを候補にし、
    最後はヘッダー検査で判定する。ファイル名がスラッグに沿っていない自治体
    （132217_kiyoseshi_koukyoushisetu1.csv「公共施設一覧」など）は文言で拾う。
    """
    parser = _CsvLinkParser(page_url)
    parser.feed(html)
    found: list[tuple[str, str]] = []
    seen: set[str] = set()
    for url, text in parser.links:
        if url in seen:
            continue
        if _matches(dataset, {"url": url}, text):
            seen.add(url)
            found.append((url, text))
    return found


def _modified_at(resource: dict) -> str | None:
    """リソースの最終更新時点。どちらが現行の版かを後段で決める根拠に使う。

    CKAN の last_modified は登録されないことがあるので created で代替する。
    """
    return resource.get("last_modified") or resource.get("created")


def _formats(resources: list[dict]) -> list[str]:
    """パッケージが実際に持つリソース形式。台帳の理由欄に入れる。"""
    seen = []
    for resource in resources:
        fmt = (resource.get("format") or "").upper() or "UNKNOWN"
        if fmt not in seen:
            seen.append(fmt)
    return sorted(seen)


def classify(
    packages_path: str, datasets: list[OdsDataset]
) -> tuple[
    list[tuple[OdsDataset, dict, dict]],
    list[tuple[OdsDataset, dict, dict | None, str]],
    list[tuple[OdsDataset, dict, dict]],
]:
    """packages.ndjson から取り込み対象と、取り込まなかったパッケージ・リソースを判定する。

    リソース URL のファイル名スラッグを主判定、データセットタイトルを副判定とする。
    副判定はパッケージ内の全 CSV リソースを候補にし、ヘッダー検査で最終判定する。

    同一 URL が複数のリソースとして登録されている場合（更新時点だけが異なる版を
    同じファイルに上書き公開している自治体がある）は最初の1件だけを対象にする。
    **落とした側も台帳に残す。** 月次公開の一部で、新しい月のリソースが前月のファイルを
    指したまま登録されている例があり（練馬区の地域・年齢別人口 令和7年11月は
    令和7年10月と同じ URL）、この場合その月のデータはどこにも存在しない。台帳に行が
    無いと、取り込み側が落としたのか原典に無いのかを後から区別できない。

    種別の照合は CSV かどうかに関わらず行う。**CSV ゲートを先に置くと、HTML や PDF
    でしか登録されていないパッケージが台帳に1行も残らず、「その自治体が公開していない」
    と区別が付かなくなる。** 一致したのに CSV が1つも無いパッケージも第2の戻り値に入れ、
    呼び出し側が skipped として1行だけ記録する。

    ただし CSV が無くても HTML のリソースがあるパッケージは、第3の戻り値（たどるページ）に
    入れる。自治体のサイトのページへのリンクだけで登録し、CSV はそのページに置いている
    自治体がある。ページの中の CSV は呼び出し側が取得時に探す。

    Returns:
        (targets, skipped, pages)
        targets: 取り込み対象の (種別, パッケージ, リソース)
        skipped: 取得を試みない (種別, パッケージ, リソース or None, 理由)。
                 パッケージ単位の行（CSV リソースが無い場合）はリソースが None
        pages:   CSV を探しに行くページの (種別, パッケージ, HTML リソース)
    """
    targets = []
    skipped = []
    pages = []
    # (種別, ページの URL) → 採用したページのリソース ID。同じページを複数のパッケージが
    # 指していることがあり、2つ目以降は duplicate_url として台帳に残す
    seen_pages: dict[tuple[str, str], str] = {}
    # (種別, URL) → 採用したリソース ID
    seen: dict[tuple[str, str], str] = {}
    # 同じパッケージが2度現れたときに、同じリソースを2度たどらないための既処理集合。
    # package_search はページング中にパッケージの更新が入ると同じものを返しうる
    seen_resources: set[tuple[str, str]] = set()
    seen_no_csv: set[tuple[str, str]] = set()

    with open(packages_path, encoding="utf-8") as f:
        for line in f:
            package = json.loads(line)
            if package.get("license_id") not in ALLOWED_LICENSES:
                continue
            title = package.get("title") or ""
            resources = package.get("resources") or []

            for dataset in datasets:
                hits = [r for r in resources if _matches(dataset, r, title)]
                if not hits:
                    continue

                csv_hits = [r for r in hits if _is_csv(r)]
                html_hits = [r for r in hits if _is_html(r)]
                if not csv_hits and html_hits:
                    for page in html_hits:
                        if (dataset.id, page["id"]) in seen_resources:
                            continue
                        seen_resources.add((dataset.id, page["id"]))
                        key = (dataset.id, page.get("url") or "")
                        kept = seen_pages.get(key)
                        if kept is not None:
                            skipped.append(
                                (dataset, package, page, f"duplicate_url: kept={kept}")
                            )
                            continue
                        seen_pages[key] = page["id"]
                        pages.append((dataset, package, page))
                    continue
                if not csv_hits:
                    key = (dataset.id, package["id"])
                    if key not in seen_no_csv:
                        seen_no_csv.add(key)
                        skipped.append(
                            (
                                dataset,
                                package,
                                None,
                                f"no_csv_resource: formats={','.join(_formats(resources))}",
                            )
                        )
                    continue

                for resource in csv_hits:
                    if (dataset.id, resource["id"]) in seen_resources:
                        continue
                    seen_resources.add((dataset.id, resource["id"]))

                    key = (dataset.id, resource.get("url") or "")
                    kept = seen.get(key)
                    if kept is not None:
                        skipped.append(
                            (dataset, package, resource, f"duplicate_url: kept={kept}")
                        )
                        continue
                    seen[key] = resource["id"]
                    targets.append((dataset, package, resource))

    targets.sort(
        key=lambda t: (t[0].id, t[1]["organization"]["name"], t[2]["id"])
    )
    skipped.sort(
        key=lambda t: (
            t[0].id,
            t[1]["organization"]["name"],
            t[2]["id"] if t[2] else "",
            t[1]["id"],
        )
    )
    pages.sort(key=lambda t: (t[0].id, t[1]["organization"]["name"], t[2]["id"]))
    return targets, skipped, pages


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
            with urlopen(req, timeout=60, context=SSL_CONTEXT) as resp:
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
    識別列（既定は名称）が空の行は実体を持たないため落とす（表末尾のバージョン表記など）。
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
        if not record.get(dataset.identity_column):
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
    targets, skipped, pages = classify(packages_path, datasets)
    logger.info(
        f"  {len(targets)} resources classified, {len(skipped)} skipped, {len(pages)} pages to follow"
    )

    throttle = _HostThrottle()
    fetched_at = datetime.now(UTC).isoformat()

    writers = {d.id: (dest / f"{d.id}.ndjson").open("w", encoding="utf-8") for d in datasets}
    ok_counts = dict.fromkeys(writers, 0)

    with (dest / "source_files.ndjson").open("w", encoding="utf-8") as source_files:

        def log_source(dataset, package, resource, **fields):
            # resource=None はパッケージ単位の行（CSV リソースが1つも無かった場合）。
            # リソースが存在しないので、リソース側の列は空にする
            entry = {
                "dataset_id": dataset.id,
                "package_id": package["id"],
                "package_title": package.get("title"),
                "resource_id": resource["id"] if resource else None,
                "resource_name": resource.get("name") if resource else None,
                "org_code": package["organization"]["name"],
                "org_title": package["organization"]["title"],
                "url": resource.get("url") if resource else None,
                "via_page_url": resource.get("_via_page_url") if resource else None,
                "fetched_at": fetched_at,
                **fields,
            }
            source_files.write(json.dumps(entry, ensure_ascii=False) + "\n")

        def ingest(dataset, package, resource):
            url = resource.get("url") or ""
            try:
                data = _fetch(url, throttle)
            except Exception as e:
                logger.info(f"  failed: {url} ({e})")
                log_source(
                    dataset, package, resource,
                    status="failed", reason=f"fetch_error: {e}",
                )
                return

            # CSV を装った zip/xlsx（PK マジック）はテキストとして扱えないため隔離
            if data[:4] == b"PK\x03\x04":
                log_source(
                    dataset, package, resource,
                    status="skipped", reason="not_csv: zip/xlsx content",
                )
                return

            text, encoding = _decode(data)
            rows = list(csv.reader(text.splitlines()))
            header_index = _find_header(rows, dataset.header_map)
            if header_index is None:
                log_source(
                    dataset, package, resource,
                    status="skipped", reason="header_mismatch", encoding=encoding,
                )
                return

            records, mapped = _normalize_rows(rows, header_index, dataset)
            # 種別の必須列を取れないファイルは種別誤判定とみなして隔離する
            if any(column not in mapped for column in dataset.required_columns):
                log_source(
                    dataset, package, resource,
                    status="skipped",
                    reason=f"required_columns_missing: mapped={mapped}",
                    encoding=encoding,
                )
                return

            for record in records:
                record["_package_id"] = package["id"]
                record["_resource_id"] = resource["id"]
                # 同じ月を複数のリソースが持つときにどちらを採るかの根拠。
                # 読むのは raw_population だけだが、種別を問わず書いておく
                record["_resource_modified"] = _modified_at(resource)
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

        # 取得を試みなかったリソース・パッケージ。台帳に行が無いと「公開していない」
        # 「取り込み側が落とした」の見分けが付かないので、理由つきで1行だけ残す
        for dataset, package, resource, reason in skipped:
            log_source(dataset, package, resource, status="skipped", reason=reason)

        for dataset, package, resource in targets:
            ingest(dataset, package, resource)

        # カタログに CSV として登録された URL は上で取ったので、ページからは取り直さない。
        # 値は取り込んだリソース ID（duplicate_url の kept= に入れる）
        registered = {(d.id, r.get("url") or ""): r["id"] for d, _, r in targets}
        for dataset, package, page in pages:
            page_url = page.get("url") or ""
            try:
                html, _ = _decode(_fetch(page_url, throttle))
            except Exception as e:
                logger.info(f"  failed: {page_url} ({e})")
                log_source(
                    dataset, package, page,
                    status="failed", reason=f"page_fetch_error: {e}",
                )
                continue

            found = find_csv_links(html, page_url, dataset)
            links = [(url, text) for url, text in found if (dataset.id, url) not in registered]
            if not found:
                log_source(
                    dataset, package, page,
                    status="skipped", reason="no_csv_on_page",
                )
                continue
            if not links:
                kept = registered[(dataset.id, found[0][0])]
                log_source(
                    dataset, package, page,
                    status="skipped", reason=f"duplicate_url: kept={kept}",
                )
                continue

            for url, text in links:
                registered[(dataset.id, url)] = f"{page['id']}#{Path(urlparse(url).path).name}"
                # ページのリソースから派生した擬似リソース。ID はページのリソース ID と
                # ファイル名で作り、ビルドのたびに同じ値になるようにする
                ingest(
                    dataset,
                    package,
                    {
                        "id": f"{page['id']}#{Path(urlparse(url).path).name}",
                        "name": text or page.get("name"),
                        "url": url,
                        "last_modified": page.get("last_modified"),
                        "created": page.get("created"),
                        "_via_page_url": page_url,
                    },
                )

    for writer in writers.values():
        writer.close()
    for dataset_id, count in ok_counts.items():
        logger.info(f"  {dataset_id}: {count} files ingested")
