{# ごみの分別方法一覧のステージング。数値・真偽・日付の列を持たない品目マスタのため
   生値をそのまま保持し、_メタ列のみ package_id 等へ改名する。
   料金・粗大ごみ回収料金は「500円」「計量」「申込制…」など自由記述が混在するため文字列のまま。 #}

select
    municipality_code,
    item_id,
    organization_name,
    collection_area,
    item_name,
    item_name_kana,
    item_name_en,
    separation_category,
    caution,
    fee_type,
    fee,
    bulky_fee,
    fee_notes,
    notes,
    _extras as extras,
    _package_id as package_id,
    _resource_id as resource_id,
    _org_code as org_code,
    _org_title as org_title,
    _source_url as source_url
from {{ ref('raw_garbage_separation') }}
