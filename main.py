"""東京都オープンデータカタログ データパイプライン。

1. catalog:   カタログメタデータ取得（CKAN API、全データセット・組織・グループ）
2. ods:       自治体標準オープンデータセット取得（ods_datasets.yml 定義の種別）
3. hokenjo:   都の保健所台帳取得（食品関係営業・環境衛生施設。geocode の前に実行する）
4. geocode:   住所をジオコーディング（ods と hokenjo の後に実行する）
5. childcare: 子育て施設データ取得（認可保育所・児童館。catalog の後に実行する）
6. stats:     都の統計データ取得（住民基本台帳による世帯と人口。catalog の後に実行する）
7. dbt:       dbt ビルド
"""

import logging

from dbt.cli.main import dbtRunner

from pipelines.childcare import download_childcare
from pipelines.ckan import download_catalog
from pipelines.geocode import geocode
from pipelines.hokenjo import download_hokenjo
from pipelines.ods import download_and_normalize
from pipelines.resident_population import download_resident_population

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
    logger.info("1/7: catalog (カタログメタデータ)")
    download_catalog("data/catalog")

    # 2. 自治体標準オープンデータセット（catalog のメタデータから対象を判定）
    logger.info("2/7: ods (自治体標準オープンデータセット)")
    download_and_normalize()

    # 3. 都の保健所台帳（配布ページから CSV のリンクを解決）
    logger.info("3/7: hokenjo (保健所台帳)")
    download_hokenjo("data/hokenjo")

    # 4. 住所のジオコーディング（ods と hokenjo が書いた NDJSON の住所を読む）
    logger.info("4/7: geocode (住所のジオコーディング)")
    geocode()

    # 5. 子育て施設データ（catalog のメタデータから最新版の一覧を解決）
    logger.info("5/7: childcare (子育て施設データ)")
    download_childcare("data/childcare")

    # 6. 都の統計データ（catalog のメタデータから最新月を解決）
    logger.info("6/7: stats (住民基本台帳による世帯と人口)")
    download_resident_population("data/resident_population")

    # 7. dbt ビルド
    logger.info("7/7: dbt build")
    dbt_build()


if __name__ == "__main__":
    main()
