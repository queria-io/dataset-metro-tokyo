-- 食品関係営業台帳（東京都が設置する保健所の管轄。時点は source_as_of）
select
    source_as_of,
    permit_type,
    name,
    address,
    business_type,
    application_type,
    phone_number,
    permit_date,
    operator_name,
    operator_address,
    operator_phone_number,
    representative_name,
    city_code,
    geo_lat,
    geo_lon,
    geo_source,
    geo_level,
    {{ ods_geometry() }} as geometry
from {{ ref('stg_food_establishment') }}
