{# 東京都「東京の労働力」年平均の第6表（主な職業別就業者数）。
   pipelines/labour_force_by_occupation.py が各年の表の実数の行を男女 × 年 × 職業の行に分けて
   data/labour_force_by_occupation/labour_force_by_occupation.ndjson に保存する。
   同じ年の値が複数の年の表に載るので、report_year（どの年の表か）を残している。
   取得元 URL は raw_labour_force_by_occupation_source を参照。 #}

{{ config(materialized='table') }}

select *
from read_json(
    'data/labour_force_by_occupation/labour_force_by_occupation.ndjson',
    format='newline_delimited',
    columns={
        'report_year': 'VARCHAR',
        'year': 'VARCHAR',
        'sex': 'VARCHAR',
        'occupation': 'VARCHAR',
        'value': 'VARCHAR'
    }
)
