{# 東京都「毎月勤労統計調査」年報の第13表〜第21表（規模、産業別の指数）。
   pipelines/labour_index.py が各年の年報から公表年の行（各月と年平均）を取り出し、
   横持ちの産業の列を産業ごとの行に分け、指数と前年比・前年同月比を1行にまとめて
   data/labour_index/labour_index.ndjson に保存する。取得元 URL は raw_labour_index_source を参照。 #}

{{ config(materialized='table') }}

select *
from read_json(
    'data/labour_index/labour_index.ndjson',
    format='newline_delimited',
    columns={
        'report_year': 'VARCHAR',
        'index_type': 'VARCHAR',
        'base_year': 'VARCHAR',
        'establishment_size': 'VARCHAR',
        'industry': 'VARCHAR',
        'year': 'VARCHAR',
        'period': 'VARCHAR',
        'index_value': 'VARCHAR',
        'change_rate': 'VARCHAR'
    }
)
