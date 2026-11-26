{# 東京都「東京の労働力」（労働力調査結果）四半期平均の第2表
   （就業状態、活動状態別15歳以上人口）。
   pipelines/labour_force_activity_quarterly.py が各四半期の表の四半期の行を
   男女 × 四半期 × 区分の行に分けて
   data/labour_force_activity_quarterly/labour_force_activity_quarterly.ndjson に保存する。
   各四半期の表に載る全期間分を、どの四半期の表か（report_year・report_quarter）と合わせて持つ。
   取得元 URL は raw_labour_force_activity_quarterly_source を参照。 #}

{{ config(materialized='table') }}

select *
from read_json(
    'data/labour_force_activity_quarterly/labour_force_activity_quarterly.ndjson',
    format='newline_delimited',
    columns={
        'report_year': 'VARCHAR',
        'report_quarter': 'VARCHAR',
        'year': 'VARCHAR',
        'quarter': 'VARCHAR',
        'sex': 'VARCHAR',
        'item': 'VARCHAR',
        'value': 'VARCHAR'
    }
)
