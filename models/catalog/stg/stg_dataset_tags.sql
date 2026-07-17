{# データセットとタグの対応（1行=1データセット×1タグ）。 #}

with exploded as (
    select
        id as package_id,
        unnest(from_json(tags, '[{"name": "VARCHAR"}]')) as t
    from {{ ref('raw_packages') }}
)

select
    package_id,
    t.name as tag
from exploded
