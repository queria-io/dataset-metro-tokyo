-- 認可保育所（令和7年5月1日時点）
select
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
