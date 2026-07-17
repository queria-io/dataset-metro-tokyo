"""東京都オープンデータカタログ CKAN API からのメタデータ取得。

カタログサイト (catalog.data.metro.tokyo.lg.jp) の CKAN API v3 から
全データセット・組織・グループのメタデータを取得し、NDJSON で保存する。
件数は約 9,600 データセット（10 リクエスト程度）と小さいため、
毎回全量を取得して洗い替える。

データソース: 東京都オープンデータカタログ
https://catalog.data.metro.tokyo.lg.jp/
"""

import json
import logging
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

logger = logging.getLogger("pipelines")

BASE_URL = "https://catalog.data.metro.tokyo.lg.jp/api/3/action"
USER_AGENT = "dataset-metro-tokyo"

# package_search の rows 上限（CKAN 側の制限値）
PAGE_SIZE = 1000
# ページ間・リクエスト間の待機秒数
REQUEST_INTERVAL = 0.5
# 5xx / 接続断のリトライ回数
MAX_RETRIES = 3


def _get(action: str, params: dict | None = None) -> dict:
    """CKAN API を呼び出し result を返す。5xx・接続断は指数バックオフで再試行する。"""
    url = f"{BASE_URL}/{action}"
    if params:
        url += "?" + urlencode(params)

    for attempt in range(MAX_RETRIES + 1):
        try:
            req = Request(url, headers={"User-Agent": USER_AGENT})
            with urlopen(req) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            if not body.get("success"):
                raise RuntimeError(f"CKAN API error: {action}: {body.get('error')}")
            return body["result"]
        except (HTTPError, URLError, TimeoutError) as e:
            status = getattr(e, "code", None)
            retryable = status is None or status >= 500
            if not retryable or attempt == MAX_RETRIES:
                raise
            wait = 2**attempt
            logger.info(f"  retry {action} in {wait}s ({e})")
            time.sleep(wait)

    raise AssertionError("unreachable")


def iter_packages():
    """package_search を rows=1000 でページングし、全データセットを yield する。"""
    start = 0
    while True:
        result = _get("package_search", {"rows": PAGE_SIZE, "start": start})
        results = result["results"]
        if not results:
            return
        yield from results
        start += len(results)
        if start >= result["count"]:
            return
        time.sleep(REQUEST_INTERVAL)


def download_catalog(dest_dir: str) -> None:
    """カタログメタデータ（データセット・組織・グループ）を NDJSON で保存する。

    毎回全量を取得して上書きする（洗い替え）。
    """
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)

    packages_path = dest / "packages.ndjson"
    with packages_path.open("w", encoding="utf-8") as f:
        count = 0
        for package in iter_packages():
            f.write(json.dumps(package, ensure_ascii=False) + "\n")
            count += 1
    logger.info(f"  packages.ndjson: {count} datasets")

    for action, filename in [
        ("organization_list", "organizations.ndjson"),
        ("group_list", "groups.ndjson"),
    ]:
        path = dest / filename
        with path.open("w", encoding="utf-8") as f:
            count = 0
            # all_fields=true の返却件数は CKAN 設定
            # (group_and_organization_list_all_fields_max、既定25) で頭打ちに
            # なるため、offset でページングする
            offset = 0
            while True:
                time.sleep(REQUEST_INTERVAL)
                items = _get(action, {"all_fields": True, "offset": offset})
                if not items:
                    break
                for item in items:
                    f.write(json.dumps(item, ensure_ascii=False) + "\n")
                count += len(items)
                offset += len(items)
        logger.info(f"  {filename}: {count} rows")
