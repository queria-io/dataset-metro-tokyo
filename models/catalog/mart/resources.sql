-- 全データセットのリソース（配布ファイル）一覧
select
    resource_id,
    package_id,
    name,
    description,
    format,
    url,
    mimetype,
    size_bytes,
    created,
    last_modified,
    resource_position
from {{ ref('stg_resources') }}
