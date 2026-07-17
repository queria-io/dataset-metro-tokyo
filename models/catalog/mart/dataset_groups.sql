-- データセットとグループ（分野分類）の対応
select
    package_id,
    group_code
from {{ ref('stg_dataset_groups') }}
