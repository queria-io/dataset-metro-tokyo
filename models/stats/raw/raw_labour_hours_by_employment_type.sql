{# 東京都「毎月勤労統計調査」年報の第7-1表・第7-2表（就業形態別月間出勤日数・実労働時間）。
   pipelines/labour_hours_by_employment_type.py が各年の年報から公表年の行（各月と年平均）を
   取り出して data/labour_hours_by_employment_type/labour_hours_by_employment_type.ndjson に保存する。
   取得元 URL は raw_labour_hours_by_employment_type_source を参照。 #}

{{ config(materialized='table') }}

select *
from read_json(
    'data/labour_hours_by_employment_type/labour_hours_by_employment_type.ndjson',
    format='newline_delimited',
    columns={
        'report_year': 'VARCHAR',
        'establishment_size': 'VARCHAR',
        'industry': 'VARCHAR',
        'year': 'VARCHAR',
        'period': 'VARCHAR',
        'general_days_worked': 'VARCHAR',
        'general_total_hours': 'VARCHAR',
        'general_scheduled_hours': 'VARCHAR',
        'general_overtime_hours': 'VARCHAR',
        'part_time_days_worked': 'VARCHAR',
        'part_time_total_hours': 'VARCHAR',
        'part_time_scheduled_hours': 'VARCHAR',
        'part_time_overtime_hours': 'VARCHAR'
    }
)
