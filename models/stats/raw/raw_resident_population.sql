{# 東京都「住民基本台帳による世帯と人口」の月次 CSV。
   pipelines/resident_population.py が 2001年1月分以降の月次ファイルを取得し、
   2種類の様式のヘッダーを共通キーに割り当てて
   data/resident_population/resident_population.ndjson に保存する。
   取り込んだ月と取得元 URL は raw_resident_population_source を参照。 #}

{{ config(materialized='table') }}

select *
from read_json(
    'data/resident_population/resident_population.ndjson',
    format='newline_delimited',
    columns={
        'year_month': 'VARCHAR',
        'area_level': 'VARCHAR',
        'area_code': 'VARCHAR',
        'area_name': 'VARCHAR',
        'population_total': 'VARCHAR',
        'population_change': 'VARCHAR',
        'japanese_total': 'VARCHAR',
        'japanese_male': 'VARCHAR',
        'japanese_female': 'VARCHAR',
        'foreign_total': 'VARCHAR',
        'foreign_male': 'VARCHAR',
        'foreign_female': 'VARCHAR',
        'household_total': 'VARCHAR',
        'household_japanese_only': 'VARCHAR',
        'household_foreign_only': 'VARCHAR',
        'household_mixed': 'VARCHAR'
    }
)
