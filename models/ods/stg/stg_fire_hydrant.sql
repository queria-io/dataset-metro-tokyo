{# 消防水利施設のステージング。緯度経度と口径を数値化する。
   種別は自治体ごとに表記が揺れる（防火水槽 / 防火水そう など）が、
   定義書に統制語彙が無いため生値を保持する。 #}

{{ ods_geocoded_source('raw_fire_hydrant') }}
select
    municipality_code,
    facility_id,
    organization_name,
    facility_type,
    location_municipality_code,
    town_id,
    address,
    prefecture,
    city,
    town,
    street_number,
    building_name,
    try_cast(lat as double) as lat,
    try_cast(lon as double) as lon,
    {{ ods_geo_columns(geocoded=true) }},
    try_cast(diameter as integer) as diameter,
    notes,
    _extras as extras,
    _package_id as package_id,
    _resource_id as resource_id,
    _org_code as org_code,
    _org_title as org_title,
    _source_url as source_url
from geocoded
