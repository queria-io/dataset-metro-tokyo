{# 小中学校通学区域のステージング。登録日・廃止日を DATE に変換し、
   行政サービス拠点種別（POIコード）から学校種別を導出する。
   POIコードは定義書で小学校=1503・中学校=1504 のみが定義されているため、
   それ以外の値は生コードを保持して種別を NULL にする。 #}

select
    municipality_code,
    school_id,
    school_code,
    prefecture,
    district,
    city,
    ward,
    school_municipality_code,
    name,
    name_kana,
    poi_code,
    case poi_code
        when '1503' then '小学校'
        when '1504' then '中学校'
    end as school_type,
    {{ ods_date('registered_date') }} as registered_date,
    {{ ods_date('abolished_date') }} as abolished_date,
    district_addresses,
    notes,
    polygon_file,
    _extras as extras,
    _package_id as package_id,
    _resource_id as resource_id,
    _org_code as org_code,
    _org_title as org_title,
    _source_url as source_url
from {{ ref('raw_school_district') }}
