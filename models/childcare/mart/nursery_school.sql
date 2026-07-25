-- 認可保育所（東京都福祉局が公開する最新版。時点は source_edition）
select
    source_edition,
    establisher_type,
    name,
    postal_code,
    address,
    lon,
    lat,
    crs,
    phone_number,
    capacity
from {{ ref('stg_nursery_school') }}
