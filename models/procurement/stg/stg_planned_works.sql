{# 工事の発注予定のステージング。緯度・経度を DOUBLE に型変換する。
   工期は原典が「2026-12」（年月）と「2026-11-01」（年月日）の両方で書くため文字列のまま持つ。 #}

select
    org_code,
    org_name,
    category,
    period_label,
    work_type,
    title,
    location,
    location_prefecture,
    location_city,
    location_town,
    location_block,
    location_building,
    try_cast(lat as double) as lat,
    try_cast(lon as double) as lon,
    period_start,
    period_end,
    summary,
    bidding_method,
    bidding_timing,
    note,
    source_resource,
    source_url
from {{ ref('raw_planned_works') }}
