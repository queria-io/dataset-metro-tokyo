{# 東京都生計分析調査「都民のくらしむき」年報の長期時系列表1（主な支出及び対前年増加率、全世帯）。
   pipelines/household_budget.py が列（項目）を行に分けて
   data/household_budget/household_budget.ndjson に保存する。
   取得元 URL は raw_household_budget_source を参照。 #}

{{ config(materialized='table') }}

select *
from read_json(
    'data/household_budget/household_budget.ndjson',
    format='newline_delimited',
    columns={
        'year': 'VARCHAR',
        'measure': 'VARCHAR',
        'item_path': 'VARCHAR',
        'unit': 'VARCHAR',
        'value': 'VARCHAR'
    }
)
