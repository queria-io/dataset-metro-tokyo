{# 東京都「毎月勤労統計調査」年報の第6-1表・第6-2表（月間出勤日数・実労働時間）。
   pipelines/labour_hours.py が各年の年報から公表年の行（各月と年平均）を取り出して
   data/labour_hours/labour_hours.ndjson に保存する。
   取得元 URL は raw_labour_hours_source を参照。 #}

{{ config(materialized='table') }}

select *
from read_json(
    'data/labour_hours/labour_hours.ndjson',
    format='newline_delimited',
    columns={
        'report_year': 'VARCHAR',
        'establishment_size': 'VARCHAR',
        'industry': 'VARCHAR',
        'year': 'VARCHAR',
        'period': 'VARCHAR',
        'days_worked': 'VARCHAR',
        'days_worked_male': 'VARCHAR',
        'days_worked_female': 'VARCHAR',
        'total_hours': 'VARCHAR',
        'total_hours_male': 'VARCHAR',
        'total_hours_female': 'VARCHAR',
        'scheduled_hours': 'VARCHAR',
        'scheduled_hours_male': 'VARCHAR',
        'scheduled_hours_female': 'VARCHAR',
        'overtime_hours': 'VARCHAR',
        'overtime_hours_male': 'VARCHAR',
        'overtime_hours_female': 'VARCHAR'
    }
)
