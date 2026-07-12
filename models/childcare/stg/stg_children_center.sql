{# 児童館のステージング。列名を英語化し、経度・緯度を DOUBLE、
   定員を INTEGER に型変換する（'-' や空欄は NULL）。 #}

select
    "設置" as establisher_type,
    "施設名" as name,
    "郵便番号" as postal_code,
    "所在地" as address,
    try_cast("経度" as double) as lon,
    try_cast("緯度" as double) as lat,
    "座標系" as crs,
    "電話番号" as phone_number,
    try_cast(nullif(nullif(trim("定員"), ''), '-') as integer) as capacity
from {{ ref('raw_children_center') }}
