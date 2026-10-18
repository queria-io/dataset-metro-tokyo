{# 東京都「毎月勤労統計調査」年報の第1-1表・第1-2表（月間現金給与額）。
   pipelines/labour_earnings.py が各年の年報から公表年の行（各月と年平均）を取り出して
   data/labour_earnings/labour_earnings.ndjson に保存する。
   取得元 URL は raw_labour_earnings_source を参照。 #}

{{ config(materialized='table') }}

select *
from read_json(
    'data/labour_earnings/labour_earnings.ndjson',
    format='newline_delimited',
    columns={
        'report_year': 'VARCHAR',
        'establishment_size': 'VARCHAR',
        'industry': 'VARCHAR',
        'year': 'VARCHAR',
        'period': 'VARCHAR',
        'cash_earnings': 'VARCHAR',
        'cash_earnings_male': 'VARCHAR',
        'cash_earnings_female': 'VARCHAR',
        'contractual_earnings': 'VARCHAR',
        'contractual_earnings_male': 'VARCHAR',
        'contractual_earnings_female': 'VARCHAR',
        'scheduled_earnings': 'VARCHAR',
        'overtime_earnings': 'VARCHAR',
        'special_earnings': 'VARCHAR',
        'special_earnings_male': 'VARCHAR',
        'special_earnings_female': 'VARCHAR'
    }
)
