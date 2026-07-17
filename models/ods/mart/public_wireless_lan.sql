-- 公衆無線LANアクセスポイント一覧（自治体標準ODS、区市町村横断）
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
    lat,
    lon,
    installer,
    ssid,
    coverage_area,
    url,
    notes,
    extras,
    org_code,
    org_title,
    package_id,
    source_url
from {{ ref('stg_public_wireless_lan') }}
