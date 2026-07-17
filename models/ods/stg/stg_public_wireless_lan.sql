{# 公衆無線LANアクセスポイントのステージング。緯度経度を数値化する。 #}

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
    installer,
    ssid,
    coverage_area,
    url,
    notes,
    _extras as extras,
    _package_id as package_id,
    _resource_id as resource_id,
    _org_code as org_code,
    _org_title as org_title,
    _source_url as source_url
from {{ ref('raw_public_wireless_lan') }}
