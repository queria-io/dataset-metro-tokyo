{# 東京の労働力（四半期平均の第1表）の取得元（1行 = 1ファイル）。
   pipelines/labour_force_quarterly.py が data/labour_force_quarterly/source.ndjson に保存する。 #}

{{ config(materialized='table') }}

select *
from read_json(
    'data/labour_force_quarterly/source.ndjson',
    format='newline_delimited',
    columns={
        'year': 'VARCHAR',
        'quarter': 'VARCHAR',
        'table': 'VARCHAR',
        'url': 'VARCHAR',
        'fetched_at': 'VARCHAR',
        'row_count': 'VARCHAR'
    }
)
