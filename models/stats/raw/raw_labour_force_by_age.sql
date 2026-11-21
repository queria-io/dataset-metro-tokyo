{# 東京都「東京の労働力」年平均の第3表（年齢階級別就業状態）。
   pipelines/labour_force_by_age.py が男女計・男・女の3ファイルの実数の列を
   男女 × 年 × 年齢階級 × 区分の行に分けて
   data/labour_force_by_age/labour_force_by_age.ndjson に保存する。
   同じ年の値が複数の年の表に載るので、report_year（どの年の表か）を残している。
   取得元 URL は raw_labour_force_by_age_source を参照。 #}

{{ config(materialized='table') }}

select *
from read_json(
    'data/labour_force_by_age/labour_force_by_age.ndjson',
    format='newline_delimited',
    columns={
        'report_year': 'VARCHAR',
        'year': 'VARCHAR',
        'sex': 'VARCHAR',
        'age_group': 'VARCHAR',
        'item': 'VARCHAR',
        'value': 'VARCHAR'
    }
)
