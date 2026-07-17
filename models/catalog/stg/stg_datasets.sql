{# データセットメタデータのステージング。列名を英語化し、日時を TIMESTAMP に型変換。
   extras（key-value の JSON 配列）から「更新頻度」を抽出する。 #}

select
    id as package_id,
    name as dataset_code,
    title,
    notes as description,
    json_extract_string(organization, '$.name') as organization_code,
    json_extract_string(organization, '$.title') as organization_title,
    license_id,
    license_title,
    maintainer,
    list_filter(
        from_json(extras, '[{"key":"VARCHAR","value":"VARCHAR"}]'),
        e -> e.key = '更新頻度'
    )[1].value as update_frequency,
    try_cast(num_resources as integer) as num_resources,
    try_cast(num_tags as integer) as num_tags,
    try_cast(metadata_created as timestamp) as metadata_created,
    try_cast(metadata_modified as timestamp) as metadata_modified
from {{ ref('raw_packages') }}
