"""東京都オープンデータカタログ データパイプライン。

1. catalog:   カタログメタデータ取得（CKAN API、全データセット・組織・グループ）
2. ods:       自治体標準オープンデータセット取得（ods_datasets.yml 定義の種別）
3. childcare: 子育て施設データ取得（認可保育所・児童館。catalog の後に実行する）
4. dbt:       dbt ビルド
"""

import logging

from dbt.cli.main import dbtRunner

from pipelines.childcare import download_childcare
from pipelines.ckan import download_catalog
from pipelines.ods import download_and_normalize

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
    logger.info("1/4: catalog (カタログメタデータ)")
    download_catalog("data/catalog")

    # 2. 自治体標準オープンデータセット（catalog のメタデータから対象を判定）
    logger.info("2/4: ods (自治体標準オープンデータセット)")
    download_and_normalize()

    # 3. 子育て施設データ（catalog のメタデータから最新版の一覧を解決）
    logger.info("3/4: childcare (子育て施設データ)")
    download_childcare("data/childcare")

    # 4. dbt ビルド
    logger.info("4/4: dbt build")
    dbt_build()


if __name__ == "__main__":
    main()
