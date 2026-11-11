{# 東京都「東京の労働力」（労働力調査結果）年平均の第1表
   （就業状態別15歳以上人口、産業別就業者数及び完全失業者数）。
   pipelines/labour_force.py が各年の表を区分 × 男女の行に分けて
   data/labour_force/labour_force.ndjson に保存する。
   取得元 URL は raw_labour_force_source を参照。 #}

{{ config(materialized='table') }}

select *
from read_json(
    'data/labour_force/labour_force.ndjson',
    format='newline_delimited',
    columns={
        'year': 'VARCHAR',
        'item': 'VARCHAR',
        'sex': 'VARCHAR',
        'value': 'VARCHAR',
        'previous_year_value': 'VARCHAR',
        'change': 'VARCHAR',
        'change_rate': 'VARCHAR'
    }
)
