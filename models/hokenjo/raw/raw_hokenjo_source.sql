{# 取り込んだ保健所台帳の記録。台帳ごとの配布 URL・時点・行数。
   pipelines/hokenjo.py が data/hokenjo/source.ndjson に書く。 #}

{{ config(materialized='table') }}

select *
from read_json(
    'data/hokenjo/source.ndjson',
    format='newline_delimited',
    columns={
        'ledger': 'VARCHAR',
        'url': 'VARCHAR',
        'as_of': 'VARCHAR',
        'fetched_at': 'VARCHAR',
        'row_count': 'BIGINT'
    }
)
