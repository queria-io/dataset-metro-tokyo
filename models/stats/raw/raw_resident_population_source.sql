{# 住民基本台帳による世帯と人口の取得元（1行=1月分）。
   pipelines/resident_population.py が data/resident_population/source.ndjson に保存する。 #}

{{ config(materialized='table') }}

select *
from read_json(
    'data/resident_population/source.ndjson',
    format='newline_delimited',
    columns={
        'year_month': 'VARCHAR',
        'url': 'VARCHAR',
        'fetched_at': 'VARCHAR',
        'status': 'VARCHAR',
        'row_count': 'VARCHAR'
    }
)
