{# 毎月勤労統計調査（常用労働者数・パートタイム労働者比率）の取得元（1行 = 1ファイル）。
   pipelines/labour_employment.py が data/labour_employment/source.ndjson に保存する。 #}

{{ config(materialized='table') }}

select *
from read_json(
    'data/labour_employment/source.ndjson',
    format='newline_delimited',
    columns={
        'report_year': 'VARCHAR',
        'table': 'VARCHAR',
        'url': 'VARCHAR',
        'fetched_at': 'VARCHAR',
        'row_count': 'VARCHAR'
    }
)
