{# 東京都「東京の労働力」年平均の第8表（年齢階級・雇用形態別の役員を除く雇用者数）。
   pipelines/labour_force_by_employment_type.py が各年の表の実数の行を
   男女 × 年 × 雇用形態 × 年齢階級の行に分けて
   data/labour_force_by_employment_type/labour_force_by_employment_type.ndjson に保存する。
   同じ年の値が複数の年の表に載るので、report_year（どの年の表か）を残している。
   取得元 URL は raw_labour_force_by_employment_type_source を参照。 #}

{{ config(materialized='table') }}

select *
from read_json(
    'data/labour_force_by_employment_type/labour_force_by_employment_type.ndjson',
    format='newline_delimited',
    columns={
        'report_year': 'VARCHAR',
        'year': 'VARCHAR',
        'sex': 'VARCHAR',
        'employment_type': 'VARCHAR',
        'age_group': 'VARCHAR',
        'value': 'VARCHAR'
    }
)
