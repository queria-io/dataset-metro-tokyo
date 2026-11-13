{# 東京都「東京の労働力」年平均の第2表（就業状態、活動状態別15歳以上人口）。
   pipelines/labour_force_activity.py が各年の表の実数の行を男女 × 年 × 区分の行に分けて
   data/labour_force_activity/labour_force_activity.ndjson に保存する。
   同じ年の値が複数の年の表に載るので、report_year（どの年の表か）を残している。
   取得元 URL は raw_labour_force_activity_source を参照。 #}

{{ config(materialized='table') }}

select *
from read_json(
    'data/labour_force_activity/labour_force_activity.ndjson',
    format='newline_delimited',
    columns={
        'report_year': 'VARCHAR',
        'year': 'VARCHAR',
        'sex': 'VARCHAR',
        'item': 'VARCHAR',
        'value': 'VARCHAR'
    }
)
