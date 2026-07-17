{# 東京都オープンデータカタログ CKAN API package_search の生データ（1行=1データセット）。
   pipelines/ckan.py が data/catalog/packages.ndjson に保存する。
   ネスト構造（organization / resources / tags / groups / extras）は JSON 型のまま保持し、
   展開・型変換は stg 以降で行う。 #}

{{ config(materialized='table') }}

select *
from read_json(
    'data/catalog/packages.ndjson',
    format='newline_delimited',
    columns={
        'id': 'VARCHAR',
        'name': 'VARCHAR',
        'title': 'VARCHAR',
        'notes': 'VARCHAR',
        'license_id': 'VARCHAR',
        'license_title': 'VARCHAR',
        'license_url': 'VARCHAR',
        'maintainer': 'VARCHAR',
        'metadata_created': 'VARCHAR',
        'metadata_modified': 'VARCHAR',
        'num_resources': 'VARCHAR',
        'num_tags': 'VARCHAR',
        'owner_org': 'VARCHAR',
        'private': 'VARCHAR',
        'state': 'VARCHAR',
        'type': 'VARCHAR',
        'url': 'VARCHAR',
        'organization': 'JSON',
        'extras': 'JSON',
        'groups': 'JSON',
        'resources': 'JSON',
        'tags': 'JSON'
    }
)
