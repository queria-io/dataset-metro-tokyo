{# データセットとグループ（分野分類）の対応（1行=1データセット×1グループ）。 #}

with exploded as (
    select
        id as package_id,
        unnest(from_json(groups, '[{"name": "VARCHAR", "title": "VARCHAR"}]')) as g
    from {{ ref('raw_packages') }}
)

select
    package_id,
    g.name as group_code,
    g.title as group_title
from exploded
