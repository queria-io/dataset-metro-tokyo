{# 東京都「毎月勤労統計調査」年報の第10-1表・第10-2表（常用労働者数・パートタイム労働者比率）。
   pipelines/labour_employment.py が各年の年報から公表年の行（各月と年平均）を取り出して
   data/labour_employment/labour_employment.ndjson に保存する。
   取得元 URL は raw_labour_employment_source を参照。 #}

{{ config(materialized='table') }}

select *
from read_json(
    'data/labour_employment/labour_employment.ndjson',
    format='newline_delimited',
    columns={
        'report_year': 'VARCHAR',
        'establishment_size': 'VARCHAR',
        'industry': 'VARCHAR',
        'year': 'VARCHAR',
        'period': 'VARCHAR',
        'employees_start': 'VARCHAR',
        'employees_start_male': 'VARCHAR',
        'employees_start_female': 'VARCHAR',
        'employees_added': 'VARCHAR',
        'employees_added_male': 'VARCHAR',
        'employees_added_female': 'VARCHAR',
        'employees_removed': 'VARCHAR',
        'employees_removed_male': 'VARCHAR',
        'employees_removed_female': 'VARCHAR',
        'employees': 'VARCHAR',
        'employees_male': 'VARCHAR',
        'employees_female': 'VARCHAR',
        'part_time_ratio': 'VARCHAR',
        'part_time_ratio_male': 'VARCHAR',
        'part_time_ratio_female': 'VARCHAR'
    }
)
