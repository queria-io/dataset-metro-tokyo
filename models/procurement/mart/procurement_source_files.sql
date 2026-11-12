{{ config(alias='source_files') }}

-- 調達情報の取得結果（1行=1リソース）
select
    package_name,
    org_name,
    kind,
    category,
    period_label,
    resource_name,
    url,
    status,
    reason,
    rows,
    fetched_at
from {{ ref('raw_source_files') }}
