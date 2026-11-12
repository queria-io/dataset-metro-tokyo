{# 区市町村が公表した随意契約の締結状況の生データ（1行=1契約）。
   pipelines/procurement.py が data/procurement/private_contracts.ndjson に書く。 #}

{{ config(materialized='table') }}

select *
from read_json(
    'data/procurement/private_contracts.ndjson',
    format='newline_delimited',
    columns={
        'seq_no': 'VARCHAR',
        'title': 'VARCHAR',
        'business_type': 'VARCHAR',
        'contract_amount_text': 'VARCHAR',
        'contract_amount': 'BIGINT',
        'contract_date_text': 'VARCHAR',
        'contract_date': 'VARCHAR',
        'performance_period': 'VARCHAR',
        'performance_start': 'VARCHAR',
        'performance_end': 'VARCHAR',
        'contractor': 'VARCHAR',
        'contractor_area': 'VARCHAR',
        'reason': 'VARCHAR',
        'requesting_section': 'VARCHAR',
        'category': 'VARCHAR',
        'period_label': 'VARCHAR',
        'period_start_month': 'VARCHAR',
        'period_end_month': 'VARCHAR',
        'org_code': 'VARCHAR',
        'org_name': 'VARCHAR',
        'source_resource': 'VARCHAR',
        'source_url': 'VARCHAR'
    }
)
