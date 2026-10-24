{# 毎月勤労統計調査（就業形態別常用労働者数）の取得元（1行 = 1ファイル）。
   pipelines/labour_employment_by_employment_type.py が data/labour_employment_by_employment_type/source.ndjson に保存する。 #}

{{ config(materialized='table') }}

select *
from read_json(
    'data/labour_employment_by_employment_type/source.ndjson',
    format='newline_delimited',
    columns={
        'report_year': 'VARCHAR',
        'table': 'VARCHAR',
        'url': 'VARCHAR',
        'fetched_at': 'VARCHAR',
        'row_count': 'VARCHAR'
    }
)
