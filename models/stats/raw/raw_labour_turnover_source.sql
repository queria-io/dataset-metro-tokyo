{# 毎月勤労統計調査（労働異動率）の取得元（1行 = 1ファイル）。
   pipelines/labour_turnover.py が data/labour_turnover/source.ndjson に保存する。 #}

{{ config(materialized='table') }}

select *
from read_json(
    'data/labour_turnover/source.ndjson',
    format='newline_delimited',
    columns={
        'report_year': 'VARCHAR',
        'table': 'VARCHAR',
        'url': 'VARCHAR',
        'fetched_at': 'VARCHAR',
        'row_count': 'VARCHAR'
    }
)
