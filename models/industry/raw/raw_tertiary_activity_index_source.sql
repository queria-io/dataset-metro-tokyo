{# 第3次産業活動指数の取得元（1行 = 1ファイル）。
   pipelines/tertiary_activity_index.py が data/tertiary_activity_index/source.ndjson に保存する。 #}

{{ config(materialized='table') }}

select *
from read_json(
    'data/tertiary_activity_index/source.ndjson',
    format='newline_delimited',
    columns={
        'index_type': 'VARCHAR',
        'url': 'VARCHAR',
        'fetched_at': 'VARCHAR',
        'row_count': 'VARCHAR'
    }
)
