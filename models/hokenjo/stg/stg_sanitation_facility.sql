{# 環境衛生施設台帳のステージング。日付を DATE にし、住所から求めた座標を付ける。

   施設所在地はビル名が別列になっているので、住所の突合には施設所在地だけを使う
   （pipelines/geocode.py も同じ列を読む）。 #}

{{ ods_geocoded_source('raw_sanitation_facility', columns=['lg_code']) }}

select
    try_cast(ledger.as_of as date) as source_as_of,
    geocoded.facility_type,
    geocoded.permit_number,
    nullif(geocoded.business_form, '') as business_form,
    geocoded.name,
    geocoded.address,
    nullif(geocoded.building, '') as building,
    nullif(geocoded.phone_number, '') as phone_number,
    coalesce(
        try_strptime(geocoded.permit_date, '%Y/%m/%d'),
        try_cast(geocoded.permit_date as timestamp)
    )::date as permit_date,
    nullif(geocoded.operator_name, '') as operator_name,
    nullif(geocoded.operator_address, '') as operator_address,
    nullif(geocoded.operator_building, '') as operator_building,
    nullif(geocoded.operator_phone_number, '') as operator_phone_number,
    nullif(geocoded.representative_name, '') as representative_name,
    left(geocoded.abr_lg_code, 5) as city_code,
    geocoded.abr_lat as geo_lat,
    geocoded.abr_lon as geo_lon,
    case when geocoded.abr_lat is not null then 'abr' end as geo_source,
    geocoded.abr_level as geo_level
from geocoded
left join {{ ref('raw_hokenjo_source') }} as ledger
    on ledger.ledger = geocoded.facility_type
