-- グループ（分野分類）の一覧
select
    group_code,
    title,
    description,
    dataset_count
from {{ ref('stg_groups') }}
