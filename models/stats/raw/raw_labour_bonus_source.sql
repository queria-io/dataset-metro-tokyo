{# 毎月勤労統計調査（夏季・冬季賞与）の取得元（1行 = 1ファイル）。
   pipelines/labour_bonus.py が data/labour_bonus/source.ndjson に保存する。 #}

{{ config(materialized='table') }}

select *
from read_json(
    'data/labour_bonus/source.ndjson',
    format='newline_delimited',
    columns={
        'report_year': 'VARCHAR',
        'table': 'VARCHAR',
        'url': 'VARCHAR',
        'fetched_at': 'VARCHAR',
        'row_count': 'VARCHAR'
    }
)
