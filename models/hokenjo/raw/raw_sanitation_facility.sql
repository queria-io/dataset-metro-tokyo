{# 東京都保健医療局「環境衛生施設台帳」（理容所・美容所・旅館・クリーニング所）の生データ。
   pipelines/hokenjo.py が配布ページから CSV のリンクを解決し、標準キーに
   正規化した NDJSON を data/hokenjo/sanitation_facility.ndjson に書く。 #}

{{ config(materialized='table') }}

select *
from read_json(
    'data/hokenjo/sanitation_facility.ndjson',
    format='newline_delimited',
    columns={
        'facility_type': 'VARCHAR',
        'permit_number': 'VARCHAR',
        'business_form': 'VARCHAR',
        'name': 'VARCHAR',
        'address': 'VARCHAR',
        'building': 'VARCHAR',
        'phone_number': 'VARCHAR',
        'permit_date': 'VARCHAR',
        'operator_name': 'VARCHAR',
        'operator_address': 'VARCHAR',
        'operator_building': 'VARCHAR',
        'operator_phone_number': 'VARCHAR',
        'representative_name': 'VARCHAR',
        '_org_code': 'VARCHAR',
        '_org_title': 'VARCHAR',
        '_source_url': 'VARCHAR'
    }
)
