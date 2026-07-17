"""東京都オープンデータカタログ データパイプライン。

1. catalog:   カタログメタデータ取得（CKAN API、全データセット・組織・グループ）
2. childcare: 子育て施設データ取得（認可保育所・児童館）
3. dbt:       dbt ビルド
"""

import logging

from dbt.cli.main import dbtRunner

from pipelines.childcare import download_childcare
from pipelines.ckan import download_catalog

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("pipelines")


def dbt_build():
    dbt = dbtRunner()

    result = dbt.invoke(["deps"])
    if not result.success:
        raise SystemExit("dbt deps failed")

    result = dbt.invoke(["build"])
    if not result.success:
        raise SystemExit("dbt build failed")

    result = dbt.invoke(["docs", "generate"])
    if not result.success:
        raise SystemExit("dbt docs generate failed")


def main():
    # 1. カタログメタデータ（CKAN API）
    logger.info("1/3: catalog (カタログメタデータ)")
    download_catalog("data/catalog")

    # 2. 子育て施設データ（東京都福祉局 社会福祉施設等一覧）
    logger.info("2/3: childcare (子育て施設データ)")
    download_childcare("data/childcare")

    # 3. dbt ビルド
    logger.info("3/3: dbt build")
    dbt_build()


if __name__ == "__main__":
    main()
