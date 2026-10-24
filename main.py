"""東京都オープンデータカタログ データパイプライン。

1. catalog:   カタログメタデータ取得（CKAN API、全データセット・組織・グループ）
2. ods:       自治体標準オープンデータセット取得（ods_datasets.yml 定義の種別）
3. hokenjo:   都の保健所台帳取得（食品関係営業・環境衛生施設。geocode の前に実行する）
4. geocode:   住所をジオコーディング（ods と hokenjo の後に実行する）
5. childcare: 子育て施設データ取得（認可保育所・児童館。catalog の後に実行する）
6. stats:     都の統計データ取得（住民基本台帳による世帯と人口。catalog の後に実行する）
7. stats:     都の統計データ取得（外国人人口の時系列）
8. stats:     都の統計データ取得（毎月勤労統計調査の月間現金給与額）
9. stats:     都の統計データ取得（毎月勤労統計調査の月間出勤日数・実労働時間）
10. stats:    都の統計データ取得（毎月勤労統計調査の常用労働者数・パートタイム労働者比率）
11. stats:    都の統計データ取得（毎月勤労統計調査の就業形態別月間現金給与額）
12. stats:    都の統計データ取得（毎月勤労統計調査の就業形態別月間出勤日数・実労働時間）
13. stats:    都の統計データ取得（毎月勤労統計調査の就業形態別常用労働者数）
14. stats:    都の統計データ取得（毎月勤労統計調査の規模別月間現金給与額）
15. dbt:      dbt ビルド
"""

import logging

from dbt.cli.main import dbtRunner

from pipelines.childcare import download_childcare
from pipelines.ckan import download_catalog
from pipelines.foreign_population import download_foreign_population
from pipelines.geocode import geocode
from pipelines.hokenjo import download_hokenjo
from pipelines.labour_earnings import download_labour_earnings
from pipelines.labour_earnings_by_employment_type import (
    download_labour_earnings_by_employment_type,
)
from pipelines.labour_earnings_by_size import download_labour_earnings_by_size
from pipelines.labour_employment import download_labour_employment
from pipelines.labour_employment_by_employment_type import (
    download_labour_employment_by_employment_type,
)
from pipelines.labour_hours import download_labour_hours
from pipelines.labour_hours_by_employment_type import (
    download_labour_hours_by_employment_type,
)
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
    logger.info("1/15: catalog (カタログメタデータ)")
    download_catalog("data/catalog")

    # 2. 自治体標準オープンデータセット（catalog のメタデータから対象を判定）
    logger.info("2/15: ods (自治体標準オープンデータセット)")
    download_and_normalize()

    # 3. 都の保健所台帳（配布ページから CSV のリンクを解決）
    logger.info("3/15: hokenjo (保健所台帳)")
    download_hokenjo("data/hokenjo")

    # 4. 住所のジオコーディング（ods と hokenjo が書いた NDJSON の住所を読む）
    logger.info("4/15: geocode (住所のジオコーディング)")
    geocode()

    # 5. 子育て施設データ（catalog のメタデータから最新版の一覧を解決）
    logger.info("5/15: childcare (子育て施設データ)")
    download_childcare("data/childcare")

    # 6. 都の統計データ（catalog のメタデータから最新月を解決）
    logger.info("6/15: stats (住民基本台帳による世帯と人口)")
    download_resident_population("data/resident_population")

    # 7. 都の統計データ（外国人人口の時系列。1ファイルに全年が入る）
    logger.info("7/15: stats (外国人人口)")
    download_foreign_population("data/foreign_population")

    # 8. 都の統計データ（毎月勤労統計調査。年報の一覧から各年の表を解決する）
    logger.info("8/15: stats (毎月勤労統計調査)")
    download_labour_earnings("data/labour_earnings")

    # 9. 都の統計データ（毎月勤労統計調査の第6表。第1表と同じ年報から取る）
    logger.info("9/15: stats (毎月勤労統計調査の労働時間)")
    download_labour_hours("data/labour_hours")

    # 10. 都の統計データ（毎月勤労統計調査の第10表。第1表と同じ年報から取る）
    logger.info("10/15: stats (毎月勤労統計調査の常用労働者数)")
    download_labour_employment("data/labour_employment")

    # 11. 都の統計データ（毎月勤労統計調査の第2表。第1表と同じ年報から取る）
    logger.info("11/15: stats (毎月勤労統計調査の就業形態別現金給与額)")
    download_labour_earnings_by_employment_type(
        "data/labour_earnings_by_employment_type"
    )

    # 12. 都の統計データ（毎月勤労統計調査の第7表。第1表と同じ年報から取る）
    logger.info("12/15: stats (毎月勤労統計調査の就業形態別労働時間)")
    download_labour_hours_by_employment_type("data/labour_hours_by_employment_type")

    # 13. 都の統計データ（毎月勤労統計調査の第11表。第1表と同じ年報から取る）
    logger.info("13/15: stats (毎月勤労統計調査の就業形態別常用労働者数)")
    download_labour_employment_by_employment_type(
        "data/labour_employment_by_employment_type"
    )

    # 14. 都の統計データ（毎月勤労統計調査の第3表。第1表と同じ年報から取る）
    logger.info("14/15: stats (毎月勤労統計調査の規模別現金給与額)")
    download_labour_earnings_by_size("data/labour_earnings_by_size")

    # 15. dbt ビルド
    logger.info("15/15: dbt build")
    dbt_build()


if __name__ == "__main__":
    main()
