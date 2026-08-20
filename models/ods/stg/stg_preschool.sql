{# 子育て施設のステージング。緯度経度・収容定員を数値化し、
   一時預かり・病児保育を BOOLEAN に正規化する。 #}

{{ ods_geocoded_source('raw_preschool') }}
select
    municipality_code,
    facility_id,
    name,
    name_kana,
    facility_type,
    address,
    prefecture,
    city,
    postal_code,
    phone_number,
    try_cast(lat as double) as lat,
    try_cast(lon as double) as lon,
    {{ ods_geo_columns(geocoded=true) }},
    access,
    parking,
    corporate_name,
    try_cast(capacity as integer) as capacity,
    age_range,
    available_days,
    start_time,
    end_time,
    available_notes,
    {{ ods_flag('temporary_care') }} as temporary_care,
    {{ ods_flag('sick_care') }} as sick_care,
    url,
    notes,
    _extras as extras,
    _package_id as package_id,
    _resource_id as resource_id,
    _org_code as org_code,
    _org_title as org_title,
    _source_url as source_url
from geocoded
