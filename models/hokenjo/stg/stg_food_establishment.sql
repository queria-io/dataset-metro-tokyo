{# 食品関係営業台帳のステージング。日付を DATE にし、住所から求めた座標を付ける。

   台帳は緯度経度を持たないので、座標はすべて ABR（アドレス・ベース・レジストリ）
   由来になる。geo_source は 'abr' か NULL の2値で、原典座標を採る ODS のような
   'source' / 'source_swapped' は出ない。 #}

{{ ods_geocoded_source('raw_food_establishment') }}

select
    try_cast(ledger.as_of as date) as source_as_of,
    geocoded.permit_type,
    geocoded.name,
    geocoded.address,
    geocoded.business_type,
    nullif(geocoded.application_type, '') as application_type,
    nullif(geocoded.phone_number, '') as phone_number,
    coalesce(
        try_strptime(geocoded.permit_date, '%Y/%m/%d'),
        try_cast(geocoded.permit_date as timestamp)
    )::date as permit_date,
    nullif(geocoded.operator_name, '') as operator_name,
    nullif(geocoded.operator_address, '') as operator_address,
    nullif(geocoded.operator_phone_number, '') as operator_phone_number,
    nullif(geocoded.representative_name, '') as representative_name,
    geocoded.abr_lat as geo_lat,
    geocoded.abr_lon as geo_lon,
    case when geocoded.abr_lat is not null then 'abr' end as geo_source,
    geocoded.abr_level as geo_level
from geocoded
left join {{ ref('raw_hokenjo_source') }} as ledger
    on ledger.ledger = geocoded.permit_type
