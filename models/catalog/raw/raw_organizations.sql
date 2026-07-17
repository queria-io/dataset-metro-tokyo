{# 東京都オープンデータカタログ CKAN API organization_list(all_fields) の生データ。
   pipelines/ckan.py が data/catalog/organizations.ndjson に保存する。 #}

{{ config(materialized='table') }}

select *
from read_json(
    'data/catalog/organizations.ndjson',
    format='newline_delimited',
    columns={
        'id': 'VARCHAR',
        'name': 'VARCHAR',
        'title': 'VARCHAR',
        'description': 'VARCHAR',
        'package_count': 'VARCHAR',
        'created': 'VARCHAR',
        'state': 'VARCHAR'
    }
)
