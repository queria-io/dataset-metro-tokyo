"""東京都 子育て施設データのダウンロード。

東京都オープンデータカタログで公開される東京都福祉局「社会福祉施設等一覧」から、
認可保育所と児童館の CSV をダウンロードする。

一覧は年2回（5月時点・10月時点）新しいデータセットとして公開され、その都度
パッケージ ID も配布ファイル名も変わる。そのため URL は固定せず、catalog スキーマ用に
取得済みの packages.ndjson から最新版を解決する。配布 CSV は cp932 のため、
dbt の read_csv がそのまま読めるよう UTF-8 に変換して保存する。

データソース: 東京都オープンデータカタログ
https://catalog.data.metro.tokyo.lg.jp/
"""

import json
import logging
import re
from datetime import UTC, datetime
from pathlib import Path
from urllib.request import Request, urlopen

logger = logging.getLogger("pipelines")

# 一覧を公開している組織（CKAN の organization name）とデータセットの系列
ORG_NAME = "t000054"  # 東京都福祉局
PACKAGE_TITLE_PREFIX = "社会福祉施設等一覧"

# 保存ファイル名 -> リソース名。リソース名は版が変わっても一定
SOURCES = {
    "nursery_school.csv": "認可保育所",
    "children_center.csv": "児童館",
}

# 配布ファイル名の先頭に付く版（YYYYMM）。タイトルの和暦表記は版ごとに揺れる
# （「令和７年５月１日時点」/「令和7年10月１日時点」）ため、版の比較にはこちらを使う
_EDITION_RE = re.compile(r"/(\d{6})-[^/]+\.csv$")

_SOURCE_FILENAME = "source.ndjson"


def _resolve_latest(packages_path: Path) -> tuple[str, dict, dict[str, dict]]:
    """カタログメタデータから最新版の一覧を解決する。

    対象リソースが揃っているパッケージのうち、配布ファイル名の版（YYYYMM）が
    最新のものを採用し、(版, パッケージ, 保存ファイル名 -> リソース) を返す。
    """
    best: tuple[str, dict, dict[str, dict]] | None = None

    with packages_path.open(encoding="utf-8") as f:
        for line in f:
            package = json.loads(line)
            if (package.get("organization") or {}).get("name") != ORG_NAME:
                continue
            if not (package.get("title") or "").startswith(PACKAGE_TITLE_PREFIX):
                continue

            found: dict[str, dict] = {}
            editions: set[str] = set()
            for resource in package.get("resources") or []:
                name = (resource.get("name") or "").strip()
                matched = next(
                    (f for f, n in SOURCES.items() if n == name and f not in found),
                    None,
                )
                if matched is None:
                    continue
                edition = _EDITION_RE.search(resource.get("url") or "")
                if edition is None:
                    continue
                found[matched] = resource
                editions.add(edition.group(1))

            # 版が古いものはリソース名が異なる（平成30年版は「保育所」）ため揃わない
            if len(found) != len(SOURCES):
                continue

            edition = max(editions)
            if best is None or edition > best[0]:
                best = (edition, package, found)

    if best is None:
        raise RuntimeError(
            f"社会福祉施設等一覧の最新版を解決できません"
            f"（organization={ORG_NAME}, resources={list(SOURCES.values())}）: {packages_path}"
        )
    return best


def _load_previous(source_path: Path) -> dict[str, str]:
    """前回取得時の 保存ファイル名 -> URL を返す。未取得なら空。"""
    if not source_path.exists():
        return {}
    previous = {}
    for line in source_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            entry = json.loads(line)
            previous[entry["file"]] = entry["url"]
    return previous


def download_childcare(
    dest_dir: str, packages_path: str = "data/catalog/packages.ndjson"
) -> None:
    """認可保育所・児童館の CSV をダウンロードし UTF-8 に変換して保存する。

    取得元は catalog のメタデータから解決した最新版で、どの版を取り込んだかは
    source.ndjson に記録する。同じ版を取得済みの場合はダウンロードをスキップする。
    """
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)

    edition, package, resolved = _resolve_latest(Path(packages_path))
    logger.info(f"  latest edition: {edition} ({package.get('title')})")

    source_path = dest / _SOURCE_FILENAME
    previous = _load_previous(source_path)
    fetched_at = datetime.now(UTC).isoformat()
    entries = []

    for filename, resource in resolved.items():
        path = dest / filename
        url = resource["url"]

        if path.exists() and previous.get(filename) == url:
            logger.info(f"  skip (already exists: {path})")
        else:
            logger.info(f"  downloading {filename}...")
            req = Request(url, headers={"User-Agent": "dataset-metro-tokyo"})
            with urlopen(req) as resp:
                data = resp.read()

            text = data.decode("cp932")
            path.write_text(text, encoding="utf-8")
            rows = len(text.strip().splitlines()) - 1
            logger.info(f"  {filename}: {rows} rows downloaded")

        entries.append(
            {
                "file": filename,
                "edition": f"{edition[:4]}-{edition[4:]}",
                "package_id": package["id"],
                "package_title": package.get("title"),
                "resource_name": (resource.get("name") or "").strip(),
                "url": url,
                "fetched_at": fetched_at,
            }
        )

    with source_path.open("w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
