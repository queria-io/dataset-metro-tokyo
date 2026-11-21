{# 東京都「第3次産業活動指数」（月次）。
   pipelines/tertiary_activity_index.py が原指数と季節調整済指数の CSV の横持ち（列 = 月）を
   業種 × 月 × 指数の種類の縦持ちに直して data/tertiary_activity_index/tertiary_activity_index.ndjson
   に保存する。取得元 URL は raw_tertiary_activity_index_source を参照。 #}

{{ config(materialized='table') }}

select *
from read_json(
    'data/tertiary_activity_index/tertiary_activity_index.ndjson',
    format='newline_delimited',
    columns={
        'index_type': 'VARCHAR',
        'item_class': 'VARCHAR',
        'item_code': 'VARCHAR',
        'item_name': 'VARCHAR',
        'item_name_en': 'VARCHAR',
        'weight': 'VARCHAR',
        'year': 'VARCHAR',
        'month': 'VARCHAR',
        'value': 'VARCHAR'
    }
)
