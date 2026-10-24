{# 東京都「毎月勤労統計調査」年報の第11-1表・第11-2表（就業形態別常用労働者数）。
   pipelines/labour_employment_by_employment_type.py が各年の年報から公表年の行（各月と年平均）を
   取り出して data/labour_employment_by_employment_type/labour_employment_by_employment_type.ndjson に保存する。
   取得元 URL は raw_labour_employment_by_employment_type_source を参照。 #}

{{ config(materialized='table') }}

select *
from read_json(
    'data/labour_employment_by_employment_type/labour_employment_by_employment_type.ndjson',
    format='newline_delimited',
    columns={
        'report_year': 'VARCHAR',
        'establishment_size': 'VARCHAR',
        'industry': 'VARCHAR',
        'year': 'VARCHAR',
        'period': 'VARCHAR',
        'general_employees_start': 'VARCHAR',
        'general_employees_added': 'VARCHAR',
        'general_employees_removed': 'VARCHAR',
        'general_employees': 'VARCHAR',
        'part_time_employees_start': 'VARCHAR',
        'part_time_employees_added': 'VARCHAR',
        'part_time_employees_removed': 'VARCHAR',
        'part_time_employees': 'VARCHAR'
    }
)
