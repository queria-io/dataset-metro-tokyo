{# 東京都保健医療局「食品関係営業台帳」（許可・届出）の生データ。
   pipelines/hokenjo.py が配布ページから CSV のリンクを解決し、標準キーに
   正規化した NDJSON を data/hokenjo/food_establishment.ndjson に書く。
   取り込んだ台帳と時点は raw_hokenjo_source を参照。 #}

{{ config(materialized='table') }}

select *
from read_json(
    'data/hokenjo/food_establishment.ndjson',
    format='newline_delimited',
    columns={
        'permit_type': 'VARCHAR',
        'name': 'VARCHAR',
        'address': 'VARCHAR',
        'business_type': 'VARCHAR',
        'application_type': 'VARCHAR',
        'phone_number': 'VARCHAR',
        'permit_date': 'VARCHAR',
        'operator_name': 'VARCHAR',
        'operator_address': 'VARCHAR',
        'operator_phone_number': 'VARCHAR',
        'representative_name': 'VARCHAR',
        '_org_code': 'VARCHAR',
        '_org_title': 'VARCHAR',
        '_source_url': 'VARCHAR'
    }
)
