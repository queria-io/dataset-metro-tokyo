{# 東京都「毎月勤労統計調査」年報の第5表（夏・冬季賞与の産業別支給状況）。
   pipelines/labour_bonus.py が各年の年報から産業ごとの行を取り出し、年報の公表年を付けて
   data/labour_bonus/labour_bonus.ndjson に保存する。
   取得元 URL は raw_labour_bonus_source を参照。 #}

{{ config(materialized='table') }}

select *
from read_json(
    'data/labour_bonus/labour_bonus.ndjson',
    format='newline_delimited',
    columns={
        'report_year': 'VARCHAR',
        'establishment_size': 'VARCHAR',
        'industry': 'VARCHAR',
        'year': 'VARCHAR',
        'summer_bonus': 'VARCHAR',
        'summer_bonus_change_rate': 'VARCHAR',
        'summer_paying_establishment_ratio': 'VARCHAR',
        'summer_receiving_employee_ratio': 'VARCHAR',
        'summer_bonus_months': 'VARCHAR',
        'summer_bonus_months_change': 'VARCHAR',
        'winter_bonus': 'VARCHAR',
        'winter_bonus_change_rate': 'VARCHAR',
        'winter_paying_establishment_ratio': 'VARCHAR',
        'winter_receiving_employee_ratio': 'VARCHAR',
        'winter_bonus_months': 'VARCHAR',
        'winter_bonus_months_change': 'VARCHAR'
    }
)
