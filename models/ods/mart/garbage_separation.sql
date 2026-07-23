-- ごみの分別方法一覧（自治体標準ODS、区市町村横断）
select
    municipality_code,
    item_id,
    organization_name,
    item_name,
    item_name_kana,
    item_name_en,
    separation_category,
    caution,
    fee_type,
    fee,
    bulky_fee,
    fee_notes,
    collection_area,
    notes,
    extras,
    org_code,
    org_title,
    package_id,
    source_url
from {{ ref('stg_garbage_separation') }}
