{# 東京の労働力（年平均の第6表）の取得元（1行 = 1ファイル）。
   pipelines/labour_force_by_occupation.py が
   data/labour_force_by_occupation/source.ndjson に保存する。 #}

{{ config(materialized='table') }}

select *
from read_json(
    'data/labour_force_by_occupation/source.ndjson',
    format='newline_delimited',
    columns={
        'report_year': 'VARCHAR',
        'url': 'VARCHAR',
        'fetched_at': 'VARCHAR',
        'row_count': 'VARCHAR'
    }
)
