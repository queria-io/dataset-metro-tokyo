-- 環境衛生施設台帳（東京都が設置する保健所の管轄。時点は source_as_of）
select
    source_as_of,
    facility_type,
    permit_number,
    business_form,
    name,
    address,
    building,
    phone_number,
    permit_date,
    operator_name,
    operator_address,
    operator_building,
    operator_phone_number,
    representative_name,
    geo_lat,
    geo_lon,
    geo_source,
    geo_level,
    {{ ods_geometry() }} as geometry
from {{ ref('stg_sanitation_facility') }}
