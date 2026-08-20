{# 指定緊急避難場所のステージング。緯度経度・標高を数値化し、
   災害種別を BOOLEAN に正規化する（1/○=true、0/×=false、空欄=NULL）。 #}

{% set flags = [
    'for_flood', 'for_landslide', 'for_storm_surge', 'for_earthquake',
    'for_tsunami', 'for_large_fire', 'for_inland_flooding', 'for_volcano',
    'shelter_overlap',
] %}

{{ ods_geocoded_source('raw_evacuation_space') }}
select
    municipality_code,
    facility_id,
    name,
    name_kana,
    address,
    prefecture,
    city,
    postal_code,
    phone_number,
    try_cast(lat as double) as lat,
    try_cast(lon as double) as lon,
    {{ ods_geo_columns(geocoded=true) }},
    try_cast(elevation as double) as elevation,
    {% for flag in flags %}
    {{ ods_flag(flag) }} as {{ flag }},
    {% endfor %}
    capacity_note,
    target_area,
    url,
    notes,
    _extras as extras,
    _package_id as package_id,
    _resource_id as resource_id,
    _org_code as org_code,
    _org_title as org_title,
    _source_url as source_url
from geocoded
