{# 自治体標準ODS「観光施設一覧」の生データ。
   pipelines/ods.py が対象 CSV を標準キーに正規化して data/ods/tourism.ndjson に保存する。 #}

{{ config(materialized='table') }}

select *
from read_json(
    'data/ods/tourism.ndjson',
    format='newline_delimited',
    columns={
        'municipality_code': 'VARCHAR',
        'facility_id': 'VARCHAR',
        'name': 'VARCHAR',
        'name_kana': 'VARCHAR',
        'name_en': 'VARCHAR',
        'poi_code': 'VARCHAR',
        'address': 'VARCHAR',
        'prefecture': 'VARCHAR',
        'city': 'VARCHAR',
        'building_name': 'VARCHAR',
        'postal_code': 'VARCHAR',
        'lat': 'VARCHAR',
        'lon': 'VARCHAR',
        'corporate_number': 'VARCHAR',
        'available_days': 'VARCHAR',
        'start_time': 'VARCHAR',
        'end_time': 'VARCHAR',
        'available_notes': 'VARCHAR',
        'fee': 'VARCHAR',
        'fee_details': 'VARCHAR',
        'description': 'VARCHAR',
        'description_en': 'VARCHAR',
        'access': 'VARCHAR',
        'parking': 'VARCHAR',
        'barrier_free': 'VARCHAR',
        'contact_name': 'VARCHAR',
        'contact_phone': 'VARCHAR',
        'contact_extension': 'VARCHAR',
        'image': 'VARCHAR',
        'image_license': 'VARCHAR',
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
