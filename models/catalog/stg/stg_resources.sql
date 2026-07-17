{# リソース（配布ファイル）のステージング。raw_packages の resources JSON 配列を
   1行=1リソースに展開し、型変換する。 #}

with exploded as (
    select
        id as package_id,
        unnest(from_json(resources, '[{
            "id": "VARCHAR",
            "name": "VARCHAR",
            "description": "VARCHAR",
            "format": "VARCHAR",
            "url": "VARCHAR",
            "mimetype": "VARCHAR",
            "size": "VARCHAR",
            "created": "VARCHAR",
            "last_modified": "VARCHAR",
            "metadata_modified": "VARCHAR",
            "datastore_active": "VARCHAR",
            "position": "VARCHAR"
        }]')) as r
    from {{ ref('raw_packages') }}
)

select
    r.id as resource_id,
    package_id,
    r.name,
    r.description,
    r.format,
    r.url,
    r.mimetype,
    try_cast(r.size as bigint) as size_bytes,
    try_cast(r.created as timestamp) as created,
    try_cast(r.last_modified as timestamp) as last_modified,
    try_cast(r.metadata_modified as timestamp) as metadata_modified,
    try_cast(r.datastore_active as boolean) as datastore_active,
    try_cast(r."position" as integer) as resource_position
from exploded
