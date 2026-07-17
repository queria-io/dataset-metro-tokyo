{# 自治体標準ODS「医療機関一覧」の生データ。
   pipelines/ods.py が対象 CSV を標準キーに正規化して data/ods/hospital.ndjson に保存する。 #}

{{ config(materialized='table') }}

select *
from read_json(
    'data/ods/hospital.ndjson',
    format='newline_delimited',
    columns={
        'municipality_code': 'VARCHAR',
        'facility_id': 'VARCHAR',
        'name': 'VARCHAR',
        'name_kana': 'VARCHAR',
        'institution_type': 'VARCHAR',
        'address': 'VARCHAR',
        'prefecture': 'VARCHAR',
        'city': 'VARCHAR',
        'postal_code': 'VARCHAR',
        'phone_number': 'VARCHAR',
        'lat': 'VARCHAR',
        'lon': 'VARCHAR',
        'corporate_name': 'VARCHAR',
        'medical_institution_code': 'VARCHAR',
        'consultation_days': 'VARCHAR',
        'start_time': 'VARCHAR',
        'end_time': 'VARCHAR',
        'consultation_notes': 'VARCHAR',
        'after_hours': 'VARCHAR',
        'departments': 'VARCHAR',
        'beds': 'VARCHAR',
        'disaster_base': 'VARCHAR',
        'status': 'VARCHAR',
        'url': 'VARCHAR',
        'notes': 'VARCHAR',
        '_extras': 'JSON',
        '_package_id': 'VARCHAR',
        '_resource_id': 'VARCHAR',
        '_org_code': 'VARCHAR',
        '_org_title': 'VARCHAR',
        '_source_url': 'VARCHAR',
        '_fetched_at': 'VARCHAR'
    }
)
