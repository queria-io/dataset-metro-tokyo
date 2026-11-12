{# 物品買入れの発注予定のステージング。原典の列をそのまま持つ。 #}

select
    org_code,
    org_name,
    category,
    period_label,
    item_type,
    title,
    delivery_place,
    delivery_deadline,
    summary,
    bidding_method,
    bidding_timing,
    note,
    source_resource,
    source_url
from {{ ref('raw_planned_goods') }}
