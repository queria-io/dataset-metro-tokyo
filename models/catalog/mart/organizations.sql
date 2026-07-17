-- データ提供組織（都庁各局・区市町村）の一覧
select
    organization_code,
    title,
    organization_type,
    description,
    dataset_count
from {{ ref('stg_organizations') }}
