-- 東京都オープンデータカタログの全データセット一覧
select
    package_id,
    dataset_code,
    title,
    description,
    organization_code,
    organization_title,
    license_id,
    license_title,
    maintainer,
    update_frequency,
    num_resources,
    metadata_created,
    metadata_modified,
    'https://catalog.data.metro.tokyo.lg.jp/dataset/' || dataset_code as portal_url
from {{ ref('stg_datasets') }}
