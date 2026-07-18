{# 自治体標準ODS「文化財一覧」の生データ。
   pipelines/ods.py が対象 CSV を標準キーに正規化して data/ods/cultural_property.ndjson に保存する。 #}

{{ config(materialized='table') }}

select *
from read_json(
    'data/ods/cultural_property.ndjson',
    format='newline_delimited',
    columns={
        'municipality_code': 'VARCHAR',
        'facility_id': 'VARCHAR',
        'name': 'VARCHAR',
        'name_kana': 'VARCHAR',
        'name_alias': 'VARCHAR',
        'name_en': 'VARCHAR',
        'property_class': 'VARCHAR',
        'property_type': 'VARCHAR',
        'place_name': 'VARCHAR',
        'address': 'VARCHAR',
        'prefecture': 'VARCHAR',
        'city': 'VARCHAR',
        'building_name': 'VARCHAR',
        'postal_code': 'VARCHAR',
        'phone_number': 'VARCHAR',
        'lat': 'VARCHAR',
        'lon': 'VARCHAR',
        'quantity': 'VARCHAR',
        'quantity_unit': 'VARCHAR',
        'corporate_number': 'VARCHAR',
        'owner': 'VARCHAR',
        'designated_date': 'VARCHAR',
        'available_days': 'VARCHAR',
        'start_time': 'VARCHAR',
        'end_time': 'VARCHAR',
        'available_notes': 'VARCHAR',
        'image': 'VARCHAR',
        'image_license': 'VARCHAR',
        'summary': 'VARCHAR',
        'summary_en': 'VARCHAR',
        'description': 'VARCHAR',
        'description_en': 'VARCHAR',
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
