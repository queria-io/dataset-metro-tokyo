{# 都民のくらしむき（長期時系列表1）の取得元（1行 = 1ファイル）。
   pipelines/household_budget.py が data/household_budget/source.ndjson に保存する。 #}

{{ config(materialized='table') }}

select *
from read_json(
    'data/household_budget/source.ndjson',
    format='newline_delimited',
    columns={
        'report_year': 'VARCHAR',
        'url': 'VARCHAR',
        'fetched_at': 'VARCHAR',
        'row_count': 'VARCHAR'
    }
)
