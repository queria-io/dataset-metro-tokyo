"""東京都 子育て施設データのダウンロード。

東京都オープンデータカタログで公開される東京都福祉局
「社会福祉施設等一覧（令和7年5月1日時点）」から、認可保育所と児童館の
CSV をダウンロードする。配布 CSV は cp932 のため、dbt の read_csv が
そのまま読めるよう UTF-8 に変換して保存する。

データソース: 東京都オープンデータカタログ
https://catalog.data.metro.tokyo.lg.jp/
"""

import logging
from pathlib import Path
from urllib.request import Request, urlopen

logger = logging.getLogger("pipelines")

SOURCES = {
    "nursery_school.csv": (
        "https://www.opendata.metro.tokyo.lg.jp/fukushi/202505-2-1-hoikusyo.csv"
    ),
    "children_center.csv": (
        "https://www.opendata.metro.tokyo.lg.jp/fukushi/202505-2-2_06-zidoukan.csv"
    ),
}


def download_childcare(dest_dir: str) -> None:
    """認可保育所・児童館の CSV をダウンロードし UTF-8 に変換して保存する。

    既にダウンロード済みの場合はスキップする。
    """
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)

    for filename, url in SOURCES.items():
        path = dest / filename
        if path.exists():
            logger.info(f"  skip (already exists: {path})")
            continue

        logger.info(f"  downloading {filename}...")
        req = Request(url, headers={"User-Agent": "dataset-metro-tokyo"})
        with urlopen(req) as resp:
            data = resp.read()

        text = data.decode("cp932")
        path.write_text(text, encoding="utf-8")
        rows = len(text.strip().splitlines()) - 1
        logger.info(f"  {filename}: {rows} rows downloaded")
