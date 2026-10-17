{# 外国人人口の取得元（1行 = 1ファイル）。
   pipelines/foreign_population.py が data/foreign_population/source.ndjson に保存する。 #}

{{ config(materialized='table') }}

select *
from read_json(
    'data/foreign_population/source.ndjson',
    format='newline_delimited',
    columns={
        'url': 'VARCHAR',
        'fetched_at': 'VARCHAR',
        'row_count': 'VARCHAR'
    }
)
