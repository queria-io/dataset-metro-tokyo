{# グループ（分野分類）のステージング。 #}

select
    name as group_code,
    title,
    description,
    try_cast(package_count as integer) as dataset_count,
    try_cast(created as timestamp) as created
from {{ ref('raw_groups') }}
