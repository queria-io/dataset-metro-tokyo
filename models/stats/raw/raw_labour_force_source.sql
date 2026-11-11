{# 東京の労働力（年平均の第1表）の取得元（1行 = 1ファイル）。
   pipelines/labour_force.py が data/labour_force/source.ndjson に保存する。 #}

{{ config(materialized='table') }}

select *
from read_json(
    'data/labour_force/source.ndjson',
    format='newline_delimited',
    columns={
        'year': 'VARCHAR',
        'table': 'VARCHAR',
        'url': 'VARCHAR',
        'fetched_at': 'VARCHAR',
        'row_count': 'VARCHAR'
    }
)
