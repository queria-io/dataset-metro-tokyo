{# 教育機関一覧のステージング。緯度経度を数値化し、属性情報の設定日・廃止日を DATE に正規化する。
   学校種・設置区分は自治体ごとに統制コード（A1/B1 等）と日本語ラベルが混在するため生値を保持する。
   所在地は市区町村/町字/番地以下に分かれ、連結表記の列を持たない。 #}

select
    school_code,
    school_type,
    prefecture_code,
    establishment_category,
    establisher,
    branch_type,
    main_school_code,
    main_school_name,
    name,
    name_kana,
    name_alias,
    city,
    town,
    street_number,
    postal_code,
    try_cast(lat as double) as lat,
    try_cast(lon as double) as lon,
    contact_name,
    phone_number,
    {{ ods_date('attribute_set_date') }} as attribute_set_date,
    {{ ods_date('attribute_abolished_date') }} as attribute_abolished_date,
    old_survey_number,
    new_school_code,
    _extras as extras,
    _package_id as package_id,
    _resource_id as resource_id,
    _org_code as org_code,
    _org_title as org_title,
    _source_url as source_url
from {{ ref('raw_educational_institution') }}
