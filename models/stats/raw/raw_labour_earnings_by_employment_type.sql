{# 東京都「毎月勤労統計調査」年報の第2-1表・第2-2表（就業形態別月間現金給与額）。
   pipelines/labour_earnings_by_employment_type.py が各年の年報から公表年の行（各月と年平均）を
   取り出して data/labour_earnings_by_employment_type/labour_earnings_by_employment_type.ndjson に保存する。
   取得元 URL は raw_labour_earnings_by_employment_type_source を参照。 #}

{{ config(materialized='table') }}

select *
from read_json(
    'data/labour_earnings_by_employment_type/labour_earnings_by_employment_type.ndjson',
    format='newline_delimited',
    columns={
        'report_year': 'VARCHAR',
        'establishment_size': 'VARCHAR',
        'industry': 'VARCHAR',
        'year': 'VARCHAR',
        'period': 'VARCHAR',
        'general_cash_earnings': 'VARCHAR',
        'general_contractual_earnings': 'VARCHAR',
        'general_scheduled_earnings': 'VARCHAR',
        'general_overtime_earnings': 'VARCHAR',
        'general_special_earnings': 'VARCHAR',
        'part_time_cash_earnings': 'VARCHAR',
        'part_time_contractual_earnings': 'VARCHAR',
        'part_time_scheduled_earnings': 'VARCHAR',
        'part_time_overtime_earnings': 'VARCHAR',
        'part_time_special_earnings': 'VARCHAR'
    }
)
