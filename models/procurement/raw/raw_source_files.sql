{# 調達情報の取得結果（1行=1リソース）。
   pipelines/procurement.py が data/procurement/source_files.ndjson に書く。 #}

{{ config(materialized='table') }}

select *
from read_json(
    'data/procurement/source_files.ndjson',
    format='newline_delimited',
    columns={
        'package_id': 'VARCHAR',
        'package_name': 'VARCHAR',
        'org_name': 'VARCHAR',
        'resource_name': 'VARCHAR',
        'url': 'VARCHAR',
        'kind': 'VARCHAR',
        'category': 'VARCHAR',
        'period_label': 'VARCHAR',
        'status': 'VARCHAR',
        'reason': 'VARCHAR',
        'rows': 'BIGINT',
        'fetched_at': 'VARCHAR'
    }
)
