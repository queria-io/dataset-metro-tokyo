{# 自治体標準ODS「子育て施設一覧」の生データ。
   pipelines/ods.py が対象 CSV を標準キーに正規化して data/ods/preschool.ndjson に保存する。 #}

{{ config(materialized='table') }}

select *
from read_json(
    'data/ods/preschool.ndjson',
    format='newline_delimited',
    columns={
        'municipality_code': 'VARCHAR',
        'facility_id': 'VARCHAR',
        'name': 'VARCHAR',
        'name_kana': 'VARCHAR',
        'facility_type': 'VARCHAR',
        'address': 'VARCHAR',
        'prefecture': 'VARCHAR',
        'city': 'VARCHAR',
        'postal_code': 'VARCHAR',
        'phone_number': 'VARCHAR',
        'lat': 'VARCHAR',
        'lon': 'VARCHAR',
        'access': 'VARCHAR',
        'parking': 'VARCHAR',
        'corporate_name': 'VARCHAR',
        'capacity': 'VARCHAR',
        'age_range': 'VARCHAR',
        'available_days': 'VARCHAR',
        'start_time': 'VARCHAR',
        'end_time': 'VARCHAR',
        'available_notes': 'VARCHAR',
        'temporary_care': 'VARCHAR',
        'sick_care': 'VARCHAR',
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
