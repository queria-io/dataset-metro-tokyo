{# 東京都「東京の労働力」年平均の参考表（東京都、南関東及び全国の完全失業率）。
   pipelines/labour_force_unemployment_rate.py が各年の表の実数の行を地域 × 男女の行に分けて
   data/labour_force_unemployment_rate/labour_force_unemployment_rate.ndjson に保存する。
   同じ年の値が複数の年の表に載るので、report_year（どの年の表か）を残している。
   取得元 URL は raw_labour_force_unemployment_rate_source を参照。 #}

{{ config(materialized='table') }}

select *
from read_json(
    'data/labour_force_unemployment_rate/labour_force_unemployment_rate.ndjson',
    format='newline_delimited',
    columns={
        'report_year': 'VARCHAR',
        'year': 'VARCHAR',
        'area': 'VARCHAR',
        'sex': 'VARCHAR',
        'value': 'VARCHAR'
    }
)
