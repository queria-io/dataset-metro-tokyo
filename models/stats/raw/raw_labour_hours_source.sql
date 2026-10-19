{# 毎月勤労統計調査（月間出勤日数・実労働時間）の取得元（1行 = 1ファイル）。
   pipelines/labour_hours.py が data/labour_hours/source.ndjson に保存する。 #}

{{ config(materialized='table') }}

select *
from read_json(
    'data/labour_hours/source.ndjson',
    format='newline_delimited',
    columns={
        'report_year': 'VARCHAR',
        'table': 'VARCHAR',
        'url': 'VARCHAR',
        'fetched_at': 'VARCHAR',
        'row_count': 'VARCHAR'
    }
)
