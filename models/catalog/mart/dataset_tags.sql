-- データセットとタグの対応
select
    package_id,
    tag
from {{ ref('stg_dataset_tags') }}
