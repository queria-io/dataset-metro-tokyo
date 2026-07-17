{# ODS 取り込み結果のステージング。行数・取得日時を型変換する。 #}

select
    dataset_id,
    package_id,
    package_title,
    resource_id,
    resource_name,
    org_code,
    org_title,
    url,
    status,
    reason,
    encoding,
    try_cast(row_count as integer) as row_count,
    try_cast(fetched_at as timestamp) as fetched_at
from {{ ref('raw_ods_source_files') }}
