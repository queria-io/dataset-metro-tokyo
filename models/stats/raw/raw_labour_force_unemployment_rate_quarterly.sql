{# 東京都「東京の労働力」四半期平均の参考表（東京都、南関東及び全国の完全失業率）。
   pipelines/labour_force_unemployment_rate_quarterly.py が各四半期の表の四半期の行を地域 × 男女の行に分けて
   data/labour_force_unemployment_rate_quarterly/labour_force_unemployment_rate_quarterly.ndjson に保存する。
   同じ四半期の値が複数の表に載るので、report_year・report_quarter（どの年・四半期の表か）を残している。
   取得元 URL は raw_labour_force_unemployment_rate_quarterly_source を参照。 #}

{{ config(materialized='table') }}

select *
from read_json(
    'data/labour_force_unemployment_rate_quarterly/labour_force_unemployment_rate_quarterly.ndjson',
    format='newline_delimited',
    columns={
        'report_year': 'VARCHAR',
        'report_quarter': 'VARCHAR',
        'year': 'VARCHAR',
        'quarter': 'VARCHAR',
        'area': 'VARCHAR',
        'sex': 'VARCHAR',
        'value': 'VARCHAR'
    }
)
