{# 東京都「毎月勤労統計調査」年報の第12-1表・第12-2表（産業別労働異動率）。
   pipelines/labour_turnover.py が各年の年報から公表年の行（各月と年平均）を取り出し、
   横持ちの産業の列を産業ごとの行に分けて data/labour_turnover/labour_turnover.ndjson に保存する。
   取得元 URL は raw_labour_turnover_source を参照。 #}

{{ config(materialized='table') }}

select *
from read_json(
    'data/labour_turnover/labour_turnover.ndjson',
    format='newline_delimited',
    columns={
        'report_year': 'VARCHAR',
        'establishment_size': 'VARCHAR',
        'industry': 'VARCHAR',
        'year': 'VARCHAR',
        'period': 'VARCHAR',
        'hiring_rate': 'VARCHAR',
        'separation_rate': 'VARCHAR'
    }
)
