{# 東京都「外国人人口」時系列（各年1月1日現在）。
   pipelines/foreign_population.py が横持ちの CSV（列 = 和暦の年）を
   国籍・地域 × 地域 × 年 の縦持ちに直して
   data/foreign_population/foreign_population.ndjson に保存する。
   取得元 URL は raw_foreign_population_source を参照。 #}

{{ config(materialized='table') }}

select *
from read_json(
    'data/foreign_population/foreign_population.ndjson',
    format='newline_delimited',
    columns={
        'year': 'VARCHAR',
        'year_label': 'VARCHAR',
        'area_level': 'VARCHAR',
        'area_code': 'VARCHAR',
        'area_name': 'VARCHAR',
        'nationality': 'VARCHAR',
        'population': 'VARCHAR'
    }
)
