{# ODS 取り込みの実行結果（1行=1リソース）。
   pipelines/ods.py が data/ods/source_files.ndjson に保存する。 #}

{{ config(materialized='table') }}

select *
from read_json(
    'data/ods/source_files.ndjson',
    format='newline_delimited',
    columns={
        'dataset_id': 'VARCHAR',
        'package_id': 'VARCHAR',
        'package_title': 'VARCHAR',
        'resource_id': 'VARCHAR',
        'resource_name': 'VARCHAR',
        'org_code': 'VARCHAR',
        'org_title': 'VARCHAR',
        'url': 'VARCHAR',
        'fetched_at': 'VARCHAR',
        'status': 'VARCHAR',
        'reason': 'VARCHAR',
        'encoding': 'VARCHAR',
        'row_count': 'VARCHAR'
    }
)
