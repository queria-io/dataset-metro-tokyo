{# 東京の労働力（四半期平均の参考表）の取得元（1行 = 1ファイル）。
   pipelines/labour_force_unemployment_rate_quarterly.py が
   data/labour_force_unemployment_rate_quarterly/source.ndjson に保存する。 #}

{{ config(materialized='table') }}

select *
from read_json(
    'data/labour_force_unemployment_rate_quarterly/source.ndjson',
    format='newline_delimited',
    columns={
        'report_year': 'VARCHAR',
        'report_quarter': 'VARCHAR',
        'url': 'VARCHAR',
        'fetched_at': 'VARCHAR',
        'row_count': 'VARCHAR'
    }
)
