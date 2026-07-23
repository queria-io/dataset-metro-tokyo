{# 自治体標準ODS「支援制度情報」の生データ。
   pipelines/ods.py が対象 CSV を標準キーに正規化して data/ods/support_system.ndjson に保存する。 #}

{{ config(materialized='table') }}

select *
from read_json(
    'data/ods/support_system.ndjson',
    format='newline_delimited',
    columns={
        'municipality_code': 'VARCHAR',
        'organization_name': 'VARCHAR',
        'system_org': 'VARCHAR',
        'system_id': 'VARCHAR',
        'system_type': 'VARCHAR',
        'title': 'VARCHAR',
        'subtitle': 'VARCHAR',
        'target_person': 'VARCHAR',
        'target_area': 'VARCHAR',
        'summary': 'VARCHAR',
        'content': 'VARCHAR',
        'application_method': 'VARCHAR',
        'application_period': 'VARCHAR',
        'acceptance_start_date': 'VARCHAR',
        'acceptance_end_date': 'VARCHAR',
        'legal_basis': 'VARCHAR',
        'reference_url': 'VARCHAR',
        'related_systems': 'VARCHAR',
        'contact': 'VARCHAR',
        'online_application_url': 'VARCHAR',
        'keyword': 'VARCHAR',
        'published_date': 'VARCHAR',
        'contact_name': 'VARCHAR',
        'contact_phone': 'VARCHAR',
        'contact_email': 'VARCHAR',
        'contact_form_url': 'VARCHAR',
        'postal_code': 'VARCHAR',
        'contact_address': 'VARCHAR',
        'url': 'VARCHAR',
        '_extras': 'JSON',
        '_package_id': 'VARCHAR',
        '_resource_id': 'VARCHAR',
        '_org_code': 'VARCHAR',
        '_org_title': 'VARCHAR',
        '_source_url': 'VARCHAR',
        '_fetched_at': 'VARCHAR'
    }
)
