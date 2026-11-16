{# 東京の労働力（年平均の第8表）の取得元（1行 = 1ファイル）。
   pipelines/labour_force_by_employment_type.py が
   data/labour_force_by_employment_type/source.ndjson に保存する。 #}

{{ config(materialized='table') }}

select *
from read_json(
    'data/labour_force_by_employment_type/source.ndjson',
    format='newline_delimited',
    columns={
        'report_year': 'VARCHAR',
        'url': 'VARCHAR',
        'fetched_at': 'VARCHAR',
        'row_count': 'VARCHAR'
    }
)
